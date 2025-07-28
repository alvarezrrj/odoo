# OpenUpgrade Migration Framework - Quick Start Guide

This guide demonstrates how to use the OpenUpgrade Migration Framework to generate migration scripts for Odoo module upgrades.

## Quick Example

Let's say you have a module called `inventory_management` that you're upgrading from version 1.5.0 to 2.0.0.

### Step 1: Analyze the Changes

```bash
cd /path/to/odoo/18.0/openupgrade_scripts/

# Analyze differences between module versions
./openupgrade_tool.py analyze \
    --source /path/to/inventory_management_v1.5.0 \
    --target /path/to/inventory_management_v2.0.0 \
    --output analysis.json
```

### Step 2: Generate Migration Scripts

```bash
# Generate migration scripts based on analysis
./openupgrade_tool.py generate \
    --module inventory_management \
    --version 2.0.0 \
    --analysis analysis.json \
    --output ./migrations/
```

### Step 3: Or Do Both in One Command

```bash
# Analyze and generate in one step
./openupgrade_tool.py full \
    --module inventory_management \
    --version 2.0.0 \
    --source /path/to/inventory_management_v1.5.0 \
    --target /path/to/inventory_management_v2.0.0 \
    --output ./migrations/
```

## What Gets Generated

The framework generates three migration scripts in the OpenUpgrade format:

```
migrations/
└── inventory_management/
    └── 2.0.0/
        ├── pre-migration.py
        ├── post-migration.py
        └── end-migration.py
```

### pre-migration.py
Handles structural changes before the module update:
- Field and table renames
- Model renames  
- Database schema preparation

### post-migration.py
Handles data migrations after the module update:
- Data transformations
- Default value assignments
- Record updates and cleanup

### end-migration.py
Handles final cleanup and optimization:
- Index creation
- Constraint updates
- Orphaned record cleanup

## Real Example Output

Here's what the framework detected and generated for a sample module upgrade:

```
Migration Summary for inventory_management 2.0.0
==================================================

Manifest Changes:
  - Version: 1.5.0 → 2.0.0
  - Added dependencies: stock, account

Model Changes:
  - Added model: inventory.category
  - Removed model: inventory.old_tracking

Field Changes:
  - Added field: inventory.item.category_id (many2one)
  - Removed field: inventory.item.old_status
  - Type changed: inventory.item.quantity (integer → float)

Manual Migration Steps Required:
  - Review data handling for removed field inventory.item.old_status
  - Handle data from removed model inventory.old_tracking

Generated Scripts:
  - pre-migration.py: Handles structural changes before module update
  - post-migration.py: Handles data migrations after module update
  - end-migration.py: Handles cleanup and final tasks
```

## Using the Generated Scripts

1. **Copy scripts to OpenUpgrade structure:**
```bash
cp migrations/inventory_management/2.0.0/* \
   /path/to/openupgrade/addons/inventory_management/migrations/2.0.0/
```

2. **Review and customize scripts** based on your specific business logic

3. **Test migration** on a copy of production data

4. **Run the migration** using OpenUpgrade tools

## Framework Features

- **Automatic Change Detection**: Analyzes Python models, XML data, views, and security
- **OpenUpgrade Integration**: Uses standard OpenUpgrade utilities and patterns
- **Customizable Templates**: Easy to modify for specific migration needs  
- **Command Line Interface**: Simple workflow for common tasks
- **Comprehensive Documentation**: Detailed guides and examples

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the [templates/](templates/) directory for customizable script templates
- Explore the [openupgradelib.py](openupgradelib.py) utilities
- Review generated example scripts in the `examples/` directory

## Getting Help

The framework provides verbose logging to help debug issues:

```bash
./openupgrade_tool.py --verbose full --module my_module ...
```

For complex migrations that require manual intervention, the framework will identify these in the migration summary and provide guidance on what needs manual attention.