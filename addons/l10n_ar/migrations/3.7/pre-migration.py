# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""
Pre-migration script for l10n_ar module upgrade from 17.0 to 18.0.

This script handles field removals and data preparations before the module upgrade.
"""

import logging
from odoo import api, SUPERUSER_ID
from odoo.tools.sql import column_exists, table_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration script for l10n_ar upgrade to version 3.7 (Odoo 18.0).
    
    Changes handled:
    1. Backup and remove l10n_ar_currency_rate field from account_move table
    2. Backup and remove l10n_ar_special_purchase_document_type_ids Many2many relation
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("Starting l10n_ar pre-migration to version 3.7")
    
    # 1. Handle l10n_ar_currency_rate field removal from account.move
    _backup_currency_rate_field(cr)
    
    # 2. Handle l10n_ar_special_purchase_document_type_ids Many2many removal from res.partner
    _backup_special_purchase_document_types(cr)
    
    _logger.info("Completed l10n_ar pre-migration to version 3.7")


def _backup_currency_rate_field(cr):
    """
    Backup l10n_ar_currency_rate field data before removal.
    
    The l10n_ar_currency_rate field is being removed from account.move model
    in version 18.0 as it's no longer needed.
    """
    if not table_exists(cr, 'account_move') or not column_exists(cr, 'account_move', 'l10n_ar_currency_rate'):
        _logger.info("l10n_ar_currency_rate field does not exist in account_move, skipping backup")
        return
    
    _logger.info("Backing up l10n_ar_currency_rate field from account_move")
    
    # Create backup table for currency rates if there's meaningful data
    cr.execute("""
        SELECT COUNT(*)
        FROM account_move
        WHERE l10n_ar_currency_rate IS NOT NULL
          AND l10n_ar_currency_rate != 0
          AND l10n_ar_currency_rate != 1
    """)
    
    count = cr.fetchone()[0]
    if count > 0:
        _logger.info(f"Found {count} account moves with custom currency rates, creating backup table")
        
        # Create backup table
        cr.execute("""
            CREATE TABLE IF NOT EXISTS account_move_l10n_ar_currency_rate_backup (
                move_id INTEGER PRIMARY KEY,
                currency_rate NUMERIC,
                backup_date TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Backup the data
        cr.execute("""
            INSERT INTO account_move_l10n_ar_currency_rate_backup (move_id, currency_rate)
            SELECT id, l10n_ar_currency_rate
            FROM account_move
            WHERE l10n_ar_currency_rate IS NOT NULL
              AND l10n_ar_currency_rate != 0
              AND l10n_ar_currency_rate != 1
            ON CONFLICT (move_id) DO NOTHING
        """)
        
        _logger.info("Currency rate data backed up successfully")
    else:
        _logger.info("No custom currency rates found, skipping backup table creation")


def _backup_special_purchase_document_types(cr):
    """
    Backup l10n_ar_special_purchase_document_type_ids Many2many relation before removal.
    
    The l10n_ar_special_purchase_document_type_ids field is being removed from res.partner model
    in version 18.0 as it's deprecated.
    """
    if not table_exists(cr, 'res_partner_document_type_rel'):
        _logger.info("res_partner_document_type_rel table does not exist, skipping backup")
        return
    
    _logger.info("Backing up l10n_ar_special_purchase_document_type_ids Many2many relation")
    
    # Check if there's data to backup
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner_document_type_rel
    """)
    
    count = cr.fetchone()[0]
    if count > 0:
        _logger.info(f"Found {count} special purchase document type relations, creating backup table")
        
        # Create backup table
        cr.execute("""
            CREATE TABLE IF NOT EXISTS res_partner_l10n_ar_special_purchase_document_types_backup (
                partner_id INTEGER,
                document_type_id INTEGER,
                backup_date TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (partner_id, document_type_id)
            )
        """)
        
        # Backup the data
        cr.execute("""
            INSERT INTO res_partner_l10n_ar_special_purchase_document_types_backup 
                (partner_id, document_type_id)
            SELECT partner_id, document_type_id
            FROM res_partner_document_type_rel
            ON CONFLICT (partner_id, document_type_id) DO NOTHING
        """)
        
        _logger.info("Special purchase document types data backed up successfully")
    else:
        _logger.info("No special purchase document types found, skipping backup table creation")