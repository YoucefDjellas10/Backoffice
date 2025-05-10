/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Model } from "@web/model/model";
import { KeepLast } from "@web/core/utils/concurrency";
import { deserializeDate, deserializeDateTime, serializeDateTime } from "@web/core/l10n/dates";
import { Domain } from "@web/core/domain";
import { groupBy } from "@web/core/utils/arrays";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { DateTime } = luxon;

export class GanttModel extends Model {
    setup(params) {
        this.metaData = {
            ...params,
        };
        this.collapseFirstLevel = params.collapseFirstLevel;

        this.rpc = useService("rpc");

        this.data = {
            groupByKey: false,
        };
        this.gantt = {
            scale : params.defaultScale || 'month',
            focus_date : false,
            start_date : false,
            to_date : false,
            end_date : false,
            date_display : false,
        };

        this.searchParams = null;
        this.keepLast = new KeepLast();
        this._nextMetaData = null;
    }

    async load(searchParams) {
        this.searchParams = searchParams
        const metaData = this._buildMetaData();
        
        const params = {
            groupedBy: this._getGroupedBy(metaData, searchParams),
            pagerOffset: 0,
        };
        if (!metaData.scale) {
            Object.assign(
                params,
                this._getInitialRangeParams(this._buildMetaData(params), searchParams)
            );
        }
        this.setFocusDate(metaData.initialDate, metaData.defaultScale);
        this.data = await this._fetchData(this._buildMetaData(params));
    }
    _getInitialRangeParams(metaData, searchParams) {
        const { context } = searchParams;
        const scale = context.default_scale || metaData.defaultScale;

        let focusDate = "initialDate" in context ? deserializeDateTime(context.initialDate) : DateTime.local();
        
        if (metaData.offset) {
            focusDate = focusDate.plus({ [scale]: metaData.offset });
        }
        return { focusDate, scale };
    }
    _getGroupedBy(metaData, searchParams) {
        let groupedBy = [...searchParams.groupBy];
        groupedBy = this._filterDateIngroupedBy(metaData, groupedBy);
        if (!groupedBy.length) {
            groupedBy = metaData.defaultGroupBy;
        }
        return groupedBy;
    }
    _filterDateIngroupedBy(metaData, groupedBy) {
        return groupedBy.filter((gb) => {
            const [fieldName] = gb.split(":");
            const { type } = metaData.fields[fieldName];
            return !["date", "datetime"].includes(type);
        });
    }
    _buildMetaData(params = {}) {
        this._nextMetaData = { ...(this._nextMetaData || this.metaData) };
        if (params.groupedBy) {
            this._nextMetaData.groupedBy = params.groupedBy;
        }
        return this._nextMetaData;
    }
    async fetchData(params) {
        var data = await this._fetchData(this._buildMetaData(params));
        return data;
    }
    async _fetchData(metaData, additionalContext) {
        
        const { groupedBy, pagerLimit, pagerOffset, resModel } = metaData;    
            
        const context = {
            ...this.searchParams.context,
            group_by: groupedBy,
            ...additionalContext,
        };

        const domain = this._getDomain(metaData);
        const fields = this._getFields(metaData);
        
        const specification = {};
        for (const fieldName of fields) {
            specification[fieldName] = {};
            if (metaData.fields[fieldName] && metaData.fields[fieldName].type === "many2one") {
                specification[fieldName].fields = { display_name: {} };
            }            
        }
        const orderBy = [];
        if (metaData.defaultOrder) {
            orderBy.push(metaData.defaultOrder);
            if (metaData.defaultOrder) {
                orderBy.push("asc");
            }
        }

        const data = {};
        var groups =  [];
        if (groupedBy.length> 0){
            groups = await this.rpc("/web/dataset/call_kw/${metaData.resModel}/read_group", {
                args: [],
                kwargs: {
                    domain: domain,
                    fields: fields,
                    groupby: groupedBy,
                    context: context,
                    offset: 0,
                    lazy: groupedBy.length === 1,
                }, 
                method: "read_group",
                model: metaData.resModel,
            });
            groups.forEach((g) => (g.fromServer = true));
        }
        data.groups = groups;

        var records = await this.rpc("/web/dataset/call_kw/${metaData.resModel}/search_read", {
            args: [],
            kwargs: {
                context: context,
                domain: domain,
                fields: fields,
            },
            method: "search_read",
            model: metaData.resModel,
        });
        data.count = records.length;
        var parseRecords = this._parseServerData(metaData, records);
        var oldRows = this.allRows;
        this.allRows = {};
        data.rows = this._generateGanttRows(metaData,{
            groupedBy: groupedBy,
            groups: groups,
            oldRows: oldRows,
            parentPath: [],
            records: parseRecords,
        });

        data.groupByKey = groupedBy,
        this.metaData = metaData;
        this._nextMetaData = null;
        return data;
    }
    _parseServerData(metaData,records){
        var self = this;
        const { fields } = metaData;
        const parsedRecords = [];
        for (const record of records) {
            const parsedRecord = self._parseServerValue(fields, record);
            parsedRecords.push(parsedRecord);
        }
        return parsedRecords;
    }
    _parseServerValue(fields, values) {
        const parsedValues = {};
        if (!values) {
            return parsedValues;
        }
        for (const fieldName in values) {
            
            const field = fields[fieldName];
            const value = values[fieldName];
            
            switch (field.type) {
                case "date": {
                    parsedValues[fieldName] = value ? deserializeDate(value) : false;
                    break;
                }
                case "datetime": {
                    parsedValues[fieldName] = value ? deserializeDateTime(value) : false;
                    break;
                }
                case "html": {
                    return markup(value);
                }
                case "selection": {
                    if (value === false) {
                        // process selection: convert false to 0, if 0 is a valid key
                        const hasKey0 = field.selection.some((option) => option[0] === 0);
                        parsedValues[fieldName] = hasKey0 ? 0 : value;
                    } else {
                        parsedValues[fieldName] = value;
                    }
                    break;
                }
                default: {
                    parsedValues[fieldName] = value;
                }
            }
        }
        return parsedValues;
    }
    _generateGanttRows(metaData, params) {
        const { groupedBy, groups, oldRows, parentPath, records } = params;
        const groupLevel = metaData.groupedBy.length - groupedBy.length;
        
        if (!groupedBy.length || !groups.length) {
            const row = {
                groupLevel,
                id: JSON.stringify([...parentPath, {}]),
                isGroup: false,
                name: "",
                records,
            };
            this.allRows[row.id] = row;
            return [row];
        }

        const rows = [];
        const groupedByField = groupedBy[0];
        const currentLevelGroups = groupBy(groups, group => {
            if (group[groupedByField] === undefined) {
                group[groupedByField] = false;
            }
            return group[groupedByField];
        });
        const isM2MGrouped = metaData.fields[groupedByField].type === "many2many";
        let groupedRecords;
        if (isM2MGrouped) {
            groupedRecords = {};
            for (const [key, currentGroup] of Object.entries(currentLevelGroups)) {
                groupedRecords[key] = [];
                const value = currentGroup[0][groupedByField];
                for (const r of records || []) {
                    if (
                        !value && r[groupedByField].length === 0 ||
                        value && r[groupedByField].includes(value[0])
                    ) {
                        groupedRecords[key].push(r)
                    }
                }
            }
        } else {
            groupedRecords = groupBy(records || [], groupedByField);
        }

        for (const key in currentLevelGroups) {
            const subGroups = currentLevelGroups[key];
            const groupRecords = groupedRecords[key] || [];
            let value;
            if (groupRecords && groupRecords.length && !isM2MGrouped) {
                value = groupRecords[0][groupedByField];
            } else {
                value = subGroups[0][groupedByField];
            }
            const part = {};
            part[groupedByField] = value;
            const path = [...parentPath, part];
            const id = JSON.stringify(path);
            const resId = Array.isArray(value) ? value[0] : value;
            const minNbGroups = this.collapseFirstLevel ? 0 : 1;
            const isGroup = groupedBy.length > minNbGroups;
            const fromServer = subGroups.some((g) => g.fromServer);
            const row = {
                name: this._getRowName(metaData,groupedByField, value),
                groupedBy,
                groupedByField,
                groupLevel,
                id,
                resId,
                isGroup,
                fromServer,
                isOpen: !Object.values(oldRows).find(item => item.id === JSON.stringify(parentPath) && item.isOpen === false),
                records: groupRecords,
            };

            if (isGroup) {
                row.rows = this._generateGanttRows(metaData,{
                    ...params,
                    groupedBy: groupedBy.slice(1),
                    groups: subGroups,
                    oldRows,
                    parentPath: path,
                    records: groupRecords,
                });
                row.childrenRowIds = [];
                row.rows.forEach(function (subRow) {
                    row.childrenRowIds.push(subRow.id);
                    row.childrenRowIds = row.childrenRowIds.concat(subRow.childrenRowIds || []);
                });
            }

            rows.push(row);
            this.allRows[row.id] = row;
        }
        return rows;   
    }
    _getRowName(metaData, groupedByField, value) {
        const field = metaData.fields[groupedByField];
        return this._getFieldFormattedValue(value, field);
    }
    _getFieldFormattedValue(value, field) {
        if (field.type === "boolean") {
            return value ? "True" : "False";
        } 
        else if (!value) {
            return _t("Undefined %s", field.string);
        } 
        else if (field.type === "many2many") {
            return value[1];
        }
        const formatter = registry.category("formatters").get(field.type);
        return formatter(value, field);
    }
    _getDomain(metaData) {
        const domain = Domain.and([
            this.searchParams.domain,
            [
                "|",
                [metaData.dateStopField, '<=', serializeDateTime(this.gantt.to_date)],
                "&",
                [metaData.dateStartField, ">=", serializeDateTime(this.gantt.start_date)],
                [metaData.dateStopField, '=', false]
            ],
        ])
        return domain.toList()
    }
    _getFields(metaData) {
        const fields = new Set([
            "display_name",
            metaData.dateStartField,
            metaData.dateStopField,
            ...metaData.groupedBy,
        ]);

        if (metaData.progressField) {
            fields.add(metaData.progressField);
        }

        if (metaData.colorField) {
            fields.add(metaData.colorField);
        }

        if (metaData.taskType) {
            fields.add(metaData.taskType);
        }
        
        if (metaData.deadLine) {
            fields.add(metaData.deadLine);
        }

        if(metaData.taskPriority){
            fields.add(metaData.taskPriority);
        }

        return [...fields];
    }

