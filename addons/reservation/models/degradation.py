from odoo import fields, models


class Degradation(models.Model):
    _name = 'degradation'
    _description = 'degradation de la caution'

    name = fields.Char(string='nom')
    type_degradation = fields.Many2one('type.degradation', string='Type de dégradation')
    degradation = fields.Many2one('bareme.degradation', string='Dégradation',
                                  domain="[('type', '=', type_degradation), ('categorie', '=', categorie_lv)]")
    type = fields.Many2one(string='Type de dégradation', related='degradation.type', store=True)
    categorie = fields.Many2one(string='Catégorie', related='degradation.categorie', store=True)
    devise = fields.Many2one(string='devise', related='degradation.devise', store=True)
    devise_eur = fields.Many2one(string='devise', related='degradation.devise_eur', store=True)
    prix = fields.Monetary(string='Prix', currency_field='devise', related='degradation.prix', store=True)
    prix_eur = fields.Monetary(string='Prix', currency_field='devise_eur', related='degradation.prix_eur', store=True)
    livraison = fields.Many2one('livraison', string='livraison')
    categorie_lv = fields.Many2one(string='categorie lv', related='livraison.categorie', store=True)
    note = fields.Text(string='Note')
