from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import ValidationError


class Supplement(models.Model):
    _name = 'supplements'
    _description = 'supplement sur les tarif de nuit et le retard'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    heure_debut = fields.Char(string='Heure début')
    heure_fin = fields.Char(string='Heure Fin')
    heure_debut_float = fields.Float(string='Heure début (float)', compute='_compute_heure_float', store=True)
    heure_fin_float = fields.Float(string='Heure Fin (float)', compute='_compute_heure_float', store=True)
    montant = fields.Integer(string='Montant')
    reatrd = fields.Integer(string='si depasse (heure)')
    valeur = fields.Integer(string='valeur %')

    @api.depends('heure_debut', 'heure_fin', 'montant', 'reatrd', 'valeur')
    def _compute_name(self):
        for record in self:
            if record.heure_debut:
                record.name = f'Heure entre {record.heure_debut} et {record.heure_fin} supplément de {record.montant} €'
            elif record.reatrd != 0:
                record.name = f'Retour retard de {record.reatrd} heures supplément {record.valeur}%'
            else:
                record.name = ''

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

