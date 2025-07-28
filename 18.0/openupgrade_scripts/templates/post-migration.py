# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
Template for post-migration script
"""

import logging
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """
    Post-migration tasks for {{ module_name }} {{ version }}
    
    This script runs after the module upgrade and handles:
    - Data migrations and transformations
    - Field type conversions
    - Default value assignments
    - Record updates
    """
    cr = env.cr
    
    # Example: Set default values for new fields
    # cr.execute("""
    #     UPDATE table_name 
    #     SET new_field = 'default_value' 
    #     WHERE new_field IS NULL
    # """)
    
    # Example: Migrate data between fields
    # cr.execute("""
    #     UPDATE table_name 
    #     SET new_field = old_field 
    #     WHERE old_field IS NOT NULL
    # """)
    
    # Example: Transform field values
    # cr.execute("""
    #     UPDATE table_name 
    #     SET field_name = CASE 
    #         WHEN field_name = 'old_value' THEN 'new_value'
    #         ELSE field_name 
    #     END
    # """)
    
    # Example: Update module dependencies
    # openupgrade.update_module_dependencies(cr, '{{ module_name }}', 
    #     old_dependencies=['old_dep'],
    #     new_dependencies=['new_dep']
    # )
    
    # Example: Delete obsolete records
    # openupgrade.delete_records_safely_by_xml_id(env, [
    #     '{{ module_name }}.obsolete_record_id',
    # ])
    
    _logger.info("Post-migration completed successfully")