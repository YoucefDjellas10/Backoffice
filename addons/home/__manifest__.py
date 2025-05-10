{
    'name': 'Home Photo Module',
    'version': '1.0',
    'summary': 'Module that displays a photo on the homepage',
    'description': 'This module displays a static image on a new homepage view.',
    'author': 'Your Name',
    'category': 'Website',
    'depends': ['base'],
    'data': [
        'views/home_view.xml',
        'security/ir.model.access.csv',

    ],
    'assets': {
        'web.assets_frontend': [
            'home\static\src\img\homepage.png',
        ],
    },
    'installable': True,
    'application': False,
}
