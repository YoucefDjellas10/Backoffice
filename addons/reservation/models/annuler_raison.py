from odoo import fields, models


class AnnulerRaison(models.Model):
    _name = 'annuler.raison'
    _description = 'raison d annulation '

    name = fields.Char(string='Raison')
    name_en = fields.Char(string='Raison EN')
    name_ar = fields.Char(string='Raison AR')
