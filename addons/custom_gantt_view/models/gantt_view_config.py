# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Linto C.T(Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from datetime import datetime
from odoo import models, fields, api


class ViewExtended(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(
        selection_add=[('gantt_custom', "GanttView")]
    )


class WindowActionExtended(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(
        selection_add=[('gantt_custom', "GanttView")], ondelete={'gantt_custom': 'cascade'}
    )


class GanttContents(models.Model):
    _name = 'custom.gantt.content'
    _description = 'custom gantt content'

    @api.model
    def fetch_gantt_contents(self, FieldsInfo, res_ids=False):
        if not FieldsInfo and not res_ids:
            return False
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        if res_ids == False:
            result = self.env[FieldsInfo['model']].search([
                (FieldsInfo['date_assign'], '!=', None),
                (FieldsInfo['date_end'], '!=', None),
            ])
        else:
            result = self.env[FieldsInfo['model']].search([
                ('id', 'in', res_ids),
                (FieldsInfo['date_assign'], '!=', None),
                (FieldsInfo['date_end'], '!=', None),
            ])
        task_array = {}
        for rec in result:
            type_field = rec[FieldsInfo['col']]
            if type_field.id not in task_array:
                task_array[type_field.id] = [{
                    'id': str(type_field.id),
                    'parent': True,
                    'child': False,
                    'type_id': type_field.id,
                    'rec_id': False,
                    'name': type_field[type_field._rec_name],
                    'start': rec[FieldsInfo['date_assign']],
                    'end': rec[FieldsInfo['date_end']],
                    # 'dependencies': '',
                    'custom_class': 'bar-milestone'
                }, {
                    'id': str(rec.id),
                    'parent': False,
                    'child': True,
                    'type_id': type_field.id,
                    'rec_id': rec.id,
                    # 'name': rec[rec._rec_name],
                    'name': rec[rec._rec_name] if not isinstance(rec._fields[rec._rec_name], (fields.Many2one)) else rec[rec._rec_name].name,
                    'start': rec[FieldsInfo['date_assign']],
                    'end': rec[FieldsInfo['date_end']],
                    'dependencies': str(type_field.id),
                    'custom_class': 'bar-milestone',
                }]
            elif type_field.id in task_array:
                temp = {
                    'id': str(rec.id) + str(type_field.id),
                    'child': True,
                    'parent': False,
                    'rec_id': rec.id,
                    'type_id': type_field.id,
                    'name': rec[rec._rec_name] if not isinstance(rec._fields[rec._rec_name], (fields.Many2one)) else rec[rec._rec_name].name,
                    'start': rec[FieldsInfo['date_assign']],
                    'end': rec[FieldsInfo['date_end']],
                    'dependencies': str(type_field.id),
                    'custom_class': 'bar-milestone',
                }
                task_array[type_field.id].append(temp)
                if rec[FieldsInfo['date_assign']] < task_array[type_field.id][0]['start']:
                    task_array[type_field.id][0]['start'] = rec[FieldsInfo['date_assign']]
                if rec[FieldsInfo['date_end']] > task_array[type_field.id][0]['end']:
                    task_array[type_field.id][0]['end'] = rec[FieldsInfo['date_end']]

        return [task_array, today]

    @api.model
    def update_time_range(self, task, result, start, end):
        """Updates time range"""
        model = result['model']
        if not task or not result:
            return False
        # fetch child record
        child_rec = self.env[model].search([('id', '=', task['rec_id'])])
        start_1= start[:10]
        start_2 = start[12:19]
        start_time = start_1 + " " + start_2
        date_start_time = datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S")

        end_1 = end[:10]
        end_2 = end[12:19]
        end_time = end_1 + " " + end_2
        date_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        child_rec.write({
            result['date_assign']: date_start_time,
            result['date_end']: date_end_time
        })
        return
