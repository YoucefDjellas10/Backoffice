/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

class Caisse extends Component {
    static template = "gestion_finance.CaisseTemplate";
}

registry.category("actions").add("caisse_action", Caisse);
