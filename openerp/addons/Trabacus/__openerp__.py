# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Trabacus',
    'version': '1.0',
    'category': 'Travel Management',
    
    'summary': 'Leads, Sales Orders, Invoicing, Reports',
    'description': """
            Module for Travel Enterprises
""",

    'author': 'Trabacus Technologies',
    'maintainer': 'Trabacus Technologies',
    'website': 'http://www.trabacus.com',
    
    'depends': ['base', 'crm','crm_todo', 'sale_crm', 'account', 'account_voucher','multi_company'],
    
    'data': [
             'tr_users.xml',
             
             'security/tr_security_groups.xml',
             'security/tr_security_menu.xml',
             'default_data.xml',
             'data_workflow.xml',
             'wizard/tr_wizard.xml',
             'views/tr_report.xml',
             
             'views/tr_report_wizard.xml',

             'tr_config.xml', 
             'tr_partner.xml',
             'tr_lead.xml',
             
             'tr_product.xml',
             'tr_product_flight.xml',
             'tr_product_domp.xml',
            
             'tr_invoice_car.xml',
             'tr_invoice_cruise.xml',
             'tr_invoice_flight.xml',
             'tr_invoice_hotel.xml',
             'tr_invoice_railway.xml', 
             'tr_invoice_visa.xml',
             'tr_invoice_insurance.xml',
             'tr_invoice_other.xml',
             
             'tr_invoice_package.xml',
             'tr_invoice.xml',
             'tr_invoices_sales.xml',
             'tr_invoices_supplier.xml',
             'tr_invoices_purchase.xml',
             'tr_account.xml',
             
             'wizard/tr_bsp_reconcilation.xml',
             'wizard/tr_invoice2refund.xml',
             
             'report/standard/tr_account_ledger.xml',
             'security/tr_security_rules.xml',
             'security/ir.model.access.csv',
             
             
              'data_config.xml'
             ], 
             
    'css': ['static/src/css/trabacus.css'],
    'js': ['static/src/js/trabacus.js'], 
    
    'installable': True,
    'auto_install': False,
} 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: