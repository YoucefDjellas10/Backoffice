from odoo import fields, models, api


class Zone(models.Model):
    _name = 'zone'
    _description = 'zone par région'

    name = fields.Char(string='Nom de la zone')
    country = fields.Many2one('res.country', string='Pays')
    lieux = fields.One2many('lieux', 'zone', string='lieux')
    manager = fields.Many2one('res.users', string='Manager')
    agent = fields.Many2many('res.users', string='agent')

    def open_create_lieux_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer un nouveau Lieu',
            'res_model': 'lieux',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('lieux.lieux_form_view').id,
            'target': 'new',
            'context': {
                'default_zone': self.id,
            }
        }
class ResUsers(models.Model):
    _inherit = 'res.users'

    zone_ids = fields.Many2many('zone', string='Zones assignées', compute='_compute_zone_ids', store=True)

    def _compute_zone_ids(self):
        for user in self:
            user.zone_ids = self.env['zone'].search([('agent', 'in', user.ids)])





