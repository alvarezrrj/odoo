# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
End-migration script for l10n_ar module from 17.0 to 18.0

This script performs final validations and cleanup after all modules have been updated:
1. Final validation of CUIT format compliance
2. Verification of fiscal position ranking system
3. Cleanup of migration backup data
4. Final integrity checks
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    End-migration steps for l10n_ar module upgrade from 17.0 to 18.0
    
    Args:
        cr: Database cursor
        version: Version from which we are migrating
    """
    _logger.info("Starting l10n_ar end-migration from version %s to 18.0", version)
    
    # Validate CUIT formats for Argentinian partners
    _validate_cuit_formats(cr)
    
    # Verify fiscal position ranking system is working
    _verify_fiscal_position_ranking(cr)
    
    # Validate chart template configurations
    _validate_chart_templates(cr)
    
    # Clean up migration backup data
    _cleanup_migration_data(cr)
    
    # Perform final integrity checks
    _final_integrity_checks(cr)
    
    _logger.info("Completed l10n_ar end-migration successfully")


def _validate_cuit_formats(cr):
    """Validate that all CUIT numbers follow the correct format"""
    _logger.info("Validating CUIT formats for Argentinian partners")
    
    # Get CUIT identification type
    cr.execute("""
        SELECT id FROM l10n_latam_identification_type 
        WHERE name = 'CUIT' AND country_id = (
            SELECT id FROM res_country WHERE code = 'AR'
        )
    """)
    cuit_type_result = cr.fetchone()
    if not cuit_type_result:
        _logger.warning("CUIT identification type not found")
        return
    
    cuit_type_id = cuit_type_result[0]
    
    # Check for invalid CUIT formats
    cr.execute("""
        SELECT p.id, p.name, p.vat
        FROM res_partner p
        WHERE p.l10n_latam_identification_type_id = %s
        AND p.vat IS NOT NULL
        AND (
            LENGTH(REGEXP_REPLACE(p.vat, '[^0-9]', '', 'g')) != 11  -- Should be 11 digits
            OR p.vat !~ '^[0-9]{2}-[0-9]{8}-[0-9]$'  -- Format: XX-XXXXXXXX-X
        )
        LIMIT 10
    """, (cuit_type_id,))
    
    invalid_cuits = cr.fetchall()
    if invalid_cuits:
        _logger.warning("Found %d partners with invalid CUIT format (showing first 10):", len(invalid_cuits))
        for partner_id, name, vat in invalid_cuits:
            _logger.warning("Partner ID %d (%s): Invalid CUIT format '%s'", partner_id, name, vat)
    else:
        _logger.info("All CUIT formats are valid")


def _verify_fiscal_position_ranking(cr):
    """Verify that fiscal position ranking system is properly configured"""
    _logger.info("Verifying fiscal position ranking system configuration")
    
    # Check that fiscal positions have proper AFIP responsibility type mapping
    cr.execute("""
        SELECT 
            COUNT(CASE WHEN rel.l10n_ar_afip_responsibility_type_id IS NOT NULL THEN 1 END) as with_afip,
            COUNT(*) as total
        FROM account_fiscal_position fp
        LEFT JOIN account_fiscal_position_l10n_ar_afip_responsibility_type_rel rel 
        ON rel.account_fiscal_position_id = fp.id
        JOIN res_company c ON c.id = fp.company_id
        WHERE c.country_id = (SELECT id FROM res_country WHERE code = 'AR')
        AND fp.auto_apply = true
    """)
    
    result = cr.fetchone()
    if result:
        with_afip, total = result
        if total > 0:
            percentage = (with_afip / total) * 100
            _logger.info("Fiscal position AFIP mapping: %d/%d (%.1f%%) have AFIP responsibility type mapping", 
                        with_afip, total, percentage)
            
            if percentage < 80:  # Less than 80% configured
                _logger.warning("Low percentage of fiscal positions have AFIP responsibility type mapping")


def _validate_chart_templates(cr):
    """Validate chart template configurations"""
    _logger.info("Validating chart template configurations")
    
    # Check that AR chart templates have proper sequence values
    cr.execute("""
        SELECT code, sequence, name
        FROM account_chart_template
        WHERE code IN ('ar_base', 'ar_ex', 'ar_ri')
        ORDER BY sequence
    """)
    
    templates = cr.fetchall()
    expected_sequences = {'ar_ri': 0, 'ar_base': 1, 'ar_ex': 2}
    
    for code, sequence, name in templates:
        expected = expected_sequences.get(code)
        if sequence != expected:
            _logger.warning("Chart template %s has sequence %s, expected %s", code, sequence, expected)
        else:
            _logger.info("Chart template %s has correct sequence %s", code, sequence)


def _cleanup_migration_data(cr):
    """Clean up temporary migration data"""
    _logger.info("Cleaning up migration backup data")
    
    # Check if backup table exists and log its contents
    cr.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'l10n_ar_migration_backup_special_docs'
        AND table_schema = current_schema()
    """)
    
    if cr.fetchone():
        # Log how much data we're about to clean up
        cr.execute("SELECT COUNT(*) FROM l10n_ar_migration_backup_special_docs")
        backup_count = cr.fetchone()[0] if cr.fetchone() else 0
        
        if backup_count > 0:
            _logger.info("Migration backup contained data for %d partners with special purchase documents", backup_count)
            
            # Optionally, create a final report of what was migrated
            cr.execute("""
                SELECT partner_name, array_length(document_type_names, 1) as doc_count
                FROM l10n_ar_migration_backup_special_docs
                ORDER BY partner_name
                LIMIT 5
            """)
            sample_data = cr.fetchall()
            _logger.info("Sample migrated data: %s", sample_data)
        
        # Drop the backup table
        cr.execute("DROP TABLE l10n_ar_migration_backup_special_docs")
        _logger.info("Cleaned up migration backup table")


