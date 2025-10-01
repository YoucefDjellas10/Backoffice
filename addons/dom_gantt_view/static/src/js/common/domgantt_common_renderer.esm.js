/** @odoo-module **/
import {App, onMounted, onPatched, useEffect, useExternalListener} from "@odoo/owl";
import {useCalendarPopover, useClickHandler} from "@web/views/calendar/hooks";
import {CalendarCommonRenderer} from "@web/views/calendar/calendar_common/calendar_common_renderer";
import {DomGanttCommonPopover} from "./domgantt_common_popover.esm";
import {DomGanttModelResource} from "./domgantt_model_resource.esm";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {getColor} from "@web/views/calendar/colors";
import {templates} from "@web/core/assets";
import {useDebounced} from "@web/core/utils/timing";
import {useDomGantt} from "../hooks.esm";

const MARKED_TITLE_SEPARATOR = "__DOMTTSEP__";
// Const RESOURCE_ORDER_PREFIX = "O__";
const SCALE_TO_FC_VIEW = {
    day: "resourceTimelineDay",
    week: "resourceTimelineWeek",
    month: "resourceTimelineMonth",
    year: "resourceTimelineYear",
};

export class DomGanttCommonRenderer extends CalendarCommonRenderer {
    setup() {
        this.fc = useDomGantt("fullCalendar", this.gantt_options);
        this.click = useClickHandler(this.onClick, this.onDblClick);
        this.popover = useCalendarPopover(this.constructor.components.Popover);
        this.onWindowResizeDebounced = useDebounced(this.onWindowResize, 200);

        onMounted(() => {
            this.scrollToTime();
        });
        onPatched(() => {
            this.scrollToTime();
        });
        useEffect(() => {
            this.updateSize();
        });

        if (this.props.model.pagingEnable) {
            useExternalListener(window, "scroll", this.onWindowScroll, true);
        }
    }
    scrollToTime() {
        browser.setTimeout(() => {
            if (this.fc.api.view) {
                const toDay = luxon.DateTime.now();
                if (this.props.model.scale === "day") {
                    // Need to wait React
                    this.fc.api.scrollToTime(toDay.toFormat("HH:mm"));
                } else {
                    this.fc.api.scrollToTime({
                        // Day: toDay.toObject().day,
                        month: toDay.toObject().month - 1,
                        // Year: toDay.toObject().year,
                    });
                }
            }
        }, 0);
    }

    get gantt_options() {
        const options = this.cleanOptions(this.options);
        const options_extra = {
            initialView: SCALE_TO_FC_VIEW[this.props.model.scale],
            displayEventTime: !this.props.model.meta.isTimeHidden,
            displayEventEnd: !this.props.model.meta.isTimeEndHidden,
            weekends: true,
            weekNumbers: false,
            resourceAreaHeaderContent: "",
            resourceAreaColumns: this._getResourceAreaColumns(),
            resources: (_, successRS) => successRS(this.mapRecordsToResources()),
            resourceLabelDidMount: this.onResourceLabelDidMount,
            eventAdd: this.onEventAdd,
            eventChange: this.onEventChange,
            eventRemove: this.onEventRemove,
            eventsSet: this.onEventSet,
        };
        if (this.props.model.meta.resourceWidth) {
            options_extra.resourceAreaWidth = this.props.model.meta.resourceWidth;
        }
        if (this.props.model.meta.resourceOrder) {
            const resourceOrders = this._getResourceOrders();
            if (resourceOrders && resourceOrders.key) {
                options_extra.resourceOrder = resourceOrders.key;
            }
        }
        if (this.props.model.meta.slotMinWidth) {
            options_extra.slotMinWidth = this.props.model.meta.slotMinWidth;
        }
        if (this.props.model.meta.resourceGroupField) {
            options_extra.resourceGroupField = this.props.model.meta.resourceGroupField;
        }
        if (this.props.model.meta.eventTimeFormatDigits) {
            options_extra.eventTimeFormat = {
                // Like '14:30'
                hour: "2-digit",
                minute: "2-digit",
                // Second: '2-digit',
                hour12: false,
            };
        }
        let nowDate = luxon.DateTime.local().startOf("day");
        if (
            nowDate < this.props.model.data.range.start ||
            nowDate > this.props.model.data.range.end
        ) {
            nowDate = this.props.model.data.range.start;
            options_extra.nowIndicator = false;
        }
        options_extra.now = nowDate.toString();
        Object.assign(options, options_extra);
        return options;
    }
    async onWindowScroll(ev) {
        const div = ev.target;
        if (div.scrollTop + div.clientHeight >= div.scrollHeight) {
            if (await this.props.model._nextPage()) {
                setTimeout(await this._showEventByPage(), 15000);
            }
        }
    }
    async _showEventByPage() {
        if (!this.fc.api) return;
        // eslint-disable-next-line array-callback-return
        Object.values(this.props.model.currentPageRecord).map((r) => {
            const eventRaw = this.convertRecordToEvent(r);
            this.fc.api.addEvent(eventRaw);
            if (!this.fc.api.getResourceById(eventRaw.resourceId)) {
                // Create the resource
                this._createResourceByEvent(r);
            }
        });
    }

