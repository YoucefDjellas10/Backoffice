# -*- coding: utf-8 -*-
{
    'name': "MRP Date Filters",

    'summary': "MRP Date Filters",

    'description': """
    This add-on is a funtional plug-in that creates a fixed filter bar in the MRP module for list views.
    
    """,

    'author': "Odoo.RED team",
    'website': "https://cdn.odoo.red",
    'category': 'Extra Tools',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'gestion_finance', 'reservation'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_header_search/static/src/js/date_search.js',
            'mrp_header_search/static/src/js/header_select_model.js',
            'mrp_header_search/static/src/js/mrp_production_list.js',
            'mrp_header_search/static/src/xml/header_select_model.xml',
            'mrp_header_search/static/src/css/header_select_model.css',
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'images': ['static/description/images/mrp.jpg'],
    'sequence': 100
}
