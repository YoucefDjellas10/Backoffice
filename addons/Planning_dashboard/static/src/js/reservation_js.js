/* @odoo-module */

import { registry } from '@web/core/registry';
const { Component, onMounted, useState } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";

export class TreeReservationJs extends Component {
    setup() {
        this.state = useState({
            zones: [],
            selectedZone: null,
            models: [],
            selectedModel: null,
            defaultStartDate: this.getFormattedDate(new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)),
            defaultEndDate: this.getFormattedDate(new Date()),
            confirmationStates: [
                { id: 'en_attend', name: 'En attente' },
                { id: 'rejete', name: 'Rejeté' },
                { id: 'annule', name: 'Annulé' },
                { id: 'confirmee', name: 'Confirmé' },
            ],
            selectedConfirmationState: null,
            reservationCount: 0,
            // Ajouts pour la pagination
            currentPage: 1,
            itemsPerPage: 30,
            totalPages: 1,
        });

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchModels();

            if (this.state.reservationCount === 0) {
                document.getElementById('date-du').value = this.state.defaultStartDate;
                document.getElementById('date-au').value = this.state.defaultEndDate;
            }

            await this.searchReservations(false);
        });
    }

    // Méthodes existantes inchangées
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

    updateSelectedZone(event) {
        const selectedZone = event.target.value;
        this.state.selectedZone = selectedZone;
    }

    updateSelectedModel(event) {
        const selectedModel = event.target.value;
        this.state.selectedModel = selectedModel;
    }

    getFormattedDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    resetFilters() {
        document.getElementById('reference').value = '';
        document.getElementById('prenom').value = '';
        document.getElementById('nom').value = '';
        document.getElementById('email').value = '';
        document.getElementById('date-reservation').value = '';
        document.getElementById('date-du').value = '';
        document.getElementById('date-au').value = '';
        document.getElementById('modeles').value = '';
        document.getElementById('pays').value = '';
        document.getElementById('etat').value = '';

        this.state.selectedModel = null;
        this.state.selectedZone = null;
        this.state.selectedConfirmationState = null;
        this.state.reservationCount = 0;
        this.state.currentPage = 1; // Reset à la première page
        this.searchReservations(false);
    }

    updateSelectedConfirmationState(event) {
        const selectedConfirmationState = event.target.value;
        this.state.selectedConfirmationState = selectedConfirmationState;
    }

    async deleteReservation(reservationId) {
        const confirmed = confirm("Voulez-vous vraiment supprimer cette réservation ?");
        if (confirmed) {
            try {
                await jsonrpc("/web/dataset/call_kw/reservation/unlink", {
                    model: 'reservation',
                    method: 'unlink',
                    args: [[parseInt(reservationId)]],
                    kwargs: {}
                });
                await this.searchReservations(true);
                alert("Réservation supprimée avec succès");
            } catch (error) {
                console.error("Erreur lors de la suppression :", error);
                alert("Une erreur est survenue lors de la suppression");
            }
        }
    }

    // Méthodes pour la pagination
    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
            this.searchReservations(true);
        }
    }

    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.searchReservations(true);
        }
    }

    changeItemsPerPage(event) {
        this.state.itemsPerPage = parseInt(event.target.value);
        this.state.currentPage = 1;
        this.searchReservations(true);
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
            <
        </button>
        <span class="page-info">${this.state.currentPage}/${this.state.totalPages}</span>
        <button class="butn123 pagination-btn" onclick="component.nextPage()" ${this.state.currentPage === this.state.totalPages ? 'disabled' : ''}>
            >
        </button>
    `;

    window.component = this;
}

    async searchReservations(useFilters = true) {
        try {
            let filters = null;
            if (useFilters) {
                filters = {
                    reference: document.getElementById('reference').value,
                    prenom: document.getElementById('prenom').value,
                    nom: document.getElementById('nom').value,
                    modeles: document.getElementById('modeles').value,
                    pays: document.getElementById('pays').value,
                    email: document.getElementById('email').value,
                    etat: document.getElementById('etat').value,
                    date_debut_reservation: document.getElementById('date-reservation').value,
                    date_du: document.getElementById('date-du').value,
                    date_au: document.getElementById('date-au').value
                };
            }

            const response = await jsonrpc("/web/dataset/call_kw/planning.dashboard/action_search_reservations", {
                model: 'planning.dashboard',
                method: 'action_search_reservations',
                args: [{}],
                kwargs: { filters: filters }
            });

            const tbody = document.querySelector('.ta-BLE tbody');
            tbody.innerHTML = '';
            let totalCount = 0;
            let allReservations = [];

            if (response) {
                for (const day in response) {
                    if (Array.isArray(response[day])) {
                        allReservations = allReservations.concat(response[day]);
                        totalCount += response[day].length;
                    }
                }

                const startIndex = (this.state.currentPage - 1) * this.state.itemsPerPage;
                const endIndex = startIndex + this.state.itemsPerPage;
                const paginatedReservations = allReservations.slice(startIndex, endIndex);

                if (paginatedReservations.length > 0) {
                    paginatedReservations.forEach(reservation => {
                        const [ref, client, dateCreation, datePrise, duree, modele, zone, total, reservationId, status] = reservation;

                        const formattedDateCreation = this.formatDate(dateCreation);
                        const formattedDatePrise = this.formatDate(datePrise);

                        const row = document.createElement('tr');
                        switch(status) {
                            case 'annule': row.classList.add('ANNle'); break;
                            case 'confirmee': row.classList.add('CONFirm'); break;
                            case 'rejete': row.classList.add('rejetée'); break;
                            case 'en_attend': row.classList.add('enAtteN'); break;
                            default: row.classList.add('enAtteN');
                        }
                        row.innerHTML = `
                            <td style="padding: 4px 2px">${ref}</td>
                            <td style="padding: 4px 2px">${client}</td>
                            <td style="padding: 4px 2px">${formattedDateCreation}</td>
                            <td style="padding: 4px 2px">${formattedDatePrise}</td>
                            <td style="padding: 4px 2px">${duree}</td>
                            <td style="padding: 4px 2px">${modele}</td>
                            <td style="padding: 4px 2px">${zone}</td>
                            <td style="padding: 4px 2px">${total}</td>
                            <td style="padding: 4px 2px">
                                <button class="butn123 config-btn" data-reservation-id="${reservationId}">
                                    <ion-icon name="cog-outline"></ion-icon>
                                </button>
                                <button class="butn123 delete-btn" data-reservation-id="${reservationId}">
                                    <ion-icon name="trash-outline"></ion-icon>
                                </button>
                            </td>
                        `;

                        row.querySelector('.config-btn').addEventListener('click', (e) => {
    const id = e.currentTarget.getAttribute('data-reservation-id');
    const url = `${window.location.origin}/web#id=${id}&menu_id=264&action=360&model=reservation&view_type=form`;
    window.open(url, '_blank');
});

                        row.querySelector('.delete-btn').addEventListener('click', (e) => {
                            const id = e.currentTarget.getAttribute('data-reservation-id');
                            this.deleteReservation(id);
                        });

                        tbody.appendChild(row);
                    });
                }
            }

            if (totalCount === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" style="text-align:center">Aucune réservation trouvée</td>
                    </tr>
                `;
            }

            this.state.totalPages = Math.ceil(totalCount / this.state.itemsPerPage);
            this.state.reservationCount = totalCount;
            this.updatePaginationControls();

        } catch (error) {
            this.state.reservationCount = 0;
            console.error("Erreur lors de la recherche des réservations :", error);
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        if (dateString.includes('/')) return dateString;

        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;

            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();

            return `${day}/${month}/${year}`;
        } catch (e) {
            return dateString;
        }
    }
}

TreeReservationJs.template = "TreeReservation";
registry.category("actions").add("tree_reservation", TreeReservationJs);