    _setScale(scale) {
        this.setFocusDate(this.gantt.focus_date, scale);
    }

    _setFocusDate(focusDate) {
        this.setFocusDate(focusDate, this.gantt.scale);
    }

    setFocusDate(focusDate, scale) {
        this.gantt.focus_date = focusDate;
        this.gantt.scale = scale;
        switch (scale) {
            case "day":
                this.gantt.start_date = focusDate.minus({ 'days' : 1 }).startOf('day');
                this.gantt.to_date = focusDate.plus({ 'days' : 3 }).endOf('day');
                this.gantt.end_date = this.gantt.to_date.plus({ 'days' : 1 });
                break;
            case "week":
                this.gantt.start_date = focusDate.minus({ 'weeks' : 1 }).startOf('week');
                this.gantt.to_date = focusDate.endOf('week').plus({ 'weeks' : 3 });
                this.gantt.end_date = this.gantt.to_date.plus({ 'weeks' : 1 });
                break;
            case "month":
                this.gantt.start_date = focusDate.minus({ 'months' : 1 }).startOf('month');
                this.gantt.to_date = focusDate.endOf('month').plus({ 'months' : 3 });
                this.gantt.end_date = this.gantt.to_date.plus({ 'months' : 1 });
                break;
            case "year":
                this.gantt.start_date = focusDate.minus({ 'years' : 1 }).startOf('year');
                this.gantt.to_date = focusDate.endOf('year').plus({ 'years' : 3 });
                this.gantt.end_date = this.gantt.to_date.plus({ 'years' : 1 });
                break;
        }
        this.gantt.date_display = this._dateReformat(focusDate, scale);
    }

    _dateReformat(date, scale){
        switch(scale) {                                    
            case "year":
                return date.toFormat("yyyy");
            case "month":
                return date.toFormat("MMM yyyy");
            case "week":
                var date_start = date.startOf("week").toFormat("dd/MM/yyyy");
                var date_end = date.endOf("week").toFormat("dd/MM/yyyy");
                return date_start + " - " + date_end;
            case "day":
                return date.toFormat("dd/MM/yyyy");
        }
    }
}
