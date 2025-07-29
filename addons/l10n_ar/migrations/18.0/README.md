# l10n_ar Migration from 17.0 to 18.0

This directory contains migration scripts for upgrading the Argentina localization module from Odoo 17.0 to 18.0.

## Summary of Changes

### Key Improvements in 18.0

1. **Enhanced AFIP Integration**
   - Improved fiscal position detection using new ranking system
   - Better CUIT validation with enhanced error messages
   - Automatic chart template selection based on AFIP responsibility type

2. **Deprecated Field Removal**
   - Removed `l10n_ar_special_purchase_document_type_ids` field from `res.partner`
   - This field was marked as deprecated and is no longer needed

3. **Improved Validation**
   - Enhanced document number validation for invoices
   - Better error messages with proper translation support
   - Stricter CUIT format validation with component checking

4. **Chart Template Enhancements**
   - Added sequence fields for proper template ordering
   - Automatic template loading based on company AFIP responsibility type
   - Better error handling during template installation

## Migration Scripts

### pre-migration.py
**Purpose**: Preparation before module upgrade
- Backs up data from deprecated fields
- Creates migration statistics
- Validates current configuration state

**Actions**:
- Creates backup table `l10n_ar_migration_backup_special_docs` for deprecated field data
- Logs statistics about affected partners, fiscal positions, and companies
- Validates current AFIP responsibility type assignments

### post-migration.py
**Purpose**: Cleanup and data migration after module upgrade
- Removes deprecated database structures
- Updates configurations for new features
- Validates migrated data

**Actions**:
- Drops deprecated `res_partner_document_type_rel` table
- Sets proper sequence values for chart templates (ar_ri: 0, ar_base: 1, ar_ex: 2)
- Updates partners to use CUIT identification type where appropriate
- Ensures sale journals have proper AFIP POS configuration
- Validates fiscal position configurations

### end-migration.py
**Purpose**: Final validation and cleanup after all modules are updated
- Performs comprehensive data validation
- Cleans up migration artifacts
- Ensures system integrity

**Actions**:
- Validates CUIT formats compliance (11 digits, XX-XXXXXXXX-X format)
- Verifies fiscal position ranking system configuration
- Validates chart template sequence assignments
- Removes migration backup tables
- Performs final integrity checks for orphaned references

## Manual Migration Steps

### Required Manual Actions

1. **Review Fiscal Positions**
   After migration, review your fiscal positions to ensure they have proper AFIP responsibility type mappings:
   ```
   Go to: Accounting > Configuration > Fiscal Positions
   Check: Each fiscal position has appropriate AFIP responsibility types assigned
   ```

2. **Validate CUIT Numbers**
   Check that all CUIT numbers are properly formatted:
   ```
   Go to: Contacts
   Filter: Argentinian partners with AFIP responsibility type
   Verify: CUIT format is XX-XXXXXXXX-X (e.g., 20-12345678-9)
   ```

3. **Update Sale Journal Configuration**
   Ensure all sale journals have AFIP POS numbers configured:
   ```
   Go to: Accounting > Configuration > Journals
   Filter: Sale journals for Argentinian companies
   Check: AFIP POS Number is properly set
   ```

### Optional Manual Actions

1. **Chart Template Selection**
   For new companies, the system will automatically select the appropriate chart template based on AFIP responsibility type. For existing companies, you may want to verify the chart template matches the company's AFIP responsibility:
   
   - **Responsable Inscripto** → `ar_ri` template
   - **Monotributo** → `ar_base` template  
   - **Exento** → `ar_ex` template

2. **Document Type Validation**
   If you previously used the deprecated `l10n_ar_special_purchase_document_type_ids` field, review your purchase document type requirements and ensure they are properly configured through the standard document type system.

## Troubleshooting

### Common Issues

1. **CUIT Validation Errors**
   - **Issue**: Partners with invalid CUIT format
   - **Solution**: Update CUIT numbers to format XX-XXXXXXXX-X
   - **Check**: Valid prefixes are 20, 23, 24, 27, 30, 33, 34, 50, 51, 55

2. **Fiscal Position Not Auto-Selected**
   - **Issue**: Fiscal position not automatically applied
   - **Solution**: Ensure fiscal position has correct AFIP responsibility type mapping
   - **Check**: Fiscal position has `l10n_ar_afip_responsibility_type_ids` configured

3. **Journal Document Number Validation**
   - **Issue**: Document numbers not validating properly
   - **Solution**: Ensure document numbers follow format 1-1 or 00001-00000001
   - **Check**: AFIP POS number is configured in journal

### Validation Queries

You can run these SQL queries to validate the migration:

```sql
-- Check for partners without proper AFIP responsibility type
SELECT id, name FROM res_partner 
WHERE country_id = (SELECT id FROM res_country WHERE code = 'AR')
AND l10n_ar_afip_responsibility_type_id IS NULL
AND is_company = true;

-- Check fiscal positions without AFIP responsibility mapping
SELECT fp.id, fp.name FROM account_fiscal_position fp
JOIN res_company c ON c.id = fp.company_id
WHERE c.country_id = (SELECT id FROM res_country WHERE code = 'AR')
AND NOT EXISTS (
    SELECT 1 FROM account_fiscal_position_l10n_ar_afip_responsibility_type_rel rel
    WHERE rel.account_fiscal_position_id = fp.id
);

-- Check for invalid CUIT formats
SELECT id, name, vat FROM res_partner 
WHERE l10n_latam_identification_type_id = (
    SELECT id FROM l10n_latam_identification_type 
    WHERE name = 'CUIT' AND country_id = (SELECT id FROM res_country WHERE code = 'AR')
)
AND vat !~ '^[0-9]{2}-[0-9]{8}-[0-9]$';
```

## Support

If you encounter issues during migration:

1. Check the migration logs for detailed error messages
2. Review the manual migration steps above
3. Run the validation queries to identify specific issues
4. Consult the Odoo documentation for Argentina localization

For additional support, refer to the official Odoo documentation or community forums.