/** @odoo-module */

import {registry} from '@web/core/registry'
const {Component, onMounted, useState, useRef} = owl
import {jsonrpc} from "@web/core/network/rpc_service"
import {useService} from "@web/core/utils/hooks";

export class previsionnaireDashboard extends Component {



}
previsionnaireDashboard.template = "PrevisionDashBoardMain"
registry.category("actions").add("previsionnaire_dashboard_main", previsionnaireDashboard)