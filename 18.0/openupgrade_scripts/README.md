# OpenUpgrade Migration Framework for Odoo 18.0

This framework provides tools for generating OpenUpgrade migration scripts for Odoo modules. It analyzes differences between module versions and generates appropriate migration scripts following OpenUpgrade best practices.

## Overview

The framework consists of several components:

1. **Module Analyzer** - Analyzes differences between two module versions
2. **Migration Script Generator** - Generates migration scripts based on analysis
3. **OpenUpgrade Library** - Utilities for common migration tasks
4. **Command Line Tool** - Easy-to-use interface for the framework
5. **Templates** - Reusable templates for migration scripts

## Installation

### Prerequisites

- Python 3.8+
- Odoo 18.0
- Jinja2 (for template rendering)

### Setup

```bash
# Install required dependencies
pip install jinja2

# The framework is located in the Odoo 18.0 directory
cd /path/to/odoo/18.0/openupgrade_scripts/
```

## Usage

### Command Line Interface

The framework provides a command-line tool for easy migration script generation:

```bash
./openupgrade_tool.py --help
```

#### Basic Workflow

1. **Analyze module changes:**
```bash
./openupgrade_tool.py analyze \\
    --source /path/to/old/module \\
    --target /path/to/new/module \\
    --output analysis.json
```

2. **Generate migration scripts:**
```bash
./openupgrade_tool.py generate \\
    --module my_module \\
    --version 1.1.0 \\
    --analysis analysis.json \\
    --output ./migrations/
```

3. **Or do both in one step:**
```bash
./openupgrade_tool.py full \\
    --module my_module \\
    --version 1.1.0 \\
    --source /path/to/old/module \\
    --target /path/to/new/module \\
    --output ./migrations/
```

4. **Create example scripts:**
```bash
./openupgrade_tool.py create-example \\
    --module my_module \\
    --version 1.1.0 \\
    --output ./migrations/
```

### Programmatic Usage

You can also use the framework programmatically:

```python
from module_analyzer import analyze_module_changes
from migration_generator import generate_migration_scripts

# Analyze changes
analysis = analyze_module_changes('/path/to/old/module', '/path/to/new/module')

# Generate scripts
scripts, summary = generate_migration_scripts('my_module', '1.1.0', analysis)

print(summary)
```

## Framework Components

### 1. Module Analyzer

The `ModuleAnalyzer` class detects changes between module versions:

- **Manifest changes** - Version, dependencies
- **Model changes** - New/removed models, field changes
- **Data file changes** - XML/CSV file modifications
- **View changes** - UI view modifications
- **Security changes** - Access rule changes

### 2. Migration Script Generator

The `MigrationScriptGenerator` class creates three types of migration scripts:

- **pre-migration.py** - Runs before module update (renames, structure changes)
- **post-migration.py** - Runs after module update (data migrations, transformations)
- **end-migration.py** - Runs at the end (cleanup, constraints, indexes)

### 3. OpenUpgrade Library

The `openupgradelib` module provides utilities for common migration tasks:

#### Field Operations
```python
# Rename fields
openupgrade.rename_fields(env, [
    ('model.name', 'old_field', 'new_field'),
])

# Rename columns
openupgrade.rename_columns(cr, 'table_name', {
    'old_column': 'new_column',
})

# Convert field types
openupgrade.convert_field_type(cr, 'table', 'field', 'varchar', 'text')
```

#### Model Operations
```python
# Rename models
openupgrade.rename_models(cr, [
    ('old.model', 'new.model'),
])

# Rename tables
openupgrade.rename_tables(cr, [
    ('old_table', 'new_table'),
])
```

#### Data Operations
```python
# Migrate field values
openupgrade.migrate_field_values(cr, 'table', {
    'field': "CASE WHEN old_field = 'x' THEN 'y' ELSE old_field END"
})

# Delete obsolete records
openupgrade.delete_obsolete_records(cr, 'module', ['xml_id1', 'xml_id2'])

# Clean up orphaned records
openupgrade.cleanup_orphaned_records(cr, 'table', 'fk_field', 'ref_table')
```

#### Infrastructure Operations
```python
# Add indexes
openupgrade.add_missing_indexes(cr, {
    'table_name': ['column1', 'column2']
})

# Ensure foreign key constraints
openupgrade.ensure_foreign_key_constraints(cr, [
    ('table', 'column', 'ref_table', 'ref_column', 'cascade'),
])
```

## Migration Script Structure

### Pre-migration Script

Handles structural changes that need to happen before the module update:

