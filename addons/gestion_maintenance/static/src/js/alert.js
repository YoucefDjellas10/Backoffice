/* @odoo-module */

import { registry } from '@web/core/registry';
const { Component, onMounted, useState } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";

export class FilterAlert extends Component {
    setup() {
        this.state = useState({
            zones: [],
            selectedZone: null,
            models: [],
            selectedModel: null,
            vehicules: [],
            selectedVehicule: null,
            maintenanceTypes: [],
            selectedType: null,
            maintenanceCount: 0,
            currentPage: 1,
            itemsPerPage: 30,
            totalPages: 1
        });

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchModels();
            await this.fetchVehicules();
            await this.fetchMaintenanceTypes();
            await this.searchAlerts();
        });
    }

    async fetchZones() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/planning.dashboard/get_all_zones", {
                model: 'planning.dashboard',
                method: 'get_all_zones',
                args: [{}],
                kwargs: {}
            });
            this.state.zones = response.map(zone => ({ id: zone.id, name: zone.name }));
        } catch (error) {
            console.error("Erreur lors de la récupération des zones :", error);
        }
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
        console.log("Vehicules data:", response);
        this.state.vehicules = response.map(v => ({
            id: v.id,
            name: v.name || v.numero  // Utilise le champ le plus approprié
        }));
    } catch (error) {
        console.error("Fetch vehicules error:", error);
    }
}


    async fetchMaintenanceTypes() {
    try {
        const response = await jsonrpc("/web/dataset/call_kw/alert.record/get_all_maintenance_types", {
            model: 'alert.record',  // Assurez-vous que c'est le bon modèle
            method: 'get_all_maintenance_types',
            args: [],
            kwargs: {}
        });
        console.log("Maintenance Types:", response);
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


    changeItemsPerPage(event) {
    this.state.itemsPerPage = parseInt(event.target.value);
    this.state.currentPage = 1;
    this.searchAlerts();
}

    resetFilters() {
        document.getElementById('modeles').value = '';
        document.getElementById('zones').value = '';
        document.getElementById('vehicules').value = '';
        document.getElementById('types').value = '';

        this.state.selectedModel = null;
        this.state.selectedZone = null;
        this.state.selectedVehicule = null;
        this.state.selectedType = null;
        this.state.currentPage = 1;
        this.searchAlerts();
    }
    updatePaginationControls() {
    let paginationDiv = document.querySelector('.pagination-controls');
    if (!paginationDiv) {
        paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination-controls';
        document.querySelector('.ta-BLE').parentNode.appendChild(paginationDiv);
    }

    paginationDiv.innerHTML = `
        <button class="butn123 pagination-btn" onclick="component.prevPage()" ${this.state.currentPage === 1 ? 'disabled' : ''}>
            <ion-icon name="chevron-back-outline"></ion-icon>
        </button>
        <span class="page-info">${this.state.currentPage}/${this.state.totalPages}</span>
        <button class="butn123 pagination-btn" onclick="component.nextPage()" ${this.state.currentPage === this.state.totalPages ? 'disabled' : ''}>
            <ion-icon name="chevron-forward-outline"></ion-icon>
        </button>

    `;

    window.component = this;
}

    async searchAlerts() {
    try {
        const filters = {
            model_id: this.state.selectedModel,
            vehicule_id: this.state.selectedVehicule,
            type: this.state.selectedType,
            zone_id: this.state.selectedZone
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
        this.updatePaginationControls();
    } catch (error) {
        console.error("Erreur lors de la recherche des alertes :", error);
    }
}


    formatDate(dateString) {
        if (!dateString || dateString === 'N/A') return '';

        const date = new Date(dateString);

        if (isNaN(date.getTime())) return dateString;

        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();

        return `${day}/${month}/${year}`;
    }


    updateMaintenanceTable(records) {
    const tbody = document.querySelector('.ta-BLE tbody');
    tbody.innerHTML = '';

    if (records && records.length > 0) {
        records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
               <td>${record.reference_id === 'N/A' ? '' : record.reference_id || ''}</td>
<td>${record.maintenance_type === 'N/A' ? '' : record.maintenance_type || ''}</td>
<td>${record.numero === 'N/A' ? '' : record.numero || ''}</td>
<td>${this.formatDate(record.echeance)}</td>
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
}

FilterAlert.template = "gestion_maintenance.FilterAlert";
registry.category("actions").add("alert_js_global", FilterAlert);
