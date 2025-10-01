from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReservationInheritGantt(models.Model):
    _inherit = "reservation"

    colors = fields.Integer('Color', default=4)