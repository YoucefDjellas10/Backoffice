/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { GanttArchParser } from "./gantt_arch_parser";
import { GanttController } from "./gantt_controller";
import { GanttRenderer } from "./gantt_renderer";
import { GanttModel } from "./gantt_model";

export const GanttView = {
    type: "ganttview",
    display_name: _t("Gantt View"),
    icon: "fa fa-tasks",
    multiRecord: true,
    ArchParser: GanttArchParser,
    Controller: GanttController,
    Model: GanttModel,
    Renderer: GanttRenderer,
    searchMenuTypes: ["filter", "groupBy"],
    buttonTemplate: "web_gantt_compact_view.Buttons",
    props: (genericProps, view, config) => {
        let modelParams = genericProps.state;
        if (!modelParams) {
            const { arch,  resModel, fields, context} = genericProps;
            const parser = new view.ArchParser();
            const archInfo = parser.parse(arch);
            const views = config.views || [];
            
            modelParams = {
                context: context,
                fields: fields,
                
                defaultScale: archInfo.defaultScale,
                dateStartField : archInfo.dateStartField,
                dateStopField : archInfo.dateStopField,
                progressField : archInfo.progressField,
                colorField : archInfo.colorField,
                taskType : archInfo.taskType,
                deadLine : archInfo.deadLine,
                roundDndDates : archInfo.roundDndDates,
                taskPriority : archInfo.taskPriority,
                initialDate: archInfo.initialDate,
                activeActions:archInfo.activeActions,
                
                hasFormView: views.some((view) => view[1] === "form"),
                resModel: resModel,
                defaultOrder: 'id',
                defaultGroupBy: [],
            };
        }

        return {
            ...genericProps,
            Model: view.Model,
            modelParams,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
        };
    }
};

registry.category('views').add('ganttview', GanttView);
