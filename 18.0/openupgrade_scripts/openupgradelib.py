# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
OpenUpgrade Library - Common utilities for Odoo migration scripts
"""

import logging
from odoo import api, SUPERUSER_ID
from odoo.tools import sql

_logger = logging.getLogger(__name__)


def rename_columns(cr, table_name, column_mapping):
    """
    Rename columns in a table.
    
    :param cr: Database cursor
    :param table_name: Name of the table
    :param column_mapping: Dictionary mapping old column names to new ones
    """
    for old_name, new_name in column_mapping.items():
        if sql.column_exists(cr, table_name, old_name):
            sql.rename_column(cr, table_name, old_name, new_name)
            _logger.info(f"Renamed column {old_name} to {new_name} in table {table_name}")


def rename_tables(cr, table_mapping):
    """
    Rename tables.
    
    :param cr: Database cursor
    :param table_mapping: Dictionary mapping old table names to new ones
    """
    for old_name, new_name in table_mapping.items():
        if sql.table_exists(cr, old_name):
            cr.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
            _logger.info(f"Renamed table {old_name} to {new_name}")


def rename_models(cr, model_mapping):
    """
    Rename models in ir_model and related tables.
    
    :param cr: Database cursor
    :param model_mapping: Dictionary mapping old model names to new ones
    """
    for old_model, new_model in model_mapping.items():
        _logger.info(f"Renaming model {old_model} to {new_model}")
        
        # Update ir_model
        cr.execute("""
            UPDATE ir_model 
            SET model = %s 
            WHERE model = %s
        """, (new_model, old_model))
        
        # Update ir_model_fields
        cr.execute("""
            UPDATE ir_model_fields 
            SET model = %s 
            WHERE model = %s
        """, (new_model, old_model))
        
        # Update ir_model_data
        cr.execute("""
            UPDATE ir_model_data 
            SET model = %s 
            WHERE model = %s
        """, (new_model, old_model))


def rename_fields(cr, model, field_mapping):
    """
    Rename fields in ir_model_fields and handle column renames.
    
    :param cr: Database cursor
    :param model: Model name
    :param field_mapping: Dictionary mapping old field names to new ones
    """
    # Get table name for the model
    cr.execute("SELECT id FROM ir_model WHERE model = %s", (model,))
    if not cr.fetchone():
        _logger.warning(f"Model {model} not found")
        return
    
    table_name = model.replace('.', '_')
    
    for old_field, new_field in field_mapping.items():
        _logger.info(f"Renaming field {old_field} to {new_field} in model {model}")
        
        # Update ir_model_fields
        cr.execute("""
            UPDATE ir_model_fields 
            SET name = %s 
            WHERE model = %s AND name = %s
        """, (new_field, model, old_field))
        
        # Rename column if it exists
        if sql.column_exists(cr, table_name, old_field):
            sql.rename_column(cr, table_name, old_field, new_field)


def delete_obsolete_records(cr, module, xml_ids):
    """
    Delete obsolete records by their XML IDs.
    
    :param cr: Database cursor
    :param module: Module name
    :param xml_ids: List of XML IDs to delete
    """
    for xml_id in xml_ids:
        _logger.info(f"Deleting obsolete record {module}.{xml_id}")
        cr.execute("""
            DELETE FROM ir_model_data 
            WHERE module = %s AND name = %s
        """, (module, xml_id))


def migrate_field_values(cr, table, field_mapping):
    """
    Migrate field values using SQL transformations.
    
    :param cr: Database cursor
    :param table: Table name
    :param field_mapping: Dictionary mapping field names to SQL expressions
    """
    for field, expression in field_mapping.items():
        if sql.column_exists(cr, table, field):
            _logger.info(f"Migrating values for field {field} in table {table}")
            cr.execute(f"UPDATE {table} SET {field} = {expression} WHERE {field} IS NOT NULL")


def add_missing_indexes(cr, table_indexes):
    """
    Add missing database indexes.
    
    :param cr: Database cursor
    :param table_indexes: Dictionary mapping table names to list of column names
    """
    for table, columns in table_indexes.items():
        if sql.table_exists(cr, table):
            for column in columns:
                if sql.column_exists(cr, table, column):
                    index_name = f"{table}_{column}_index"
                    cr.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table} ({column})
                    """)
                    _logger.info(f"Created index {index_name}")


