from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import ValidationError


class ListeAttente(models.Model):
    _name = 'lite.atente'
    _description = 'liste d\'attente '

    name = fields.Char(string='id')
    client = fields.Many2one('liste.client', string='Client')
    full_name = fields.Char(string='Nom et Prenom')
    email = fields.Char(string='Email')
    phone_number = fields.Char(string='numero de telephone')
    car_model = fields.Many2one('modele', string='Modele')
    lieu_depart = fields.Many2one('lieux', string='lieu de depart')
    date_depart = fields.Date(string='date de depart')
    lieu_retour = fields.Many2one('lieux', string='lieu de retour')
    date_retour = fields.Date(string='date de retour')
    heure_debut = fields.Char(string='Heure début')
    heure_fin = fields.Char(string='Heure Fin')
    heure_debut_float = fields.Float(string='Heure début (float)', compute='_convert_hour_to_float', store=True)
    heure_fin_float = fields.Float(string='Heure Fin (float)', compute='_convert_hour_to_float', store=True)

    @api.depends('heure_debut', 'heure_fin')
    def _compute_heure_float(self):
        for record in self:
            record.heure_debut_float = self._convert_hour_to_float(record.heure_debut)
            record.heure_fin_float = self._convert_hour_to_float(record.heure_fin)

    def _convert_hour_to_float(self, heure_str):
        if heure_str:
            try:
                time_obj = datetime.strptime(heure_str, '%H:%M')
                return time_obj.hour + time_obj.minute / 60
            except ValueError:
                raise ValidationError(f"L'heure {heure_str} n'est pas au format HH:MM")
        return 0.0

