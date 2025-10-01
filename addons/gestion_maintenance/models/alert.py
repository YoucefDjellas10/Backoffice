from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AlertRecord(models.Model):
    _name = 'alert.record'
    _description = 'Alert'
    _rec_name = 'reference_id'

    reference_id = fields.Char(string='Reference ID', readonly=True, required=True,
                               default=lambda self: self._generate_reference_id())
    vehicule_id = fields.Many2one('vehicule', string='Véhicules')
    km_actuel = fields.Float(string="Kilométrage Actuel")

    numero = fields.Char(string='Numéro', related='vehicule_id.numero', store=True)
    dernier_klm = fields.Integer(string='Dernier kilometrage', related='vehicule_id.dernier_klm', store=True)
    zone = fields.Many2one(string='Zone de livraison', related='vehicule_id.zone', store=True)
    manager = fields.Many2one(string='Manager', related='zone.manager', store=True)
    agent = fields.Many2many(string='Agent', related='zone.agent')
    maintenance_id = fields.Many2one('maintenance.record', string='Maintenance Record')
    alert_km = fields.Integer(string='Alert Km', related='maintenance_id.alert_km', store=True)
    echeance = fields.Char(string='Échéance', compute='_compute_echeance', store=True)
    maintenance_created = fields.Boolean(string='Alert Created', default=False)
    status = fields.Selection([
        ('en_attente', 'En attente'),
        ('realise', 'Réalisé'),
        ('verifie', 'Vérifié')], string='Statut')

    @api.depends('type_maintenance_id', 'alert_km', 'date_prochaine_alerte')
    def _compute_echeance(self):
        for record in self:
            if record.type_maintenance_id and record.type_maintenance_id.type == 'duree':
                # Si type_maintenance_id est 'duree', l'échéance est la date_prochaine_alerte
                record.echeance = record.date_prochaine_alerte
            else:
                # Sinon, l'échéance est alert_km + 'Km'
                record.echeance = f"{record.alert_km} Km"

    type_maintenance_id = fields.Many2one(string='Maintenance', related='maintenance_id.type_maintenance_id',
                                          store=True)
    type = fields.Selection(string='Type', related='maintenance_id.type')
    date_prochaine_alerte = fields.Date(string='Date d Alerte')
    prix_da = fields.Float(string='Prix en DA')
    prix_eur = fields.Float(string='Prix en EUR')
    type_maintenance_id1 = fields.Many2one(string='Maintenance', related='maintenance_id.type_maintenance_id')
    type1 = fields.Selection(string='Le type de maintenance', related='type_maintenance_id1.type')
    date_prochaine = fields.Date(string='Prochaine date')
    klm_prochaine = fields.Char(string='Kilométrage')

    @api.model
    def _generate_reference_id(self):
        last_record = self.search([], limit=1, order='reference_id desc')
        if last_record:
            last_number = int(last_record.reference_id[5:]) if last_record.reference_id and len(
                last_record.reference_id) > 5 else 0
        else:
            last_number = 0
        new_number = last_number + 1
        return f"Alert-{new_number:04d}"

    @api.onchange('km_actuel')
    def _onchange_km_actuel(self):
        if self.km_actuel:
            self.vehicule_id.write({'dernier_klm': self.km_actuel})
            _logger.info("Dernier kilometrage updated to: %s", self.km_actuel)

    def action_create_maintenance_record(self):
        self.ensure_one()
        self.status = 'realise'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Maintenance Record',
            'res_model': 'maintenance.record',
            'view_mode': 'form',
            'view_id': self.env.ref('gestion_maintenance.view_maintenace_popup_form').id,
            'target': 'new',
            'context': {
                'default_vehicule_id': self.vehicule_id.id,
                'default_type_maintenance_id': self.type_maintenance_id.id,
                'default_alert_id': self.id,
                'default_km_actuel': 0,
                'show_km_actuel': True
            },
        }


    def action_verifier(self):
        self.ensure_one()
        self.status = 'verifie'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Maintenance Record',
            'res_model': 'alert.record',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('gestion_maintenance.view_maintenace_verifier_popup_form').id,
            'target': 'new',

        }

    @api.model
    def search_alerts(self, filters=None, offset=0, limit=30):
        domain = []
        if filters:
            if filters.get('model_id'):
                domain.append(('vehicule_id.modele', '=', int(filters['model_id'])))  # Changé de modele_id à modele
            if filters.get('zone_id'):
                domain.append(('vehicule_id.zone', '=', int(filters['zone_id'])))
            if filters.get('vehicule_id'):
                domain.append(('vehicule_id', '=', int(filters['vehicule_id'])))
            if filters.get('type'):
                domain.append(('type_maintenance_id', '=', int(filters['type'])))

        alerts = self.search(domain, offset=offset, limit=limit)
        result = [{
            'id': alert.id,
            'reference_id': alert.reference_id,
            'maintenance_type': alert.type_maintenance_id.name if alert.type_maintenance_id else 'N/A',
            'numero': alert.vehicule_id.numero if alert.vehicule_id else 'N/A',
            'echeance': alert.date_prochaine_alerte if alert.date_prochaine_alerte else 'N/A',
            'dernier_klm': alert.vehicule_id.dernier_klm if alert.vehicule_id else 0,
        } for alert in alerts]

        return {'records': result, 'total_count': len(alerts)}

    @api.model
    def get_all_models(self):
        model_records = self.env['model.vehicule'].search([])
        return [{'id': model.id, 'name': model.name} for model in model_records]

    @api.model
    def get_all_zones(self):
        zone_records = self.env['res.zone'].search([])
        return [{'id': zone.id, 'name': zone.name} for zone in zone_records]

    @api.model
    def get_all_vehicule(self):
        vehicules = self.env['vehicule'].search([])
        return [{
            'id': v.id,
            'numero': v.numero,
            'name': f"{v.numero} - {v.matricule}"  # Plus d'info pour l'utilisateur
        } for v in vehicules]

    @api.model
    def get_all_maintenance_types(self):
        types = self.env['type.maintenance.record'].search([])
        return [{
            'id': t.id,
            'name': t.name,
            'type': t.type  # Ajoutez ceci si vous voulez filtrer par type
        } for t in types]

