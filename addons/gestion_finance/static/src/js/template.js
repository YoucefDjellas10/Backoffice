/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

class FinanceStatic extends Component {}
FinanceStatic.template = "FinanceStaticTemplate";

registry.category("actions").add("finance_static", FinanceStatic);
