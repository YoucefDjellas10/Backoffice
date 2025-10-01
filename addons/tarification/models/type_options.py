from odoo import fields, models


class TypeOptions(models.Model):
    _name = 'type.options'
    _description = 'types des options possible'

    name = fields.Char(string='Type')
