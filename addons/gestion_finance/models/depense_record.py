from odoo import fields, models, api


class DepenseRecord(models.Model):
    _name = 'depense.record'
    _description = 'Dépenses'

    name = fields.Char(string='id', readonly=True, copy=False)
    type_depense = fields.Many2one('type.depens', string='Type de dépense')
    zone = fields.Many2one(string='zone', related='caisse.zone', store=True)
    caisse = fields.Many2one('caisse.record', string='Caisse')
    maintenance = fields.Many2one('maintenance.record', string='Maintenance')
    vehicule = fields.Many2one(string='Véhicule', related='maintenance.vehicule_id')
    type_maintenance_id = fields.Many2one(string='Maintenance', related='maintenance.type_maintenance_id')
    euro = fields.Many2one('res.currency', string='euro',
                           default=lambda self: self.env['res.currency'].browse(125).id)
    dinar = fields.Many2one('res.currency', string='Dinar algérien',
                            default=lambda self: self.env['res.currency'].browse(111).id)
    montant_da = fields.Monetary(string='Montant DA', currency_field='dinar')
    montant_eur = fields.Monetary(string='Montant €', currency_field='euro',
                                  compute='_compute_montant_eur', strore=True)
    vehicule_numero = fields.Many2one('vehicule', string='Vehicule')
    note = fields.Text(string='Note')
    status = fields.Selection([('en_attente', 'en attente'),
                               ('valde_mr', 'Validé par MR'),
                               ('valide_mg', 'Validé par MG'),
                               ('valide', 'Validé')], string='Etat', default='en_attente')


    carburant_motif = fields.Selection([('plein_client', 'Plein client'),
                                        ('complement', 'Complément'),
                                        ('service', 'Service'),
                                        ('mission', 'Mission'),
                                        ('autre', 'Autre'),],string='Justif. carburant')


    manager_note = fields.Text(string='Note Manager')


    def action_valide_mr(self):
        self.status = 'valde_mr'

    def action_valide_mg(self):
        self.status = 'valide_mg'

    def action_valide(self):
        self.status = 'valide'

    @api.depends('montant_da', 'montant_eur')
    def _compute_montant_eur(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.montant_eur = record.montant_da / taux
            else:
                record.montant_eur = 0

    @api.model
    def create(self, vals):
        record = super(DepenseRecord, self).create(vals)
        record.name = 'dépense-{:02d}'.format(record.id)
        return record
