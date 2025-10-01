/** @odoo-module **/
import {CalendarController} from "@web/views/calendar/calendar_controller";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {_t} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";

export class DomGanttController extends CalendarController {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.state = useState({
            showSideBar: false,
        });
    }

    onClickAddButton() {
        if (!this.model.meta.canCreate) return;
        const context = {...this.model.meta.context};
        context.from_ui = true;
        if (this.model.formViewId) {
            this.displayDialog(FormViewDialog, {
                resModel: this.model.resModel,
                title: _t("New") + " " + this.model.meta.label || "",
                viewId: this.model.formViewId,
                onRecordSaved: () => {
                    this.model.load();
                },
                context: context,
            });
        } else {
            this.actionService.doAction(
                {
                    type: "ir.actions.act_window",
                    res_model: this.model.resModel,
                    views: [[false, "form"]],
                },
                {
                    additionalContext: context,
                }
            );
        }
    }
}

DomGanttController.template = "dom_gantt_view.DomGanttController";
