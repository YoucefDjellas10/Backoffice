{
    'name': 'Planning Dashboard',
    'version': '17.0.1.0.0',
    'summary': 'Module de gestion du planning avec un tableau de bord',
    'sequence': 10,
    'author': 'Ton Nom',
    'category': 'Planning',
    'depends': ['base' , 'gestion_du_parc'],
    'data': [
        'views/planning_dashboard_view.xml',
        'views/manual_optimization.xml',
        'views/manual_optimization_list.xml',
        'views/block_car_list.xml',
        'views/block_car.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'Planning_dashboard/static/src/js/planning_js.js',
            'Planning_dashboard/static/src/js/reservation_js.js',
            'Planning_dashboard/static/src/css/planning_css.css',
            'Planning_dashboard/static/src/css/reservation_css.css',
            'Planning_dashboard/static/src/xml/planning_ouest.xml',
            'Planning_dashboard/static/src/xml/reservation.xml',
            'Planning_dashboard/static/src/xml/manuel_opptimisation.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
