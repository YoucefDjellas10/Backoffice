/** @odoo-module **/
import {ActionSwiper} from "@web/core/action_swiper/action_swiper";
import {CalendarRenderer} from "@web/views/calendar/calendar_renderer";
import {DomGanttCommonRenderer} from "./common/domgantt_common_renderer.esm";

export class DomGanttRenderer extends CalendarRenderer {}

DomGanttRenderer.components = {
    day: DomGanttCommonRenderer,
    week: DomGanttCommonRenderer,
    month: DomGanttCommonRenderer,
    year: DomGanttCommonRenderer,
    ActionSwiper,
};
