# L10N_AR Migration from 17.0 to 18.0

This document describes the migration process for the `l10n_ar` (Argentina - Accounting) module from Odoo 17.0 to 18.0.

## Overview

The l10n_ar module has undergone several changes in version 18.0 that require database migration to ensure data integrity and proper functionality.

## Migration Scripts

The migration is handled by three scripts located in `addons/l10n_ar/migrations/3.7/`:

1. **pre-migration.py** - Handles field removals and data backup before upgrade
2. **post-migration.py** - Performs data updates and configuration changes after upgrade  
3. **end-migration.py** - Final cleanup and validation

## Changes Migrated

### 1. Field Removals

#### `account.move.l10n_ar_currency_rate`
- **Status**: REMOVED in 18.0
- **Reason**: This field is no longer needed as currency rate handling has been improved
- **Migration**: Data is backed up to `account_move_l10n_ar_currency_rate_backup` table
- **Impact**: Custom currency rates on invoices will need to be handled differently

#### `res.partner.l10n_ar_special_purchase_document_type_ids`
- **Status**: REMOVED in 18.0
- **Reason**: Field was deprecated and no longer needed
- **Migration**: Data is backed up to `res_partner_l10n_ar_special_purchase_document_types_backup` table
- **Impact**: Special purchase document types need to be configured differently

### 2. Model Method Changes

#### `account.fiscal.position._get_fiscal_position()` → `_get_fpos_ranking_functions()`
- **Status**: REFACTORED in 18.0
- **Reason**: Improved performance and maintainability
- **Migration**: Logic is automatically updated, no data migration needed
- **Impact**: Fiscal position detection may be more accurate

#### Product Type Logic in AFIP Concept Calculation
- **Status**: CHANGED in 18.0
- **Change**: `consumable = {'consu', 'product'}` → `consumable = {'consu'}`
- **Impact**: AFIP concept calculation for invoices with 'product' type items may change
- **Migration**: Affected invoices are logged for manual review

### 3. Manifest Changes

#### Dependencies
- **Added**: `'account'` dependency
- **Added**: `'auto_install': ['account']` directive
- **Impact**: Module will auto-install with account module

#### Documentation
- **Changed**: Documentation URL updated from 17.0 to master

## Backup Tables Created

The migration creates backup tables for removed fields:

### `account_move_l10n_ar_currency_rate_backup`
```sql
CREATE TABLE account_move_l10n_ar_currency_rate_backup (
    move_id INTEGER PRIMARY KEY,
    currency_rate NUMERIC,
    backup_date TIMESTAMP DEFAULT NOW()
);
```

### `res_partner_l10n_ar_special_purchase_document_types_backup`
```sql
CREATE TABLE res_partner_l10n_ar_special_purchase_document_types_backup (
    partner_id INTEGER,
    document_type_id INTEGER,
    backup_date TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (partner_id, document_type_id)
);
```

## Manual Actions Required

### 1. Review Currency Rates
If your database uses custom currency rates on invoices:
1. Check the `account_move_l10n_ar_currency_rate_backup` table for backed up data
2. Implement alternative currency rate handling if needed
3. Consider using Odoo's standard currency rate mechanism

### 2. Review Special Purchase Document Types
If you were using special purchase document types on partners:
1. Check the `res_partner_l10n_ar_special_purchase_document_types_backup` table
2. Reconfigure document types using the standard AFIP configuration
3. Update any custom workflows that depended on this field

### 3. Review Invoices with Product Type Items
If you have invoices with product type items:
1. Check the migration logs for affected invoice IDs
2. Verify that AFIP concepts are still calculated correctly
3. Update any custom logic that depended on the old product type classification

## Validation Steps

After migration, perform these validation steps:

### 1. Test Fiscal Position Detection
```python
# In Odoo shell
partner = env['res.partner'].search([('l10n_ar_afip_responsibility_type_id', '!=', False)], limit=1)
fpos = env['account.fiscal.position']._get_fiscal_position(partner)
print(f"Fiscal position for {partner.name}: {fpos.name if fpos else 'None'}")
```

### 2. Test AFIP Concept Calculation
```python
# In Odoo shell
invoice = env['account.move'].search([
    ('company_id.country_id.code', '=', 'AR'),
    ('state', '=', 'posted')
], limit=1)
invoice._compute_l10n_ar_afip_concept()
print(f"AFIP concept for {invoice.name}: {invoice.l10n_ar_afip_concept}")
```

### 3. Check Data Integrity
```sql
-- Check for orphaned AFIP responsibility types
SELECT COUNT(*) FROM res_partner 
WHERE l10n_ar_afip_responsibility_type_id IS NOT NULL
  AND l10n_ar_afip_responsibility_type_id NOT IN (
      SELECT id FROM l10n_ar_afip_responsibility_type
  );

-- Check for orphaned document types
SELECT COUNT(*) FROM account_move 
WHERE l10n_latam_document_type_id IS NOT NULL
  AND l10n_latam_document_type_id NOT IN (
      SELECT id FROM l10n_latam_document_type
  );
```

## Cleanup

After validating the migration is successful, you can remove the backup tables:

```sql
DROP TABLE IF EXISTS account_move_l10n_ar_currency_rate_backup;
DROP TABLE IF EXISTS res_partner_l10n_ar_special_purchase_document_types_backup;
```

## Troubleshooting

### Migration Fails to Start
- Ensure the l10n_ar module is installed and functional in 17.0
- Check database permissions for creating backup tables
- Verify that all dependencies are properly installed

### Data Inconsistencies After Migration
- Check the backup tables for original data
- Verify that chart of account templates were properly reloaded
- Review custom modules that might interact with removed fields

### Performance Issues
- The new fiscal position ranking system should improve performance
- If you experience issues, check for custom fiscal position configurations
- Consider rebuilding fiscal position caches

## Support

For issues specific to this migration:
1. Check the migration logs in the Odoo server output
2. Verify that all backup tables were created successfully
3. Review the validation results in the end-migration script output
4. Consult the backup tables for data recovery if needed

For general l10n_ar module support, refer to the official Odoo documentation:
https://www.odoo.com/documentation/master/applications/finance/fiscal_localizations/argentina.html