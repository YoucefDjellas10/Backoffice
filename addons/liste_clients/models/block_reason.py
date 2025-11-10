from odoo import fields, models, api


class BlockReason(models.Model):
    _name = 'block.reason'
    _description = 'block reason'

    name = fields.Char(string='Nom')
