from odoo import fields, models, api


class TransferArgent(models.Model):
    _name = 'transfer.argent'
    _description = 'transfer d\'argent'

    name = fields.Char(string='Numero de transaction', readonly=True)
    de = fields.Many2one('caisse.record', string='De')
    vers = fields.Many2one('caisse.record', string='Vers')
    euro = fields.Many2one('res.currency', string='euro', default=lambda self: self.env['res.currency'].browse(125).id)
    montant = fields.Monetary(string='Montant €', currency_field='euro')
    dinar = fields.Many2one('res.currency', string='Dinar algérien',
                            default=lambda self: self.env['res.currency'].browse(111).id)
    montant_dzd = fields.Monetary(string='Montant DA', currency_field='dinar')
    note = fields.Text(string='Note')

    @api.model
    def create(self, vals):
        record = super(TransferArgent, self).create(vals)
        record.name = 'TRX-%03d' % record.id
        return record
