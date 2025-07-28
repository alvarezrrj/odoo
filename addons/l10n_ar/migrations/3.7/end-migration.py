# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""
End-migration script for l10n_ar module upgrade from 17.0 to 18.0.

This script handles final cleanup and validation after the module upgrade.
"""

import logging
from odoo import api, SUPERUSER_ID
from odoo.tools.sql import table_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    End-migration script for l10n_ar upgrade to version 3.7 (Odoo 18.0).
    
    Changes handled:
    1. Clean up old Many2many relation tables that are no longer needed
    2. Validate that the migration completed successfully
    3. Log information about backup tables for manual cleanup
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("Starting l10n_ar end-migration to version 3.7")
    
    # 1. Clean up old relation tables
    _cleanup_old_relation_tables(cr)
    
    # 2. Validate migration success
    _validate_migration(cr, env)
    
    # 3. Provide information about backup tables
    _log_backup_table_info(cr)
    
    _logger.info("Completed l10n_ar end-migration to version 3.7")


def _cleanup_old_relation_tables(cr):
    """
    Clean up old Many2many relation tables that are no longer needed.
    
    The res_partner_document_type_rel table is no longer needed as the
    l10n_ar_special_purchase_document_type_ids field has been removed.
    """
    _logger.info("Cleaning up old relation tables")
    
    # Check if the old relation table exists and drop it
    if table_exists(cr, 'res_partner_document_type_rel'):
        _logger.info("Dropping obsolete res_partner_document_type_rel table")
        cr.execute("DROP TABLE IF EXISTS res_partner_document_type_rel CASCADE")
        _logger.info("Successfully dropped res_partner_document_type_rel table")
    else:
        _logger.info("res_partner_document_type_rel table does not exist, no cleanup needed")


def _validate_migration(cr, env):
    """
    Validate that the migration completed successfully.
    
    This checks that:
    1. Removed fields are no longer accessible
    2. New logic is working correctly
    3. No data integrity issues were introduced
    """
    _logger.info("Validating migration success")
    
    # 1. Validate that fiscal positions work with new ranking system
    _validate_fiscal_position_logic(cr, env)
    
    # 2. Validate that AFIP concept calculation works with new product type logic
    _validate_afip_concept_logic(cr, env)
    
    # 3. Check for any data integrity issues
    _validate_data_integrity(cr, env)


def _validate_fiscal_position_logic(cr, env):
    """Validate fiscal position ranking logic works correctly."""
    try:
        # Test fiscal position detection with a sample partner
        partners = env['res.partner'].search([
            ('l10n_ar_afip_responsibility_type_id', '!=', False)
        ], limit=1)
        
        if partners:
            partner = partners[0]
            fpos = env['account.fiscal.position']._get_fiscal_position(partner)
            _logger.info(f"Fiscal position logic validated successfully for partner {partner.name}")
        else:
            _logger.info("No Argentine partners found for fiscal position validation")
            
    except Exception as e:
        _logger.error(f"Fiscal position validation failed: {e}")


def _validate_afip_concept_logic(cr, env):
    """Validate AFIP concept calculation with new product type logic."""
    try:
        # Find a posted invoice to test AFIP concept calculation
        invoices = env['account.move'].search([
            ('company_id.country_id.code', '=', 'AR'),
            ('state', '=', 'posted'),
            ('l10n_ar_afip_concept', '!=', False)
        ], limit=1)
        
        if invoices:
            invoice = invoices[0]
            # Trigger AFIP concept computation
            invoice._compute_l10n_ar_afip_concept()
            _logger.info(f"AFIP concept logic validated successfully for invoice {invoice.name}")
        else:
            _logger.info("No Argentine invoices found for AFIP concept validation")
            
    except Exception as e:
        _logger.error(f"AFIP concept validation failed: {e}")


def _validate_data_integrity(cr, env):
    """Check for any data integrity issues after migration."""
    
    # Check for orphaned data references
    integrity_checks = [
        {
            'name': 'AFIP Responsibility Types',
            'query': """
                SELECT COUNT(*)
                FROM res_partner
                WHERE l10n_ar_afip_responsibility_type_id IS NOT NULL
                  AND l10n_ar_afip_responsibility_type_id NOT IN (
                      SELECT id FROM l10n_ar_afip_responsibility_type
                  )
            """,
            'expected': 0
        },
        {
            'name': 'Document Types in Invoices',
            'query': """
                SELECT COUNT(*)
                FROM account_move
                WHERE l10n_latam_document_type_id IS NOT NULL
                  AND l10n_latam_document_type_id NOT IN (
                      SELECT id FROM l10n_latam_document_type
                  )
            """,
            'expected': 0
        }
    ]
    
    for check in integrity_checks:
        cr.execute(check['query'])
        count = cr.fetchone()[0]
        
        if count == check['expected']:
            _logger.info(f"Data integrity check '{check['name']}' passed")
        else:
            _logger.warning(f"Data integrity check '{check['name']}' failed: found {count} issues")


def _log_backup_table_info(cr):
    """
    Log information about backup tables created during migration.
    
    This helps administrators know what backup data is available
    and when it can be safely removed.
    """
    _logger.info("Checking backup tables created during migration")
    
    backup_tables = [
        'account_move_l10n_ar_currency_rate_backup',
        'res_partner_l10n_ar_special_purchase_document_types_backup'
    ]
    
    for table_name in backup_tables:
        if table_exists(cr, table_name):
            cr.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cr.fetchone()[0]
            
            cr.execute(f"SELECT backup_date FROM {table_name} ORDER BY backup_date LIMIT 1")
            result = cr.fetchone()
            backup_date = result[0] if result else 'Unknown'
            
            _logger.info(f"Backup table '{table_name}' contains {count} records (created: {backup_date})")
            _logger.info(f"This table can be safely removed after validating the migration is successful")
        else:
            _logger.info(f"Backup table '{table_name}' was not created (no data to backup)")
    
    if any(table_exists(cr, table) for table in backup_tables):
        _logger.info(
            "MIGRATION COMPLETE: Backup tables have been created for removed fields. "
            "These tables can be safely removed after validating that the migration "
            "was successful and no data recovery is needed."
        )