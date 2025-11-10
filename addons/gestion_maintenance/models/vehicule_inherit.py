
from odoo import models, fields, api
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class VehiculeInherit(models.Model):
    _inherit = 'vehicule'

    dernier_klm = fields.Integer(string='Dernier kilometrage')


    @api.model
    def cron_verifier_maintenance(self):
        try:
            vehicules = self.env['vehicule'].search([])
            _logger.info(f"Début vérification maintenance pour {len(vehicules)} véhicules")

            types_maintenances = self.env['type.maintenance.record'].search([])
            _logger.info(f"Nombre de types de maintenance: {len(types_maintenances)}")

            alertes_creees = 0

            for vehicule in vehicules:
                for type_maintenance in types_maintenances:
                    maintenance_existante = self.env['maintenance.record'].search([
                        ('vehicule_id', '=', vehicule.id),
                        ('type_maintenance_id', '=', type_maintenance.id)
                    ], limit=1)

                    if not maintenance_existante:
                        alerte_existante = self.env['alert.record'].search([
                            ('vehicule_id', '=', vehicule.id),
                            ('maintenance_id.type_maintenance_id', '=', type_maintenance.id),
                            ('status', '=', 'en_attente')
                        ], limit=1)

                        if not alerte_existante:
                            if type_maintenance.type != 'km':
                                echeance = datetime.now().strftime('%d/%m/%Y')
                                valeurs_alerte = {
                                    'status': 'en_attente',
                                    'vehicule_id': vehicule.id,
                                    'km_actuel': vehicule.dernier_klm,
                                    'type_maintenance_id': type_maintenance.id,
                                    'echeance': echeance,
                                }

                                self.env['alert.record'].create(valeurs_alerte)
                                alertes_creees += 1

                                _logger.info(
                                    f"Alerte créée - Véhicule: {vehicule.numero}, "
                                    f"Type maintenance: {type_maintenance.name}, "
                                    f"Échéance: {echeance}"
                                )
                            else:
                                if vehicule.dernier_klm >= (type_maintenance.kilometrage_restant - type_maintenance.km):
                                    echeance = f"{type_maintenance.kilometrage_restant} Km"
                                    valeurs_alerte = {
                                        'status': 'en_attente',
                                        'vehicule_id': vehicule.id,
                                        'km_actuel': vehicule.dernier_klm,
                                        'type_maintenance_id': type_maintenance.id,
                                        'echeance': echeance,
                                        
                                    }

                                    self.env['alert.record'].create(valeurs_alerte)
                                    alertes_creees += 1

                                    _logger.info(
                                        f"Alerte créée (durée) - Véhicule: {vehicule.numero}, "
                                        f"Type maintenance: {type_maintenance.name}, "
                                        f"Date affichage: {date_affichage.strftime('%d/%m/%Y')}, "
                                        f"Échéance: {echeance}"
                                    )

                    else:
                        derniere_maintenance = self.env['maintenance.record'].search([
                            ('vehicule_id', '=', vehicule.id),
                            ('type_maintenance_id', '=', type_maintenance.id)
                        ], order='date desc', limit=1)

                        if derniere_maintenance.type_maintenance_id.type == 'duree':
                            duree_nombre = derniere_maintenance.type_maintenance_id.duree_nombre
                            duree_unite = derniere_maintenance.type_maintenance_id.duree_unite

                            if duree_unite == 'jour':
                                duree_delta = timedelta(days=duree_nombre)
                            elif duree_unite == 'mois':
                                duree_delta = timedelta(days=duree_nombre * 30)
                            else:  # année
                                duree_delta = timedelta(days=duree_nombre * 365)

                            delai_nombre = derniere_maintenance.type_maintenance_id.duree_nombre_
                            delai_unite = derniere_maintenance.type_maintenance_id.duree_unite_

                            if delai_unite == 'jour':
                                delai_delta = timedelta(days=delai_nombre)
                            elif delai_unite == 'mois':
                                delai_delta = timedelta(days=delai_nombre * 30)
                            else:  # année
                                delai_delta = timedelta(days=delai_nombre * 365)

                            date_derniere = fields.Date.to_date(derniere_maintenance.date)
                            date_affichage = date_derniere + duree_delta - delai_delta

                            date_aujourdhui = fields.Date.today()
                            if date_affichage <= date_aujourdhui:
                                alerte_existante = self.env['alert.record'].search([
                                    ('vehicule_id', '=', vehicule.id),
                                    ('maintenance_id.type_maintenance_id', '=', type_maintenance.id),
                                    ('status', '=', 'en_attente')
                                ], limit=1)

                                if not alerte_existante:
                                    date_prochaine = date_derniere + duree_delta
                                    echeance = date_prochaine.strftime('%d/%m/%Y')

                                    valeurs_alerte = {
                                        'status': 'en_attente',
                                        'vehicule_id': vehicule.id,
                                        'km_actuel': vehicule.dernier_klm,
                                        'type_maintenance_id': type_maintenance.id,
                                        'echeance': echeance,
                                        'date_prochaine_alerte': date_prochaine,
                                    }

                                    self.env['alert.record'].create(valeurs_alerte)
                                    alertes_creees += 1

                                    _logger.info(
                                        f"Alerte créée (durée) - Véhicule: {vehicule.numero}, "
                                        f"Type maintenance: {type_maintenance.name}, "
                                        f"Date affichage: {date_affichage.strftime('%d/%m/%Y')}, "
                                        f"Échéance: {echeance}"
                                    )

                        else:
                            kilometrage_derniere = derniere_maintenance.kilometrage or 0
                            kilometrage_restant = derniere_maintenance.type_maintenance_id.kilometrage_restant or 0
                            km_type = derniere_maintenance.type_maintenance_id.km or 0

                            delais = kilometrage_derniere + kilometrage_restant - km_type

                            if vehicule.dernier_klm >= delais:
                                alerte_existante = self.env['alert.record'].search([
                                    ('vehicule_id', '=', vehicule.id),
                                    ('maintenance_id.type_maintenance_id', '=', type_maintenance.id),
                                    ('status', '=', 'en_attente')
                                ], limit=1)

                                if not alerte_existante:
                                    km_prochaine = kilometrage_derniere + kilometrage_restant
                                    echeance = f"{km_prochaine} Km"

                                    valeurs_alerte = {
                                        'status': 'en_attente',
                                        'vehicule_id': vehicule.id,
                                        'km_actuel': vehicule.dernier_klm,
                                        'type_maintenance_id': type_maintenance.id,
                                        'echeance': echeance,
                                        'alert_km': km_prochaine,
                                    }

                                    self.env['alert.record'].create(valeurs_alerte)
                                    alertes_creees += 1

                                    _logger.info(
                                        f"Alerte créée (km) - Véhicule: {vehicule.numero}, "
                                        f"Type maintenance: {type_maintenance.name}, "
                                        f"Kilométrage actuel: {vehicule.dernier_klm} km, "
                                        f"Délai: {delais} km, "
                                        f"Échéance: {echeance}"
                                    )
                                else:
                                    if alerte_existante.status == 'verifie' and alerte_existante.klm_prochaine:
                                        klm_prochaine_value = int(alerte_existante.klm_prochaine.replace(' Km', '').strip())
                                        if klm_prochaine_value <= vehicule.dernier_klm:
                                            km_prochaine = kilometrage_derniere + kilometrage_restant
                                            echeance = f"{km_prochaine} Km"

                                            valeurs_alerte = {
                                                'status': 'en_attente',
                                                'vehicule_id': vehicule.id,
                                                'km_actuel': vehicule.dernier_klm,
                                                'type_maintenance_id': type_maintenance.id,
                                                'echeance': echeance,
                                                'alert_km': km_prochaine,
                                            }

                                            self.env['alert.record'].create(valeurs_alerte)
                                            alertes_creees += 1

                                            _logger.info(
                                                f"Alerte créée (km) - Véhicule: {vehicule.numero}, "
                                                f"Type maintenance: {type_maintenance.name}, "
                                                f"Kilométrage actuel: {vehicule.dernier_klm} km, "
                                                f"Délai: {delais} km, "
                                                f"Échéance: {echeance}"
                                            )
            _logger.info(f"Fin vérification maintenance - {alertes_creees} alertes créées")

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification maintenance: {str(e)}")
            raise

