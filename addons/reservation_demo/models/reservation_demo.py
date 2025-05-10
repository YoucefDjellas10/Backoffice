import random
import string
from datetime import datetime

from odoo import api, fields, models


class ReservationDemo(models.Model):
    _name = "reservation.demo"
    _description = "Reservation"

    name = fields.Char(
        string="Reference",
        readonly=True,
        default=lambda self: self._generate_unique_code_(),
        unique=True,
    )
    car = fields.Many2one("cars.demo")
    model = fields.Many2one(string="Car model", related="car.model")
    start_date = fields.Datetime(string="Start date")
    end_date = fields.Datetime(string="End date")
    color = fields.Integer(string="color")

    @api.model
    def _generate_unique_code_(self):
        current_date = datetime.now()
        year = current_date.strftime("%y")
        month = current_date.strftime("%m")
        unique_code = ""
        while True:
            random_digits = "".join(random.choices(string.digits, k=3))
            unique_code = f"SEA{year}{month}{random_digits}"
            if not self.env["reservation.demo"].search([("name", "=", unique_code)]):
                break
        return unique_code
