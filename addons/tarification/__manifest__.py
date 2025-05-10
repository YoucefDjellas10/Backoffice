# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Tarification',
    'summary': 'tarifs par modèles',
    'description': "tarifs par modèles",
    'depends': ['base', 'gestion_du_parc'],
    'data': [
        'views/saison_view.xml',
        'views/periode_view.xml',
        'views/tarif_view.xml',
        'views/modele_inherit_view.xml',
        'views/tarif_popup_view.xml',
        'views/type_option_view.xml',
        'views/options_view.xml',
        'views/frais_livraison_view.xml',
        'views/supplement_view.xml',
        'views/promition_view.xml',
        'views/type_degradation_view.xml',
        'views/bareme_degradation_view.xml',
    ],

    # 'assets': {
        # 'web.assets_backend': [
        #     'tarification/static/js/tarification_home.js',
        #     'tarification/static/src/xml/tarif_home_template.xml',
        # ],
    # },
    'application': True,
}
