# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
Pre-migration script for l10n_ar module from 17.0 to 18.0

This script handles the preparation for the migration by:
1. Backing up data from deprecated fields before they are removed
2. Preparing for enhanced validation logic
3. Logging current state for post-migration validation
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration steps for l10n_ar module upgrade from 17.0 to 18.0
    
    Args:
        cr: Database cursor
        version: Version from which we are migrating
    """
    _logger.info("Starting l10n_ar pre-migration from version %s to 18.0", version)
    
    # Check if the deprecated field exists in res.partner
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' 
        AND column_name = 'l10n_ar_special_purchase_document_type_ids'
    """)
    
    if cr.fetchone():
        _logger.info("Found deprecated field l10n_ar_special_purchase_document_type_ids in res.partner")
        
        # Create a backup table for the deprecated field data
        cr.execute("""
            CREATE TABLE IF NOT EXISTS l10n_ar_migration_backup_special_docs AS
            SELECT 
                p.id as partner_id,
                p.name as partner_name,
                array_agg(dt.id) as document_type_ids,
                array_agg(dt.name) as document_type_names
            FROM res_partner p
            JOIN res_partner_document_type_rel rel ON rel.partner_id = p.id
            JOIN l10n_latam_document_type dt ON dt.id = rel.document_type_id
            WHERE p.l10n_ar_afip_responsibility_type_id IS NOT NULL
            GROUP BY p.id, p.name
        """)
        
        # Log how many partners will be affected
        cr.execute("""
            SELECT COUNT(DISTINCT partner_id) 
            FROM l10n_ar_migration_backup_special_docs
        """)
        count = cr.fetchone()[0] if cr.fetchone() else 0
        _logger.info("Backed up special purchase document data for %d partners", count)
    
    # Validate current AFIP responsibility types before migration
    cr.execute("""
        SELECT COUNT(*) 
        FROM res_partner 
        WHERE l10n_ar_afip_responsibility_type_id IS NOT NULL
        AND country_id = (SELECT id FROM res_country WHERE code = 'AR')
    """)
    ar_partners_count = cr.fetchone()[0] if cr.fetchone() else 0
    _logger.info("Found %d Argentinian partners with AFIP responsibility types", ar_partners_count)
    
    # Check for fiscal positions that use l10n_ar_afip_responsibility_type_ids
    cr.execute("""
        SELECT COUNT(DISTINCT fp.id)
        FROM account_fiscal_position fp
        JOIN account_fiscal_position_l10n_ar_afip_responsibility_type_rel rel 
        ON rel.account_fiscal_position_id = fp.id
    """)
    fpos_count = cr.fetchone()[0] if cr.fetchone() else 0
    _logger.info("Found %d fiscal positions with AFIP responsibility type mappings", fpos_count)
    
    # Check for companies using AR chart templates
    cr.execute("""
        SELECT COUNT(*)
        FROM res_company 
        WHERE chart_template IN ('ar_base', 'ar_ex', 'ar_ri')
        OR country_id = (SELECT id FROM res_country WHERE code = 'AR')
    """)
    ar_companies_count = cr.fetchone()[0] if cr.fetchone() else 0
    _logger.info("Found %d companies using Argentinian configuration", ar_companies_count)
    
    _logger.info("Completed l10n_ar pre-migration preparation")