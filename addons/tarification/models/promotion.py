from odoo import fields, models, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class Promotion(models.Model):
    _name = 'promotion'
    _description = 'les promotions'

    name = fields.Char(string='Nom')
    tout_modele = fields.Selection([('oui', 'Oui'), ('non', 'Non'), ('aleatoire', 'Aléatoire')], string='Appliquer sur tout les modèles',
                                   default='oui', required=True)
    modele = fields.Many2many('modele', string='Modèle')
    date_debut = fields.Date(string='Date début', default=fields.Date.today)
    date_fin = fields.Date(string='Date fin', default=lambda self: fields.Date.today() + timedelta(days=30))
    debut_visibilite = fields.Date(string='Début visibilité', default=fields.Date.today)
    fin_visibilite = fields.Date(string='Fin visibilité', default=lambda self: fields.Date.today() + timedelta(days=30))
    code_promo = fields.Char(string='Code promo')
    reduction = fields.Integer(string='Réduction %')
    tout_zone = fields.Selection([('oui', 'Oui'), ('non', 'Non'), ('aleatoire', 'Aléatoire')], string='Appliquer sur tout les zones',
                                   default='oui', required=True)

    nbr_model = fields.Integer(string='nbr modele', default=1)
    nbr_zone = fields.Integer(string='nbr zone', default=1)
    zone = fields.Many2many('zone', string='Zone')
    active_passive = fields.Boolean(string='Active')
    model_one = fields.Many2one('modele', string='Modele', compute='_compute_models', store=True)
    model_two = fields.Many2one('modele', string='Modele', compute='_compute_models', store=True)
    model_three = fields.Many2one('modele', string='Modele', compute='_compute_models', store=True)
    model_four = fields.Many2one('modele', string='Modele', compute='_compute_models', store=True)
    model_five = fields.Many2one('modele', string='Modele', compute='_compute_models', store=True)
    zone_one = fields.Many2one('zone', string='zone', compute='_compute_zone', store=True)
    zone_two = fields.Many2one('zone', string='zone', compute='_compute_zone', store=True)
    zone_three = fields.Many2one('zone', string='zone', compute='_compute_zone', store=True)

    @api.onchange('modele')
    def _check_modele_limit(self):
        if len(self.modele) > 5:
            raise ValidationError("Vous ne pouvez sélectionner que 5 modèles maximum.")

    @api.onchange('zone')
    def _check_zone_limit(self):
        if len(self.zone) > 3:
            raise ValidationError("Vous ne pouvez sélectionner que 3 zones maximum.")

    @api.depends('modele')
    def _compute_models(self):
        for record in self:
            model = record.modele[:5]
            models_list = model.mapped('id')

            record.model_one = models_list[0] if len(models_list) > 0 else False
            record.model_two = models_list[1] if len(models_list) > 1 else False
            record.model_three = models_list[2] if len(models_list) > 2 else False
            record.model_four = models_list[3] if len(models_list) > 3 else False
            record.model_five = models_list[4] if len(models_list) > 4 else False

    @api.depends('zone')
    def _compute_zone(self):
        for record in self:
            zone = record.zone[:5]
            zone_list = zone.mapped('id')

            record.zone_one = zone_list[0] if len(zone_list) > 0 else False
            record.zone_two = zone_list[1] if len(zone_list) > 1 else False
            record.zone_three = zone_list[2] if len(zone_list) > 2 else False






