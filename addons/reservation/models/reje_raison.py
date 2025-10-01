from odoo import fields, models


class RejeRaison(models.Model):
    _name = 'reje.raison'
    _description = 'raison de reje '

    name = fields.Char(string='Raison')
