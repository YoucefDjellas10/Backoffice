/** @odoo-module */

import { registry } from "@web/core/registry";
import { GanttRenderer } from "./gantt_renderer.js";
import { GanttController } from "./gantt_controller.js";
import { GanttArchParser } from "./gantt_arch_parser.js";
import { RelationalModel } from "@web/model/relational_model/relational_model";

/**
Created a class GanttView to combine all the pieces together, then register the
view in the views registry
*/
export const GanttView = {
    type: "gantt",
    display_name: "Gantt",
    icon: "fa fa-align-left",
    multiRecord: true,
    Controller: GanttController,
    Renderer: GanttRenderer,
    Model: RelationalModel,
    ArchParser: GanttArchParser,
    buttonTemplate: "web.ListView.Buttons",
    props: (genericProps, view) => {
        const { ArchParser } = view;
        const { arch, relatedModels, resModel } = genericProps;
        const archInfo = new ArchParser().parse(arch, relatedModels, resModel);
        return {
            ...genericProps,
            Model: view.Model,
            Renderer: view.Renderer,
            archInfo,
        };
    },
};
registry.category("views").add("gantt", GanttView);
