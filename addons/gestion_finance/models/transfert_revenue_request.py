from odoo import fields, models, api
from odoo.exceptions import UserError


class TransfertRevenueRequest(models.Model):
    _name = 'transfert.revenue.request'
    _description = 'Demande de transfert de recettes'
    _order = 'create_date desc'

    name = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')
    date_from = fields.Datetime(string='Du', required=True)
    date_to = fields.Datetime(string='Au', required=True)
    zone_id = fields.Many2one('zone', string='Zone', required=True)
    manager_id = fields.Many2one('res.users', string='Manager', readonly=True)

    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('demande', 'Demandé'),
        ('verse', 'Versé')
    ], string='Statut', default='brouillon', required=True)

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise €',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
    )
    currency_dzd = fields.Many2one(
        'res.currency',
        string='Devise DZD',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'DZD')], limit=1)
    )

    # SUPPRIMER revenue_ids et utiliser uniquement revenues
    revenues = fields.One2many('revenue.record', 'transfer', string='Recettes')

    total_montant = fields.Monetary(string='Total €', currency_field='currency_id', compute='_compute_totals',
                                    store=True)
    total_montant_dzd = fields.Monetary(string='Total DA', currency_field='currency_dzd', compute='_compute_totals',
                                        store=True)

    @api.depends('revenues.montant', 'revenues.montant_dzd')
    def _compute_totals(self):
        for record in self:
            total_eur = sum(record.revenues.mapped('montant')) or 0
            total_dzd = sum(record.revenues.mapped('montant_dzd')) or 0
            record.total_montant = total_eur
            record.total_montant_dzd = total_dzd

    @api.onchange('zone_id')
    def _onchange_zone_id(self):
        for record in self:
            if record.zone_id and record.zone_id.manager:
                record.manager_id = record.zone_id.manager
            else:
                record.manager_id = False

            if record.zone_id:
                last_request = self.search([
                    ('zone_id', '=', record.zone_id.id),
                    ('state', 'in', ['verse', 'demande'])
                ], order='date_to desc', limit=1)
                if last_request and last_request.date_to:
                    record.date_from = last_request.date_to

    def action_calculer(self):
        for record in self:
            if record.state != 'brouillon':
                raise UserError("Le calcul n'est possible qu'à l'état brouillon.")

            # Recherche des recettes selon les critères + mode_paiement = liquide
            revenues = self.env['revenue.record'].search([
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to),
                ('zone', '=', record.zone_id.id),
                ('transfer', '=', False),
                ('mode_paiement', '=', 'liquide'),
            ])

            if not revenues:
                raise UserError("Aucune recette en liquide trouvée pour cette période et cette zone.")

            # Associer les recettes trouvées à ce transfert
            revenues.write({'transfer': record.id})

            # Recalcul des totaux
            record._compute_totals()

            # Notification + rafraîchissement
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Calcul terminé',
        
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': record._name,
                        'res_id': record.id,
                        'views': [[False, 'form']],
                        'target': 'current'
                    }
                }
            }

    def action_demander(self):
        for record in self:
            if record.state != 'brouillon':
                raise UserError("Seules les demandes en brouillon peuvent être soumises.")
            if not record.revenues:
                raise UserError("Aucune recette trouvée pour cette période et cette zone.")
            record.state = 'demande'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_verser(self):
        for record in self:
            if record.state != 'demande':
                raise UserError("Seules les demandes soumises peuvent être marquées comme versées.")

            # Met à jour les lignes de recettes
            for revenue in record.revenues:
                revenue.verifier = 'verifier'

            # Change l'état
            record.state = 'verse'

        # Rafraîchit la vue pour que la barre de statut se mette à jour
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': 'Le transfert a été marqué comme versé.',
                'type': 'success',
                'sticky': False,
            }
        }, {
            'type': 'ir.actions.act_window',
            'res_model': 'transfert.revenue.request',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': 'Le transfert a été marqué comme versé.',
                'type': 'success',
                'sticky': False
            }
        }

    @api.model
    def create(self, vals):
        if vals.get('zone_id') and not vals.get('manager_id'):
            zone = self.env['zone'].browse(vals['zone_id'])
            if zone.manager:
                vals['manager_id'] = zone.manager.id
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('transfert.revenue.request') or 'Nouveau'
        return super().create(vals)

    def write(self, vals):
        if 'zone_id' in vals:
            zone = self.env['zone'].browse(vals['zone_id'])
            vals['manager_id'] = zone.manager.id if zone.manager else False
        if any(record.state in ['demande', 'verse'] for record in self):
            if any(f in vals for f in {'date_from', 'date_to', 'zone_id'}):
                raise UserError("Impossible de modifier une demande déjà soumise ou versée.")
        return super().write(vals)


class RevenueInherit(models.Model):
    _inherit = 'revenue.record'

    transfer = fields.Many2one('transfert.revenue.request', string='Transfert')
