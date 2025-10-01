from odoo import fields, models


class Cars(models.Model):
    _name = "cars.demo"
    _description = "cars"

    name = fields.Char(string="car")
    model = fields.Many2one("car.model.demo", string="car model")
