from odoo import fields, models


class TypeDepense(models.Model):
    _name = 'type.depens'
    _description = 'types des depenses'

    name = fields.Char(string='Type de Dépense')
