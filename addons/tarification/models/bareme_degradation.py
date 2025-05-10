from odoo import fields, models, api


class BaremeDegradation(models.Model):
    _name = 'bareme.degradation'
    _description = 'bareme de degradation'

    name = fields.Char(string='Nom De dégradation')
    type = fields.Many2one('type.degradation', string='Type de dégradation')
    categorie = fields.Many2one('categorie', string='Catégorie')
    devise = fields.Many2one('res.currency', string='devise', readonly=True,
                             default=lambda self: self.env.ref('base.DZD').id)
    devise_eur = fields.Many2one('res.currency', string='devise', readonly=True,
                                 default=lambda self: self.env.ref('base.EUR').id)
    prix = fields.Monetary(string='Prix', currency_field='devise')
    prix_eur = fields.Monetary(string='Prix', currency_field='devise_eur', compute='_compute_prix_eur', store=True)

    @api.depends('prix')
    def _compute_prix_eur(self):
        taux_change = self.env['taux.change'].browse(2)
        for record in self:
            if taux_change:
                record.prix_eur = record.prix / taux_change.montant if taux_change.montant else 0
            else:
                record.prix_eur = 0

