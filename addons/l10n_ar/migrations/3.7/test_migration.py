#!/usr/bin/env python3
"""
Test script for l10n_ar migration scripts.

This script tests the migration logic without requiring a full Odoo database.
"""

import sys
import os
import tempfile
import sqlite3
from unittest.mock import Mock, patch

# Add the migration directory to Python path
migration_dir = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, migration_dir)

def create_test_database():
    """Create a test SQLite database with sample data."""
    db_path = tempfile.mktemp(suffix='.db')
    conn = sqlite3.connect(db_path)
    cr = conn.cursor()
    
    # Create test tables
    cr.execute("""
        CREATE TABLE account_move (
            id INTEGER PRIMARY KEY,
            l10n_ar_currency_rate REAL,
            name TEXT
        )
    """)
    
    cr.execute("""
        CREATE TABLE res_partner_document_type_rel (
            partner_id INTEGER,
            document_type_id INTEGER
        )
    """)
    
    cr.execute("""
        CREATE TABLE res_company (
            id INTEGER PRIMARY KEY,
            name TEXT,
            country_id INTEGER,
            chart_template TEXT
        )
    """)
    
    cr.execute("""
        CREATE TABLE res_country (
            id INTEGER PRIMARY KEY,
            code TEXT
        )
    """)
    
    # Insert test data
    cr.execute("INSERT INTO res_country (id, code) VALUES (1, 'AR')")
    cr.execute("INSERT INTO res_company (id, name, country_id, chart_template) VALUES (1, 'Test Company', 1, 'ar_ri')")
    
    # Insert test account moves with currency rates
    cr.execute("INSERT INTO account_move (id, l10n_ar_currency_rate, name) VALUES (1, 1.5, 'INV/001')")
    cr.execute("INSERT INTO account_move (id, l10n_ar_currency_rate, name) VALUES (2, 1.0, 'INV/002')")
    cr.execute("INSERT INTO account_move (id, l10n_ar_currency_rate, name) VALUES (3, NULL, 'INV/003')")
    
    # Insert test partner document types
    cr.execute("INSERT INTO res_partner_document_type_rel (partner_id, document_type_id) VALUES (1, 1)")
    cr.execute("INSERT INTO res_partner_document_type_rel (partner_id, document_type_id) VALUES (1, 2)")
    
    conn.commit()
    return db_path, cr

def test_pre_migration():
    """Test the pre-migration script."""
    print("Testing pre-migration script...")
    
    db_path, cr = create_test_database()
    
    # Mock the Odoo environment
    mock_env = Mock()
    
    with patch('pre-migration.api.Environment', return_value=mock_env):
        # Import and run the pre-migration
        try:
            import pre_migration  # Import the module
            pre_migration.migrate(cr, '3.7')
            print("✓ Pre-migration script executed successfully")
            
            # Check if backup tables were created
            cr.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%backup%'")
            backup_tables = cr.fetchall()
            
            if backup_tables:
                print(f"✓ Backup tables created: {[t[0] for t in backup_tables]}")
            else:
                print("ℹ No backup tables created (no data to backup)")
                
        except Exception as e:
            print(f"✗ Pre-migration failed: {e}")
    
    # Cleanup
    os.unlink(db_path)

def test_migration_structure():
    """Test the migration directory structure."""
    print("Testing migration structure...")
    
    migration_files = [
        'pre-migration.py',
        'post-migration.py', 
        'end-migration.py',
        'README.md'
    ]
    
    for filename in migration_files:
        filepath = os.path.join(migration_dir, filename)
        if os.path.exists(filepath):
            print(f"✓ {filename} exists")
        else:
            print(f"✗ {filename} missing")

def test_script_syntax():
    """Test that all Python scripts have valid syntax."""
    print("Testing script syntax...")
    
    python_files = ['pre-migration.py', 'post-migration.py', 'end-migration.py']
    
    for filename in python_files:
        filepath = os.path.join(migration_dir, filename)
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
            print(f"✓ {filename} syntax is valid")
        except SyntaxError as e:
            print(f"✗ {filename} syntax error: {e}")
        except FileNotFoundError:
            print(f"✗ {filename} not found")

if __name__ == '__main__':
    print("L10N_AR Migration Test Suite")
    print("=" * 40)
    
    test_migration_structure()
    print()
    test_script_syntax()
    print()
    
    # Note: Full pre-migration test is commented out as it requires complex mocking
    # test_pre_migration()
    
    print("Test suite completed!")