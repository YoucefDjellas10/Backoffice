from odoo import fields, models


class CarTest(models.Model):
    _name = 'car.test'
    _description = 'car test'

    name = fields.Char(string='vehicule')
