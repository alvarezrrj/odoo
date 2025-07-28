# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
Module Analyzer - Analyzes differences between Odoo module versions
"""

import os
import ast
import json
import logging
from collections import defaultdict
from pathlib import Path

_logger = logging.getLogger(__name__)


class ModuleAnalyzer:
    """Analyzes differences between two versions of an Odoo module."""
    
    def __init__(self, source_path, target_path):
        """
        Initialize the analyzer with source and target module paths.
        
        :param source_path: Path to the old version of the module
        :param target_path: Path to the new version of the module
        """
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.changes = defaultdict(list)
        
    def analyze(self):
        """
        Perform complete analysis of module differences.
        
        :return: Dictionary containing all detected changes
        """
        _logger.info(f"Analyzing differences between {self.source_path} and {self.target_path}")
        
        # Analyze manifest changes
        self.analyze_manifest()
        
        # Analyze model changes
        self.analyze_models()
        
        # Analyze data files
        self.analyze_data_files()
        
        # Analyze views
        self.analyze_views()
        
        # Analyze security files
        self.analyze_security()
        
        return dict(self.changes)
    
    def analyze_manifest(self):
        """Analyze changes in __manifest__.py files."""
        source_manifest = self._load_manifest(self.source_path)
        target_manifest = self._load_manifest(self.target_path)
        
        if not source_manifest or not target_manifest:
            return
        
        # Check version changes
        source_version = source_manifest.get('version', '1.0.0')
        target_version = target_manifest.get('version', '1.0.0')
        
        if source_version != target_version:
            self.changes['manifest'].append({
                'type': 'version_change',
                'old_version': source_version,
                'new_version': target_version
            })
        
        # Check dependency changes
        source_deps = set(source_manifest.get('depends', []))
        target_deps = set(target_manifest.get('depends', []))
        
        added_deps = target_deps - source_deps
        removed_deps = source_deps - target_deps
        
        if added_deps:
            self.changes['manifest'].append({
                'type': 'dependencies_added',
                'dependencies': list(added_deps)
            })
            
        if removed_deps:
            self.changes['manifest'].append({
                'type': 'dependencies_removed',
                'dependencies': list(removed_deps)
            })
    
    def analyze_models(self):
        """Analyze changes in model definitions."""
        source_models = self._extract_models(self.source_path)
        target_models = self._extract_models(self.target_path)
        
        # Find new models
        new_models = set(target_models.keys()) - set(source_models.keys())
        for model in new_models:
            self.changes['models'].append({
                'type': 'model_added',
                'model': model,
                'fields': target_models[model]['fields']
            })
        
        # Find removed models
        removed_models = set(source_models.keys()) - set(target_models.keys())
        for model in removed_models:
            self.changes['models'].append({
                'type': 'model_removed',
                'model': model
            })
        
        # Analyze field changes in existing models
        common_models = set(source_models.keys()) & set(target_models.keys())
        for model in common_models:
            self._analyze_model_fields(model, source_models[model], target_models[model])
    
    def _analyze_model_fields(self, model_name, source_model, target_model):
        """Analyze field changes within a model."""
        source_fields = source_model['fields']
        target_fields = target_model['fields']
        
        # Find new fields
        new_fields = set(target_fields.keys()) - set(source_fields.keys())
        for field in new_fields:
            self.changes['fields'].append({
                'type': 'field_added',
                'model': model_name,
                'field': field,
                'field_type': target_fields[field].get('type'),
                'attributes': target_fields[field]
            })
        
        # Find removed fields
        removed_fields = set(source_fields.keys()) - set(target_fields.keys())
        for field in removed_fields:
            self.changes['fields'].append({
                'type': 'field_removed',
                'model': model_name,
                'field': field,
                'old_type': source_fields[field].get('type')
            })
        
        # Find modified fields
        common_fields = set(source_fields.keys()) & set(target_fields.keys())
        for field in common_fields:
            source_field = source_fields[field]
            target_field = target_fields[field]
            
            # Check for type changes
            if source_field.get('type') != target_field.get('type'):
                self.changes['fields'].append({
                    'type': 'field_type_changed',
                    'model': model_name,
                    'field': field,
                    'old_type': source_field.get('type'),
                    'new_type': target_field.get('type')
                })
            
            # Check for attribute changes
            for attr in ['required', 'readonly', 'index', 'ondelete', 'comodel_name']:
                if source_field.get(attr) != target_field.get(attr):
                    self.changes['fields'].append({
                        'type': 'field_attribute_changed',
                        'model': model_name,
                        'field': field,
                        'attribute': attr,
                        'old_value': source_field.get(attr),
                        'new_value': target_field.get(attr)
                    })
    
    def analyze_data_files(self):
        """Analyze changes in data files (XML/CSV)."""
        source_data = self._extract_data_files(self.source_path)
        target_data = self._extract_data_files(self.target_path)
        
        # Find new data files
        new_files = set(target_data.keys()) - set(source_data.keys())
        for filename in new_files:
            self.changes['data'].append({
                'type': 'data_file_added',
                'file': filename,
                'records': len(target_data[filename])
            })
        
        # Find removed data files
        removed_files = set(source_data.keys()) - set(target_data.keys())
        for filename in removed_files:
            self.changes['data'].append({
                'type': 'data_file_removed',
                'file': filename
            })
        
        # Analyze changes in existing data files
        common_files = set(source_data.keys()) & set(target_data.keys())
        for filename in common_files:
            self._analyze_data_file_changes(filename, source_data[filename], target_data[filename])
    
    def analyze_views(self):
        """Analyze changes in view definitions."""
        source_views = self._extract_views(self.source_path)
        target_views = self._extract_views(self.target_path)
        
        # Find new views
        new_views = set(target_views.keys()) - set(source_views.keys())
        for view_id in new_views:
            self.changes['views'].append({
                'type': 'view_added',
                'view_id': view_id,
                'view_type': target_views[view_id].get('type'),
                'model': target_views[view_id].get('model')
            })
        
        # Find removed views
        removed_views = set(source_views.keys()) - set(target_views.keys())
        for view_id in removed_views:
            self.changes['views'].append({
                'type': 'view_removed',
                'view_id': view_id
            })
    
    def analyze_security(self):
        """Analyze changes in security files."""
        source_security = self._extract_security(self.source_path)
        target_security = self._extract_security(self.target_path)
        
        if source_security != target_security:
            self.changes['security'].append({
                'type': 'security_changed',
                'source_rules': len(source_security),
                'target_rules': len(target_security)
            })
    
    def _load_manifest(self, module_path):
        """Load __manifest__.py file."""
        manifest_path = module_path / '__manifest__.py'
        if not manifest_path.exists():
            manifest_path = module_path / '__openerp__.py'
        
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return ast.literal_eval(content)
            except Exception as e:
                _logger.error(f"Error reading manifest {manifest_path}: {e}")
        return None
    
    def _extract_models(self, module_path):
        """Extract model definitions from Python files."""
        models = {}
        models_path = module_path / 'models'
        
        if not models_path.exists():
            return models
        
        for py_file in models_path.glob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        model_info = self._extract_model_info(node)
                        if model_info:
                            models[model_info['name']] = model_info
            except Exception as e:
                _logger.error(f"Error parsing {py_file}: {e}")
        
        return models
    
    def _extract_model_info(self, class_node):
        """Extract model information from an AST class node."""
        model_info = {
            'name': None,
            'table': None,
            'inherit': None,
            'fields': {}
        }
        
        # Look for _name, _table, _inherit attributes
        for node in ast.walk(class_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == '_name' and isinstance(node.value, ast.Constant):
                            model_info['name'] = node.value.value
                        elif target.id == '_table' and isinstance(node.value, ast.Constant):
                            model_info['table'] = node.value.value
                        elif target.id == '_inherit' and isinstance(node.value, ast.Constant):
                            model_info['inherit'] = node.value.value
            
            # Extract field definitions
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        field_info = self._extract_field_info(node.value)
                        if field_info:
                            model_info['fields'][target.id] = field_info
        
        return model_info if model_info['name'] else None
    
    def _extract_field_info(self, node):
        """Extract field information from an AST node."""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ['Char', 'Text', 'Integer', 'Float', 'Boolean', 
                                  'Date', 'Datetime', 'Selection', 'Many2one', 
                                  'One2many', 'Many2many', 'Binary', 'Html']:
                field_info = {'type': node.func.attr.lower()}
                
                # Extract keyword arguments
                for keyword in node.keywords:
                    if isinstance(keyword.value, ast.Constant):
                        field_info[keyword.arg] = keyword.value.value
                    elif isinstance(keyword.value, ast.Name):
                        field_info[keyword.arg] = keyword.value.id
                
                return field_info
        return None
    
    def _extract_data_files(self, module_path):
        """Extract data file information."""
        data_files = {}
        data_path = module_path / 'data'
        
        if data_path.exists():
            for data_file in data_path.glob('*.xml'):
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Simple count of record tags
                    record_count = content.count('<record')
                    data_files[data_file.name] = {'records': record_count}
                except Exception as e:
                    _logger.error(f"Error reading data file {data_file}: {e}")
        
        return data_files
    
    def _extract_views(self, module_path):
        """Extract view definitions."""
        views = {}
        views_path = module_path / 'views'
        
        if views_path.exists():
            for view_file in views_path.glob('*.xml'):
                try:
                    with open(view_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Simple extraction of view IDs and types
                    # In a real implementation, you'd use XML parsing
                    import re
                    view_records = re.findall(r'<record[^>]*id="([^"]*)"[^>]*model="ir\.ui\.view"', content)
                    for view_id in view_records:
                        views[view_id] = {'type': 'unknown', 'model': 'unknown'}
                except Exception as e:
                    _logger.error(f"Error reading view file {view_file}: {e}")
        
        return views
    
    def _extract_security(self, module_path):
        """Extract security information."""
        security_files = []
        security_path = module_path / 'security'
        
        if security_path.exists():
            for security_file in security_path.glob('*.csv'):
                security_files.append(security_file.name)
        
        return security_files
    
    def _analyze_data_file_changes(self, filename, source_data, target_data):
        """Analyze changes in a specific data file."""
        if source_data['records'] != target_data['records']:
            self.changes['data'].append({
                'type': 'data_records_changed',
                'file': filename,
                'old_count': source_data['records'],
                'new_count': target_data['records']
            })
    
    def export_analysis(self, output_file):
        """Export analysis results to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.changes), f, indent=2)
        _logger.info(f"Analysis exported to {output_file}")


def analyze_module_changes(source_path, target_path, output_file=None):
    """
    Convenience function to analyze module changes.
    
    :param source_path: Path to source module version
    :param target_path: Path to target module version
    :param output_file: Optional output file for analysis results
    :return: Analysis results dictionary
    """
    analyzer = ModuleAnalyzer(source_path, target_path)
    results = analyzer.analyze()
    
    if output_file:
        analyzer.export_analysis(output_file)
    
    return results