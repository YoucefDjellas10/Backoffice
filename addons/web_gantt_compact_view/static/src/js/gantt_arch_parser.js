/** @odoo-module */

import { unique } from "@web/core/utils/arrays";
import { visitXML } from "@web/core/utils/xml";
import { getActiveActions } from "@web/views/utils";
import { deserializeDateTime} from "@web/core/l10n/dates";

const { DateTime } = luxon;

export class GanttArchParser {
    parse(arch) {
        const archInfo = {
            fieldNames: [],
            activeActions: getActiveActions(arch),
        };

        visitXML(arch, (node) => {
            switch (node.tagName) {
                case "ganttview":
                    this.visitGanttView(node, archInfo);
                    break;
                case "field":
                    this.visitField(node, archInfo);
                    break;
            }
        });

        archInfo.fieldNames = unique(archInfo.fieldNames);
        return archInfo;
    }

    visitGanttView(node, archInfo) {
        
        archInfo.defaultScale = 'month';
        if (node.hasAttribute("initial_date")) {
            //var initial_date = "2019-08-11 00:00"; //sample date format
            var startDate =  new Date(node.getAttribute("initial_date")).toISOString().replace(/T|Z/g, ' ').trim().substring(0, 19);
            var startDateStr = deserializeDateTime(startDate);
            archInfo.initialDate = startDateStr;
        }else{
            archInfo.initialDate = DateTime.now();
        }

        if (node.hasAttribute("date_start")) {
            archInfo.dateStartField = node.getAttribute("date_start");
        }
        if (node.hasAttribute("date_stop")) {
            archInfo.dateStopField = node.getAttribute("date_stop");
        }
        if (node.hasAttribute("progress")) {
            archInfo.progressField = node.getAttribute("progress");
        }
        if (node.hasAttribute("color")) {
            archInfo.colorField = node.getAttribute("color");
        }
        if (node.hasAttribute("task_type")) {
            archInfo.taskType = node.getAttribute("task_type");
        }
        if (node.hasAttribute("deadline")) {
            archInfo.deadLine = node.getAttribute("deadline");
        }
        if (node.hasAttribute("round_dnd_dates")) {
            archInfo.roundDndDates = node.getAttribute("round_dnd_dates");
        }
        if (node.hasAttribute("priority")) {
            archInfo.taskPriority = node.getAttribute("priority");
        }

        const { canCreate: canCreate, canDelete: canDelete, canEdit: canEdit } = getActiveActions(node);

        archInfo.canCreate = canCreate;
        archInfo.canDelete = canDelete;
        archInfo.canEdit = canEdit;
    }
    visitField(node, params) {
        params.fieldNames.push(node.getAttribute("name"));
    }
}
