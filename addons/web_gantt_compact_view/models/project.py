from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = "project.task"
        
    date_from = fields.Datetime(string='Planned start', index=True, copy=False)
    date_to = fields.Datetime(string='Planned stop', index=True, copy=False)
    color = fields.Integer('Color', default=4)
    task_priority = fields.Selection([
        ('normal', 'Normal'),
        ('low', 'Low'),        
        ('high', 'High')
    ], string='Priority', required=True, default='normal')
    progress = fields.Integer(tracking=True)

    @api.onchange('date_to')
    def onchange_gantt_stop_date(self):
        if self.date_from and self.date_to and self.date_to < self.date_from:
            self.date_to = self.date_from