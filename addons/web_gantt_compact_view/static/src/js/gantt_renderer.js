/** @odoo-module */

import { _lt, _t } from "@web/core/l10n/translation";
import { Component, onMounted, useRef, useState} from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { uniqueId } from "@web/core/utils/functions";
import { serializeDateTime, deserializeDateTime } from "@web/core/l10n/dates";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

const { DateTime } = luxon;

export class GanttRenderer extends Component {
    setup() {
        this.viewContainerRef = useRef("viewContainer");
        this.titleContainerRef = useRef("titleContainer");
        this.dialog = useService('dialog');
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.dialogService = useService("dialog");
        
        this.state = useState({
            data: [],
            date_display: false,
        });

        useBus(this.env.bus, "render-gantt", this.renderView.bind(this));
        useBus(this.env.bus, "task_display", this._onTaskDisplay.bind(this));
        useBus(this.env.bus, "task_update", this._onTaskUpdate.bind(this));
        useBus(this.env.bus, "task_create", this._onTaskCreate.bind(this));

        onMounted(() => {
            this.renderView();
        });

        this.gantt_events = [];
    }
    async renderView(){
        var self = this;    
        
        $(self.viewContainerRef.el).empty();

        var data = await this.props.model.fetchData();
        self.state.data = data;
        console.log(self.titleContainerRef.el, this.props.model.gantt.date_display)
        self.state.date_display = this.props.model.gantt.date_display;
        self.titleContainerRef.el.innerHTML = self.state.date_display;

        if(self.state.data.rows.length > 0){
            this._configGantt();
            this._renderGantt();
        }
        else if (self.state.data.rows.length == 0) {
            $(self.viewContainerRef.el).append(_t(
                `<div class="o_list_view">
                    <div class="o_view_nocontent">
                        <div class="o_nocontent_help">
                            <p class="o_view_nocontent_smiling_face">No record found. Let's create a new Task!</p>
                            <p>Click to add a new record.</p>
                        </div>
                    </div>
                </div>`
            ));
            return;
        };
    }
    _configGantt() {
        var self = this;
        const now = luxon.DateTime.now();

        var startDateStr = this.props.model.gantt.start_date ? this.props.model.gantt.start_date.toFormat('yyyy-MM-dd HH:mm:ss') : '';
        var EndDateStr = this.props.model.gantt.end_date ? this.props.model.gantt.end_date.toFormat('yyyy-MM-dd HH:mm:ss') : '';

        gantt.config.autosize = "y";
        gantt.config.drag_progress = false;
        gantt.config.drag_resize = true;
        gantt.config.grid_width = 280;
        gantt.config.row_height = 35;
        gantt.config.duration_unit = "minute";
        gantt.config.initial_scroll = false;
        gantt.config.preserve_scroll = true;
        
        gantt.config.start_on_monday = now.endOf("week").day;
        gantt.config.start_date = startDateStr;
        gantt.config.end_date = EndDateStr;
        gantt.config.round_dnd_dates = !!false;
        gantt.config.drag_move = this.edit ? JSON.parse(this.edit) : true;
        gantt.config.sort = true;
        gantt.config.work_time = true;
        gantt.config.skip_off_time = true;

        gantt.plugins({ 
            tooltip: true,
            fullscreen: true,
            marker: true,
            drag_timeline: true,
            fullscreen: true
        });

        gantt.config.columns = [    
            {
                name: "text",
                label: _lt("Gantt View"),
                tree: true,
                width: "*",
                resize: true,
                template: function(task) {
                    var html = '';
                    if (task.deadline && task.end_date) {
                        if ( task.end_date.valueOf() > new Date(task.deadline).valueOf()) {
                            var endTime = Math.abs(( new Date(task.end_date).getTime() ));
                            var deadLine = Math.abs(( new Date(task.deadline).getTime() + 86400000 ));
                            var overdue = Math.ceil((endTime - deadLine) / (24 * 60 * 60 * 1000));
                            if (overdue > 0){
                                html += '<div class="deadline_alert fa fa-exclamation-triangle"></div>';
                            }
                        }
                    }
                    if ((Math.round(task.progress * 100) == 100)) {
                        html += "<div class='progress_alert fa fa-check'></div>";
                    }
                    return html + task.text;
                },
            },   
            {
                name: "duration", 
                label: _lt("Duration(d)"),
                align: "center", 
                width: 80, 
            },                                             
        ];
    
        gantt.templates.grid_indent = function () {
            return "<div class='gantt_tree_indent' style='width:20px;'></div>";
        };

        gantt.templates.task_class = function (start, end, task) {
            var classes = ["o_gantt_color" + task.color + "_0"];               
            if (task.is_group) {
                classes.push("has_child");
            } else {
                classes.push("is_leaf");
            }
            return classes.join(" ");
        };

        gantt.templates.task_row_class = function (start, end, task) {
            var classes = ["level_" + task.$level];
            return classes;
        };

        gantt.templates.timeline_cell_class = function (item, date) {
            var classes = "date_" + date.getTime();
            var today = new Date();
            if (self.props.model.gantt.scale !== "year" && (date.getDay() === 0 || date.getDay() === 6)) {
                classes += " weekend_task";
            }
            if (self.props.model.gantt.scale !== "day" && date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getYear() === today.getYear()) {
                classes += " today";
            }
            return classes;
        };

        gantt.templates.task_text = function (start, end, task) {                      
            return task.text  + "<span style='text-align:left;'> (" + Math.round(task.progress * 100) + "%)</span>";
        };

        gantt.templates.tooltip_text = function(start,end,task){            
            return "<b>Task:</b> "+task.text+"<br/>" + 
                "<b>Start date:</b>" + gantt.templates.tooltip_date_format(start) + 
                "<br/><b>End date:</b> "+gantt.templates.tooltip_date_format(end) +
                "<br/><b>Progress:</b> "+ (Math.round(task.progress * 100)) + "%";
        };
        
        gantt.templates.grid_folder = function(item) {
            return "<div class='gantt_tree_icon gantt_folder_" +
            (item.$open ? "open" : "closed") + "'></div>";
        };

        gantt.templates.grid_file = function(task) {
            var html = '';
            if (!task.is_group){
                if (task.priority === 'high') {
                    html += "<div class='gantt_tree_icon gantt_file priority_high'></div>";
                }
                else if(task.priority === 'low'){
                    html += "<div class='gantt_tree_icon gantt_file priority_low'></div>";
                }
                else{
                    html += "<div class='gantt_tree_icon gantt_file priority_normal'></div>";
                }                           
            }
            return html;
        };

        gantt.templates.rightside_text = function (start, end, task) { 
            if (task.deadline) {
                var text = "";
                if (end.valueOf() > new Date(task.deadline).valueOf()) {
                    var endTime = Math.abs(( new Date(end).getTime() ));
                    var deadLine = Math.abs(( new Date(task.deadline).getTime() + 86400000 ));
                    var overdue = Math.ceil((endTime - deadLine) / (24 * 60 * 60 * 1000));
                    if (overdue > 0){
                        var text = "<b>Overdue: " + overdue + " days</b>";
                    }                        
                    return text;
                }
            }
        };
    }

