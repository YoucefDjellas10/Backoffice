/** @odoo-module */

import {registry} from '@web/core/registry'
const {Component, onMounted, useState, useRef} = owl
import {jsonrpc} from "@web/core/network/rpc_service"
import {useService} from "@web/core/utils/hooks";

export class RecetteDashboard extends Component {

    setup() {
        this.state = useState({
            totalEncaisse: 0 ,
            zones: [],
            models: [],
            vehicules: [],
            });

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchModele();
            await this.fetchVehicule();
        });
    }

    async fetchVehicule() {
        const models = await jsonrpc("/web/dataset/call_kw/reservation/get_all_modele", {
            model: 'reservation',
            method: 'get_all_modele',
            args: [{}],
            kwargs: {}
        });
        this.state.models = models.map(modele => ({ id: modele.id, name: modele.name }));
    }

    async fetchModele() {
        const vehicules = await jsonrpc("/web/dataset/call_kw/reservation/get_all_vehicule", {
            model: 'reservation',
            method: 'get_all_vehicule',
            args: [{}],
            kwargs: {}
        });
        this.state.vehicules = vehicules.map(vehicule => ({ id: vehicule.id, name: vehicule.name }));
    }

    async fetchZones() {
        const zones = await jsonrpc("/web/dataset/call_kw/reservation/get_all_zones", {
            model: 'reservation',
            method: 'get_all_zones',
            args: [{}],
            kwargs: {}
        });
        this.state.zones = zones.map(zone => ({ id: zone.id, name: zone.name }));
    }

    async getTotalEncaisse(date_from = null, date_to = null, zone = null, modele = null, vehicule = null) {
        const result = await jsonrpc('/web/dataset/call_kw', {
            model: 'revenue.record',
            method: 'get_total_encaisse',
            args: [date_from, date_to, zone, modele, vehicule],
            kwargs: {},
        });
        return result;
    }

    async applyFilter() {
        const inputDate = document.getElementById("date_debut").value;
        const inputEndDate = document.getElementById("date_fin").value;
        const inputZone = document.getElementById("zone").value;
        const inputModele = document.getElementById("modele").value;
        const inputVehicule = document.getElementById("vehicule").value;

        const total = await this.getTotalEncaisse(inputDate, inputEndDate, inputZone, inputModele, inputVehicule);
        console.log("total",total);
        this.state.totalEncaisse = total;
    }
}
RecetteDashboard.template = "RecetteDashBoardMain"
registry.category("actions").add("recette_dashboard_main", RecetteDashboard)