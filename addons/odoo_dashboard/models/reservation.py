# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime


class ProjectProject(models.Model):
    _inherit = 'reservation'

    def get_all_zones(self):
        zones = self.env['zone'].search([])
        return [{'id': zone.id, 'name': zone.name} for zone in zones]

    def get_all_modele(self):
        modele_records = self.env['modele'].search([])
        return [{'id': modele.id, 'name': modele.name} for modele in modele_records]

    def get_all_vehicule(self):
        vehicule_records = self.env['vehicule'].search([])
        return [{'id': vehicule.id, 'name': vehicule.numero} for vehicule in vehicule_records]

    @api.model
    def remplissage_action_chart(self, *args, **kwargs):
        Vehicule = self.env['vehicule']
        Reservation = self.env['reservation']
        Modele = self.env['modele']

        vehicules = Vehicule.search([])
        modeles = Modele.search([])

        result_data_percentages = []
        result_data_names = []
        date_now = fields.Datetime.now().date()

        remplissage_par_modele = {modele.id: [] for modele in modeles}

        for vehicule in vehicules:
            date_debut_service = vehicule.date_debut_service
            if not date_debut_service:
                remplissage_par_modele[vehicule.modele.id].append(0)
                continue

            total_service_days = (date_now - date_debut_service).days

            reservations = Reservation.search([('vehicule', '=', vehicule.id)])

            if not reservations:
                remplissage_par_modele[vehicule.modele.id].append(0)
                continue

            total_reserved_days = 0
            for res in reservations:
                date_debut_reservation = res.date_heure_debut.date()
                date_fin_reservation = res.date_heure_fin.date()

                duree_reservation = (date_fin_reservation - date_debut_reservation).days
                total_reserved_days += duree_reservation

            if total_service_days > 0:
                pourcentage_remplissage = (total_reserved_days / total_service_days) * 100
            else:
                pourcentage_remplissage = 0

            remplissage_par_modele[vehicule.modele.id].append(round(pourcentage_remplissage, 2))

        for modele in modeles:
            remplissages = remplissage_par_modele[modele.id]
            if remplissages:
                moyenne_remplissage = sum(remplissages) / len(remplissages)
            else:
                moyenne_remplissage = 0

            result_data_percentages.append(round(moyenne_remplissage, 2))
            result_data_names.append(modele.name)

        return [result_data_percentages, result_data_names]
