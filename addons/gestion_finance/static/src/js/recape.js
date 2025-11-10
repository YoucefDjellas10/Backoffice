/* @odoo-module */

import { registry } from '@web/core/registry';
const { Component, onMounted, useState } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";

export class RecapeJs extends Component {
    setup() {
        const now = new Date();

        this.state = useState({
            zones: [],
            typesDepense: [],
            vehicules: [],
            depenses: [],
            depenseCount: 0,
            totalMontant: 0,
            currentPage: 1,
            itemsPerPage: 30,
            totalPages: 1
        });

        onMounted(async () => {
    await this.fetchZones();
    await this.fetchTypesDepense();
    await this.fetchVehicules();

    // Valeurs par défaut
    document.getElementById('mois').value = now.getMonth() + 1;
    document.getElementById('annee').value = now.getFullYear();
    document.getElementById('statut').value = 'valide';  // ✅ Défaut = "Validé"

    await this.searchDepenses();
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

    async fetchTypesDepense() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/type.depens/search_read", {
                model: 'type.depens',
                method: 'search_read',
                args: [[], ['id', 'name']],
                kwargs: {}
            });
            this.state.typesDepense = response.map(type => ({ id: type.id, name: type.name }));
        } catch (error) {
            console.error("Erreur lors de la récupération des types de dépense :", error);
        }
    }

    async fetchVehicules() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/vehicule/search_read", {
                model: 'vehicule',
                method: 'search_read',
                args: [[], ['id', 'numero']],
                kwargs: {}
            });
            this.state.vehicules = response.map(vehicule => ({ id: vehicule.id, name: vehicule.numero }));
        } catch (error) {
            console.error("Erreur lors de la récupération des véhicules :", error);
        }
    }

    // Méthode pour changer le nombre d'éléments par page
    changeItemsPerPage(event) {
        this.state.itemsPerPage = parseInt(event.target.value);
        this.state.currentPage = 1;
        this.searchDepenses();
    }

    async searchDepenses() {
        try {
            const mois = document.getElementById('mois').value;
            const annee = document.getElementById('annee').value;
            const zone = document.getElementById('zone').value;
            const typeDepense = document.getElementById('type_depense').value;
            const vehicule = document.getElementById('vehicule').value;
            const statut = document.getElementById('statut').value;

            // Validation des champs obligatoires
            if (!mois || !annee) {
                alert("Le mois et l'année sont obligatoires");
                return;
            }

            const filters = {
                mois: parseInt(mois),
                annee: parseInt(annee),
                zone: zone ? parseInt(zone) : null,
                type_depense: typeDepense ? parseInt(typeDepense) : null,
                vehicule: vehicule ? parseInt(vehicule) : null,
                statut: statut || null
            };

            const response = await jsonrpc("/web/dataset/call_kw/depense.record/action_search_depenses", {
                model: 'depense.record',
                method: 'action_search_depenses',
                args: [],
                kwargs: {
                    filters: filters,
                    page: this.state.currentPage,
                    limit: this.state.itemsPerPage
                }
            });

            // ✅ Suppression du mapping avec status_class
            this.state.depenses = response.depenses || [];

            this.state.depenseCount = response.total_count || 0;
            this.state.totalMontant = response.total_montant || 0;
            this.state.totalPages = Math.ceil(this.state.depenseCount / this.state.itemsPerPage);

            // Ajouter les écouteurs d'événements pour les boutons de configuration
            this.attachEventListeners();

        } catch (error) {
            console.error("Erreur lors de la recherche des dépenses :", error);
            this.state.depenses = [];
            this.state.depenseCount = 0;
            this.state.totalMontant = 0;
            this.state.totalPages = 1;
        }
    }

    attachEventListeners() {
        document.querySelectorAll('.config-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const depenseId = e.currentTarget.getAttribute('data-depense-id');
                this.openDepenseForm(depenseId);
            });
        });
    }

    openDepenseForm(depenseId) {
        const url = `${window.location.origin}/web?debug=1#id=${depenseId}&menu_id=1465&action=360&model=depense.record&view_type=form`;
        window.open(url, '_blank');
    }

    resetFilters() {
        const now = new Date();
        document.getElementById('mois').value = now.getMonth() + 1;
        document.getElementById('annee').value = now.getFullYear();
        document.getElementById('zone').value = '';
        document.getElementById('type_depense').value = '';
        document.getElementById('vehicule').value = '';
        document.getElementById('statut').value = '';
        this.state.currentPage = 1;
        this.searchDepenses();
    }

    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
            this.searchDepenses();
        }
    }

    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.searchDepenses();
        }
    }
}

RecapeJs.template = "RecapeTree";
registry.category("actions").add("recape", RecapeJs);
