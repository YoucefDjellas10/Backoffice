from odoo import fields,models


class AlgerianCities(models.Model):
    _name = 'algerian.cities'
    _description = 'algerian cities'

    name = fields.Char(string='city')
