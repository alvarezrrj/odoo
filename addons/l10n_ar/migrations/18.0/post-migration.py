# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
Post-migration script for l10n_ar module from 17.0 to 18.0

This script handles the cleanup and data migration after module upgrade:
1. Cleans up deprecated field references
2. Validates the new fiscal position ranking system 
3. Ensures proper AFIP responsibility type handling
4. Updates chart template configurations
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration steps for l10n_ar module upgrade from 17.0 to 18.0
    
    Args:
        cr: Database cursor
        version: Version from which we are migrating
    """
    _logger.info("Starting l10n_ar post-migration from version %s to 18.0", version)
    
    # Clean up the deprecated many2many relation table if it exists
    cr.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'res_partner_document_type_rel'
        AND table_schema = current_schema()
    """)
    
    if cr.fetchone():
        _logger.info("Cleaning up deprecated res_partner_document_type_rel table")
        cr.execute("DROP TABLE IF EXISTS res_partner_document_type_rel CASCADE")
    
    # Ensure proper sequence values are set for chart templates
    _logger.info("Setting proper sequence values for Argentinian chart templates")
    
    # Set sequence for ar_ri template (highest priority)
    cr.execute("""
        UPDATE account_chart_template 
        SET sequence = 0 
        WHERE code = 'ar_ri'
    """)
    
    # Set sequence for ar_base template 
    cr.execute("""
        UPDATE account_chart_template 
        SET sequence = 1 
        WHERE code = 'ar_base'
    """)
    
    # Set sequence for ar_ex template
    cr.execute("""
        UPDATE account_chart_template 
        SET sequence = 2 
        WHERE code = 'ar_ex'
    """)
    
    # Validate CUIT identification types for Argentinian partners
    _logger.info("Validating CUIT identification types for Argentinian partners")
    
    # Get the CUIT identification type ID
    cr.execute("""
        SELECT id FROM l10n_latam_identification_type 
        WHERE name = 'CUIT' AND country_id = (
            SELECT id FROM res_country WHERE code = 'AR'
        )
    """)
    cuit_type_id = cr.fetchone()
    
    if cuit_type_id:
        cuit_type_id = cuit_type_id[0]
        
        # Update partners with AR country and empty identification type to use CUIT
        cr.execute("""
            UPDATE res_partner 
            SET l10n_latam_identification_type_id = %s
            WHERE country_id = (SELECT id FROM res_country WHERE code = 'AR')
            AND l10n_latam_identification_type_id IS NULL
            AND l10n_ar_afip_responsibility_type_id IS NOT NULL
            AND is_company = true
        """, (cuit_type_id,))
        
        updated_count = cr.rowcount
        _logger.info("Updated %d Argentinian companies to use CUIT identification type", updated_count)
    
    # Validate fiscal position configurations
    _logger.info("Validating fiscal position configurations for new ranking system")
    
    # Check for fiscal positions without proper AFIP responsibility type configuration
    cr.execute("""
        SELECT fp.id, fp.name
        FROM account_fiscal_position fp
        JOIN res_company c ON c.id = fp.company_id
        WHERE c.country_id = (SELECT id FROM res_country WHERE code = 'AR')
        AND NOT EXISTS (
            SELECT 1 FROM account_fiscal_position_l10n_ar_afip_responsibility_type_rel rel
            WHERE rel.account_fiscal_position_id = fp.id
        )
        AND fp.auto_apply = true
    """)
    
    unconfigured_fpos = cr.fetchall()
    if unconfigured_fpos:
        _logger.warning("Found %d fiscal positions without AFIP responsibility type configuration: %s", 
                       len(unconfigured_fpos), 
                       [fpos[1] for fpos in unconfigured_fpos])
    
    # Update journal configurations for enhanced document number validation
    _logger.info("Updating journal configurations for enhanced validation")
    
    # Ensure all AR sale journals have proper AFIP POS configuration
    cr.execute("""
        UPDATE account_journal 
        SET l10n_ar_afip_pos_number = COALESCE(l10n_ar_afip_pos_number, 1)
        WHERE type = 'sale' 
        AND company_id IN (
            SELECT id FROM res_company 
            WHERE country_id = (SELECT id FROM res_country WHERE code = 'AR')
        )
        AND l10n_ar_afip_pos_number IS NULL
    """)
    
    updated_journals = cr.rowcount
    if updated_journals > 0:
        _logger.info("Updated %d sale journals with default AFIP POS number", updated_journals)
    
    # Log migration statistics
    _log_migration_statistics(cr)
    
    _logger.info("Completed l10n_ar post-migration")


def _log_migration_statistics(cr):
    """Log statistics about the migration results"""
    
    # Count Argentinian partners
    cr.execute("""
        SELECT COUNT(*) 
        FROM res_partner 
        WHERE country_id = (SELECT id FROM res_country WHERE code = 'AR')
        AND l10n_ar_afip_responsibility_type_id IS NOT NULL
    """)
    ar_partners = cr.fetchone()[0] if cr.fetchone() else 0
    
    # Count fiscal positions with AFIP responsibility types
    cr.execute("""
        SELECT COUNT(DISTINCT fp.id)
        FROM account_fiscal_position fp
        JOIN account_fiscal_position_l10n_ar_afip_responsibility_type_rel rel 
        ON rel.account_fiscal_position_id = fp.id
    """)
    configured_fpos = cr.fetchone()[0] if cr.fetchone() else 0
    
    # Count AR companies
    cr.execute("""
        SELECT COUNT(*)
        FROM res_company 
        WHERE country_id = (SELECT id FROM res_country WHERE code = 'AR')
    """)
    ar_companies = cr.fetchone()[0] if cr.fetchone() else 0
    
    _logger.info("Migration statistics - AR Partners: %d, Configured Fiscal Positions: %d, AR Companies: %d",
                ar_partners, configured_fpos, ar_companies)