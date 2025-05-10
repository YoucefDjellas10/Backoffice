from odoo import fields, models


class HistoriqueSolde(models.Model):
    _name = 'historique.solde'
    _description = 'historique des soldes'

    name = fields.Char(string='id')
    client = fields.Many2one('liste.client', string='client')
    reservation = fields.Many2one('reservation', string='Reservation')
    devise = fields.Many2one('res.currency', string='Devise', readonly=True,
                             default=lambda self: self.env.ref('base.EUR').id)
    montant = fields.Monetary(string='Montant', currency_field='devise')


class ListeClientHistorique(models.Model):
    _inherit = 'liste.client'

    historique_solde = fields.One2many('historique.solde', 'client', string='historique solde')
    soldes_char = fields.Char(string="Soldes Char")

