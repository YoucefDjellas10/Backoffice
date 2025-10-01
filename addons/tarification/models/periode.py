from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Periode(models.Model):
    _name = 'periode'
    _description = 'periode des saison pour les tarifs'

    name = fields.Char(string='Période', compute='_compute_name', store=True)
    saison = fields.Many2one('saison', string='Saison', required=True)
    date_debut = fields.Date(string='Date début', required=True)
    date_fin = fields.Date(string='Date Fin', required=True)
    tarif_id = fields.Many2one('tarifs', string='Tarif')

    @api.depends('saison', 'date_debut', 'date_fin')
    def _compute_name(self):
        for record in self:
            saison_name = record.saison.name if record.saison else ''
            date_debut = record.date_debut.strftime('%d/%m/%Y') if record.date_debut else ''
            date_fin = record.date_fin.strftime('%d/%m/%Y') if record.date_fin else ''
            record.name = saison_name + ' - ' + date_debut + ' - ' + date_fin

    @api.constrains('date_debut', 'date_fin')
    def _check_date_overlap(self):
        for record in self:
            overlapping_periods = self.env['periode'].search([
                ('id', '!=', record.id),
                ('date_debut', '<=', record.date_fin),
                ('date_fin', '>=', record.date_debut),
            ])
            if overlapping_periods:
                overlapping_names = ", ".join(overlapping_periods.mapped('name'))
                raise ValidationError(
                    f"La période saisie chevauche avec la période suivante: {overlapping_names}"
                )
