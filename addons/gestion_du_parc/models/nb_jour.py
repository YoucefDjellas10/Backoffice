from odoo import fields, models, api
from odoo.exceptions import ValidationError


class NombreDeJour(models.Model):
    _name = 'nb.jour'
    _description = 'nombre de jours de location pour le tarif'

    name = fields.Char(string='jour et+', compute='_compute_name', store=True)
    de = fields.Integer(string='de')
    au = fields.Integer(string='au')

    @api.depends('de')
    def _compute_name(self):
        for record in self:
            record.name = str(record.de) + ' et +'

    @api.constrains('de', 'au')
    def _check_intervals(self):
        for record in self:
            if record.de >= record.au:
                raise ValidationError("La valeur de 'au' doit être strictement supérieure à la valeur de 'de'.")

            overlapping_records = self.search([
                ('id', '!=', record.id),
                ('de', '<=', record.au),
                ('au', '>=', record.de)
            ])
            if overlapping_records:
                overlapping_intervals = ", ".join(
                    f"de: {rec.de}, au: {rec.au}"
                    for rec in overlapping_records
                )
                raise ValidationError(
                    f"Les intervalles se chevauchent avec les enregistrements suivants : {overlapping_intervals}"
                )
