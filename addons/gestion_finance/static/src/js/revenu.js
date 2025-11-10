/** @odoo-module **/

import { Component, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";

class RevenuComponent extends Component {
    static template = "Revenu";

    setup() {
        this.state = useState({
            zones: [],
            selectedZone: null,
            models: [],
            selectedModel: null,
            selectedModePaiement: null, // Nouveau state pour le mode de paiement
            defaultStartDate: this.getFormattedDate(new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)),
            defaultEndDate: this.getFormattedDate(new Date()),
            encaissementCount: 0,
            currentPage: 1,
            itemsPerPage: 30,
            totalPages: 1,
        });

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchModels();

            if (this.state.encaissementCount === 0) {
                document.getElementById('date-du').value = this.state.defaultStartDate;
                document.getElementById('date-au').value = this.state.defaultEndDate;
            }

            await this.searchEncaissements(false);
        });
    }

    async fetchZones() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/zone/search_read", {
                model: 'zone',
                method: 'search_read',
                args: [[], ['id', 'name']],
                kwargs: {}
            });
            this.state.zones = response.map(zone => ({ id: zone.id, name: zone.name }));
        } catch (error) {
            console.error("Erreur lors de la récupération des zones :", error);
        }
    }

    async fetchModels() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/modele/search_read", {
                model: 'modele',
                method: 'search_read',
                args: [[], ['id', 'name']],
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

    // Nouvelle méthode pour gérer le mode de paiement
    updateSelectedModePaiement(event) {
        const selectedModePaiement = event.target.value;
        this.state.selectedModePaiement = selectedModePaiement;
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
        document.getElementById('date-du').value = '';
        document.getElementById('date-au').value = '';
        document.getElementById('modeles').value = '';
        document.getElementById('pays').value = '';
        document.getElementById('mode-paiement').value = ''; // Reset du nouveau filtre

        this.state.selectedModel = null;
        this.state.selectedZone = null;
        this.state.selectedModePaiement = null; // Reset du state
        this.state.encaissementCount = 0;
        this.state.currentPage = 1;
        this.searchEncaissements(false);
    }

    async deleteEncaissement(encaissementId) {
        const confirmed = confirm("Voulez-vous vraiment supprimer cet encaissement ?");
        if (confirmed) {
            try {
                await jsonrpc("/web/dataset/call_kw/revenue.record/unlink", {
                    model: 'revenue.record',
                    method: 'unlink',
                    args: [[parseInt(encaissementId)]],
                    kwargs: {}
                });
                await this.searchEncaissements(true);
                alert("Encaissement supprimé avec succès");
            } catch (error) {
                console.error("Erreur lors de la suppression :", error);
                alert("Une erreur est survenue lors de la suppression");
            }
        }
    }

    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
            this.searchEncaissements(true);
        }
    }

    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.searchEncaissements(true);
        }
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
                Précédent
            </button>
            <span class="page-info">${this.state.currentPage}/${this.state.totalPages}</span>
            <button class="butn123 pagination-btn" onclick="component.nextPage()" ${this.state.currentPage === this.state.totalPages ? 'disabled' : ''}>
                Suivant
            </button>
        `;

        window.component = this;
    }

    async getTauxChange() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/taux.change/search_read", {
                model: 'taux.change',
                method: 'search_read',
                args: [[['id', '=', 1]], ['montant']],
                kwargs: {}
            });
            return response.length > 0 ? response[0].montant : 1;
        } catch (error) {
            console.error("Erreur lors de la récupération du taux de change :", error);
            return 1;
        }
    }

    async searchEncaissements(useFilters = true) {
        try {
            let domain = [];
            let reservationDomain = [];

            if (useFilters) {
                const reference = document.getElementById('reference').value;
                const prenom = document.getElementById('prenom').value;
                const modeles = document.getElementById('modeles').value;
                const pays = document.getElementById('pays').value;
                const modePaiement = document.getElementById('mode-paiement').value; // Nouveau filtre
                const date_du = document.getElementById('date-du').value;
                const date_au = document.getElementById('date-au').value;

                if (reference) {
                    domain.push(['reservation.name', 'ilike', reference]);
                    reservationDomain.push(['name', 'ilike', reference]);
                }
                if (prenom) {
                    domain.push(['reservation.prenom', 'ilike', prenom]);
                    reservationDomain.push(['prenom', 'ilike', prenom]);
                }
                if (modeles) {
                    domain.push(['modele', '=', parseInt(modeles)]);
                    reservationDomain.push(['modele', '=', parseInt(modeles)]);
                }
                if (pays) {
                    domain.push(['zone', '=', parseInt(pays)]);
                    reservationDomain.push(['zone', '=', parseInt(pays)]);
                }
                // Ajout du filtre mode de paiement
                if (modePaiement) {
                    domain.push(['mode_paiement', '=', modePaiement]);
                }
                if (date_du) {
                    domain.push(['create_date', '>=', date_du + ' 00:00:00']);
                    reservationDomain.push(['create_date', '>=', date_du + ' 00:00:00']);
                }
                if (date_au) {
                    domain.push(['create_date', '<=', date_au + ' 23:59:59']);
                    reservationDomain.push(['create_date', '<=', date_au + ' 23:59:59']);
                }
            }

            const tauxChange = await this.getTauxChange();

            const response = await jsonrpc("/web/dataset/call_kw/revenue.record/search_read", {
                model: 'revenue.record',
                method: 'search_read',
                args: [domain, ['name', 'create_date', 'reservation', 'total_encaisse', 'montant', 'mode_paiement']], // Ajout mode_paiement
                kwargs: {
                    limit: this.state.itemsPerPage,
                    offset: (this.state.currentPage - 1) * this.state.itemsPerPage
                }
            });

            reservationDomain.push(['status', '=', 'confirmee']);
            const reservationsResponse = await jsonrpc("/web/dataset/call_kw/reservation/search_read", {
                model: 'reservation',
                method: 'search_read',
                args: [reservationDomain, ['total_reduit_euro']],
                kwargs: {}
            });

            let totalReservations = 0;
            reservationsResponse.forEach(reservation => {
                const montantEuroEnDinars = (reservation.total_reduit_euro || 0) * tauxChange;
                totalReservations += montantEuroEnDinars;
            });

            const encaissementsWithReservations = await Promise.all(
                response.map(async (encaissement) => {
                    if (encaissement.reservation && encaissement.reservation[0]) {
                        try {
                            const reservationDetails = await jsonrpc("/web/dataset/call_kw/reservation/read", {
                                model: 'reservation',
                                method: 'read',
                                args: [encaissement.reservation[0], [
                                    'name',
                                    'prenom',
                                    'create_date',
                                    'date_heure_debut',
                                    'nbr_jour_reservation',
                                    'modele',
                                    'zone'
                                ]],
                                kwargs: {}
                            });

                            return {
                                ...encaissement,
                                reservationDetails: reservationDetails[0]
                            };
                        } catch (error) {
                            console.error("Erreur lors de la récupération des détails de réservation:", error);
                            return {
                                ...encaissement,
                                reservationDetails: null
                            };
                        }
                    }
                    return {
                        ...encaissement,
                        reservationDetails: null
                    };
                })
            );

            // GROUPEMENT PAR RÉFÉRENCE
            const encaissementsGroupes = new Map();

            for (const encaissement of encaissementsWithReservations) {
                const montantEuroEnDinars = (encaissement.montant || 0) * tauxChange;
                const totalEncaisseComplet = (encaissement.total_encaisse || 0) + montantEuroEnDinars;

                if (encaissement.reservationDetails) {
                    const reference = encaissement.reservationDetails.name;

                    if (encaissementsGroupes.has(reference)) {
                        const existing = encaissementsGroupes.get(reference);
                        existing.totalEncaisse += totalEncaisseComplet;
                        // Ajouter les modes de paiement s'ils sont différents
                        if (encaissement.mode_paiement && !existing.modesPaiement.includes(encaissement.mode_paiement)) {
                            existing.modesPaiement.push(encaissement.mode_paiement);
                        }
                    } else {
                        encaissementsGroupes.set(reference, {
    reference,
    client: encaissement.reservationDetails.prenom || '',
    dateCreation: encaissement.reservationDetails.create_date,
    datePrise: encaissement.reservationDetails.date_heure_debut,
    duree: encaissement.reservationDetails.nbr_jour_reservation || '',
    modele: encaissement.reservationDetails.modele ? encaissement.reservationDetails.modele[1] : '',
    zone: encaissement.reservationDetails.zone ? encaissement.reservationDetails.zone[1] : '',
    totalEncaisse: totalEncaisseComplet,
    modesPaiement: encaissement.mode_paiement ? [encaissement.mode_paiement] : []
});
                    }
                }
            }

            const tbody = document.querySelector('.ta-BLE tbody');
            tbody.innerHTML = '';

            let totalSum = 0;

            if (encaissementsGroupes.size > 0) {
                encaissementsGroupes.forEach((item) => {
                    totalSum += item.totalEncaisse;

                    const row = document.createElement('tr');
                    row.style.border = '1px solid #324690';

                    // Formatage des modes de paiement
                    const modesFormates = item.modesPaiement.length > 0
                        ? item.modesPaiement.map(mode => this.getModeLabel(mode)).join(', ')
                        : 'N/A';

                    row.innerHTML = `
    <td style="padding: 8px 4px">${item.reference || ''}</td>
    <td style="padding: 8px 4px">${item.client || ''}</td>
    <td style="padding: 8px 4px">${this.formatDate(item.dateCreation)}</td>
    <td style="padding: 8px 4px">${this.formatDate(item.datePrise)}</td>
    <td style="padding: 8px 4px">${item.duree || ''}</td>
    <td style="padding: 8px 4px">${item.modele || ''}</td>
    <td style="padding: 8px 4px">${item.zone || ''}</td>
    <td style="padding: 8px 4px">${modesFormates === 'N/A' ? '' : modesFormates}</td>
    <td style="padding: 8px 4px; font-weight: bold; color: #324690;">${this.formatCurrency(item.totalEncaisse)}</td>
