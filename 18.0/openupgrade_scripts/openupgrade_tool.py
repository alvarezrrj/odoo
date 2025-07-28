#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
OpenUpgrade Migration Tool - Command line interface for generating migration scripts
"""

import argparse
import sys
import logging
from pathlib import Path

# Add the current directory to the Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from module_analyzer import analyze_module_changes
from migration_generator import generate_migration_scripts

_logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def analyze_command(args):
    """Handle the analyze command."""
    _logger.info(f"Analyzing module changes from {args.source} to {args.target}")
    
    source_path = Path(args.source)
    target_path = Path(args.target)
    
    if not source_path.exists():
        _logger.error(f"Source path does not exist: {source_path}")
        return 1
    
    if not target_path.exists():
        _logger.error(f"Target path does not exist: {target_path}")
        return 1
    
    # Perform analysis
    results = analyze_module_changes(source_path, target_path, args.output)
    
    # Print summary
    print("\nAnalysis Summary:")
    print("=" * 50)
    
    if results.get('manifest'):
        print(f"Manifest changes: {len(results['manifest'])}")
    if results.get('models'):
        print(f"Model changes: {len(results['models'])}")
    if results.get('fields'):
        print(f"Field changes: {len(results['fields'])}")
    if results.get('data'):
        print(f"Data file changes: {len(results['data'])}")
    if results.get('views'):
        print(f"View changes: {len(results['views'])}")
    if results.get('security'):
        print(f"Security changes: {len(results['security'])}")
    
    print(f"\nAnalysis completed. Results saved to: {args.output}")
    return 0


def generate_command(args):
    """Handle the generate command."""
    _logger.info(f"Generating migration scripts for {args.module} version {args.version}")
    
    analysis_file = Path(args.analysis)
    if not analysis_file.exists():
        _logger.error(f"Analysis file does not exist: {analysis_file}")
        return 1
    
    # Load analysis results
    import json
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)
    
    # Generate scripts
    scripts, summary = generate_migration_scripts(
        args.module, args.version, analysis_results, args.output
    )
    
    # Print summary
    print("\nMigration Scripts Generated:")
    print("=" * 50)
    print(summary)
    
    if args.output:
        output_dir = Path(args.output) / args.module / args.version
        print(f"\nScripts saved to: {output_dir}")
        for script_name in scripts.keys():
            print(f"  - {script_name}")
    
    return 0


def full_command(args):
    """Handle the full command (analyze + generate)."""
    _logger.info(f"Running full migration for {args.module} from {args.source} to {args.target}")
    
    # Step 1: Analyze
    analysis_results = analyze_module_changes(args.source, args.target)
    
    # Step 2: Generate
    scripts, summary = generate_migration_scripts(
        args.module, args.version, analysis_results, args.output
    )
    
    # Print results
    print("\nFull Migration Analysis and Script Generation:")
    print("=" * 60)
    print(summary)
    
    if args.output:
        output_dir = Path(args.output) / args.module / args.version
        print(f"\nScripts saved to: {output_dir}")
        for script_name in scripts.keys():
            print(f"  - {script_name}")
    
    return 0


def create_example_command(args):
    """Handle the create-example command."""
    _logger.info(f"Creating example migration scripts for {args.module}")
    
    # Create example analysis results
    example_analysis = {
        'manifest': [
            {
                'type': 'version_change',
                'old_version': '1.0.0',
                'new_version': '1.1.0'
            },
            {
                'type': 'dependencies_added',
                'dependencies': ['base_automation']
            }
        ],
        'models': [
            {
                'type': 'model_added',
                'model': f'{args.module}.new_model',
                'fields': {'name': {'type': 'char'}, 'active': {'type': 'boolean'}}
            }
        ],
        'fields': [
            {
                'type': 'field_added',
                'model': f'{args.module}.existing_model',
                'field': 'new_field',
                'field_type': 'char'
            },
            {
                'type': 'field_removed',
                'model': f'{args.module}.existing_model',
                'field': 'old_field',
                'old_type': 'text'
            },
            {
                'type': 'field_type_changed',
                'model': f'{args.module}.existing_model',
                'field': 'changed_field',
                'old_type': 'char',
                'new_type': 'text'
            }
        ],
        'data': [
            {
                'type': 'data_file_added',
                'file': 'new_data.xml',
                'records': 5
            }
        ],
        'views': [
            {
                'type': 'view_added',
                'view_id': f'{args.module}_new_view',
                'view_type': 'form',
                'model': f'{args.module}.new_model'
            }
        ]
    }
    
    # Generate scripts
    scripts, summary = generate_migration_scripts(
        args.module, args.version, example_analysis, args.output
    )
    
    print("\nExample Migration Scripts Created:")
    print("=" * 50)
    print(summary)
    
    if args.output:
        output_dir = Path(args.output) / args.module / args.version
        print(f"\nExample scripts saved to: {output_dir}")
        for script_name in scripts.keys():
            print(f"  - {script_name}")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='OpenUpgrade Migration Tool for Odoo 18.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze changes between two module versions
  %(prog)s analyze --source /path/to/old/module --target /path/to/new/module --output analysis.json
  
  # Generate migration scripts from analysis
  %(prog)s generate --module my_module --version 1.1.0 --analysis analysis.json --output ./migrations/
  
  # Do both analyze and generate in one step
  %(prog)s full --module my_module --version 1.1.0 --source /path/to/old/module --target /path/to/new/module --output ./migrations/
  
  # Create example migration scripts
  %(prog)s create-example --module my_module --version 1.1.0 --output ./migrations/
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze module changes')
    analyze_parser.add_argument('--source', required=True,
                               help='Path to source (old) module version')
    analyze_parser.add_argument('--target', required=True,
                               help='Path to target (new) module version')
    analyze_parser.add_argument('--output', required=True,
                               help='Output file for analysis results (JSON)')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate migration scripts')
    generate_parser.add_argument('--module', required=True,
                                help='Module name')
    generate_parser.add_argument('--version', required=True,
                                help='Target version')
    generate_parser.add_argument('--analysis', required=True,
                                help='Analysis results file (JSON)')
    generate_parser.add_argument('--output', required=True,
                                help='Output directory for migration scripts')
    
    # Full command
    full_parser = subparsers.add_parser('full', help='Analyze and generate in one step')
    full_parser.add_argument('--module', required=True,
                            help='Module name')
    full_parser.add_argument('--version', required=True,
                            help='Target version')
    full_parser.add_argument('--source', required=True,
                            help='Path to source (old) module version')
    full_parser.add_argument('--target', required=True,
                            help='Path to target (new) module version')
    full_parser.add_argument('--output', required=True,
                            help='Output directory for migration scripts')
    
    # Create example command
    example_parser = subparsers.add_parser('create-example', help='Create example migration scripts')
    example_parser.add_argument('--module', required=True,
                               help='Module name')
    example_parser.add_argument('--version', default='1.1.0',
                               help='Target version (default: 1.1.0)')
    example_parser.add_argument('--output', required=True,
                               help='Output directory for migration scripts')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    setup_logging(args.verbose)
    
    # Execute the appropriate command
    if args.command == 'analyze':
        return analyze_command(args)
    elif args.command == 'generate':
        return generate_command(args)
    elif args.command == 'full':
        return full_command(args)
    elif args.command == 'create-example':
        return create_example_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())