from odoo import fields, models


class TypeDegradation(models.Model):
    _name = 'type.degradation'
    _description = 'type de degradation'

    name = fields.Char(string='Type de dégradation')

