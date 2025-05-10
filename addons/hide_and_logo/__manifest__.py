{
    'name': 'Hide and Logo',
    'version': '1.0',
    'category': 'Customization',
    'summary': 'Add a logo to the header next to the username',
    'description': 'This module adds a custom logo to the header next to the username.',
    'depends': ['web'],
    'data': [
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hide_and_logo/static/src/css/custom_header.css',
            'hide_and_logo/static/src/js/custom_header.js',
        ],
    },
    'installable': True,
    'application': False,
}