    _renderGantt(){
        var self = this;            
        var ganttData = this._renderRows();
        this._renderGanttData(ganttData);
        this._configureGanttEvents();
    }
    _renderRows(){
        var self = this;
        var ganttData = [];
        var rowWidgets = [];
        var linkWidgets = [];
        
        var build_tasks = function (rows, groupedBy, parent=false) {
            rows.forEach(function (row) {
                if (groupedBy.length) {
                    if (row.records.length === 0){
                        return;
                    }
                    var project_id = uniqueId("gantt_project_");
                    var t = {
                        'id': project_id,
                        'text': row.name,
                        'is_group': true,
                        'start_date':false,
                        'open': true,
                        'color': '#f4f7f4',
                        'textColor': '#000000',
                        'create': row.create,
                        'is_task': false,
                    }    
                   
                    if (row.records){
                        var progress = 0;
                        for(var m = 0, mlen = row.records.length; m < mlen; ++m){
                            progress  = progress + (row.records[m].progress / 100);
                        }
                        t.progress = progress / row.records.length || 0;;
                    }
                    if (parent){
                        t.parent = parent;
                    }
                    rowWidgets.push(t);
                    if (row.isGroup && row.isOpen) {
                        var subRowWidgets = build_tasks(row.rows, groupedBy.slice(1), project_id);   
                        if (subRowWidgets != undefined){
                            rowWidgets = rowWidgets.concat(subRowWidgets);
                        }                            
                    }
                    else{
                        if (row.records){
                            for(var j = 0, jlen = row.records.length; j < jlen; ++j){
                                var task_id = uniqueId("gantt_task_");
                                rowWidgets.push({
                                    'id': task_id,
                                    'text': row.records[j].display_name || '',
                                    'active': row.records[j].active || true,
                                    'start_date': self._getTaskStart(row.records[j]),
                                    'end_date': self._getTaskStop(row.records[j]),
                                    'progress': self._getTaskProgress(row.records[j]),
                                    'parent': project_id,
                                    'open': true,
                                    'color': self._getTaskColor(row.records[j]),
                                    'type':row.records[j].type,
                                    'deadline': self._getTaskDeadline(row.records[j]),
                                    'priority': self._getTaskPriority(row.records[j]),
                                    'resId': row.records[j].id,
                                    'is_task': true,
                                });
                            }
                        }
                    }
                }
                else{
                    if (row.records){
                        for(var k = 0, klen = row.records.length; k < klen; ++k){
                            var task_id = uniqueId("gantt_task_");
                            rowWidgets.push({
                                'id': task_id,
                                'text': row.records[k].display_name || '',
                                'active': row.records[k].active || true,
                                'start_date': self._getTaskStart(row.records[k]),
                                'end_date': self._getTaskStop(row.records[k]),
                                'progress': self._getTaskProgress(row.records[k]),
                                'open': true,
                                'color': self._getTaskColor(row.records[k]),
                                'type': self._getTaskType(row.records[k]),
                                'rollup': true,
                                'deadline': self._getTaskDeadline(row.records[k]),
                                'priority': self._getTaskPriority(row.records[k]),
                                'resId': row.records[k].id,
                                'is_task': true,
                            })
                        }
                    } 
                }
            })
            
        };

        build_tasks(this.state.data.rows, this.state.data.groupByKey);
        ganttData['data'] = rowWidgets;

        var _findTaskRow = function(id){  
            var target;
            rowWidgets.forEach(function (row) {
                for (const key in row) {
                    if (row['resId'] === id){
                        target = row;
                    }
                }
            });
            
            return target;
        };
        return ganttData;
    }
    _getTaskStart(r){
        var self = this;
        var task_start;
        if (r[self.props.model.metaData.dateStartField]) {
            task_start =  new Date(r[self.props.model.metaData.dateStartField]);
        }                
        else{
            return false;
        }
        return task_start;
    }
    _getTaskStop(r){
        var self = this;
        var task_stop;
        if (r[self.props.model.metaData.dateStopField]) {
            task_stop = new Date(r[self.props.model.metaData.dateStopField]);
            if (!task_stop) {
                task_stop = task_start.clone().add(1, 'hours').toDate();
                task_stop =  '';
            }
        }
        return task_stop;
    }
    _getTaskProgress(r){
        var self = this;
        var progress;
        if (typeof r[self.props.model.metaData.progressField] === "number") {
            progress = r[self.props.model.metaData.progressField] || 0;
        } 
        else {
            progress = 0;
        }
        return progress / 100;
    }