`;

                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" style="text-align:center">Aucun encaissement trouvé</td>
                    </tr>
                `;
            }

            document.querySelector('#total-amount').textContent = this.formatCurrency(totalSum);
            document.querySelector('#total-reservations').textContent = this.formatCurrency(totalReservations);

            const countResponse = await jsonrpc("/web/dataset/call_kw/revenue.record/search_count", {
                model: 'revenue.record',
                method: 'search_count',
                args: [domain],
                kwargs: {}
            });

            this.state.totalPages = Math.ceil(countResponse / this.state.itemsPerPage);
            this.state.encaissementCount = countResponse;
            this.updatePaginationControls();

        } catch (error) {
            console.error("Erreur lors de la recherche des encaissements :", error);
            document.querySelector('#total-amount').textContent = this.formatCurrency(0);
            document.querySelector('#total-reservations').textContent = this.formatCurrency(0);
            this.state.encaissementCount = 0;
        }
    }

    getModeLabel(mode) {
        switch(mode) {
            case 'carte': return 'Banque';
            case 'liquide': return 'Liquide';
            case 'autre': return 'Autre';
        default: return mode || '';
        }
    }

    formatCurrency(amount) {
        if (amount === null || amount === undefined) return '0,00 DA';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'DZD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount).replace('DZD', 'DA');
    }

    formatCurrencyEuro(amount) {
        if (amount === null || amount === undefined) return '0,00 €';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    formatDate(dateString) {
    if (!dateString) return '';
    if (dateString.includes('/')) return dateString;

    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '';

        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();

        return `${day}/${month}/${year}`;
    } catch (e) {
        return '';
    }
}
}

registry.category("actions").add("revenu_finance", RevenuComponent);
