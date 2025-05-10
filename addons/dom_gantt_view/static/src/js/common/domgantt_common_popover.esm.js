/** @odoo-module **/

import {CalendarCommonPopover} from "@web/views/calendar/calendar_common/calendar_common_popover";

export class DomGanttCommonPopover extends CalendarCommonPopover {
    get isEventEditable() {
        return this.props.model.canEdit;
    }
}
