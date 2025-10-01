# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Lieux',
    'summary': 'lieux et emplacement des agences',
    'description': "lieux et emplacement des agences",
    'depends': ['base'],
    'data': [
        'views/zone_view.xml',
        'views/algerian_cities_view.xml',
        'views/lieux_view.xml',
        'views/add_lieu_popup.xml',
    ],
    'application': True,
}
