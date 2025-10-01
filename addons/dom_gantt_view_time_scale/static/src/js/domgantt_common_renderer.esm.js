/** @odoo-module **/
import {DomGanttCommonRenderer} from "@dom_gantt_view/js/common/domgantt_common_renderer.esm";
import {patch} from "@web/core/utils/patch";

patch(DomGanttCommonRenderer.prototype, {
    cleanOptions(options) {
        const opt = super.cleanOptions(options);
        if (!this.props.model.meta.isDateTimeScale) {
            return opt;
        }
        const scaleHours = this.props.model.meta.scaleHours || 12;
        opt.allDaySlot = false;
        opt.slotDuration = {
//             Days: 1,
//             milliseconds: scaleHours * 60 * 60 * 1000,
            hours: scaleHours,
        };

//         If (opt.slotLabelFormat === undefined) {
//             opt.slotLabelContent = function (arg) {
//                 const dateObj = luxon.DateTime.fromJSDate(arg.date);
//                 if (arg.level === 0) {
//                     if (["month", "year"].includes(this.props.model.scale)) {
//                         if (dateObj.toFormat("d") === "1") {
//                             return dateObj.monthShort + " " + dateObj.toFormat("dd");
//                         }
//                         return dateObj.toFormat("dd") + " " + dateObj.weekdayShort[0];
//                     }
//                     return arg.text;
//                 }
//                 return dateObj.toFormat("a");
//             };
//         }
        return opt;
    },
});
