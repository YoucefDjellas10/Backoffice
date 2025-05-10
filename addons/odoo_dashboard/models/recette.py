from odoo import fields, models, api


class RevenueInherit(models.Model):
    _inherit = 'revenue.record'

    @api.model
    def get_total_encaisse(self, date_from=None, date_to=None, zone=None, modele=None, vehicule=None):
        domain = []
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        if zone:
            domain.append(('zone.id', '=', zone))
        if modele:
            domain.append(('modele.id', '=', modele))
        if vehicule:
            domain.append(('vehicule.id', '=', vehicule))
        records = self.env['revenue.record'].search(domain)
        total_encaisse = records.mapped('total_encaisse')
        total = sum(total_encaisse)
        return "{:,.0f} DZD".format(total)




