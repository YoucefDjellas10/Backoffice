from odoo import fields, models, api


class CaisseRecord(models.Model):
    _name = 'caisse.record'
    _description = 'les caisse des employés'
    _rec_name = 'user_id'

    name = fields.Char(string='Id de la caisse', readonly=True, copy=False)
    zone = fields.Many2one('zone', string='zone')
    type_caisse = fields.Selection([('agent', 'Agent'),
                                    ('manager_region', 'Manager de région'),
                                    ('manager_general', 'Manager général'),
                                    ('ceo', 'CEO')], string='Type')
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True)
    euro = fields.Many2one('res.currency', string='euro', default=lambda self: self.env['res.currency'].browse(125).id)
    caisse = fields.Monetary(string='fonds de caisse €', currency_field='euro')
    dinar = fields.Many2one('res.currency', string='Dinar algérien', default=lambda self: self.env['res.currency'].browse(111).id)
    caisse_dzd = fields.Monetary(string='fonds de caisse DA', currency_field='dinar',
                                 compute='_compute_caisse_dzd', store=True)
    trasfers = fields.One2many('transfer.argent', 'de', string='Transfers')
    recevoir = fields.One2many('transfer.argent', 'vers', string='Recevoir')
    depenses = fields.One2many('depense.record', 'caisse', string='Dépenses')

    depenses_en_attente = fields.One2many('depense.record', 'caisse', string="Dépenses", domain=[('status', '=', 'en_attente')])

    @api.depends('depenses', 'depenses.status')
    def _compute_depenses_en_attente(self):
        for record in self:
            record.depenses_en_attente = record.depenses.filtered(lambda d: d.status == 'en_attente')

    @api.depends('recevoir', 'recevoir.montant_dzd', 'trasfers', 'trasfers.montant_dzd', 'depenses',
                 'depenses.montant_da', 'depenses.status')
    def _compute_caisse_dzd(self):
        for record in self:
            total_recevoir = sum(recevoir.montant_dzd for recevoir in record.recevoir)
            total_transfers = sum(transfer.montant_dzd for transfer in record.trasfers)
            total_depenses = sum(depense.montant_da for depense in record.depenses  if depense.status != 'annule')
            record.caisse_dzd = total_recevoir - total_transfers - total_depenses

    @api.model
    def create(self, vals):
        record = super(CaisseRecord, self).create(vals)
        record.name = 'Caisse-{:02d}'.format(record.id)
        return record

    def action_open_transfer_form(self):
        return {
            'name': 'Créer un transfert',
            'type': 'ir.actions.act_window',
            'res_model': 'transfer.argent',
            'view_mode': 'form',
            'context': {
                'default_de': self.id,
            },
            'target': 'new',
        }

    def action_open_depense_form(self):
        return {
            'name': 'Ajouter une dépense',
            'type': 'ir.actions.act_window',
            'res_model': 'depense.record',
            'view_mode': 'form',
            'context': {
                'default_caisse': self.id,
            },
            'target': 'new',
        }

