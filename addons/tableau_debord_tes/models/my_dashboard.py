from odoo import models, fields


class Dashboard(models.Model):
    _name = 'my.dashboard'
    _description = 'Dashboard for Statistics'

    total_sales = fields.Float(string="Total des Ventes", compute="compute_totals")
    percentage_growth = fields.Float(string="Croissance en %", compute="compute_totals")

    def compute_totals(self):
        for record in self:
            # Calculer les ventes totales (à adapter selon ton modèle et tes besoins)
            total_sales = self.env['reservation'].search([('status', '=', 'confirme')]).mapped('total_reduit_euro')
            record.total_sales = sum(total_sales)

            # Exemple de calcul de pourcentage (à adapter selon le contexte)
            last_year_sales = self.env['reservation'].search(
                [('date_heure_debut', '>=', fields.Date.today().replace(year=fields.Date.today().year - 1))])
            if last_year_sales:
                record.percentage_growth = (sum(total_sales) / sum(last_year_sales.mapped('total_reduit_euro'))) * 100
            else:
                record.percentage_growth = 0
