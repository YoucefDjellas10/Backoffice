# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class odoo_logo_replacement(models.Model):
#     _name = 'odoo_logo_replacement.odoo_logo_replacement'
#     _description = 'odoo_logo_replacement.odoo_logo_replacement'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

