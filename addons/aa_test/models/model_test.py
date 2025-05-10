from odoo import fields, models


class ModelTest(models.Model):
    _name = 'models.test'
    _description = 'models test'

    name = fields.Char(string='Name')
    date_one = fields.Datetime(string='Date de depart')
    date_two = fields.Datetime(string='Date De retoure')
    car = fields.Many2one('car.test', string='vehicule')
    test_car = fields.Many2one('test.car', string='vehicule')
