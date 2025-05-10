from odoo import fields, models


class CarsTest(models.Model):
    _name = 'test.car'
    _description = 'car test'

    name = fields.Char(string='vehicule')
