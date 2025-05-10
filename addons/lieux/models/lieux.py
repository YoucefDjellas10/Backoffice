from odoo import fields, models, api


class Lieux(models.Model):
    _name = 'lieux'
    _description = 'lieux par zone'

    name = fields.Char(string='Agence')
    name_en = fields.Char(string='Agency')
    name_ar = fields.Char(string='وكالة')
    address = fields.Char(string='Lieu de rendez-vous')
    address_en = fields.Char(string='Meet place')
    address_ar = fields.Char(string='مكان اللقاء')
    zone = fields.Many2one('zone', string='Zone de livraison')
    country = fields.Many2one(string='Pays', related='zone.country')
    city = fields.Many2one('algerian.cities', string='Ville')
    lieu_type = fields.Selection([('airport', 'Aéroport'),
                                  ('office', 'Bureau')], string='Type de lieu')
    mobile = fields.Char(string='Mobile')
    rendez_vous = fields.Char(string='Adresse')

    def action_save(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}


