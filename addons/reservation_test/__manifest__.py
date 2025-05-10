# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'reservation test',
    'depends': ['base', 'gestion_parc_test'],
    'summary': "reservation test",
    'data': [
        'views/resrvation_test_view.xml',
        'views/car_test_inherit_view.xml',
    ],
    'application': True,
}
