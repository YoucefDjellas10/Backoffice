from odoo import fields, models


class Saison(models.Model):
    _name = 'saison'
    _description = 'saison des tarifs'

    name = fields.Char(string='Saison')
    periodes = fields.One2many('periode', 'saison', string='Périodes')
