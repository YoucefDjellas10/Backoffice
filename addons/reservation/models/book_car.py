from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import ValidationError


class BookCar(models.Model):
    _name = 'book.car'
    _description = 'recherche de disponibilité'

    name = fields.Char(string='Name')
    lieu_depart = fields.Many2one('lieux', string='lieu de depart')
    zone = fields.Many2one(string='Zone de depart', related='lieu_depart.zone', store=True)
    lieu_retour = fields.Many2one('lieux', string='lieu de retour', domain="[('zone', '=', zone)]")
    date_depart = fields.Date(string='date depart')
    date_retour = fields.Date(string='date retour')
    heure_debut = fields.Char(string='Heure début')
    heure_fin = fields.Char(string='Heure Fin')
    heure_debut_float = fields.Float(string='Heure début (float)', compute='_compute_heure_float', store=True)
    heure_fin_float = fields.Float(string='Heure Fin (float)', compute='_compute_heure_float', store=True)
    manual_lieu_retour = fields.Boolean(string='Lieu retour modifié manuellement', default=False)

    @api.depends('heure_debut', 'heure_fin')
    def _compute_heure_float(self):
        for record in self:
            record.heure_debut_float = self._convert_to_float(record.heure_debut)
            record.heure_fin_float = self._convert_to_float(record.heure_fin)

    def _convert_to_float(self, heure_str):
        if heure_str:
            try:
                time_obj = datetime.strptime(heure_str, '%H:%M')
                return time_obj.hour + time_obj.minute / 60
            except ValueError:
                raise ValidationError(f"L'heure {heure_str} n'est pas au format HH:MM")
        return 0.0

    @api.onchange('lieu_depart')
    def _onchange_lieu_depart(self):
        for record in self:
            record.lieu_retour = record.lieu_depart



