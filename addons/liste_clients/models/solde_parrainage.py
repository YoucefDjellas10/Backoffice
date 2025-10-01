from odoo import fields, models, api


class SoldeParrainage(models.Model):
    _name = 'solde.parrainage'
    _description = 'solde parrainage'

    name = fields.Char(string='Nom')
    dinar = fields.Many2one('res.currency', string='Dinar algérien',
                            default=lambda self: self.env['res.currency'].browse(111).id)
    euro = fields.Many2one('res.currency', string='euro', default=lambda self: self.env['res.currency'].browse(125).id)

    parrain_solde = fields.Monetary(string='filleul', currency_field='euro')
    parrain_solde_da = fields.Monetary(string='filleul', currency_field='dinar', compute='_compute_montant_eur_dzd',
                                       store=True)

    filleul_solde = fields.Monetary(string='Parrain', currency_field='euro')
    filleul_solde_da = fields.Monetary(string='Parrain', currency_field='dinar', compute='_compute_montant_eur_dzd',
                                       store=True)

    @api.depends('parrain_solde', 'filleul_solde')
    def _compute_montant_eur_dzd(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.parrain_solde_da = record.parrain_solde * taux
                record.filleul_solde_da = record.filleul_solde * taux
            else:
                record.parrain_solde_da = 0
                record.filleul_solde_da = 0



