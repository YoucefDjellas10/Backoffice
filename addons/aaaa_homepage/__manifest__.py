{
    'name': 'My Custom Module',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
        'views/my_module_action.xml',
        'views/my_module_menu.xml',
        'views/white_page_template.xml',
        'static/src/xml/template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'aaaa_homepage/static/src/js/white_page.js',
            'aaaa_homepage/static/src/css/white_page.css',
        ],
    },
}
