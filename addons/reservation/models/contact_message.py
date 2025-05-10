from odoo import fields, models


class ContactMessage(models.Model):
    _name = 'contact.message'
    _description = 'les message de contact de site'

    name = fields.Char(string='id', readonly=True)
    nom_complet = fields.Char(string='Nom Complet', readonly=True)
    email = fields.Char(string='E-mail', readonly=True)
    message = fields.Text(string='Message', readonly=True)
    client = fields.Many2one('liste.client', string='Client')
    create_date = fields.Datetime(string='Date')