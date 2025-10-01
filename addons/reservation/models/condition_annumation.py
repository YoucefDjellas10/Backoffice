from odoo import fields , models

class ConditionAnnulation(models.Model):
    _name = 'condition.annulation'
    _description = 'annuler avant'

    name = fields.Char(string='name', default='condition d annulation')
    haute_saison = fields.Many2one('saison', string='Haute Saison')
    basse_saison = fields.Many2one('saison', string='Basse Saison')
    haute_montant = fields.Integer(string='Jour Haute saison')
    basse_montant = fields.Integer(string='Jour Basse saison')
