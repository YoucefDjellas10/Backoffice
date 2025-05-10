/** @odoo-module */

import {registry} from '@web/core/registry'
const {Component, onMounted, useState, useRef} = owl
import {jsonrpc} from "@web/core/network/rpc_service"
import {useService} from "@web/core/utils/hooks";

export class depenseDashboard extends Component {



}
depenseDashboard.template = "DepenseDashBoardMain"
registry.category("actions").add("depense_dashboard_main", depenseDashboard)