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

