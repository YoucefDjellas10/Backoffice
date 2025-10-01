from odoo import api, fields, models, _
from odoo.exceptions import UserError
 
class LeaveReportCalendar(models.Model):
    _inherit = "hr.leave.report.calendar"
    
    color = fields.Integer('Color', default=4)