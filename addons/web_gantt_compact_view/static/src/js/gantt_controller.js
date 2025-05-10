/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadJS, loadCSS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { useModelWithSampleData } from "@web/model/model";
import { standardViewProps } from "@web/views/standard_view_props";
import { useSetupView } from "@web/views/view_hook";
import { Layout } from "@web/search/layout";
import { session } from "@web/session";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { serializeDateTime, deserializeDateTime} from "@web/core/l10n/dates";
import { Component, onWillUnmount, onWillUpdateProps, onWillStart, useRef, useState } from "@odoo/owl";
import { GanttExportDialog } from "./gantt_export_dialog"

const { DateTime } = luxon;
var  n_direction = false;

export class GanttController extends Component {
    setup() {
        this.action = useService("action");
        this.dialog = useService('dialog');

        this.state = useState({
            scale : 'month',
        });

        const Model = this.props.Model;
        const model = useModelWithSampleData(Model, this.props.modelParams);
        this.model = model;

        onWillUnmount(() => {});

        onWillUpdateProps(newProps => {
            this.model._setScale(this.state.scale);
            this.env.bus.trigger("render-gantt");
        });

        useSetupView({
            rootRef: useRef("root"),
            getLocalState: () => {
                return this.model.metaData;
            },
        });

        onWillStart(async () => {
            await loadCSS("/web_gantt_compact_view/static/lib/dhtmlxGantt/sources/dhtmlxgantt.css");
            await loadJS("/web_gantt_compact_view/static/lib/dhtmlxGantt/sources/dhtmlxgantt.js");
            await loadJS("/web_gantt_compact_view/static/lib/dhtmlxGantt/sources/api.js");
        });

        this.searchBarToggler = useSearchBarToggler();
    }

    get rendererProps() {
        return {
            model: this.model,
        };
    }
    
    onNewTask(){
        var self = this;
        var context = session.user_context;
        var startDate = serializeDateTime(DateTime.now());
        var startDateStr = deserializeDateTime(startDate);
        var endDate;

        switch (self.model.gantt.scale) {
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

        context["default_"+ self.model.metaData.dateStartField] = startDate;
        if (self.model.metaData.dateStopField) {
            context["default_"+ self.model.metaData.dateStopField] = endDate;
        } 

        self.dialog.add(FormViewDialog, {
            resModel: self.model.metaData.resModel,            
            context: session.user_context,
            onRecordSaved: async () => {
                self.onRecordSaved();                
            }
        });
    }
    displayName() {
        return this.model.root.data.display_name || (this.model.root.isNew && _t("New")) || "";
    }
    onPreviousClick(){
        var self = this;
        switch (self.model.gantt.scale) {
            case "day":
                self.setFocusDate(self.model.gantt.focus_date.minus({ 'days' : 1 }));
                break;
            case "week":
                self.setFocusDate(self.model.gantt.focus_date.minus({ 'weeks' : 1 }));
                break;
            case "month":
                self.setFocusDate(self.model.gantt.focus_date.minus({ 'months' : 1 }));
                break;
            case "year":
                self.setFocusDate(self.model.gantt.focus_date.minus({ 'years' : 1 }));
                break;
        }
    }
    onNextClick(){
        var self = this;
        switch (self.model.gantt.scale) {
            case "day":
                self.setFocusDate(self.model.gantt.focus_date.plus({ 'days' : 1 }));
                break;
            case "week":
                self.setFocusDate(self.model.gantt.focus_date.plus({ 'weeks' : 1 }));
                break;
            case "month":
                self.setFocusDate(self.model.gantt.focus_date.plus({ 'months' : 1 }));
                break;
            case "year":
                self.setFocusDate(self.model.gantt.focus_date.plus({ 'years' : 1 }));
                break;
        }
    }
    onTodayClick(){
        var self = this;
        self.setFocusDate(DateTime.now());
    }
    setFocusDate(focusDate) {
        var self = this;
        self.model._setFocusDate(focusDate);
        var currentDisplayName = this.env.config.getDisplayName().replace(/\s*\(.*?\)\s*/g, '');
        self.env.config.setDisplayName(currentDisplayName);
        return self.env.bus.trigger("render-gantt");;
    }

    setScale(scale) {
        var self = this;
        self.model._setScale(scale);
        var currentDisplayName = this.env.config.getDisplayName().replace(/\s*\(.*?\)\s*/g, '');
        self.env.config.setDisplayName(currentDisplayName);
        return this.env.bus.trigger("render-gantt");
    }

    onClickScale(ev){
        var $target = $(ev.target);
        var scale = $target.data('scale')

        if (scale === 'day'){
            this.state.scale = 'day';
        }
        else if (scale === 'week'){
            this.state.scale = 'week';
        }
        else if (scale === 'month'){
            this.state.scale = 'month';
        }
        else if (scale === 'year'){
            this.state.scale = 'year';
        }
        this.setScale(scale);
    }

    async onRecordSaved(record) {
        this.env.bus.trigger("render-gantt");
    }

    onExportPNGClick(){
        var self = this;
        self._onExportOpen('png');
    }

    onExportPDFClick(){
        var self = this;
        self._onExportOpen('pdf');
    }
    
    _onExportOpen(format){
        var self = this;
        self.dialog.add(GanttExportDialog, {
            format: format,
            scale: self.model.gantt.scale,
            gantt: gantt,
            model: self.model,
        });
    }

    onSortClick(e){
        e.preventDefault();        
        if (n_direction){
            gantt.sort("id",false);
        } 
        else {
            gantt.sort("id",true);
        }
        n_direction = !n_direction;
    }
}

GanttController.template = "web_gantt_compact_view.Contoller";
GanttController.components = {
    Layout,
    SearchBar,
};

GanttController.props = {
    ...standardViewProps,
    Model: Function,
    modelParams: Object,
    Renderer: Function,
    buttonTemplate: String,
};