    cleanOptions(options) {
        // Remove unnesscessory ones: plugins
        const opts = [
            "plugins",
            "slotLabelFormat",
            "defaultView",
            "defaultView",
            "dayRender",
            "defaultDate",
            "dir",
            "eventLimit",
            "eventLimitClick",
            "eventRender",
            "header",
            "weekLabel",
            "weekNumbersWithinDays",
            "columnHeaderFormat",
        ];
        options.eventDidMount = this.onEventRender;
        // eslint-disable-next-line array-callback-return
        opts.map((opt) => {
            delete options[opt];
        });
        if (this.props.model.meta.slotLabelFormat) {
            const slotLabelFormats = JSON.parse(this.props.model.meta.slotLabelFormat);
            if (slotLabelFormats[this.props.model.meta.scale] !== undefined) {
                options.slotLabelFormat = slotLabelFormats[this.props.model.meta.scale];
            }
        }
        return options;
    }

    mapRecordsToResources(items = null, forceUniqKey = false, forM2oMapping = false) {
        // ForM2oMapping={uniqKey: {columnName: val}}
        const resources = {};
        // {key: 'o_id,-o_title', mapping: {o_id: id, o_title: title}}
        const resourceOrders = this._getResourceOrders();
        const columnFields = this.props.model.meta.columnFields;
        const fieldNames = Object.keys(columnFields);
        const records = items || Object.values(this.props.model.records);
        // eslint-disable-next-line array-callback-return
        records.map((item) => {
            /**
             *{ id: 'd', column1: 'D', eventColor: 'green', column2: 40}
             */
            let m2oMapping = forM2oMapping;
            let uniqKeys = forceUniqKey;
            if (!forceUniqKey) {
                const uniqResources = this._getUniqueResourceIds(fieldNames, item);
                uniqKeys = uniqResources.uniqKeys;
                m2oMapping = uniqResources.m2oMapping;
            }

            for (const uniqKey of uniqKeys) {
                const resourceItem = {
                    id: uniqKey,
                    recordId: item.id,
                    postRenderFields: [],
                    forceValues: {},
                };
                // eslint-disable-next-line array-callback-return
                fieldNames.map((fieldName) => {
                    let title = item.rawRecord[fieldName];
                    if (
                        m2oMapping &&
                        m2oMapping[uniqKey] &&
                        m2oMapping[uniqKey][fieldName]
                    ) {
                        title = m2oMapping[uniqKey][fieldName];
                        resourceItem.forceValues[fieldName] = [title];
                    } else if (Array.isArray(item.rawRecord[fieldName])) {
                        // Title = item.rawRecord[fieldName][item.rawRecord[fieldName].length-1];
                        if (
                            item.rawRecord[fieldName].every((val) =>
                                Number.isInteger(val)
                            )
                        ) {
                            title = item.rawRecord[fieldName].toString();
                        } else
                            title =
                                item.rawRecord[fieldName][
                                    item.rawRecord[fieldName].length - 1
                                ];
                    }

                    const fieldObject = columnFields[fieldName];
                    if (
                        !fieldObject ||
                        (!fieldObject.attrs.gantt_group &&
                            !fieldObject.attrs.is_resource_group_field)
                    ) {
                        resourceItem.postRenderFields.push(fieldName);
                        title = this._getResourceMarkedTitle(fieldName, title);
                    }
                    resourceItem[fieldName] = title;
                });
                if (!fieldNames) {
                    resourceItem.title = item.title;
                } else if (resourceOrders && resourceOrders.mapping) {
                    for (const [resourceField, fieldName] of Object.entries(
                        resourceOrders.mapping
                    )) {
                        if (fieldNames.includes(fieldName)) {
                            let resourceVal = item.rawRecord[fieldName];
                            // eslint-disable-next-line max-depth
                            if (Array.isArray(item.rawRecord[fieldName])) {
                                resourceVal =
                                    item.rawRecord[fieldName][
                                        item.rawRecord[fieldName].length - 1
                                    ];
                            }
                            resourceItem[resourceField] = resourceVal;
                        }
                    }
                }
                this.postUpdateResourceItem(resourceItem, item, fieldNames);
                resources[resourceItem.id] = resourceItem;
            }
        });

        return [...Object.values(resources)];
    }
    // eslint-disable-next-line no-unused-vars,no-empty-function
    postUpdateResourceItem(resourceItem, item, fieldNames) {}
    _getResourceOrders() {
        const resourceOrder = this.props.model.meta.resourceOrder;
        if (!resourceOrder) return {};
        const orderKey = [];
        const mapping = {};
        const fieldNames = Object.keys(this.props.model.meta.columnFields);
        const orderFields = resourceOrder.split(",");
        // eslint-disable-next-line array-callback-return
        orderFields.map((orderField) => {
            const sortKF = orderField.trim().split(" ");
            const fieldName = sortKF[0].trim();
            const sortKey = sortKF[sortKF.length - 1].trim().toLowerCase();
            if (fieldName && fieldNames.includes(fieldName)) {
                // Let fname = RESOURCE_ORDER_PREFIX + fieldName;
                let fname = fieldName;
                mapping[fname] = fieldName;
                if (sortKey === "desc") fname = "-" + fname;
                orderKey.push(fname);
            }
        });
        // {key: 'o_id,-o_title', mapping: {o_id: id, o_title: title}}
        return {key: orderKey.join(","), mapping: mapping};
    }
    makeUpStr(str) {
        return str.replace(/[^a-zA-Z0-9]/g, "_");
    }
    _getResourceMarkedTitle(resourceId, title) {
        return this.makeUpStr(resourceId + MARKED_TITLE_SEPARATOR + title);
    }
    _getFieldNameFromMarkedTitle(markedTitle) {
        return markedTitle.split(MARKED_TITLE_SEPARATOR);
    }
    _getUniqueResourceIds(columnNames, item) {
        // This.props.model.meta.columnFields
        const uniqKeys = [];
        const m2o = {};
        // {uniqKey: {fieldName: val}}
        const m2oMapping = {};
        for (const colname of columnNames) {
            if (
                this.props.model.meta.columnFields[colname].attrs.m2o &&
                Array.isArray(item.rawRecord[colname]) &&
                item.rawRecord[colname].every((val) => Number.isInteger(val))
            ) {
                m2o[colname] = item.rawRecord[colname];
                break;
            }
        }
        if (Object.keys(m2o).length > 0) {
            // eslint-disable-next-line array-callback-return
            Object.entries(m2o).map(([colname, vals]) => {
                for (const val of vals) {
                    const keys = columnNames.map((columnName) => {
                        if (colname === columnName) return val;
                        else if (Array.isArray(item.rawRecord[columnName])) {
                            return item.rawRecord[columnName].toString();
                        }
                        return item.rawRecord[columnName];
                    });
                    const uniqKey = keys.join("_");
                    uniqKeys.push(uniqKey);
                    m2oMapping[uniqKey] = {};
                    m2oMapping[uniqKey][colname] = val;
                }
            });
        } else {
            let uniq = item.title;
            if (columnNames.length > 0) {
                const keys = columnNames.map((columnName) => {
                    if (Array.isArray(item.rawRecord[columnName])) {
                        return item.rawRecord[columnName].toString();
                    }
                    return item.rawRecord[columnName];
                });
                uniq = keys.join("_");
            }
            uniqKeys.push(uniq);
        }
        return {uniqKeys, m2oMapping};
    }
    _getResourceAreaColumns() {
        return this.props.model.data.resourceAreaColumns;
    }
    fcResourceToRecord(resource) {
        if (!resource) return {};
        const recordId = resource.extendedProps.recordId;
        const originRecord = this.props.model.records[recordId];
        if (!originRecord) return {};
        const columnFields = this.props.model.meta.columnFields;
        const fieldMapping = this.props.model.meta.fieldMapping;
        const fieldNames = Object.keys(columnFields);
        const DATE_FIELDS = ["date_start", "date_delay", "date_stop"];
        const exceptFieldMapping = Object.keys(fieldMapping).filter((fm) =>
            DATE_FIELDS.includes(fm)
        );
        let exceptFieldNames = Object.entries(fieldMapping).map(([fm, fn]) => {
            if (exceptFieldMapping.includes(fm)) return fn;
            return false;
        });
        exceptFieldNames = exceptFieldNames.filter((fn) => fn !== false);
        const resp = {};

        // eslint-disable-next-line array-callback-return
        fieldNames.map((fieldName) => {
            if (exceptFieldNames.includes(fieldName)) return false;
            const record = this._getRecordByForceValue(
                originRecord,
                resource.extendedProps.forceValues,
                fieldName
            );
            const rawRecord = record.rawRecord;
            resp[fieldName] = rawRecord[fieldName];
            if (Array.isArray(rawRecord[fieldName])) {
                if (rawRecord[fieldName].every((val) => Number.isInteger(val))) {
                    resp[fieldName] = rawRecord[fieldName];
                } else resp[fieldName] = rawRecord[fieldName][0];
            }
        });
        return resp;
    }
    fcEventToRecord(event) {
        const resp = this.superFcEventToRecord(event);
        const resourceData = this.fcResourceToRecord(event.resource);
        const newResp = Object.assign(resp, resourceData);
        return newResp;
    }
    superFcEventToRecord(event) {
        // This is copied from convertRecordToEvent(item) of CalendarCommonRenderer;
        // but add "year" to add 1 day to end, same as week and month
        const {id, allDay, date, start, end} = event;
        const res = {
            start: luxon.DateTime.fromJSDate(date || start),
            isAllDay: allDay,
        };
        if (end) {
            res.end = luxon.DateTime.fromJSDate(end);
            if (["week", "month", "year"].includes(this.props.model.scale) && allDay) {
                res.end = res.end.minus({days: 1});
            }
        }
        if (id) {
            const existingRecord = this.props.model.records[id];
            // If (["week", "month", "year"].includes(this.props.model.scale)) {
            //     res.start = res.start?.set({
            //         hour: existingRecord.start.hour,
            //         minute: existingRecord.start.minute,
            //     });
            //     if (existingRecord.end) {
            //         res.end = res.end?.set({
            //             hour: existingRecord.end.hour,
            //             minute: existingRecord.end.minute,
            //         });
            //     }
            // }
            res.id = existingRecord.id;
        }
        return res;
    }
    superConvertRecordToEvent(record) {
        // This is copied from convertRecordToEvent(item) of CalendarCommonRenderer;
        // but add "year" to add 1 day to end, same as week and month
        // const allDay =
        //     record.isAllDay || record.end.diff(record.start, "hours").hours >= 24;
        const allDay = record.isAllDay || record.endType === "date";
        let new_end = record.end.toISO();
        if (["week", "month", "year"].includes(this.props.model.scale)) {
            if (
                record.isAllDay ||
                (allDay &&
                    record.end.toMillis() !== record.end.startOf("day").toMillis())
            ) {
                new_end = record.end.plus({days: 1}).toISO();
            }
        }
        return {
            id: record.id,
            title: record.title,
            start: record.start.toISO(),
            end: new_end,
            allDay: allDay,
        };
    }
    convertRecordToEvent(item) {
        const resp = this.superConvertRecordToEvent(item);
        if (this.props.model.meta.hideEventTitle) {
            resp.title = "";
        } else if (this.props.model.meta.eventTitleField && item.rawRecord) {
            resp.title = item.rawRecord[this.props.model.meta.eventTitleField] || "";
        }
        const columnFields = this.props.model.meta.columnFields;
        const fieldNames = Object.keys(columnFields);
        const {uniqKeys, m2oMapping} = this._getUniqueResourceIds(fieldNames, item);
        resp.resourceIds = uniqKeys;
        for (const uniqKey of uniqKeys) {
            if (this.fc.api && !this.fc.api.getResourceById(uniqKey)) {
                // Create the resource
                this._createResourceByEvent(item, uniqKey, m2oMapping);
            }
        }
        return resp;
    }
    _createResourceByEvent(item, uniqKey = false, m2oMapping = false) {
        const resourceObj = this.mapRecordsToResources(
            [item],
            [uniqKey],
            m2oMapping
        )[0];
        this.fc.api.addResource(resourceObj, true);
    }
    _getRecordByForceValue(record, forceValues, fieldName) {
        const record2 = Object.assign({}, record);
        if (
            forceValues[fieldName] &&
            record2.rawRecord &&
            forceValues[fieldName] !== record2.rawRecord[fieldName]
        ) {
            record2.rawRecord = Object.assign({}, record.rawRecord);
            record2.rawRecord[fieldName] = forceValues[fieldName];
        }
        return record2;
    }
    onResourceLabelDidMount({el, resource}) {
        /**
         * Replace the name of resources by the formatted one
         */
        // el => get its parent => find its childs by extendedProps
        const $parentEle = $(el.parentElement);
        // {colname: val}
        const extendedProps = resource.extendedProps;
        const fieldNames = extendedProps.postRenderFields;
        const self = this;

        const recordId = extendedProps.recordId;
        // eslint-disable-next-line array-callback-return
        fieldNames.map((fieldName) => {
            const title = extendedProps[fieldName];
            const resourceEle = $parentEle
                .find(`:contains(${title})`)
                .filter(function () {
                    return this.innerHTML === title;
                })
                .first();
            if (resourceEle.length > 0) {
                // Do replace the resource title
                const record = self._getRecordByForceValue(
                    self.props.model.records[recordId],
                    extendedProps.forceValues,
                    fieldName
                );
                const props = {
                    record,
                    model: self.props.model.meta,
                    fieldName,
                };
                const app = new App(DomGanttModelResource, {
                    env: self.env,
                    dev: self.env.debug,
                    templates,
                    props,
                    translatableAttributes: ["data-tooltip"],
                    translateFn: _t,
                });
                resourceEle[0].innerHTML = "";
                app.mount(resourceEle[0]);
            }
        });
    }
    onEventRender(info) {
        const {el, event} = info;
        el.dataset.eventId = event.id;
        el.classList.add("o_event", "py-0");
        const record = this.props.model.records[event.id];

        if (record) {
            // This is needed in order to give the possibility to change the event template.
            // const injectedContentStr = renderToString(this.constructor.eventTemplate, {
            //     ...record,
            //     startTime: this.getStartTime(record),
            // });
            // const domParser = new DOMParser();
            // const { children } = domParser.parseFromString(injectedContentStr, "text/html").body;
            // el.querySelector(".fc-content").replaceWith(...children);

            const color = getColor(record.colorIndex);
            if (typeof color === "string") {
                el.style.backgroundColor = color;
            } else if (typeof color === "number") {
                el.classList.add(`o_calendar_color_${color}`);
            } else {
                el.classList.add("o_calendar_color_0");
            }

            if (record.isHatched) {
                el.classList.add("o_event_hatched");
            }
            if (record.isStriked) {
                el.classList.add("o_event_striked");
            }
        }

        if (!el.querySelector(".fc-bg")) {
            const bg = document.createElement("div");
            bg.classList.add("fc-bg");
            el.appendChild(bg);
        }
        const meta = this.props.model.meta;
        if (
            !meta.isTimeHidden &&
            !meta.isTimeEndHidden &&
            meta.eventTimeDisplayFar &&
            el.fcSeg.isEnd
        ) {
            const evntTimeEl = $(el.firstElementChild).find("div.fc-event-time");
            if (evntTimeEl.length === 1) {
                const textTimeArr = evntTimeEl[0].textContent.split("-");
                evntTimeEl[0].textContent = textTimeArr[0].trim();
                const evntTimeElEnd = evntTimeEl.clone();
                evntTimeElEnd[0].textContent =
                    textTimeArr[textTimeArr.length - 1].trim();
                evntTimeEl[0].parentElement.appendChild(evntTimeElEnd[0]);
            }
        }
    }
}
DomGanttCommonRenderer.components = {
    ...CalendarCommonRenderer.components,
    Popover: DomGanttCommonPopover,
};
