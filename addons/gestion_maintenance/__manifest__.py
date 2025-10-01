{
    'name': 'Gestion du maintenance',
    'summary': 'Gestion du maintenance',
    'description': "Gestion du maintenance",
    'depends': ['base','gestion_du_parc'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/alert_view.xml',
        'views/maintenance_view.xml',
        'views/type_maintenance_view.xml',
       # 'views/km_actuel.xml',
        'views/maintenance_poup.xml',
        'views/maintenance_verifier.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'gestion_maintenance/static/src/js/alert.js',
            'gestion_maintenance/static/src/js/alert_agent.js',
            'gestion_maintenance/static/src/xml/alert_agent.xml',
            'gestion_maintenance/static/src/xml/alert.xml',
        ],
    },

    'application': True,
}