    _getTaskColor(r){
        var self = this;
        var color;
        if (r[self.props.model.metaData.colorField]) {
            if (r[self.props.model.metaData.colorField] == '1'){
                color = '#F06050';
            }
            if (r[self.props.model.metaData.colorField] == '2'){
                color = '#F4A460';
            }
            if (r[self.props.model.metaData.colorField] == '3'){
                color = '#F7CD1F';
            }
            if (r[self.props.model.metaData.colorField] == '4'){
                color = '#6CC1ED';
            }
            if (r[self.props.model.metaData.colorField] == '5'){
                color = '#814968';
            }
            if (r[self.props.model.metaData.colorField] == '6'){
                color = '#EB7E7F';
            }
            if (r[self.props.model.metaData.colorField] == '7'){
                color = '#2C8397';
            }
            if (r[self.props.model.metaData.colorField] == '8'){
                color = '#475577';
            }
            if (r[self.props.model.metaData.colorField] == '9'){
                color = '#D6145F';
            }
            if (r[self.props.model.metaData.colorField] == '10'){
                color = '#30C381';
            }
            if (r[self.props.model.metaData.colorField] == '11'){
                color = '#9365B8';
            }
        }else{
            color = "#7C7BAD";
        }
        return color;
    }
    _getTaskType(r){
        var self = this;
        var type;
        if (r[self.props.model.metaData.taskType]) {
            type = r[self.props.model.metaData.taskType];
        }else{
            type = 'task';
        }
        return type;
    }
    _getTaskDeadline(r){
        var self = this;
        var deadline;
        if (r[self.props.model.metaData.deadLine]) {
            deadline = r[self.props.model.metaData.deadLine];
        }
        return deadline;
    }
    _getTaskPriority(r){
        var self = this;
        var priority;
        if (r[self.props.model.metaData.taskPriority]) {
            priority = r[self.props.model.metaData.taskPriority];
        }
        return priority;
    }

