# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Groups',
    'summary': 'Groups for access rights',
    'description': "Groups for access rights",
    'depends': ['base', 'gestion_du_parc', 'tarification', 'lieux', 'reservation', 'liste_clients', 'taux_de_change', 'gestion_maintenance'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',

    ],

    'installable': True,
    'application': True,

    'license': 'LGPL-3',
}
