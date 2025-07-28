# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
Migration Script Generator - Generates OpenUpgrade migration scripts based on analysis
"""

import os
import logging
from pathlib import Path
from jinja2 import Template

_logger = logging.getLogger(__name__)


class MigrationScriptGenerator:
    """Generates OpenUpgrade migration scripts based on module analysis."""
    
    def __init__(self, module_name, version, analysis_results):
        """
        Initialize the generator.
        
        :param module_name: Name of the module
        :param version: Target version
        :param analysis_results: Results from ModuleAnalyzer
        """
        self.module_name = module_name
        self.version = version
        self.analysis = analysis_results
        self.scripts = {}
        
    def generate_scripts(self):
        """
        Generate all migration scripts.
        
        :return: Dictionary containing script contents
        """
        _logger.info(f"Generating migration scripts for {self.module_name} version {self.version}")
        
        # Generate pre-migration script
        self.scripts['pre-migration.py'] = self._generate_pre_migration()
        
        # Generate post-migration script
        self.scripts['post-migration.py'] = self._generate_post_migration()
        
        # Generate end-migration script
        self.scripts['end-migration.py'] = self._generate_end_migration()
        
        return self.scripts
    
    def _generate_pre_migration(self):
        """Generate pre-migration script."""
        script_content = f"""# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

\"\"\"
Pre-migration script for {self.module_name} {self.version}
\"\"\"

import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    \"\"\"
    Pre-migration tasks for {self.module_name} {self.version}
    \"\"\"
    cr = env.cr
    
    # Field renames
    # openupgrade.rename_fields(env, [
    #     ('model.name', 'old_field', 'new_field'),
    # ])
    
    # Table renames
    # openupgrade.rename_tables(cr, [
    #     ('old_table', 'new_table'),
    # ])
    
    # Model renames
    # openupgrade.rename_models(cr, [
    #     ('old.model', 'new.model'),
    # ])
    
    # Column renames
    # openupgrade.rename_columns(cr, 'table_name', {{
    #     'old_column': 'new_column',
    # }})
    
    _logger.info("Pre-migration completed successfully")
"""
        return script_content
    
    def _generate_post_migration(self):
        """Generate post-migration script."""
        script_content = f"""# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

\"\"\"
Post-migration script for {self.module_name} {self.version}
\"\"\"

import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    \"\"\"
    Post-migration tasks for {self.module_name} {self.version}
    \"\"\"
    cr = env.cr
    
    # Set default values for new fields
    # cr.execute(\"\"\"
    #     UPDATE table_name 
    #     SET new_field = 'default_value' 
    #     WHERE new_field IS NULL
    # \"\"\")
    
    # Data migrations
    # cr.execute(\"\"\"
    #     UPDATE table_name 
    #     SET field = CASE 
    #         WHEN field = 'old_value' THEN 'new_value'
    #         ELSE field 
    #     END
    # \"\"\")
    
    # Update module dependencies if needed
    # openupgrade.update_module_dependencies(cr, '{self.module_name}', 
    #     old_dependencies=['old_dep'],
    #     new_dependencies=['new_dep']
    # )
    
    # Clean up obsolete records
    # openupgrade.delete_records_safely_by_xml_id(env, [
    #     '{self.module_name}.obsolete_record_id',
    # ])
    
    _logger.info("Post-migration completed successfully")
"""
        return script_content
    
    def _generate_end_migration(self):
        """Generate end-migration script."""
        script_content = f"""# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

\"\"\"
End-migration script for {self.module_name} {self.version}
\"\"\"

import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    \"\"\"
    End-migration tasks for {self.module_name} {self.version}
    \"\"\"
    cr = env.cr
    
    # Add missing indexes
    # openupgrade.add_missing_indexes(cr, {{
    #     'table_name': ['column1', 'column2']
    # }})
    
    # Ensure foreign key constraints
    # openupgrade.ensure_foreign_key_constraints(cr, [
    #     ('table', 'column', 'ref_table', 'ref_column', 'cascade'),
    # ])
    
    # Clean up orphaned records
    # openupgrade.cleanup_orphaned_records(cr, 
    #     'table_with_fk', 'fk_field', 'ref_table', 'id')
    
    # Update module version in database
    module_record = env.ref('base.module_{self.module_name}', raise_if_not_found=False)
    if module_record:
        module_record.write({{'latest_version': '{self.version}'}})
    
    _logger.info("End-migration completed successfully")
