from odoo import fields, models


class AnnulerRaison(models.Model):
    _name = 'annuler.raison'
    _description = 'raison d annulation '

    name = fields.Char(string='Raison')
