from odoo import fields, models


class SeaAnnulerRaison(models.Model):
    _name = 'sea.annuler.raison'
    _description = 'sea abbuler raison'

    name = fields.Char(string='Annuler raison')