def _final_integrity_checks(cr):
    """Perform final integrity checks"""
    _logger.info("Performing final integrity checks")
    
    # Check for orphaned AFIP responsibility type references
    cr.execute("""
        SELECT COUNT(*)
        FROM res_partner p
        WHERE p.l10n_ar_afip_responsibility_type_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM l10n_ar_afip_responsibility_type art
            WHERE art.id = p.l10n_ar_afip_responsibility_type_id
        )
    """)
    orphaned_partners = cr.fetchone()[0] if cr.fetchone() else 0
    if orphaned_partners > 0:
        _logger.error("Found %d partners with orphaned AFIP responsibility type references", orphaned_partners)
    
    # Check for companies with AR country but no AFIP responsibility type
    cr.execute("""
        SELECT COUNT(*)
        FROM res_company c
        WHERE c.country_id = (SELECT id FROM res_country WHERE code = 'AR')
        AND c.partner_id NOT IN (
            SELECT id FROM res_partner 
            WHERE l10n_ar_afip_responsibility_type_id IS NOT NULL
        )
    """)
    companies_without_afip = cr.fetchone()[0] if cr.fetchone() else 0
    if companies_without_afip > 0:
        _logger.warning("Found %d AR companies without AFIP responsibility type", companies_without_afip)
    
    # Check for sale journals without AFIP POS configuration
    cr.execute("""
        SELECT COUNT(*)
        FROM account_journal j
        JOIN res_company c ON c.id = j.company_id
        WHERE c.country_id = (SELECT id FROM res_country WHERE code = 'AR')
        AND j.type = 'sale'
        AND j.l10n_ar_afip_pos_number IS NULL
    """)
    journals_without_pos = cr.fetchone()[0] if cr.fetchone() else 0
    if journals_without_pos > 0:
        _logger.warning("Found %d sale journals without AFIP POS number configuration", journals_without_pos)
    
    _logger.info("Final integrity checks completed")