from odoo import fields, models, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import logging
import random
_logger = logging.getLogger(__name__)


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
    tout_zone = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Appliquer sur tout les zones',
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
    next_changes = fields.Datetime(string='Prochains changements')

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

    def _update_random_models(self):
        self.ensure_one()

        if self.tout_modele != 'aleatoire':
            return

        nbr_model = self.nbr_model

        if nbr_model <= 0:
            raise ValidationError(
                "Le nombre de modèles doit être supérieur à 0 pour la sélection aléatoire."
            )

        all_models = self.env['modele'].search([])

        if len(all_models) < nbr_model:
            raise ValidationError(
                f"Il n'y a pas assez de modèles disponibles. "
                f"Vous avez demandé {nbr_model} modèles mais seulement {len(all_models)} sont disponibles."
            )

        selected_models = random.sample(all_models.ids, nbr_model)

        return {
            'modele': [(6, 0, selected_models)],
            'next_changes': datetime.now() + timedelta(hours=8)
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('tout_modele') == 'aleatoire':
                nbr_model = vals.get('nbr_model', 1)

                if nbr_model <= 0:
                    raise ValidationError(
                        "Le nombre de modèles doit être supérieur à 0 pour la sélection aléatoire."
                    )

                all_models = self.env['modele'].search([])

                if len(all_models) < nbr_model:
                    raise ValidationError(
                        f"Il n'y a pas assez de modèles disponibles. "
                        f"Vous avez demandé {nbr_model} modèles mais seulement {len(all_models)} sont disponibles."
                    )

                selected_models = random.sample(all_models.ids, nbr_model)
                vals['modele'] = [(6, 0, selected_models)]
                vals['next_changes'] = datetime.now() + timedelta(hours=8)

        return super(Promotion, self).create(vals_list)

    def write(self, vals):
        result = super(Promotion, self).write(vals)

        # Après la mise à jour, vérifier si on doit régénérer les modèles aléatoires
        for record in self:
            if record.tout_modele == 'aleatoire':
                try:
                    update_vals = record._update_random_models()
                    if update_vals:
                        super(Promotion, record).write(update_vals)
                except ValidationError:
                    # Relancer l'erreur pour l'utilisateur
                    raise

        return result

    def cron_update_random_promotions(self):

        promotions = self.search([('tout_modele', '=', 'aleatoire')])

        for promotion in promotions:
            try:
                update_vals = promotion._update_random_models()
                if update_vals:
                    promotion.write(update_vals)

            except ValidationError as e:
                _logger.warning(
                    f"Promotion {promotion.name} (ID: {promotion.id}): {str(e)}"
                )
                continue
            except Exception as e:
                _logger.error(
                    f"Erreur lors de la mise à jour de la promotion {promotion.id}: {str(e)}"
                )
                continue