```python
@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    
    # Rename fields before module loads new structure
    openupgrade.rename_fields(env, [
        ('my.model', 'old_name', 'new_name'),
    ])
    
    # Rename tables
    openupgrade.rename_tables(cr, [
        ('old_table', 'new_table'),
    ])
```

### Post-migration Script

Handles data migrations and transformations after the module update:

```python
@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    
    # Set default values for new fields
    cr.execute("""
        UPDATE my_table 
        SET new_field = 'default_value' 
        WHERE new_field IS NULL
    """)
    
    # Transform existing data
    openupgrade.migrate_field_values(cr, 'my_table', {
        'status': "CASE WHEN status = 'draft' THEN 'new' ELSE status END"
    })
```

### End-migration Script

Handles final cleanup and optimization:

```python
@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    
    # Add performance indexes
    openupgrade.add_missing_indexes(cr, {
        'my_table': ['frequently_queried_field']
    })
    
    # Clean up orphaned records
    openupgrade.cleanup_orphaned_records(cr, 'child_table', 'parent_id', 'parent_table')
```

## Detected Changes and Migrations

The framework can detect and handle various types of changes:

### Field Changes

| Change Type | Detection | Migration Action |
|-------------|-----------|------------------|
| Field renamed | Name comparison | `rename_fields()` in pre-migration |
| Field removed | Missing in target | Archive/cleanup in post-migration |
| Field added | New in target | Set defaults in post-migration |
| Type changed | Type comparison | Convert data in post-migration |
| Attribute changed | Attribute comparison | Update constraints in end-migration |

### Model Changes

| Change Type | Detection | Migration Action |
|-------------|-----------|------------------|
| Model renamed | Name comparison | `rename_models()` in pre-migration |
| Model removed | Missing in target | Archive data in post-migration |
| Model added | New in target | No action needed |
| Table renamed | Explicit mapping | `rename_tables()` in pre-migration |

### Data Changes

| Change Type | Detection | Migration Action |
|-------------|-----------|------------------|
| Records added | XML comparison | Load new data |
| Records removed | XML comparison | Clean up obsolete records |
| Records modified | Content comparison | Update existing records |

## Best Practices

### 1. Migration Safety

- Always test migrations on a copy of production data
- Use transactions to ensure atomicity
- Implement rollback procedures for critical changes
- Validate data integrity after migration

### 2. Performance Considerations

- Add indexes for new foreign key fields
- Use batch processing for large data migrations
- Optimize SQL queries for better performance
- Consider using `VACUUM` after large data changes

### 3. Data Preservation

- Archive data instead of deleting when possible
- Preserve historical data with appropriate flags
- Maintain audit trails for data transformations
- Use temporary columns for complex type conversions

### 4. Error Handling

- Log all migration steps with appropriate levels
- Handle edge cases and data inconsistencies
- Provide meaningful error messages
- Implement recovery mechanisms

## Examples

### Example 1: Field Rename

Old model:
```python
class MyModel(models.Model):
    _name = 'my.model'
    
    old_name = fields.Char('Old Name')
```

New model:
```python
class MyModel(models.Model):
    _name = 'my.model'
    
    new_name = fields.Char('New Name')
```

Generated pre-migration:
```python
openupgrade.rename_fields(env, [
    ('my.model', 'old_name', 'new_name'),
])
```

### Example 2: Field Type Change

Old field: `status = fields.Char('Status')`
New field: `status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], 'Status')`

Generated post-migration:
```python
cr.execute("""
    UPDATE my_model 
    SET status = CASE 
        WHEN status = 'Draft' THEN 'draft'
        WHEN status = 'Done' THEN 'done'
        ELSE 'draft'
    END
""")
```

### Example 3: Model Addition

Generated post-migration:
```python
# Set default values for new model records
env['my.new.model'].create([
    {'name': 'Default Record', 'active': True}
])
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

2. **Analysis Failures**
   - Verify module paths are correct
   - Check file permissions
   - Ensure manifest files are valid

3. **Migration Script Errors**
   - Test scripts in development environment
   - Check database constraints
   - Verify field mappings

### Debug Mode

Enable verbose logging for detailed information:

```bash
./openupgrade_tool.py --verbose full --module my_module ...
```

## Contributing

To extend the framework:

1. Add new change detection in `ModuleAnalyzer`
2. Create corresponding migration templates in `MigrationScriptGenerator`
3. Add utility functions to `openupgradelib`
4. Update documentation and examples

## References

- [OpenUpgrade Project](https://github.com/OCA/OpenUpgrade)
- [Odoo Migration Guide](https://www.odoo.com/documentation/18.0/developer/reference/upgrades.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)