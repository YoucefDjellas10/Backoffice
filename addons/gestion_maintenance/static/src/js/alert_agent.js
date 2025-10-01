/* @odoo-module */

import { registry } from '@web/core/registry';
import { Component, onMounted, useState } from '@odoo/owl';
import { jsonrpc } from "@web/core/network/rpc_service";

export class AlertAgent extends Component {
    setup() {
        this.isAgent = false;
        this.userId = null;

        this.state = useState({
            selectedZone: null,
            models: [],
            selectedModel: null,
            vehicules: [],
            selectedVehicule: null,
            maintenanceTypes: [],
            selectedType: null,
            maintenanceCount: 0,
            currentDate: this.getFormattedDate(new Date()),
            accessDenied: false,
            userInfo: null,
            currentPage: 1,
            itemsPerPage: 30,
            totalPages: 1
        });

        onMounted(async () => {
            try {
                const user = await jsonrpc("/web/session/get_session_info", {});
                this.userId = user.uid;
                this.state.userInfo = user;

                const isAgent = await jsonrpc("/web/dataset/call_kw/res.users/has_group", {
    model: "res.users",
    method: "has_group",
    args: ["access_rights_groups.group_agent"],
    kwargs: {},
});

console.log("==> isAgent:", isAgent); // 🔍 Vérification
this.isAgent = isAgent;

                this.isAgent = isAgent;

                if (!this.isAgent) {
                    this.state.accessDenied = true;
                    return;
                }

                await this.fetchZones();
                await this.fetchModels();
                await this.fetchVehicules();
                await this.fetchMaintenanceTypes();
                await this.searchAlerts();
            } catch (error) {
                console.error("Erreur:", error);
                this.state.accessDenied = true;
            }
        });
    }

    getFormattedDate(date) {
        const options = {
            weekday: 'long',
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        };

        let dateStr = date.toLocaleDateString('fr-FR', options);
        dateStr = dateStr.split(' ');
        dateStr[0] = dateStr[0].charAt(0).toUpperCase() + dateStr[0].slice(1);
        dateStr[2] = dateStr[2].charAt(0).toUpperCase() + dateStr[2].slice(1);
        return dateStr.join(' ');
    }


    async fetchModels() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/reservation/get_all_modele", {
                model: 'reservation',
                method: 'get_all_modele',
                args: [{}],
                kwargs: {}
            });
            this.state.models = response.map(model => ({ id: model.id, name: model.name }));
        } catch (error) {
            console.error("Erreur lors de la récupération des modèles :", error);
        }
    }

    async fetchVehicules() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/alert.record/get_all_vehicule", {
                model: 'alert.record',
                method: 'get_all_vehicule',
                args: [],
                kwargs: {}
            });
            this.state.vehicules = response.map(v => ({
                id: v.id,
                name: v.name || v.numero
            }));
        } catch (error) {
            console.error("Fetch vehicules error:", error);
        }
    }

    async fetchMaintenanceTypes() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/alert.record/get_all_maintenance_types", {
                model: 'alert.record',
                method: 'get_all_maintenance_types',
                args: [],
                kwargs: {}
            });
            this.state.maintenanceTypes = response;
        } catch (error) {
            console.error("Error fetching maintenance types:", error);
        }
    }

    updateSelectedZone(event) {
        this.state.selectedZone = event.target.value;
    }

    updateSelectedModel(event) {
        this.state.selectedModel = event.target.value;
    }

    updateSelectedVehicule(event) {
        this.state.selectedVehicule = event.target.value;
    }

    updateSelectedType(event) {
        this.state.selectedType = event.target.value;
    }

    resetFilters() {
        document.getElementById('modeles').value = '';
        document.getElementById('vehicules').value = '';
        document.getElementById('types').value = '';

        this.state.selectedModel = null;
        this.state.selectedVehicule = null;
        this.state.selectedType = null;
        this.searchAlerts();
    }

    async searchAlerts() {
    try {
       console.log("==> searchAlerts called");
        const filters = {
            model_id: this.state.selectedModel,
            vehicule_id: this.state.selectedVehicule,
            type: this.state.selectedType
        };

        const response = await jsonrpc("/web/dataset/call_kw/alert.record/search_alerts", {
            model: 'alert.record',
            method: 'search_alerts',
            args: [filters, (this.state.currentPage - 1) * this.state.itemsPerPage, this.state.itemsPerPage],
            kwargs: {}
        });

        this.updateMaintenanceTable(response.records);
        this.state.maintenanceCount = response.total_count;
        this.state.totalPages = Math.ceil(response.total_count / this.state.itemsPerPage);
    } catch (error) {
        console.error("Erreur lors de la recherche des alertes :", error);
    }
}

// Add pagination methods (same as in regular version)
nextPage() {
    if (this.state.currentPage < this.state.totalPages) {
        this.state.currentPage++;
        this.searchAlerts();
    }
}

prevPage() {
    if (this.state.currentPage > 1) {
        this.state.currentPage--;
        this.searchAlerts();
    }
}

    updateMaintenanceTable(records) {
        const tbody = document.querySelector('.ta-BLE tbody');
        tbody.innerHTML = '';

        if (records && records.length > 0) {
            records.forEach(record => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${record.reference_id || 'N/A'}</td>
                    <td>${record.maintenance_type || 'N/A'}</td>
                    <td>${record.numero || 'N/A'}</td>
                    <td>${record.echeance || 'N/A'}</td>
                    <td>${record.dernier_klm || '0'} KM</td>
                    <td>
                        <button class="butn123 config-btn" data-record-id="${record.id}">
                            <ion-icon name="cog-outline"></ion-icon>
                        </button>
                    </td>
                `;

                row.querySelector('.config-btn').addEventListener('click', (e) => {
                    const id = e.currentTarget.getAttribute('data-record-id');
                    this.openRecordForm(id);
                });

                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = `
                <tr><td colspan="6" style="text-align:center">Aucun enregistrement trouvé</td></tr>
            `;
        }
    }

    openRecordForm(recordId) {
        const url = `${window.location.origin}/web?debug=1#id=${recordId}&menu_id=1768&cids=1&action=351&model=alert.record&view_type=form`;
        window.open(url, '_blank');
    }
}

AlertAgent.template = "alert_agent.AlertAgent";
registry.category("actions").add("alert_js_agent", AlertAgent);
