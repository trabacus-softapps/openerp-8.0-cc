{
    'name'    : 'Trabacus CapitalCentric',
    'version' : '1.0',
    'category': 'Restaurant',
    'summary': 'Enquiries,Invoicing,Mailing,Reports',
    'description': """
Trabacus Enterprises solution for Restaurant 
================================================""",

    'author' : 'Trabacus Technologies Pvt Ltd',
    'website': 'http://www.trabacus.com/',
    'depends': ['base','base_setup', 'crm', 'sale','account','account_accountant','account_cancel','portal_sale','account_financial_report_webkit','report_webkit'],  
    'data'   : [                                
                'security/cc_security_groups.xml', 
               'cc_report.xml',
                'cc_config.xml',  
                'cc_lead.xml',
#                 'cc_sale.xml',
                'cc_partner.xml', 
                'cc_link.xml',
                'cc_account.xml',   
                'cc_default.xml',  
                'wizard/cc_mail_message.xml',      
                'wizard/cc_invoice_group_view.xml', 
                'wizard/cc_wizard.xml',
                'reports/standard/cc_report.xml',    
                'data/crm.case.stage.csv', 
                'data/cc.time.csv',       
                'security/cc_rules.xml',        
                'security/ir.model.access.csv',  
               ], 
    
    
    'qweb': [ 'static/src/xml/cc_mail.xml',
             'static/src/xml/cc_announcement.xml'],

    'css': ['static/src/css/capital.css'],
    
    'js': ['static/src/js/form.js',
           'static/src/js/cc_mail.js',],
                   
    'installable' : True,
    'auto_install': False, 
 
}
