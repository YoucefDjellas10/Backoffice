/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useRef, useState, Component } from "@odoo/owl";
import { deserializeDateTime } from "@web/core/l10n/dates";

const { DateTime } = luxon;

export class GanttExportDialog extends Component {
    setup() {
        this.title = _t("Export PNG/PDF");
        var  today = DateTime.now();
        var  tomorrow = DateTime.now().plus({ days: 1 });
        
        this.start_date = new Date(today).toISOString().slice(0, 10).replace(/T|Z/g, ' ');
        this.end_date = new Date(tomorrow).toISOString().slice(0, 10).replace(/T|Z/g, ' ');

        this.state = useState({
            exportClassName: 'd-none',
        });

        this.startDateRef = useRef("startDate");
        this.endDateRef = useRef("endDate");
        this.setDateButtonRef = useRef("setDateButton");
        this.exportButtonRef = useRef("exportButton");
        this.notification = useService("notification");

        onMounted(async () => {

        });
        
    }
    close() {
        this.props.close && this.props.close();
    }
    onClickSetDate(){
        var self = this;

        var date_start = $(this.startDateRef.el);
        var date_end = $(this.endDateRef.el);
        
        if (Date.parse(date_start.val())  >=  Date.parse(date_end.val())){
            this.notification.add(
                _t("Start date must be anterior to end date!"),{
                    type: "warning",
                }
            );
            return;
        }
        var startDate =  new Date(date_start.val()).toISOString().slice(0, 10).replace(/T|Z/g, ' ');
        var startDateStr = deserializeDateTime(startDate);

        self.start_date = startDate;

        var DateEnd = new Date(date_end.val()).toISOString().slice(0, 10).replace(/T|Z/g, ' ');
        var DateEndStr = deserializeDateTime(DateEnd);

        self.end_date = DateEnd;

        self.props.model.gantt.start_date = startDateStr.startOf('day');
        self.props.model.gantt.to_date = DateEndStr.endOf('day');

        self.props.model.fetchData();

        self.props.gantt.config.start_date = new Date(startDateStr) ;
        self.props.gantt.config.end_date =  new Date(DateEndStr);

        self.state.exportClassName = 'all';
        self.props.gantt.render();        
    }
    onClickExport(){
        var self = this;
        var format = self.props.format;
        var date_start = $(this.startDateRef.el);
        var date_end = $(this.endDateRef.el);
        
        if (Date.parse(date_start.val())  >=  Date.parse(date_end.val())){
            this.notification.add(
                _t("Start date must be anterior to end date!"),{
                    type: "warning",
                }
            );
            return;
        }

        var startDate = new Date(date_start.val()).toISOString().slice(0, 10).replace(/T|Z/g, ' ');
        var startDateStr = deserializeDateTime(startDate);

        var DateEnd = new Date(date_end.val()).toISOString().slice(0, 10).replace(/T|Z/g, ' ');
        var DateEndStr = deserializeDateTime(DateEnd);

        var date_start = startDateStr;
        var date_end = DateEndStr;
        
        if(format === 'pdf'){
            gantt.exportToPDF({
                name: date_start + "_" + date_end + ".pdf",
                start: date_start,
                end: date_end,
            });
            self.props.close();
        }else if(format === 'png'){
            gantt.exportToPNG({
                name: date_start + "_" + date_end + ".png",
                start: date_start,
                end: date_end,
            });
            self.props.close();
        }else{
            self.notification.add(
                _t("The export format has not been specified!"),{
                    type: "warning",
                }
            );
        }
    }
}
GanttExportDialog.components = { Dialog };
GanttExportDialog.template = "web_gantt_compact_view.GanttExportDialog";
GanttExportDialog.defaultProps = {
    format: false,
    scale: false,
    gantt: { type: Object },
    model: { typeof: Object },
};