from odoo import fields, models, api, exceptions
from datetime import datetime, timedelta
import random
import string


class ReservationTest(models.Model):
    _name = 'reservation.test'

    name = fields.Char(string='Numéro de réservation', readonly=True,
                       default=lambda self: 'SEA-' + self._generate_unique_code())
    start_date = fields.Datetime(string='Date Début', required=True, default=lambda self: fields.Datetime.now())
    end_date = fields.Datetime(string='Date De retour', required=True, default=lambda self: fields.Datetime.now() + timedelta(days=3))
    car = fields.Many2one('car.test', string='Véhicule', domain="[('model', '=', car_model_search)]")
    car_model = fields.Many2one(string='Modèle', related='car.model', required=True)
    car_reservations = fields.One2many(string='Modèle', related='car.reservations')
    car_model_search = fields.Many2one('model.test', string='Modèle', required=True)
    car_search = fields.One2many(string='Modèle', related='car_model_search.cars')

    def _generate_unique_code(self):
        # Générer un code alphanumérique aléatoire
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f'{code}'

    @api.constrains('start_date', 'end_date', 'car')
    def _check_car_availability(self):
        for reservation in self:
            if reservation.car:
                overlapping_reservations = self.env['reservation.test'].search([
                    ('car', '=', reservation.car.id),
                    ('start_date', '<', reservation.end_date),
                    ('end_date', '>', reservation.start_date),
                    ('id', '!=', reservation.id)
                ])
                if overlapping_reservations:
                    raise exceptions.ValidationError(
                        "Il n'y a pas de disponibilité pour le véhicule sélectionné pendant la période spécifiée.")

    search_start_date = fields.Date(string="Date de début de recherche")
    search_end_date = fields.Date(string="Date de fin de recherche")


class CarTestInherit(models.Model):
    _inherit = 'car.test'

    reservations = fields.One2many('reservation.test', 'car', string='Réservations')
