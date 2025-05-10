# -*- coding: utf-8 -*-
# from odoo import http


# class OdooLogoReplacement(http.Controller):
#     @http.route('/odoo_logo_replacement/odoo_logo_replacement', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo_logo_replacement/odoo_logo_replacement/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo_logo_replacement.listing', {
#             'root': '/odoo_logo_replacement/odoo_logo_replacement',
#             'objects': http.request.env['odoo_logo_replacement.odoo_logo_replacement'].search([]),
#         })

#     @http.route('/odoo_logo_replacement/odoo_logo_replacement/objects/<model("odoo_logo_replacement.odoo_logo_replacement"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo_logo_replacement.object', {
#             'object': obj
#         })

