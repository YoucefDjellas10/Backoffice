/* @odoo-module */

import { registry } from '@web/core/registry';
const { Component, onMounted, useState } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";

export class EncaissementJs extends Component {
    setup() {
        // ✅ Calculer les dates par défaut
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);

        this.state = useState({
            reservations: [],
            zones: [],
            vehicules: [],
            users: [],
            revenues: [],
            revenueCount: 0,
            totalMontantDzd: 0,
            totalMontantEur: 0,
            currentPage: 1,
            itemsPerPage: 30,
            totalPages: 1,
            defaultDuDate: new Date(firstDay.getTime() - firstDay.getTimezoneOffset() * 60000).toISOString().slice(0, 10),
            defaultAuDate: new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
        });

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchVehicules();
            await this.fetchUsers();
            await this.searchRevenues();
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
            this.state.zones = response.map(z => ({ id: z.id, name: z.name }));
        } catch (error) {
            console.error("Erreur fetchZones:", error);
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
            this.state.vehicules = response.map(v => ({ id: v.id, name: v.numero }));
        } catch (error) {
            console.error("Erreur fetchVehicules:", error);
        }
    }

    async fetchUsers() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/res.users/search_read", {
                model: 'res.users',
                method: 'search_read',
                args: [[], ['id', 'name']],
                kwargs: {}
            });
            this.state.users = response.map(u => ({ id: u.id, name: u.name }));
        } catch (error) {
            console.error("Erreur fetchUsers:", error);
        }
    }

    changeItemsPerPage(event) {
        this.state.itemsPerPage = parseInt(event.target.value);
        this.state.currentPage = 1;
        this.searchRevenues();
    }

    async searchRevenues() {
        try {
            const reservation = document.getElementById('reservation').value;
            const zone = document.getElementById('zone').value;
            const du = document.getElementById('du').value;
            const au = document.getElementById('au').value;
            const vehicule = document.getElementById('vehicule').value;
            const mode_paiement = document.getElementById('mode_paiement').value;
            const effectue_par = document.getElementById('effectue_par').value;

            console.log("Filtres appliqués:", {
                reservation, zone, du, au, vehicule, mode_paiement, effectue_par
            });

            if (!du || !au) {
                alert("Les dates 'Du' et 'Au' sont obligatoires");
                return;
            }

            const filters = {
                reservation: reservation ? reservation.trim() : null, // Maintenant une string
                zone: zone ? parseInt(zone) : null,
                du: du,
                au: au,
                vehicule: vehicule ? parseInt(vehicule) : null,
                mode_paiement: mode_paiement || null,
                effectue_par: effectue_par ? parseInt(effectue_par) : null
            };

            console.log("Filtres envoyés:", filters);

            const response = await jsonrpc("/web/dataset/call_kw/revenue.record/action_search_revenues", {
                model: 'revenue.record',
                method: 'action_search_revenues',
                args: [],
                kwargs: {
                    filters: filters,
                    page: this.state.currentPage,
                    limit: this.state.itemsPerPage
                }
            });

            console.log("Réponse reçue:", response);

            this.state.revenues = response.revenues || [];
            this.state.revenueCount = response.total_count || 0;
            this.state.totalMontantDzd = response.total_montant_dzd || 0;
            this.state.totalMontantEur = response.total_montant_eur || 0;
            this.state.totalPages = Math.max(1, Math.ceil(this.state.revenueCount / this.state.itemsPerPage));

            console.log("État après mise à jour:", this.state);

            this.attachEventListeners();

            // Force le rendu
            this.render();

        } catch (error) {
            console.error("Erreur searchRevenues:", error);
            this.state.revenues = [];
            this.state.revenueCount = 0;
            this.state.totalMontantDzd = 0;
            this.state.totalMontantEur = 0;
            this.state.totalPages = 1;
            this.render();
        }
    }

    attachEventListeners() {
        document.querySelectorAll('.config-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const revId = e.currentTarget.getAttribute('data-rev-id');
                this.openRevenueForm(revId);
            });
        });
    }

    openRevenueForm(revId) {
        const url = `${window.location.origin}/web?debug=1#id=${revId}&menu_id=1465&action=360&model=revenue.record&view_type=form`;
        window.open(url, '_blank');
    }

    resetFilters() {
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);

        // ✅ Mettre à jour le state ET les champs
        this.state.defaultDuDate = firstDay.toISOString().slice(0, 10);
        this.state.defaultAuDate = now.toISOString().slice(0, 10);

        document.getElementById('du').value = this.state.defaultDuDate;
        document.getElementById('au').value = this.state.defaultAuDate;
        document.getElementById('reservation').value = ''; // Maintenant un input text
        document.getElementById('zone').value = '';
        document.getElementById('vehicule').value = '';
        document.getElementById('mode_paiement').value = '';
        document.getElementById('effectue_par').value = '';
        this.state.currentPage = 1;
        this.searchRevenues();
    }

    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
            this.searchRevenues();
        }
    }

    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.searchRevenues();
        }
    }
}

EncaissementJs.template = "EncaissementTree";
registry.category("actions").add("recape_encaissement", EncaissementJs);