    _renderGanttData(gantt_tasks) {            
        var self = this;            
        var container_height = $('.o_main_navbar').height() + $('.o_control_panel').height() + 80;
        this.viewContainerRef.el.style.minHeight = (window.outerHeight - container_height) + "px";
      
        while (this.gantt_events.length) {
            gantt.detachEvent(this.gantt_events.pop());
        }
        this._setScaleConfig(self.props.model.gantt.scale);

        gantt.init(this.viewContainerRef.el);
        gantt.clearAll();
        
        gantt.showDate(this.props.model.gantt.focus_date);
        gantt.parse(gantt_tasks);
        
        var dateToStr = gantt.date.date_to_str(gantt.config.task_date);
        var markerId = gantt.addMarker({  
            start_date: new Date(), 
            css: "today", 
            text: "Now", 
            title: dateToStr(new Date()) 
        }); 

        var scroll_state = gantt.getScrollState();
        gantt.scrollTo(scroll_state.x, scroll_state.y);
    }

    _configureGanttEvents(tasks, grouped_by, groups) {
        var self = this;

        this.gantt_events.push(gantt.attachEvent("onEmptyClick", function(e){
            self.env.bus.trigger("task_create" , e);
        }));

        this.gantt_events.push(gantt.attachEvent("onTaskClick", function (id, e) {                    
            if(gantt.getTask(id).is_group) {
                return true;
            }                    
            if(gantt.getTask(id)){
                var task = gantt.getTask(id);
                self.env.bus.trigger("task_display", {task});
            }
            return true;
        }));

        this.gantt_events.push(gantt.attachEvent("onTaskDblClick", function (){ 
            return false; 
        }));
        
        this.gantt_events.push(gantt.attachEvent("onBeforeTaskSelected", function (id) {
            if(gantt.getTask(id).is_group){   
                if($("[task_id="+id+"] .gantt_tree_icon")){
                    $("[task_id="+id+"] .gantt_tree_icon").click();
                    return false;
                }                                        
            }
            return true;
        }));

        var parent_date_update = function (id) {
            var start_date, stop_date;
            var clicked_task = gantt.getTask(id);
            
            if (!clicked_task.parent) {
                return;
            }

            var parent = gantt.getTask(clicked_task.parent);
            for(var i = 0, ilen = gantt.getChildren(parent.id).length; i < ilen; ++i){
                var task_id = gantt.getChildren(parent.id)[i];
                var task_start_date = gantt.getTask(task_id).start_date;
                var task_stop_date = gantt.getTask(task_id).end_date;
                if(!start_date){
                    start_date = task_start_date;
                }
                if(!stop_date){
                    stop_date = task_stop_date;
                }
                if(start_date > task_start_date){
                    start_date = task_start_date;
                }
                if(stop_date < task_stop_date){
                    stop_date = task_stop_date;
                }
            };

            parent.start_date = start_date;
            parent.end_date = stop_date;
            gantt.updateTask(parent.id);
            if (parent.parent) parent_date_update(parent.id);
        };
        
        this.gantt_events.push(gantt.attachEvent("onBeforeTaskDrag", function (id, mode, e){
            var task = gantt.getTask(id);
            task._start_date_original = task.start_date;
            task._end_date_original = task.end_date;
            this.lastX = e.pageX;

            if (task.is_group) {
                var attr = e.target.attributes.getNamedItem("consolidation_ids");
                if (attr) {
                    var children = attr.value.split(" ");
                    this.drag_child = children;
                    for(var i = 0, ilen = this.drag_child.length; i < ilen; ++i){
                        var child_id = this.drag_child[i];
                        var child = gantt.getTask(child_id);
                        child._start_date_original = child.start_date;
                        child._end_date_original = child.end_date;
                    };
                }
            }
            return true;
        }));
        
        this.gantt_events.push(gantt.attachEvent("onTaskDrag", function (id, mode, task, original, e){
            if(gantt.getTask(id).is_group){
                var day;                                                        
                if (self.props.model.gantt.scale === "year") {
                    day = 51840000;
                }
                if (self.props.model.gantt.scale === "month") {
                    day = 3456000;
                }
                if (self.props.model.gantt.scale === "week") {
                    day = 1728000;
                }
                if (self.props.model.gantt.scale === "day") {
                    day = 72000;
                }
                
                var diff = (e.pageX - this.lastX) * day;
                this.lastX = e.pageX;

                if (task.start_date > original.start_date){ 
                    task.start_date = original.start_date; 
                }
                if (task.end_date < original.end_date){ 
                    task.end_date = original.end_date; 
                }

                if (this.drag_child){
                    for(var i = 0, ilen = this.drag_child.length; i < ilen; ++i){
                        var child_id = this.drag_child[i];
                        var child = gantt.getTask(child_id);
                        var new_start = +child.start_date + diff;
                        var new_stop = +child.end_date + diff;
                        if (new_start < gantt.config.start_date || new_stop > gantt.config.end_date){
                            return false;
                        }
                        child.start_date = new Date(new_start);
                        child.end_date = new Date(new_stop);
                        gantt.updateTask(child.id);
                        parent_date_update(child_id);
                    };
                }
                gantt.updateTask(task.id);
                return false;
            }
            parent_date_update(id);
            return true;
        }));

        this.gantt_events.push(gantt.attachEvent("onAfterTaskDrag", function (id){
            var update_task = function (task_id) {
                var task = gantt.getTask(task_id);
                self.env.bus.trigger('task_update', {
                    task: task,
                    success: function () {
                        parent_date_update(task_id);
                    },
                    fail: function () {
                        task.start_date = task._start_date_original;
                        task.end_date = task._end_date_original;
                        gantt.updateTask(task_id);
                        delete task._start_date_original;
                        delete task._end_date_original;
                        parent_date_update(task_id);
                    }
                });
            };

            if (gantt.getTask(id).is_group && this.drag_child) {
                for(var i = 0, ilen = this.drag_child.length; i < ilen; ++i){
                    var child_id = this.drag_child[i];
                    update_task(child_id);
                };
            }
            update_task(id);
        }));         
    }

