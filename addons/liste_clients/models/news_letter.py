from odoo import models, fields


class NewsLetter(models.Model):
    _name = 'news.letter'
    _description = 'pour les mails comercial'

    name = fields.Char(string='Name')
    email = fields.Char(string='Emals')
    subscribe = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Civilité', default='oui')

