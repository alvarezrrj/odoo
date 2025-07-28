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
        template = Template("""# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

\"\"\"
Pre-migration script for {{ module_name }} {{ version }}
\"\"\"

import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    \"\"\"
    Pre-migration tasks for {{ module_name }} {{ version }}
    \"\"\"
    cr = env.cr
    
{% if field_renames %}
    # Field renames
{% for change in field_renames %}
    openupgrade.rename_fields(env, [
        ('{{ change.model }}', '{{ change.field }}', '{{ change.new_field }}'),
    ])
{% endfor %}

{% endif %}
{% if table_renames %}
    # Table renames
    openupgrade.rename_tables(cr, [
{% for change in table_renames %}
        ('{{ change.old_table }}', '{{ change.new_table }}'),
{% endfor %}
    ])

{% endif %}
{% if model_renames %}
    # Model renames
    openupgrade.rename_models(cr, [
{% for change in model_renames %}
        ('{{ change.old_model }}', '{{ change.new_model }}'),
{% endfor %}
    ])

{% endif %}
{% if column_renames %}
    # Column renames
{% for change in column_renames %}
    openupgrade.rename_columns(cr, '{{ change.table }}', {
        '{{ change.old_column }}': '{{ change.new_column }}',
    })
{% endfor %}

{% endif %}
{% if field_type_changes %}
    # Field type conversions (prepare for conversion)
{% for change in field_type_changes %}
    # Prepare field {{ change.field }} in model {{ change.model }} for type change
    # from {{ change.old_type }} to {{ change.new_type }}
    if openupgrade.column_exists(cr, '{{ change.model|replace(".", "_") }}', '{{ change.field }}'):
        cr.execute("""
            ALTER TABLE {{ change.model|replace(".", "_") }} 
            ADD COLUMN {{ change.field }}_new TEXT
        """)
{% endfor %}

{% endif %}
""")
        
        # Extract relevant changes for pre-migration
        field_renames = [c for c in self.analysis.get('fields', []) if c['type'] == 'field_renamed']
        table_renames = [c for c in self.analysis.get('models', []) if c['type'] == 'table_renamed']
        model_renames = [c for c in self.analysis.get('models', []) if c['type'] == 'model_renamed']
        column_renames = [c for c in self.analysis.get('fields', []) if c['type'] == 'column_renamed']
        field_type_changes = [c for c in self.analysis.get('fields', []) if c['type'] == 'field_type_changed']
        
        return template.render(
            module_name=self.module_name,
            version=self.version,
            field_renames=field_renames,
            table_renames=table_renames,
            model_renames=model_renames,
            column_renames=column_renames,
            field_type_changes=field_type_changes
        )
    
    def _generate_post_migration(self):
        """Generate post-migration script."""
        template = Template("""# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

\"\"\"
Post-migration script for {{ module_name }} {{ version }}
\"\"\"

import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    \"\"\"
    Post-migration tasks for {{ module_name }} {{ version }}
    \"\"\"
    cr = env.cr
    
{% if field_type_changes %}
    # Complete field type conversions
{% for change in field_type_changes %}
    # Complete conversion of field {{ change.field }} in model {{ change.model }}
    table_name = '{{ change.model|replace(".", "_") }}'
    if openupgrade.column_exists(cr, table_name, '{{ change.field }}_new'):
        # Migrate data with conversion
        cr.execute("""
            UPDATE {table} 
            SET {field}_new = {{ change.get('conversion_expression', change.field + '::text') }}
            WHERE {field} IS NOT NULL
        """.format(table=table_name, field='{{ change.field }}'))
        
        # Drop old column and rename new one
        cr.execute(f"ALTER TABLE {table_name} DROP COLUMN {{ change.field }}")
        cr.execute(f"ALTER TABLE {table_name} RENAME COLUMN {{ change.field }}_new TO {{ change.field }}")
{% endfor %}

{% endif %}
{% if new_fields %}
    # Set default values for new fields
{% for change in new_fields %}
    # Set default value for new field {{ change.field }} in model {{ change.model }}
    if openupgrade.column_exists(cr, '{{ change.model|replace(".", "_") }}', '{{ change.field }}'):
{% if change.get('default_value') %}
        cr.execute("""
            UPDATE {{ change.model|replace(".", "_") }} 
            SET {{ change.field }} = %s 
            WHERE {{ change.field }} IS NULL
        """, ('{{ change.default_value }}',))
{% endif %}
{% endfor %}

{% endif %}
{% if data_migrations %}
    # Data migrations
{% for migration in data_migrations %}
    # {{ migration.description }}
    cr.execute(\"\"\"
        {{ migration.sql }}
    \"\"\")
{% endfor %}

{% endif %}
{% if cleanup_tasks %}
    # Cleanup tasks
{% for task in cleanup_tasks %}
    # {{ task.description }}
    openupgrade.delete_records_safely_by_xml_id(env, [
{% for xml_id in task.xml_ids %}
        '{{ module_name }}.{{ xml_id }}',
{% endfor %}
    ])
{% endfor %}

{% endif %}
{% if dependency_updates %}
    # Update module dependencies
    openupgrade.update_module_dependencies(cr, '{{ module_name }}', 
{% if removed_dependencies %}
        old_dependencies={{ removed_dependencies|repr }},
{% endif %}
{% if added_dependencies %}
        new_dependencies={{ added_dependencies|repr }}
{% endif %}
    )

{% endif %}
""")
        
        # Extract relevant changes for post-migration
        field_type_changes = [c for c in self.analysis.get('fields', []) if c['type'] == 'field_type_changed']
        new_fields = [c for c in self.analysis.get('fields', []) if c['type'] == 'field_added']
        
        # Generate data migrations based on field changes
        data_migrations = []
        for change in self.analysis.get('fields', []):
            if change['type'] == 'field_removed':
                data_migrations.append({
                    'description': f"Archive records with removed field {change['field']}",
                    'sql': f"-- Manual migration needed for removed field {change['field']}"
                })
        
        # Extract dependency changes
        manifest_changes = self.analysis.get('manifest', [])
        added_dependencies = []
        removed_dependencies = []
        
        for change in manifest_changes:
            if change['type'] == 'dependencies_added':
                added_dependencies.extend(change['dependencies'])
            elif change['type'] == 'dependencies_removed':
                removed_dependencies.extend(change['dependencies'])
        
        cleanup_tasks = []
        dependency_updates = bool(added_dependencies or removed_dependencies)
        
        return template.render(
            module_name=self.module_name,
            version=self.version,
            field_type_changes=field_type_changes,
            new_fields=new_fields,
            data_migrations=data_migrations,
            cleanup_tasks=cleanup_tasks,
            dependency_updates=dependency_updates,
            added_dependencies=added_dependencies,
            removed_dependencies=removed_dependencies
        )
    
    def _generate_end_migration(self):
        """Generate end-migration script."""
        template = Template("""# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

\"\"\"
End-migration script for {{ module_name }} {{ version }}
\"\"\"

import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    \"\"\"
    End-migration tasks for {{ module_name }} {{ version }}
    \"\"\"
    cr = env.cr
    
{% if index_updates %}
    # Add missing indexes
{% for index in index_updates %}
    openupgrade.add_missing_indexes(cr, {
        '{{ index.table }}': {{ index.columns|repr }}
    })
{% endfor %}

{% endif %}
{% if constraint_updates %}
    # Update constraints
{% for constraint in constraint_updates %}
    openupgrade.ensure_foreign_key_constraints(cr, [
        ('{{ constraint.table }}', '{{ constraint.column }}', 
         '{{ constraint.ref_table }}', '{{ constraint.ref_column }}', 
         '{{ constraint.on_delete }}'),
    ])
{% endfor %}

{% endif %}
{% if cleanup_orphaned %}
    # Clean up orphaned records
{% for cleanup in cleanup_orphaned %}
    openupgrade.cleanup_orphaned_records(cr, 
        '{{ cleanup.table }}', '{{ cleanup.fk_field }}', 
        '{{ cleanup.ref_table }}', '{{ cleanup.ref_field }}')
{% endfor %}

{% endif %}
    # Update module version in database
    env.ref('base.module_{{ module_name }}').write({
        'latest_version': '{{ version }}'
    })
    
    _logger.info("Migration completed successfully for {{ module_name }} {{ version }}")
""")
        
        # Extract relevant changes for end-migration
        index_updates = []
        constraint_updates = []
        cleanup_orphaned = []
        
        # Add indexes for new foreign key fields
        for change in self.analysis.get('fields', []):
            if change['type'] == 'field_added' and change.get('field_type') in ['many2one']:
                index_updates.append({
                    'table': change['model'].replace('.', '_'),
                    'columns': [change['field']]
                })
        
        return template.render(
            module_name=self.module_name,
            version=self.version,
            index_updates=index_updates,
            constraint_updates=constraint_updates,
            cleanup_orphaned=cleanup_orphaned
        )
    
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