    _setScaleConfig(value) {            
        gantt.config.min_column_width = 48;
        gantt.config.scale_height = 48;
        gantt.config.step = 1;
                            
        switch (value) {
            case "day":                    
                gantt.config.scale_unit = "day";
                gantt.config.date_scale = "%d %M";
                gantt.templates.scale_cell_class = getcss;
                gantt.config.subscales = [{unit:"hour", step:1, date:"%H h"}];
                gantt.config.scale_height = 27;
                break;
            case "week":
                var weekScaleTemplate = function (date){
                    var dateToStr = gantt.date.date_to_str("%d %M %Y");
                    var endDate = gantt.date.add(gantt.date.add(date, 1, "week"), -1, "day");
                    return dateToStr(date) + " - " + dateToStr(endDate);
                };
                gantt.config.scale_unit = "week";
                gantt.templates.date_scale = weekScaleTemplate;
                gantt.config.subscales = [{unit:"day", step:1, date:"%d, %D", css:getcss}];
                break;
            case "month":
                gantt.config.scale_unit = "month";
                gantt.config.date_scale = "%F, %Y";
                gantt.config.subscales = [{unit:"day", step:1, date:"%d", css:getcss}];
                gantt.config.min_column_width = 25;
                break;
            case "year":
                gantt.config.scale_unit = "year";
                gantt.config.date_scale = "%Y";
                gantt.config.subscales = [{unit:"month", step:1, date:"%M"}];
                break;
        }
        function getcss(date) {
            var today = new Date();
            if(date.getDay() === 0 || date.getDay() === 6){
                return "weekend_scale";
            }
            if(date.getMonth() === today.getMonth() && date.getDate() === today.getDate()){
                return "today";
            } 
        }
    }

