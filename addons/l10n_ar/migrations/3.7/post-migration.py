# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""
Post-migration script for l10n_ar module upgrade from 17.0 to 18.0.

This script handles data updates and configurations after the module upgrade.
"""

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration script for l10n_ar upgrade to version 3.7 (Odoo 18.0).
    
    Changes handled:
    1. Update account fiscal position logic for new ranking functions
    2. Update product type filtering logic (consumable set change)
    3. Ensure all chart of account templates are properly updated
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("Starting l10n_ar post-migration to version 3.7")
    
    # 1. Update fiscal position configurations if needed
    _update_fiscal_position_ranking(cr, env)
    
    # 2. Update any invoice configurations that might be affected by product type changes
    _update_invoice_product_type_logic(cr, env)
    
    # 3. Reload chart of account templates to ensure latest configurations
    _reload_chart_templates(cr, env)
    
    _logger.info("Completed l10n_ar post-migration to version 3.7")


def _update_fiscal_position_ranking(cr, env):
    """
    Update fiscal position ranking to accommodate new _get_fpos_ranking_functions method.
    
    In 18.0, the fiscal position detection logic changed from _get_fiscal_position 
    to _get_fpos_ranking_functions for better performance and maintainability.
    """
    _logger.info("Updating fiscal position ranking configurations")
    
    # The migration is handled automatically by the new method implementation
    # but we should ensure all fiscal positions have proper AFIP responsibility types
    
    fiscal_positions = env['account.fiscal.position'].search([
        ('company_id.country_id.code', '=', 'AR')
    ])
    
    for fpos in fiscal_positions:
        if not fpos.l10n_ar_afip_responsibility_type_ids:
            _logger.info(f"Fiscal position '{fpos.name}' has no AFIP responsibility types defined")
    
    _logger.info(f"Checked {len(fiscal_positions)} Argentine fiscal positions")


def _update_invoice_product_type_logic(cr, env):
    """
    Update invoice logic for product type changes.
    
    In 18.0, the consumable product type set was changed from {'consu', 'product'} to {'consu'}.
    This may affect how AFIP concepts are computed for existing invoices.
    """
    _logger.info("Updating invoice product type logic")
    
    # Find invoices that might be affected by the product type change
    cr.execute("""
        SELECT DISTINCT am.id
        FROM account_move am
        JOIN account_move_line aml ON am.id = aml.move_id
        JOIN product_product pp ON aml.product_id = pp.id
        JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE am.company_id IN (
            SELECT id FROM res_company 
            WHERE country_id = (SELECT id FROM res_country WHERE code = 'AR')
        )
        AND am.state = 'posted'
        AND pt.type = 'product'
        AND am.l10n_ar_afip_concept IS NOT NULL
    """)
    
    affected_invoice_ids = [row[0] for row in cr.fetchall()]
    
    if affected_invoice_ids:
        _logger.info(f"Found {len(affected_invoice_ids)} invoices with 'product' type that may need AFIP concept recalculation")
        
        # These invoices should be reviewed as the AFIP concept calculation has changed
        # In practice, most 'product' type should now be treated differently in the AFIP concept calculation
        
        # We don't automatically update them as this could affect tax calculations
        # Instead, we log them for manual review
        _logger.warning(
            f"Manual review recommended for invoices with IDs: {affected_invoice_ids[:10]}... "
            f"(showing first 10 of {len(affected_invoice_ids)}) due to product type logic changes"
        )
    else:
        _logger.info("No invoices with 'product' type found, no action needed")


def _reload_chart_templates(cr, env):
    """
    Reload chart of account templates to ensure latest configurations are applied.
    
    This ensures that any chart template changes in 18.0 are properly applied
    to existing companies.
    """
    _logger.info("Reloading chart of account templates for Argentine companies")
    
    # Find all Argentine companies with l10n_ar chart templates
    argentine_companies = env['res.company'].search([
        ('country_id.code', '=', 'AR'),
        ('chart_template', 'in', ['ar_ri', 'ar_ex', 'ar_base'])
    ])
    
    for company in argentine_companies:
        try:
            _logger.info(f"Reloading chart template for company '{company.name}' with template '{company.chart_template}'")
            
            # Try to load the chart template updates
            env['account.chart.template'].try_loading(
                company.chart_template, 
                company, 
                force_create=False
            )
            
        except Exception as e:
            _logger.warning(f"Failed to reload chart template for company '{company.name}': {e}")
    
    _logger.info(f"Processed {len(argentine_companies)} Argentine companies")