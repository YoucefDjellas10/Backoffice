from odoo import fields, models, api


class RefundTable(models.Model):
    _name = 'refund.table'
    _description = 'tableau des rembourssement'

    name = fields.Char(string='ref', readonly=True)
    reservation = fields.Many2one('reservation', string='Reservation')
    currency = fields.Many2one('res.currency', string='Currency',
                               default=lambda self: self.env.ref('base.EUR').id)
    amount = fields.Monetary(currency_field='currency', string='Montant')
    status = fields.Selection([('en_attent', 'En attent'),
                               ('effectuer', 'Effectué'),
                               ('refuser', 'Refusé')], string='Statut', default='en_attent')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        record = super(RefundTable, self).create(vals)
        record.write({'name': f'refund-{record.id}'})
        return record

