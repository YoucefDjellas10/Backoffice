from odoo import fields, models


class CarModel(models.Model):
    _name = "car.model.demo"
    _description = "car models"

    name = fields.Char(string="model")
