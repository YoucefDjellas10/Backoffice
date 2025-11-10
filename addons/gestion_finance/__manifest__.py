# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Finance',
    'summary': 'Gestion des Finances',
    'description': "Gestion des Finances",
    'depends': ['base', 'reservation', 'gestion_maintenance'],
    'data': [
        'views/caisse_record_view.xml',
        'views/transfer_argent_view.xml',
        'views/revenue_record_view.xml',
        'views/depense_record_view.xml',
        'views/type_depense_view.xml',
        'views/reservation_inherit.xml',
        'views/livraison_inherit.xml',
        'views/fournisseur_view.xml',
        'views/refund_table_view.xml',
        'views/transfert_revenue_request.xml',
        'views/balance_view.xml',
        'views/template_view.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'gestion_finance/static/src/xml/recape.xml',
            'gestion_finance/static/src/js/recape.js',
            'gestion_finance/static/src/xml/encaissement.xml',
            'gestion_finance/static/src/js/encaissement.js',
            'gestion_finance/static/src/js/revenu.js',
            'gestion_finance/static/src/css/revenu.css',
            'gestion_finance/static/src/xml/revenu.xml',
            'gestion_finance/static/src/js/caisse.js',
            'gestion_finance/static/src/xml/caisse.xml',
            'gestion_finance/static/src/css/caisse.css',
            'gestion_finance/static/src/js/balance.js',
            'gestion_finance/static/src/xml/balance.xml',
            'gestion_finance/static/src/xml/template.xml',
            'gestion_finance/static/src/js/template.js',
            'gestion_finance/static/src/js/annual_balance.js',
            'gestion_finance/static/src/xml/annual_balance.xml',
        ],
        'web.assets_qweb': [
            'gestion_finance/static/src/xml/revenu.xml',
            'gestion_finance/static/src/xml/caisse.xml',
        ],
    },
    'application': True,
}