    async _onTaskCreate(event){
        var self = this;
        var context = session.user_context;
        if (this.props.model.metaData.activeActions.create) {
            if (event && event.detail.target.classList.contains('gantt_task_cell')){
                var id = event.detail.target.parentElement.attributes.task_id.value;
                var task = gantt.getTask(id);
                var  classDate =  Array.from(event.detail.target.classList).find(function (e) {
                    return e.indexOf("date_") > -1;
                });
                
                var startDate = new Date(parseInt(classDate.split("_")[1], 10)).toISOString().replace(/T|Z/g, ' ').trim().substring(0, 19);;
                var startDateStr = deserializeDateTime(startDate);
                var endDate;
                switch (self.props.model.gantt.scale) {
                    case "day":
                        endDate = serializeDateTime(startDateStr.plus({ days: 1 }));
                        break;
                    case "week":
                        endDate = serializeDateTime(startDateStr.plus({ weeks: 1 }));
                        break;
                    case "month":
                        endDate = serializeDateTime(startDateStr.plus({ months: 1 }));
                        break;
                    case "year":
                        endDate = serializeDateTime(startDateStr.plus({ years: 1 }));
                        break;
                }

                var get_create = function (item) {
                    if (item.create) {
                        context["default_"+item.create[0]] = item.create[1][0];
                    }
                    if (item.parent) {
                        var parent = gantt.getTask(item.parent);
                        get_create(parent);
                    }
                };
                get_create(task);

                context["default_" + self.props.model.metaData.dateStartField] = startDate;
                if (self.props.model.metaData.dateStopField) {
                    context["default_" + self.props.model.metaData.dateStopField] = endDate;
                } 

                context.id = 0;

                self.dialog.add(FormViewDialog, {
                    resModel: self.props.model.metaData.resModel,
                    context: session.user_context,
                    onRecordSaved: async () => {
                        self.renderView();
                    }
                });
            }
        }
    }

    async _onTaskUpdate(event) {
        var self = this;
        var taskObj = event.detail.task;
        var success = event.detail.success;
        var fail = event.detail.fail;

        var fields = self.props.model.metaData.fields;
        var dateStartField = self.props.model.metaData.dateStartField;
        var dateStopField = self.props.model.metaData.dateStopField;
        
        if (fields[dateStopField] === undefined) {
                self.dialogService.add(AlertDialog, {
                    title: _t('Error'),
                    body: _t("You have no date_stop field defined!"),
                });
            return fail();
        }

        if (fields[dateStartField].readonly || fields[dateStopField].readonly) {
            self.dialogService.add(AlertDialog, {
                title: _t('Error'),
                body: _t("You are trying to write on a read-only field!"),
            });
            return fail();
        }

        var start = taskObj.start_date;
        var end = taskObj.end_date;
        
        var data = {};

        var startDateStr = new Date(start).toISOString().replace(/T|Z/g, ' ').trim().substring(0, 19);
        var EndDateStr = new Date(end).toISOString().replace(/T|Z/g, ' ').trim().substring(0, 19);

        data[dateStartField] = startDateStr;
        data[dateStopField] = EndDateStr;
        
        var taskId = parseInt(taskObj.resId);
        const res = await this.orm.call(self.props.model.metaData.resModel, "write", [[taskId], data]).then(success, fail);;
    }


    _onTaskDisplay(event) {
        var task = event.detail.task
        var readonly = this.props.model.metaData.activeActions.edit ? "edit" : "readonly";
        this._displayTask(task, readonly);
    }

    _displayTask(task, readonly) {
        var self = this;
        var taskId = parseInt(task.resId);
        readonly = readonly ? readonly : false;

        self.dialog.add(FormViewDialog, {
            resModel: self.props.model.metaData.resModel,
            resId: parseInt(taskId),
            context: session.user_context,
            onRecordSaved: async () => {
                self.renderView();
            }
        });  
    }
}

GanttRenderer.template = "web_gantt_compact_view.ViewRenderer";
GanttRenderer.props = {
    model: { type: Object },
};