# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Gestion du parcking',
    'summary': 'Gestion du parcking',
    'description': "Gestion du parcking",
    'depends': ['base', 'lieux'],
    'data': [
        'views/categorie_view.xml',
        'views/modele_view.xml',
        'views/vehicule_view.xml',
        'views/vehicule_popup_view.xml',
        'views/nb_jour_view.xml',
    ],
    'application': True,
}
