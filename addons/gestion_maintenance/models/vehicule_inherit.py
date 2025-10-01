
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class VehiculeInherit(models.Model):
    _inherit = 'vehicule'

    dernier_klm = fields.Integer(string='Dernier kilometrage')

    @api.onchange('dernier_klm')
    def _check_and_create_alert_records(self):
        for vehicule in self:
            maintenance_records = self.env['maintenance.record'].search(
                [('vehicule_id', '=', vehicule.id), ('alert_created', '=', False)])
            for record in maintenance_records:
                if vehicule.dernier_klm >= record.alert_km:
                    _logger.info("Checking alert conditions for Maintenance Record ID: %s", record.id)
                    alert_record = self.env['alert.record'].create({
                        'vehicule_id': vehicule.id,
                        'maintenance_id': record.id,
                        'date_prochaine_alerte': fields.Date.today(),
                    })
                    _logger.info("Alert record created for Maintenance Record ID: %s, Alert Record ID: %s", record.id,
                                 alert_record.id)
                    record.write({'alert_created': True})
                else:
                    _logger.info("No alert record created for Maintenance Record ID: %s", record.id)

    @api.model
    def create(self, vals):
        _logger.info("Creating Vehicule with vals: %s", vals)
        record = super(VehiculeInherit, self).create(vals)
        _logger.info("Created Vehicule ID: %s", record.id)
        self._check_and_create_alert_records()
        return record

    def write(self, vals):
        _logger.info("Updating Vehicule with vals: %s", vals)
        result = super(VehiculeInherit, self).write(vals)
        _logger.info("Update result: %s", result)
        self._check_and_create_alert_records()
        return result
