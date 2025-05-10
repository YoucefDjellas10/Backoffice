{
    'name': 'Planning Dashboard',
    'version': '17.0.1.0.0',
    'summary': 'Module de gestion du planning avec un tableau de bord',
    'sequence': 10,
    'author': 'Ton Nom',
    'category': 'Planning',
    'depends': ['base'],
    'data': [
        'views/planning_dashboard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'Planning_dashboard/static/src/js/planning_js.js',
            'Planning_dashboard/static/src/js/reservation_js.js',
            'Planning_dashboard/static/src/css/planning_css.css',
            'Planning_dashboard/static/src/css/reservation_css.css',
            'Planning_dashboard/static/src/xml/planning_ouest.xml',
            'Planning_dashboard/static/src/xml/reservation.xml',

        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}  