"""
        return script_content
    
    def save_scripts(self, output_dir):
        """
        Save generated scripts to files.
        
        :param output_dir: Output directory path
        """
        output_path = Path(output_dir) / self.module_name / self.version
        output_path.mkdir(parents=True, exist_ok=True)
        
        for filename, content in self.scripts.items():
            script_path = output_path / filename
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            _logger.info(f"Saved migration script: {script_path}")
    
    def generate_summary(self):
        """Generate a summary of migration steps."""
        summary = []
        summary.append(f"Migration Summary for {self.module_name} {self.version}")
        summary.append("=" * 50)
        summary.append("")
        
        # Manifest changes
        manifest_changes = self.analysis.get('manifest', [])
        if manifest_changes:
            summary.append("Manifest Changes:")
            for change in manifest_changes:
                if change['type'] == 'version_change':
                    summary.append(f"  - Version: {change['old_version']} → {change['new_version']}")
                elif change['type'] == 'dependencies_added':
                    summary.append(f"  - Added dependencies: {', '.join(change['dependencies'])}")
                elif change['type'] == 'dependencies_removed':
                    summary.append(f"  - Removed dependencies: {', '.join(change['dependencies'])}")
            summary.append("")
        
        # Model changes
        model_changes = self.analysis.get('models', [])
        if model_changes:
            summary.append("Model Changes:")
            for change in model_changes:
                if change['type'] == 'model_added':
                    summary.append(f"  - Added model: {change['model']}")
                elif change['type'] == 'model_removed':
                    summary.append(f"  - Removed model: {change['model']}")
            summary.append("")
        
        # Field changes
        field_changes = self.analysis.get('fields', [])
        if field_changes:
            summary.append("Field Changes:")
            for change in field_changes:
                if change['type'] == 'field_added':
                    summary.append(f"  - Added field: {change['model']}.{change['field']} ({change.get('field_type', 'unknown')})")
                elif change['type'] == 'field_removed':
                    summary.append(f"  - Removed field: {change['model']}.{change['field']}")
                elif change['type'] == 'field_type_changed':
                    summary.append(f"  - Type changed: {change['model']}.{change['field']} ({change['old_type']} → {change['new_type']})")
            summary.append("")
        
        # Manual steps
        manual_steps = self._identify_manual_steps()
        if manual_steps:
            summary.append("Manual Migration Steps Required:")
            for step in manual_steps:
                summary.append(f"  - {step}")
            summary.append("")
        
        summary.append("Generated Scripts:")
        summary.append("  - pre-migration.py: Handles structural changes before module update")
        summary.append("  - post-migration.py: Handles data migrations after module update")
        summary.append("  - end-migration.py: Handles cleanup and final tasks")
        
        return "\n".join(summary)
    
    def _identify_manual_steps(self):
        """Identify steps that require manual intervention."""
        manual_steps = []
        
        # Check for complex field type changes
        for change in self.analysis.get('fields', []):
            if change['type'] == 'field_type_changed':
                old_type = change.get('old_type', '').lower()
                new_type = change.get('new_type', '').lower()
                
                # Complex conversions that need manual handling
                if (old_type in ['selection', 'many2one'] and new_type in ['char', 'text']) or \
                   (old_type in ['char', 'text'] and new_type in ['selection', 'many2one']):
                    manual_steps.append(
                        f"Review data conversion for {change['model']}.{change['field']} "
                        f"({old_type} → {new_type})"
                    )
        
        # Check for removed models
        for change in self.analysis.get('models', []):
            if change['type'] == 'model_removed':
                manual_steps.append(
                    f"Handle data from removed model {change['model']} - "
                    f"consider archiving or migrating to another model"
                )
        
        # Check for removed fields
        for change in self.analysis.get('fields', []):
            if change['type'] == 'field_removed':
                manual_steps.append(
                    f"Review data handling for removed field {change['model']}.{change['field']}"
                )
        
        return manual_steps


def generate_migration_scripts(module_name, version, analysis_results, output_dir=None):
    """
    Convenience function to generate migration scripts.
    
    :param module_name: Name of the module
    :param version: Target version
    :param analysis_results: Results from ModuleAnalyzer
    :param output_dir: Optional output directory
    :return: Generated scripts and summary
    """
    generator = MigrationScriptGenerator(module_name, version, analysis_results)
    scripts = generator.generate_scripts()
    summary = generator.generate_summary()
    
    if output_dir:
        generator.save_scripts(output_dir)
    
    return scripts, summary