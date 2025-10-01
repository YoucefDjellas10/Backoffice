/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class WhitePage extends Component {
    setup() {
        // Initial setup can be done here if needed
    }

    static template = "aaaa_homepage.WhitePageTemplate";
}

registry.category("actions").add("white_page_action", WhitePage);
