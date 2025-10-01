from odoo import fields, models, api


class TypeOptions(models.Model):
    _name = 'frais.livraison'
    _description = 'frais de livraison des vehicules entre les lieux'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    depart = fields.Many2one('lieux', string='Départ', required=True)
    zone = fields.Many2one(string='Zone', related='depart.zone', store=True)
    retour = fields.Many2one('lieux', string='Retour', required=True)
    montant = fields.Integer(string='Montant')

    @api.depends('depart', 'retour')
    def _compute_name(self):
        for record in self:
            if record.depart and record.retour:
                record.name = "de {} au {}".format(record.depart.name, record.retour.name)
            else:
                record.name = " "
