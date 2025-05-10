# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'Gantt View Odoo17',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Gantt View Odoo17, Gantt View, Gantt, Odoo17, Odoo Apps, Gantt Chart, Odoo17 Views',
    'description': 'This module Ensure smart management of data with the Gantt'
                   ' View.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    "data": [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_gantt_view/static/src/lib/gantt-master/dist/frappe-gantt.min.js',
            'custom_gantt_view/static/src/lib/gantt-master/dist/frappe-gantt.css',
            'custom_gantt_view/static/src/css/style.css',
            'custom_gantt_view/static/src/js/gantt_arch_parser.js',
            'custom_gantt_view/static/src/js/gantt_controller.js',
            'custom_gantt_view/static/src/js/gantt_renderer.js',
            'custom_gantt_view/static/src/js/gantt_view.js',
            'custom_gantt_view/static/src/xml/gantt_controller.xml',
            'custom_gantt_view/static/src/xml/gantt_renderer.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'price': 29.99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
