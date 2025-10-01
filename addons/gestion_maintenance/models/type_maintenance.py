from odoo import models, fields, api


class MaintenanceTypeRecord(models.Model):
    _name = 'type.maintenance.record'
    _description = 'Maintenance Type Record'

    name = fields.Char(string='Nom')
    type = fields.Selection(
        [('km', 'Kilométres'), ('duree', 'Durée')],string='Type', required=True)

    km = fields.Integer(string='Délais km')
    kilometrage_restant = fields.Integer(string='kilometrage', help='Kilométrage maximum', default=0)

    duree_nombre = fields.Integer(string='La durèe', default=1)
    duree_unite = fields.Selection([('jour', 'Jour'),
                                    ('mois', 'Mois'),
                                    ('annee', 'Année')], string='Unité', default='annee')

    duree_nombre_ = fields.Integer(string='Délais', default=1)
    duree_unite_ = fields.Selection([('jour', 'Jour'),
                                     ('mois', 'Mois'),
                                     ('annee', 'Année')], string='Unité', default='mois')
