# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Odoo Project Dashboard",
    'version': '2.0',
    'category': 'project',
    'summary': "dashboard for projects",
    'depends': ['web','sale_management', 'project', 'sale_timesheet', 'reservation', 'gestion_finance'],
    'data': [
        'views/views.xml'
    ],
    'assets': {
        'web.assets_backend': [

            # 'odoo_dashboard/static/src/css/dashboard.css',
            # 'odoo_dashboard/static/src/css/remplissage_style.css',
            # 'odoo_dashboard/static/src/css/recette_style.css',

            'https://cdn.jsdelivr.net/npm/chart.js',
            'odoo_dashboard/static/src/js/dashboard.js',
            'odoo_dashboard/static/src/js/helper.js',
            'odoo_dashboard/static/src/js/remplissage_dashboard.js',
            'odoo_dashboard/static/src/js/recette_dashboard.js',
            'odoo_dashboard/static/src/js/previsionnaire_dashboard.js',
            'odoo_dashboard/static/src/js/depense_dashboard.js',

            'odoo_dashboard/static/src/xml/dashboard.xml',
            'odoo_dashboard/static/src/xml/remplissage_template.xml',
            'odoo_dashboard/static/src/xml/recette_template.xml',
            'odoo_dashboard/static/src/xml/previsionnaire_template.xml',
            'odoo_dashboard/static/src/xml/depense_tamplate.xml',

        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
