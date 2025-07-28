#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Part of OpenUpgrade. See LICENSE file for full copyright and licensing details.

"""
Demo script showing OpenUpgrade Migration Framework capabilities
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from module_analyzer import analyze_module_changes
from migration_generator import generate_migration_scripts


def create_demo_module_v1(base_path):
    """Create demo module version 1.0.0"""
    module_path = base_path / 'demo_crm_v1'
    module_path.mkdir(exist_ok=True)
    
    # Manifest
    manifest = """{
    'name': 'Demo CRM Module',
    'version': '1.0.0',
    'category': 'Sales',
    'depends': ['base', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/demo_data.xml',
        'views/customer_views.xml',
    ],
    'installable': True,
}"""
    (module_path / '__manifest__.py').write_text(manifest)
    
    # Models
    models_dir = module_path / 'models'
    models_dir.mkdir(exist_ok=True)
    
    (models_dir / '__init__.py').write_text('from . import customer')
    
    customer_model = """# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Customer(models.Model):
    _name = 'demo.customer'
    _description = 'Demo Customer'
    
    name = fields.Char('Name', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    old_status = fields.Char('Status')  # Will be removed
    notes = fields.Text('Notes')
    partner_id = fields.Many2one('res.partner', 'Partner')
"""
    (models_dir / 'customer.py').write_text(customer_model)
    
    return module_path


def create_demo_module_v2(base_path):
    """Create demo module version 2.0.0"""
    module_path = base_path / 'demo_crm_v2'
    module_path.mkdir(exist_ok=True)
    
    # Manifest - updated version and dependencies
    manifest = """{
    'name': 'Demo CRM Module',
    'version': '2.0.0',
    'category': 'Sales',
    'depends': ['base', 'crm', 'mail'],  # Added mail dependency
    'data': [
        'security/ir.model.access.csv',
        'data/demo_data.xml',
        'data/customer_categories.xml',  # New data file
        'views/customer_views.xml',
        'views/category_views.xml',  # New views
    ],
    'installable': True,
}"""
    (module_path / '__manifest__.py').write_text(manifest)
    
    # Models
    models_dir = module_path / 'models'
    models_dir.mkdir(exist_ok=True)
    
    (models_dir / '__init__.py').write_text('from . import customer, category')
    
    # Updated customer model
    customer_model = """# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Customer(models.Model):
    _name = 'demo.customer'
    _description = 'Demo Customer'
    _inherit = ['mail.thread']  # Added mail tracking
    
    name = fields.Char('Name', required=True, tracking=True)
    email = fields.Char('Email', tracking=True)
    phone = fields.Char('Phone')
    # old_status removed, replaced with selection field
    status = fields.Selection([
        ('prospect', 'Prospect'),
        ('customer', 'Customer'),
        ('inactive', 'Inactive'),
    ], 'Status', default='prospect', tracking=True)
    notes = fields.Text('Notes')
    partner_id = fields.Many2one('res.partner', 'Partner')
    category_id = fields.Many2one('demo.customer.category', 'Category')  # New field
    priority = fields.Integer('Priority', default=1)  # New field
"""
    (models_dir / 'customer.py').write_text(customer_model)
    
    # New category model
    category_model = """# -*- coding: utf-8 -*-

from odoo import models, fields


class CustomerCategory(models.Model):
    _name = 'demo.customer.category'
    _description = 'Customer Category'
    
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
"""
    (models_dir / 'category.py').write_text(category_model)
    
    return module_path


def run_demo():
    """Run the migration framework demo"""
    print("OpenUpgrade Migration Framework Demo")
    print("=" * 50)
    
    # Create temporary directory for demo modules
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print("Creating demo modules...")
        v1_path = create_demo_module_v1(temp_path)
        v2_path = create_demo_module_v2(temp_path)
        
        print(f"✓ Created demo_crm v1.0.0 at {v1_path}")
        print(f"✓ Created demo_crm v2.0.0 at {v2_path}")
        print()
        
        # Analyze changes
        print("Analyzing module changes...")
        analysis = analyze_module_changes(str(v1_path), str(v2_path))
        
        print("✓ Analysis completed")
        print()
        
        # Generate migration scripts
        print("Generating migration scripts...")
        scripts, summary = generate_migration_scripts('demo_crm', '2.0.0', analysis)
        
        print("✓ Migration scripts generated")
        print()
        
        # Display results
        print("Migration Analysis Results:")
        print("-" * 30)
        print(summary)
        print()
        
        # Save scripts to current directory for inspection
        output_dir = Path('./demo_output')
        output_dir.mkdir(exist_ok=True)
        
        script_dir = output_dir / 'demo_crm' / '2.0.0'
        script_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in scripts.items():
            script_path = script_dir / filename
            script_path.write_text(content)
            print(f"✓ Saved {script_path}")
        
        print()
        print("Demo completed! Check the 'demo_output' directory for generated scripts.")
        print()
        print("Key features demonstrated:")
        print("- Automatic detection of manifest changes (version, dependencies)")
        print("- Model additions (demo.customer.category)")
        print("- Field changes (old_status removed, status/category_id/priority added)")
        print("- Inheritance changes (mail.thread added)")
        print("- Data file additions")
        print("- Generation of proper OpenUpgrade migration scripts")


if __name__ == '__main__':
    run_demo()