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
    ],
    'application': True,
}
