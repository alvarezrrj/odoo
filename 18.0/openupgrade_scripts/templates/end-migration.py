# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
Template for end-migration script
"""

import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """
    End-migration tasks for {{ module_name }} {{ version }}
    
    This script runs at the end of the migration process and handles:
    - Index creation
    - Constraint updates
    - Cleanup of orphaned records
    - Final validations
    """
    cr = env.cr
    
    # Example: Add missing indexes
    # openupgrade.add_missing_indexes(cr, {
    #     'table_name': ['column_name1', 'column_name2']
    # })
    
    # Example: Ensure foreign key constraints
    # openupgrade.ensure_foreign_key_constraints(cr, [
    #     ('table', 'column', 'ref_table', 'ref_column', 'cascade'),
    # ])
    
    # Example: Clean up orphaned records
    # openupgrade.cleanup_orphaned_records(cr, 
    #     'table_with_fk', 'foreign_key_field', 
    #     'referenced_table', 'id')
    
    # Example: Final data validation
    # cr.execute("""
    #     SELECT COUNT(*) FROM table_name WHERE field IS NULL
    # """)
    # null_count = cr.fetchone()[0]
    # if null_count > 0:
    #     _logger.warning(f"Found {null_count} records with NULL values in required field")
    
    # Update module version in database
    env.ref('base.module_{{ module_name }}').write({
        'latest_version': '{{ version }}'
    })
    
    _logger.info("End-migration completed successfully")