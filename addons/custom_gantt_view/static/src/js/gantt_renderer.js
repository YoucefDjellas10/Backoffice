/** @odoo-module **/

import { Component, useRef, useState, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/** Parses a date string in the format "YYYY-MM-DD HH:mm" and returns a timestamp. */
function dateParser(mydate) {
    if (mydate !== undefined) {
        var date_time = mydate.split(" ");
        var date = date_time[0].split("-");
        try{
            var time = date_time[1].split(":");
        }
        catch (err){
            var time = [23,59,0];
        }
        var finalDate = new Date(date[0], date[1]-1, date[2], time[0],time[1]);
        var finalDate = finalDate.getTime();
        return finalDate;
    }
}
/**
GanttRenderer extends Component to generate a visual representation of data by
rendering the view that includes record
*/
export class GanttRenderer extends Component {
    setup() {
        this.archInfo = this.props.archInfo
        this.model = this.props.list.resModel
        this.default_group = this.archInfo.defaultGroup ? true : false
        this.options = {}
        this.state = useState({
            tasks: [],
            groups: []
        })
        this.uiService = useService("ui");
        this.archInfo = this.props.archInfo
        this.action = useService("action");
        this.orm = useService("orm");
        this.ref = useRef('root-renderer')
        this.actionService = useService("action")
        useEffect(() => {
            this.generateGantt()
        }, () => [this.props.list])
    }
//    Generates gantt data
    async generateGantt() {
        const extractIds = (record) => {
          const required_input = [];
          if (record && record.data && record.data.id) {
            required_input.push(record.data.id);
          }
          if (record && record.records) {
            // Check if 'records' is an array before attempting to iterate over it
            if (Array.isArray(record.records)) {
              // If yes, recursively extract ids from the nested records
              const nestedIds = record.records.flatMap(extractIds);
              required_input.push(...nestedIds);
            }
          }
          return required_input;
        };
        const required_input = extractIds(this.props.list);
        var defs = [];
        this.defs = defs;
        delete this.defs;
        this._collect_field_attributes();
        return this.orm.call('custom.gantt.content', 'fetch_gantt_contents', [this.result, required_input]).then((tasks) => {
            this.taskArray = tasks;
            this.renderGantt(tasks);
        })
    }
//    Function to collect field attributes
    _collect_field_attributes() {
        var result = {
            date_assign: this.archInfo.startDate ? this.archInfo.startDate: null,
            date_end: this.archInfo.endDate ? this.archInfo.endDate: null,
            col: this.archInfo.defaultGroup ? this.archInfo.defaultGroup: null,
            model: this.archInfo.modelName ? this.archInfo.modelName: null,
        }
        if(!result['date_assign'] || !result['date_end']
            || !result['col'] || !result['model']){
            alert("Incorrect view configuration !")
        }
        this.result = result;
        return ;
    }
//    Function to create source data
    create_source(tasks){
		if(!tasks){
			return [];
		}
		var task;
		var sources = [];
        var progress, current_time, total_time, worked_time;
        current_time = dateParser(tasks[1]);
        for(var i in tasks[0]){
            total_time = 0, worked_time = 0;
            for (var j=0; j<tasks[0][i].length; j++){
                task = tasks[0][i][j];
                if(task.parent == true){
                    total_time += (dateParser(task.end) - dateParser(task.start));
                }
                else if (current_time >= dateParser(task.start)){
                    worked_time += (current_time - dateParser(task.start))
                }
            }
			for (var j=0; j<tasks[0][i].length; j++){
				task = tasks[0][i][j];
                if(task.parent == true) {
                    progress = (worked_time / total_time) * 100;
                    task.progress = progress;
                    task.custom_class = 'bar_parent';
                }
				sources.push(task);
			}
		}
		return sources;
	}
//    Function to update time
    update_time(task, start, end) {
        try{
            var parent = this.taskArray[0][task.type_id];
            var p_time, p_time_end, c_time_start, c_time_end, s_time_start, s_time_end;
            var new_s_date;
            p_time = dateParser(parent[0].start);
            p_time_end = dateParser(parent[0].end);
            s_time_start = dateParser(start);
            s_time_end = dateParser(end);
            for(var i in parent){
                if(parent[i]['id'] == task.id){
                    /*changing date of selected bar*/
                    var old_start = dateParser(parent[i].start);
                    var old_end = dateParser(parent[i].end);
                    parent[i].start = start;
                    parent[i].end = end;
                    c_time_start = dateParser(parent[i].start);
                    c_time_end = dateParser(parent[i].end);
                    new_s_date = parent[i].start;
                    /*updating date of parent*/
                    if(p_time == s_time_start){}
                    else if(p_time > s_time_start){
                        parent[0].start = start;
                    }
                    else if(p_time == old_start){
                        /*checking old start date and selecting new one
                        * this child was the the earliest task*/
                        for(var p in parent){
                            if(parent[p].parent == false){
                                if(dateParser(parent[p].start) < c_time_start){
                                    new_s_date = parent[p].start;
                                }
                            }
                        }
                        parent[0].start = new_s_date;
                    }
                    if(p_time_end == s_time_end){}
                    else if(s_time_end > p_time_end){
                        parent[0].end = end;
                    }
                    else if(old_end == p_time_end){
                        /*checking old end date and selecting new one
                        * this child was the final task*/
                        new_s_date = parent[i].end;
                        for(var p in parent){
                            if(parent[p].parent == false){
                                if(c_time_end < dateParser(parent[p].end)){
                                    new_s_date = parent[p].end;
                                }
                            }
                        }
                        parent[0].end = new_s_date;
                    }
                }
            }
        }
        catch (err){}
    }
//    Function to render gantt view
    renderGantt(taskArray) {
        var self = this;
		var sources = this.create_source(taskArray);
        var active_mode, old_mode;
        if (sources.length === 0) {
            sources = [{
                name: 'No records to display!'
            }];
        }
        var gantt = new Gantt(self.ref.el.querySelector('.gantt_custom'),sources, {
            header_height: 50,
            column_width: 30,
            step: 24,
                view_modes: ['Quarter Day', 'Half Day', 'Day', 'Week', 'Month', 'Year'],
            bar_height: 20,
            bar_corner_radius: 3,
            arrow_curve: 5,
            padding: 18,
            view_mode: self.view_mode ? self.view_mode:'Day',
            date_format: 'YYYY-MM-DD',
            custom_popup_html: null,
            on_click: function (task) {
            },
            on_date_change(task, start, end) {
                if(task.child=true){
                    /*task*/
                    var d = new Date(start);
                    var date_start = d;
                    var start_date = d.getUTCFullYear() + "-" +
                        (d.getUTCMonth() + 1) + "-" + d.getUTCDate() + " " +
                        d.getUTCHours() + ":" + d.getUTCMinutes();
                    d = new Date(end);
                    var date_end = d;
                    var end_date = d.getUTCFullYear() + "-" +
                        (d.getUTCMonth() + 1) + "-" + d.getUTCDate() + " " +
                        d.getUTCHours() + ":" + d.getUTCMinutes();
                    self.update_time(task, start_date, end_date);
                    self.orm.call('custom.gantt.content', 'update_time_range', [task, self.result, date_start, date_end])
                }
                else if(task.parent == true){
                    /*type*/
                }
            },
            on_progress_change: function(task, progress) {
            }
        });
        $('.quarter_day').click(function(){
            $('.btn-light').removeClass('active');
            $(this).addClass('active');
            self.view_mode = 'Quarter Day';
            gantt.change_view_mode('Quarter Day');
        });
        $('.half_day').click(function(){
            $('.btn-light').removeClass('active');
            $(this).addClass('active');
            self.view_mode = 'Half Day';
            gantt.change_view_mode('Half Day');
        });
        $('.full_day').click(function(){
            $('.btn-light').removeClass('active');
            $(this).addClass('active');
            self.view_mode = 'Day';
            gantt.change_view_mode('Day');
        });
        $('.week').click(function(){
            $('.btn-light').removeClass('active');
            $(this).addClass('active');
            self.view_mode = 'Week';
            gantt.change_view_mode('Week');
        });
        $('.month').click(function(){
            $('.btn-light').removeClass('active');
            $(this).addClass('active');
            self.view_mode = 'Month';
            gantt.change_view_mode('Month');
        });
        $('.year').click(function(){
            $('.btn-light').removeClass('active');
            $(this).addClass('active');
            self.view_mode = 'Year';
            gantt.change_view_mode('Year');
        });
        $('.reload_gantt_button').click(function(){
            self.renderGantt(self.taskArray);
        });
    }
}
GanttRenderer.template = 'custom_gantt_view.GanttRenderer'
