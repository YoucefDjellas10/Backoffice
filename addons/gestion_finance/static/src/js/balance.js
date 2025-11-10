/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, onWillStart, useState } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';

export class Balance extends Component {
    static template = 'BalanceTemplate';

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            managersGeneraux: [],
            ceos: [],
            zones: {},
            loading: true
        });

        onWillStart(async () => {
            await this.loadBalanceData();
        });
    }

    async loadBalanceData() {
        try {
            const data = await this.orm.call('balance', 'get_balance_data', []);
            this.state.managersGeneraux = data.managers_generaux || [];
            this.state.ceos = data.ceos || [];
            this.state.zones = data.zones || {};
            this.state.loading = false;
            console.log("✅ Données chargées:", data);
        } catch (error) {
            console.error("❌ Erreur chargement données:", error);
            this.state.loading = false;
        }
    }

    // Méthode pour formater le nombre avec séparateurs
    formatBalance(balance) {
        return new Intl.NumberFormat('fr-FR').format(balance || 0);
    }
}

// Définir les props avec les clés passées par Odoo
Balance.props = {
    action: { type: Object, optional: true },
    actionId: { type: Number, optional: true },
    className: { type: String, optional: true },
};

registry.category('actions').add('balance', Balance);
