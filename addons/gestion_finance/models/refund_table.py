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
    note = fields.Text(string='Note')

    @api.model
    def create(self, vals):
        record = super(RefundTable, self).create(vals)
        record.write({'name': f'refund-{record.id}'})
        return record

    def action_effectuer(self):
        for record in self:
            if record.status != 'effectuer':
                record.status = 'effectuer'


class ReservationInheritRefund(models.Model):
    _inherit = 'reservation'

    refunds_ids = fields.One2many('refund.table', 'reservation', string='Remboursement')
    total_refunds = fields.Monetary(
        string='Total des remboursements',
        compute='_compute_total_refunds',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one('res.currency', string='Currency',
                               default=lambda self: self.env.ref('base.EUR').id)

    @api.depends('refunds_ids.amount', 'refunds_ids.status')
    def _compute_total_refunds(self):
        for record in self:
            
            refunds_effectues = record.refunds_ids.filtered(lambda r: r.status == 'effectuer')
            record.total_refunds = sum(refunds_effectues.mapped('amount'))
