from odoo import models, fields, api
from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class MaintenanceRecord(models.Model):
    _name = 'maintenance.record'
    _description = 'Maintenance Record'
    _rec_name = 'reference_id'

    vehicule_id = fields.Many2one('vehicule', string='Véhicule', required=True)
    numero = fields.Char(string='Véhicule', related='vehicule_id.numero', store=True)
    kilometrage = fields.Integer(string='Kilométrage')
    type_maintenance_id = fields.Many2one('type.maintenance.record', string='Maintenance')
    type = fields.Selection(string='Type', related='type_maintenance_id.type')
    dernier_delai_duree = fields.Date(string='Dernier Délai de Durée')
    status = fields.Selection([
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('realise', 'Réalisé'),
        ('verifie', 'Vérifié')], string='Statut', default='en_attente')
    date = fields.Date(string='Date', default=fields.Date.today)
    note = fields.Text(string='Note')
    reference_id = fields.Char(string='Reference ID', readonly=True, required=True,
                               default=lambda self: self._generate_reference_id_(), copy=False, unique=True)
    duree_nombre = fields.Integer(string='Durée Nombre', related='type_maintenance_id.duree_nombre', store=True)
    duree_unite = fields.Selection(string='Unité de Durée', related='type_maintenance_id.duree_unite', store=True)
    delai_nombre = fields.Integer(string='Délai Nombre', related='type_maintenance_id.duree_nombre_', store=True)
    delai_unite = fields.Selection(string='Unité de Délai', related='type_maintenance_id.duree_unite_', store=True)
    euro = fields.Many2one('res.currency', string='Euro', default=lambda self: self.env.ref('base.EUR').id)
    dinar = fields.Many2one('res.currency', string='dinar', default=lambda self: self.env.ref('base.DZD').id)
    prix_da = fields.Monetary(string='Prix en DA', currency_field='dinar', required=True)
    prix_eur = fields.Monetary(string='Prix en EUR', currency_field='euro', compute='_compute_prix_eur', store=True)
    date_dernier_maintenance = fields.Date(string='Date Dernier Entretien')
    temps_restant = fields.Char(string='Temps Restant')
    date_prochaine_alerte = fields.Date(string='Date Prochaine Alerte', compute='_compute_date_prochaine_alerte',
                                        store=True)
    dernier_klm = fields.Integer(string='Dernier Kilométrage', related='vehicule_id.dernier_klm', store=True)
    km = fields.Integer(string='Délai Kilométrage', related='type_maintenance_id.km', store=True)
    alert_km = fields.Integer(string='Alert Km', readonly=True)
    kilometrage_restant = fields.Integer(string='Kilométrage Restant',
                                         related='type_maintenance_id.kilometrage_restant', store=True)
    alert_created = fields.Boolean(string='Alert Created', default=False)
    alert_id = fields.Many2one('alert.record', string='Alert')
    zone = fields.Many2one(string='Zone de livraison', related='vehicule_id.zone', store=True)
    dernier_kilometrage = fields.Integer(string='Kilométrage')

    fournisseur_payer = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='payé ?', default='oui')
    fournisseur = fields.Many2one()

    def _generate_reference_id_(self):
        last_record = self.search([], order='id desc', limit=1)
        if last_record and last_record.reference_id and last_record.reference_id[6:].isdigit():
            last_number = int(last_record.reference_id[6:])
            new_number = last_number + 1
        else:
            new_number = 1

        new_reference_id = f'Maint-{new_number:04d}'
        return new_reference_id

    @api.depends('prix_da')
    def _compute_prix_eur(self):
        taux_change = self.env['taux.change'].search([], limit=1)
        for record in self:
            if taux_change and taux_change.montant:
                record.prix_eur = record.prix_da / taux_change.montant
            else:
                record.prix_eur = 0

    @api.depends('date_dernier_maintenance', 'duree_nombre', 'duree_unite')
    def _compute_date_prochaine_alerte(self):
        for record in self:
            try:
                if record.date_dernier_maintenance and record.duree_nombre and record.duree_unite:
                    date_dernier = fields.Date.to_date(record.date_dernier_maintenance)
                    if record.duree_unite == 'jour':
                        date_prochaine = date_dernier + timedelta(days=record.duree_nombre)
                    elif record.duree_unite == 'mois':
                        date_prochaine = date_dernier + timedelta(days=record.duree_nombre * 30)
                    elif record.duree_unite == 'annee':
                        date_prochaine = date_dernier + timedelta(days=record.duree_nombre * 365)

                    record.date_prochaine_alerte = date_prochaine
                else:
                    record.date_prochaine_alerte = False
            except Exception as e:
                record.date_prochaine_alerte = False

    def action_set_en_cours(self):
        self.write({'status': 'en_cours'})

    def action_set_realise(self):
        self.write({'status': 'realise'})
        current_user = self.env.user
        caisse_record = self.env['caisse.record'].search([('user_id', '=', current_user.id)], limit=1)
        caisse_id = caisse_record.id if caisse_record else False
        depense_vals = {
            'type_depense': 1,
            'montant_da': self.prix_da,
            'caisse': caisse_id,
            'maintenance': self.id,
            'note': f"{self.type_maintenance_id.name} réalisée pour le véhicule {self.vehicule_id.numero}",
        }
        self.env['depense.record'].create(depense_vals)

    def action_set_verifie(self):
        self.write({'status': 'verifie'})

    @api.model
    def create(self, vals):
        record = super(MaintenanceRecord, self).create(vals)
        current_user = self.env.user
        caisse_record = self.env['caisse.record'].search([('user_id', '=', current_user.id)], limit=1)
        if caisse_record and record.fournisseur_payer == 'oui':
            depense_vals = {
                'caisse': caisse_record.id,
                'type_depense': 12,
                'maintenance': record.id,
                'montant_da': record.prix_da,
                'vehicule_numero': record.vehicule_id.id,
                'note': f"Maintenance {record.type_maintenance_id.name if record.type_maintenance_id else 'N/A'} - Véhicule {record.vehicule_id.numero if record.vehicule_id else 'N/A'}",
                'date_de_realisation': record.date,
            }
            self.env['depense.record'].create(depense_vals)
            _logger.info(f"Dépense créée automatiquement pour la maintenance {record.reference_id}")
        else:
            _logger.warning(
                f"Aucune caisse trouvée pour l'utilisateur {current_user.name} lors de la création de la maintenance {record.reference_id}")

        return record


    def action_create_missing_depenses(self):

        start_date = datetime(2025, 11, 9, 0, 0, 0)
        end_date = datetime(2025, 11, 10, 7, 30, 0)

        domain = [
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
            ('fournisseur_payer', '=', 'oui')
        ]

        maintenances = self.search(domain)

        _logger.info(f"Trouvé {len(maintenances)} maintenance(s) à traiter")

        created_count = 0
        skipped_count = 0
        error_count = 0

        for maintenance in maintenances:
            try:
                existing_depense = self.env['depense.record'].search([
                    ('maintenance', '=', maintenance.id)
                ], limit=1)

                if existing_depense:
                    _logger.info(f"Dépense déjà existante pour la maintenance {maintenance.reference_id}")
                    skipped_count += 1
                    continue
                caisse_record = self.env['caisse.record'].search([
                    ('user_id', '=', maintenance.create_uid.id)
                ], limit=1)

                if not caisse_record:
                    _logger.warning(
                        f"Aucune caisse trouvée pour l'utilisateur {maintenance.create_uid.name} - Maintenance {maintenance.reference_id}")
                    error_count += 1
                    continue

                depense_vals = {
                    'caisse': caisse_record.id,
                    'type_depense': 12,
                    'maintenance': maintenance.id,
                    'montant_da': maintenance.prix_da,
                    'vehicule_numero': maintenance.vehicule_id.id,
                    'note': f"Maintenance {maintenance.type_maintenance_id.name if maintenance.type_maintenance_id else 'N/A'} - Véhicule {maintenance.vehicule_id.numero if maintenance.vehicule_id else 'N/A'}",
                    'date_de_realisation': maintenance.date,
                }

                self.env['depense.record'].create(depense_vals)
                created_count += 1
                _logger.info(f"Dépense créée pour la maintenance {maintenance.reference_id}")

            except Exception as e:
                error_count += 1
                _logger.error(f"Erreur lors de la création de la dépense pour {maintenance.reference_id}: {str(e)}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Migration terminée',
                'message': f'Dépenses créées: {created_count}, Ignorées: {skipped_count}, Erreurs: {error_count}',
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': False,
            }
        }



class VehiculeInheritMaintenance(models.Model):
    _inherit = 'vehicule'

    vehicule_ids = fields.One2many('maintenance.record', 'vehicule_id', string='Vehicule')