def update_module_dependencies(cr, module, old_dependencies, new_dependencies):
    """
    Update module dependencies in ir_module_module_dependency.
    
    :param cr: Database cursor
    :param module: Module name
    :param old_dependencies: List of old dependency names to remove
    :param new_dependencies: List of new dependency names to add
    """
    # Get module ID
    cr.execute("SELECT id FROM ir_module_module WHERE name = %s", (module,))
    module_record = cr.fetchone()
    if not module_record:
        _logger.warning(f"Module {module} not found")
        return
    
    module_id = module_record[0]
    
    # Remove old dependencies
    for dep in old_dependencies:
        cr.execute("""
            DELETE FROM ir_module_module_dependency 
            WHERE module_id = %s AND name = %s
        """, (module_id, dep))
        _logger.info(f"Removed dependency {dep} from module {module}")
    
    # Add new dependencies
    for dep in new_dependencies:
        cr.execute("""
            INSERT INTO ir_module_module_dependency (module_id, name) 
            VALUES (%s, %s) 
            ON CONFLICT DO NOTHING
        """, (module_id, dep))
        _logger.info(f"Added dependency {dep} to module {module}")


def migrate_attachment_data(cr, old_field, new_field):
    """
    Migrate attachment data from one field to another.
    
    :param cr: Database cursor
    :param old_field: Old field name
    :param new_field: New field name
    """
    if sql.column_exists(cr, 'ir_attachment', old_field):
        _logger.info(f"Migrating attachment data from {old_field} to {new_field}")
        cr.execute(f"""
            UPDATE ir_attachment 
            SET {new_field} = {old_field} 
            WHERE {old_field} IS NOT NULL AND {new_field} IS NULL
        """)


def cleanup_orphaned_records(cr, table, foreign_key_field, referenced_table, referenced_field='id'):
    """
    Clean up orphaned records that reference non-existent records.
    
    :param cr: Database cursor
    :param table: Table containing the foreign key
    :param foreign_key_field: Foreign key field name
    :param referenced_table: Referenced table name
    :param referenced_field: Referenced field name (default: 'id')
    """
    if sql.table_exists(cr, table) and sql.table_exists(cr, referenced_table):
        _logger.info(f"Cleaning up orphaned records in {table}")
        cr.execute(f"""
            DELETE FROM {table} 
            WHERE {foreign_key_field} IS NOT NULL 
              AND {foreign_key_field} NOT IN (
                  SELECT {referenced_field} FROM {referenced_table}
              )
        """)
        _logger.info(f"Cleaned up {cr.rowcount} orphaned records")


def convert_field_type(cr, table, field, old_type, new_type, conversion_expr=None):
    """
    Convert field type with optional data transformation.
    
    :param cr: Database cursor
    :param table: Table name
    :param field: Field name
    :param old_type: Old PostgreSQL type
    :param new_type: New PostgreSQL type
    :param conversion_expr: Optional SQL expression for data conversion
    """
    if sql.column_exists(cr, table, field):
        temp_field = f"{field}_temp"
        
        _logger.info(f"Converting field {field} from {old_type} to {new_type} in table {table}")
        
        # Add temporary column
        cr.execute(f"ALTER TABLE {table} ADD COLUMN {temp_field} {new_type}")
        
        # Copy data with conversion
        if conversion_expr:
            cr.execute(f"UPDATE {table} SET {temp_field} = {conversion_expr}")
        else:
            cr.execute(f"UPDATE {table} SET {temp_field} = {field}::{new_type}")
        
        # Drop old column and rename new one
        cr.execute(f"ALTER TABLE {table} DROP COLUMN {field}")
        cr.execute(f"ALTER TABLE {table} RENAME COLUMN {temp_field} TO {field}")


def load_data_from_csv(cr, env, module, filename, model, mode='update'):
    """
    Load data from CSV file.
    
    :param cr: Database cursor
    :param env: Odoo environment
    :param module: Module name
    :param filename: CSV filename
    :param model: Model name
    :param mode: Load mode ('update' or 'init')
    """
    _logger.info(f"Loading data from {filename} for model {model}")
    # This would typically use Odoo's data loading mechanisms
    # Implementation depends on specific requirements
    pass


def ensure_foreign_key_constraints(cr, constraints):
    """
    Ensure foreign key constraints exist.
    
    :param cr: Database cursor
    :param constraints: List of tuples (table, column, ref_table, ref_column, on_delete)
    """
    for table, column, ref_table, ref_column, on_delete in constraints:
        if sql.table_exists(cr, table) and sql.table_exists(cr, ref_table):
            constraint_name = f"{table}_{column}_fkey"
            
            # Drop existing constraint if it exists
            sql.drop_constraint(cr, table, constraint_name)
            
            # Add new constraint
            sql.add_foreign_key(cr, table, column, ref_table, ref_column, on_delete)
            _logger.info(f"Added foreign key constraint {constraint_name}")