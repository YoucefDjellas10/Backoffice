from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class BlockCar(models.Model):
    _name = 'block.car'
    _description = 'Blocage de véhicule'

    vehicule_id = fields.Many2one('vehicule', string='Véhicule à bloquer', required=True)
    date_from = fields.Date(string='Du', required=True)
    date_to = fields.Date(string='Au', required=True)
    reason = fields.Text(string='Raison du blocage')

    @api.constrains('vehicule_id', 'date_from', 'date_to')
    def _check_vehicle_availability(self):
        for record in self:
            # Vérifier s'il y a des réservations pendant cette période
            existing_reservations = self.env['reservation'].search([
                ('vehicule', '=', record.vehicule_id.id),
                ('date_heure_debut', '<=', record.date_to),
                ('date_heure_fin', '>=', record.date_from),
                ('etat_reservation', 'in', ['reserve', 'loue'])  # Vérifier seulement réservé ou loué
            ])

            if existing_reservations:
                raise ValidationError(
                    f"Impossible de bloquer le véhicule {record.vehicule_id.numero} "
                    f"du {record.date_from} au {record.date_to} car il est déjà "
                    f"réservé ou pris pendant cette période."
                )

    @api.model
    def create(self, vals):
        # Vérifier la disponibilité avant la création
        record = super(BlockCar, self).create(vals)
        record._check_vehicle_availability()
        return record

    def write(self, vals):
        # Vérifier la disponibilité avant la modification
        result = super(BlockCar, self).write(vals)
        self._check_vehicle_availability()
        return result

    @api.model
    def get_blocked_vehicles_for_period(self, start_date, end_date):
        """
        Récupère tous les véhicules bloqués pour une période donnée
        Retourne un dict: {vehicule_id: [{'date_from': ..., 'date_to': ...}, ...]}
        """
        blocked_records = self.search([
            ('date_from', '<=', end_date),
            ('date_to', '>=', start_date)
        ])

        blocked_vehicles = {}
        for block in blocked_records:
            if block.vehicule_id.id not in blocked_vehicles:
                blocked_vehicles[block.vehicule_id.id] = []

            blocked_vehicles[block.vehicule_id.id].append({
                'date_from': block.date_from,
                'date_to': block.date_to
            })

        return blocked_vehicles

    def check_vehicle_availability(self, vehicule_id, date_from, date_to):
        """
        Méthode pour vérifier la disponibilité d'un véhicule avant création
        Retourne True si disponible, False sinon
        """
        # Vérifier les réservations existantes
        reservations = self.env['reservation'].search([
            ('vehicule', '=', vehicule_id),
            ('date_heure_debut', '<=', date_to),
            ('date_heure_fin', '>=', date_from),
            ('etat_reservation', 'in', ['reserve', 'loue'])
        ])

        # Vérifier les blocages existants (sauf celui en cours de modification)
        blocks = self.search([
            ('vehicule_id', '=', vehicule_id),
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from),
            ('id', '!=', self.id if self else False)
        ])

        return len(reservations) == 0 and len(blocks) == 0
