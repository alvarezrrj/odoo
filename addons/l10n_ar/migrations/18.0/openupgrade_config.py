# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
OpenUpgrade configuration for l10n_ar module migration from 17.0 to 18.0

This configuration file provides metadata for OpenUpgrade framework compatibility
and documents the migration strategy for automated processing.
"""

# OpenUpgrade migration configuration
# This follows the openupgradelib conventions for automated migrations

# Fields that have been removed in this version
REMOVED_FIELDS = {
    'res.partner': [
        'l10n_ar_special_purchase_document_type_ids',  # Deprecated field removed
    ],
}

# Tables that have been removed in this version  
REMOVED_TABLES = [
    'res_partner_document_type_rel',  # Many2many relation table for deprecated field
]

# Fields that have been renamed (none in this migration)
RENAMED_FIELDS = {
    # No field renames in this migration
}

# Models that have been renamed (none in this migration)
RENAMED_MODELS = {
    # No model renames in this migration
}

# XML IDs that have been removed or renamed
RENAMED_XML_IDS = {
    # No XML ID changes in this migration
}

# New columns that need special handling
NEW_COLUMNS = {
    'account_chart_template': [
        ('sequence', 'INTEGER'),  # New sequence field for template ordering
    ],
}

# Configuration for openupgradelib functions
OPENUPGRADE_CONFIG = {
    'version': '18.0',
    'module': 'l10n_ar',
    'description': 'Argentina localization migration from 17.0 to 18.0',
    'author': 'Odoo Community',
    'depends': ['account', 'l10n_latam_base', 'l10n_latam_invoice_document'],
    'migration_scripts': {
        'pre': 'pre-migration.py',
        'post': 'post-migration.py', 
        'end': 'end-migration.py',
    },
    'manual_review_required': [
        'CUIT number validation - may reject previously valid numbers',
        'Fiscal position configuration - verify AFIP responsibility type mappings',
        'Chart template selection - automatic for new companies only',
    ],
    'data_loss_risk': {
        'l10n_ar_special_purchase_document_type_ids': 'LOW',  # Deprecated field, data backed up
    },
    'performance_impact': 'MINIMAL',  # Changes improve performance overall
    'rollback_complexity': 'MEDIUM',  # Requires restoration of deprecated field structure
}

# Migration validation rules
VALIDATION_RULES = {
    'required_data_integrity': [
        'All AFIP responsibility types must have valid references',
        'All fiscal positions must have proper company assignments',
        'All CUIT numbers must follow format XX-XXXXXXXX-X',
    ],
    'optional_optimizations': [
        'Chart template sequence ordering',
        'Fiscal position ranking optimization',
        'Enhanced validation message translations',
    ],
}

# Compatibility matrix
COMPATIBILITY_MATRIX = {
    'odoo_versions': ['18.0'],
    'openupgrade_versions': ['>=5.0'],
    'python_versions': ['>=3.8'],
    'postgresql_versions': ['>=12'],
}

# Migration timeline estimates
MIGRATION_ESTIMATES = {
    'small_database': '< 5 minutes',   # < 1000 partners
    'medium_database': '5-15 minutes', # 1000-10000 partners  
    'large_database': '15-30 minutes', # > 10000 partners
    'downtime_required': True,
    'can_run_online': False,  # Requires exclusive access for schema changes
}

# Post-migration verification checklist
VERIFICATION_CHECKLIST = [
    'All Argentinian partners have valid AFIP responsibility types',
    'Fiscal positions have proper AFIP responsibility type mappings',
    'CUIT numbers validate against enhanced rules',
    'Chart templates have correct sequence ordering',
    'Sale journals have AFIP POS number configuration',
    'No orphaned references to removed fields',
    'Migration backup tables are cleaned up',
]

# Support and documentation
SUPPORT_INFO = {
    'documentation': [
        'addons/l10n_ar/migrations/18.0/README.md',
        'addons/l10n_ar/migrations/MIGRATION_SUMMARY.md',
    ],
    'validation_scripts': [
        'SQL queries provided in README.md',
        'Python validation in end-migration.py',
    ],
    'troubleshooting_guide': 'README.md#troubleshooting',
    'rollback_procedure': 'Manual restoration required for deprecated fields',
}