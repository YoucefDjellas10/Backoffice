from odoo import fields, models


class VersementRecette(models.Model):
    _name = 'versement.recette'
    _description = 'Versement des recttes'

    name = fields.Char(string='')

