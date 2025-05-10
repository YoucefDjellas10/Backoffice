/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import {DateSearch} from "./date_search";
import {patch} from "@web/core/utils/patch";
import { MrpProductionListController } from "./mrp_production_list";
import {useState} from "@odoo/owl";

patch(ListController.prototype,{
    setup(){
        super.setup()
        this.state = useState({
            mrp_date_search: false,
        });
    }
})

patch(MrpProductionListController.prototype,{
    setup(){
        super.setup()
        this.state = useState({
            mrp_date_search: true,
        });
    }
})

patch(MrpProductionListController.components,Object.assign({}, ListController.components, {DateSearch}))