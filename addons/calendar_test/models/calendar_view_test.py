from odoo import models, fields


class CalendarViewTest(models.Model):
    _name = 'calendar.view.test'
    _description = 'calendar view test'

    name = fields.Char(string='vehicule')
    date_depart = fields.Datetime(string='date depart')
    date_retoure = fields.Datetime(string='Date retoure')

