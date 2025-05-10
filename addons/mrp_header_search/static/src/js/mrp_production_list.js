/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

import { Component, useState } from "@odoo/owl";

export class MrpProductionListController extends ListController {
    setup() {
        super.setup();
    }
};

MrpProductionListController.components = {
    ...ListController.components,
};

export const MrpProductionListView = {
    ...listView,
    Controller: MrpProductionListController,
};

registry.category("views").add("mrp_header_search", MrpProductionListView);
