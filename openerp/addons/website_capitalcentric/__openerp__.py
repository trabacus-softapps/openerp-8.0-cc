{
    'name': 'Capital Centric Website',
    'category': 'Website',
    'summary': 'Generate Leads From Capital Centric',
    'version': '1.0',
    'description': """
OpenERP Capital Centric
========================""",
    'author': 'OpenERP SA',
    'depends': ['website'],
    'data': 
    [   
        'views/payments.xml',
        'cc_link.xml',
        'models/cc_config.xml',
        'views/operator_login.xml',
        'views/search.xml',
        'views/result.xml',
        'views/restaurant_login.xml',
        'views/fit.xml',
        'views/tc.xml',
        'views/help.xml',
        'views/profile.xml',
        'views/profile_contact.xml',
        'views/profile_restaurant.xml', 
        'views/choice_dining.xml', 
    ],
    
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
}
