/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component } from 'owl';

export class TarifsHome extends Component {
    setup() {
        console.log("TarifsHome Component Initialized");
    }
}

TarifsHome.template = "TarifHomeTemplate";
registry.category("actions").add("tarif_home", TarifsHome);
