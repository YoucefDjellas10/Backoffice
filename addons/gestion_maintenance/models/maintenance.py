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

    @api.model
    def create(self, vals):
        record = super(MaintenanceRecord, self).create(vals)
        current_user = self.env.user
        montant = float(vals.get('prix_da', 0))
        maintenance = vals.get('id', None)
        caisse_record = self.env['caisse.record'].search([('user_id', '=', current_user.id)], limit=1)
        caisse_id = caisse_record.id if caisse_record else False
        depense_vals = {
            'type_depense': 12,
            'montant_da': montant,
            'caisse': caisse_id,
            'maintenance': maintenance,
        }
        self.env['depense.record'].create(depense_vals)

        if record.dernier_klm is not None and record.kilometrage_restant is not None and record.km is not None:
            alert_km = record.dernier_klm + record.kilometrage_restant - record.km
            record.write({'alert_km': alert_km})
        else:
            _logger.warning("Missing values for alert_km calculation after create: %s", vals)

        alert_id = self.env.context.get('default_alert_id')
        if alert_id:
            alert_record = self.env['alert.record'].browse(alert_id)
            alert_record.write({'maintenance_created': True})

        if record.type == 'duree':
            duree_unite_mapping = {'jour': 1, 'mois': 30, 'annee': 365}
            delai_unite_mapping = {'jour': 1, 'mois': 30, 'annee': 365}

            duree_unite = duree_unite_mapping.get(record.duree_unite, 1)
            delai_unite = delai_unite_mapping.get(record.delai_unite, 1)

            # Calculer la date de prochaine alerte
            alert_date = record.date + timedelta(days=record.duree_nombre * duree_unite) - timedelta(
                days=record.delai_nombre * delai_unite)

            # Créer un enregistrement dans alert.record
            self.env['alert.record'].create({
                'vehicule_id': record.vehicule_id.id,
                'maintenance_id': record.id,
                'date_prochaine_alerte': alert_date,
            })
            record.write({'alert_created': True})
        return record

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
