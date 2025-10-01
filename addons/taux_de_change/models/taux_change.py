from odoo import fields, models
import random


class TauxChange(models.Model):
    _name = 'taux.change'
    _description = 'taux de change des devis'

    name = fields.Char(string='Name', readonly=True, default='Devise €')
    devise = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env['res.currency'].browse(125).id)
    currency_dzd = fields.Many2one('res.currency', string='Dinar Algerien', default=lambda self: self.env['res.currency'].browse(111).id)
    montant = fields.Monetary(string='Montant', currency_field='currency_dzd', store=True)
    primaire = fields.Monetary(string='Montant', currency_field='devise', store=True, default=1)
