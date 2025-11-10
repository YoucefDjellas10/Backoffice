/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";

export class AnnualBalance extends Component {
    static template = "AnnualBalanceTemplate";

    setup() {
        this.state = useState({
            years: [],
            zones: [],
            vehicles: [],
            selectedYear: new Date().getFullYear(),
            selectedZone: "",
            selectedVehicle: "",
            monthlyData: [],
            loading: true,
        });

        onMounted(async () => {
            await this.loadFilters();
            await this.fetchZones();
            await this.fetchVehicules();
            await this.loadAnnualData();
        });
    }

    // 🔹 Charger les zones (CORRIGÉ)
    async fetchZones() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/zone/search_read", {
                model: "zone",
                method: "search_read",
                args: [[], ["id", "name"]],
                kwargs: {},
            });

            this.state.zones = response.map(z => ({ id: z.id, name: z.name }));
            console.log("✅ Zones chargées :", this.state.zones);
        } catch (error) {
            console.error("❌ Erreur fetchZones:", error);
            this.state.zones = [];
        }
    }

    // 🔹 Charger les véhicules
    async fetchVehicules() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/vehicule/search_read", {
                model: "vehicule",
                method: "search_read",
                args: [[], ["id", "numero"]],
                kwargs: {},
            });

            this.state.vehicles = response.map(v => ({ id: v.id, name: v.numero }));
            console.log("✅ Véhicules chargés :", this.state.vehicles);
        } catch (error) {
            console.error("❌ Erreur fetchVehicules:", error);
            this.state.vehicles = [];
        }
    }

    // 🔹 Charger les filtres Année + Véhicule
    async loadFilters() {
        try {
            const yearsResponse = await jsonrpc("/web/dataset/call_kw/balance/get_annual_filters", {
                model: "balance",
                method: "get_annual_filters",
                args: [],
                kwargs: {},
            });
            this.state.years = yearsResponse?.years || [];

            console.log("✅ Filtres Année chargés :", {
                years: this.state.years,
            });
        } catch (error) {
            console.error("❌ Erreur lors du chargement des filtres :", error);
            this.state.years = [];
        }
    }

    // 🔹 Charger les données annuelles
    async loadAnnualData() {
        this.state.loading = true;
        try {
            const params = {
                year: this.state.selectedYear,
                zone: this.state.selectedZone ? parseInt(this.state.selectedZone) : "",
                vehicle: this.state.selectedVehicle ? parseInt(this.state.selectedVehicle) : "",
            };

            console.log("📊 Chargement des données avec params:", params);

            const result = await jsonrpc("/web/dataset/call_kw/balance/get_annual_balance_data", {
                model: "balance",
                method: "get_annual_balance_data",
                args: [params],
                kwargs: {},
            });

            this.state.monthlyData = result?.monthly_data || [];
            console.log("✅ Données annuelles chargées :", this.state.monthlyData);
        } catch (error) {
            console.error("❌ Erreur lors du chargement des données annuelles :", error);
            this.state.monthlyData = [];
        } finally {
            this.state.loading = false;
        }
    }

    // 🔹 Gestion des changements de filtres (sans recharger automatiquement)
    onYearChange(ev) {
        this.state.selectedYear = parseInt(ev.target.value) || new Date().getFullYear();
        console.log("Année sélectionnée:", this.state.selectedYear);
    }

    onZoneChange(ev) {
        this.state.selectedZone = ev.target.value || "";
        console.log("Zone sélectionnée:", this.state.selectedZone);
    }

    onVehicleChange(ev) {
        this.state.selectedVehicle = ev.target.value || "";
        console.log("Véhicule sélectionné:", this.state.selectedVehicle);
    }

    // 🔹 Bouton "Rechercher" - Lance la recherche manuellement
    async searchData() {
        await this.loadAnnualData();
    }

    // 🔹 Bouton "Rétablir" - Réinitialise les filtres
    async resetFilters() {
        this.state.selectedYear = new Date().getFullYear();
        this.state.selectedZone = "";
        this.state.selectedVehicle = "";

        // Réinitialiser les valeurs dans les select
        document.getElementById('year-select').value = this.state.selectedYear;
        document.getElementById('zone-select').value = "";
        document.getElementById('vehicle-select').value = "";

        await this.loadAnnualData();
    }

    // 🔹 Helpers
    getMonthData(monthNum) {
        const monthData = this.state.monthlyData.find(m => m.month === monthNum);
        return monthData || { month: monthNum, depense: 0, recette: 0, balance: 0 };
    }

    formatBalance(balance) {
        return new Intl.NumberFormat("fr-FR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(balance || 0);
    }

    getMonthName(monthNum) {
        const months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
        ];
        return months[monthNum - 1] || "";
    }

    // 🔹 Calculer les totaux
    getTotalDepense() {
        return this.state.monthlyData.reduce((sum, month) => sum + (month.depense || 0), 0);
    }

    getTotalRecette() {
        return this.state.monthlyData.reduce((sum, month) => sum + (month.recette || 0), 0);
    }

    getTotalBalance() {
        return this.state.monthlyData.reduce((sum, month) => sum + (month.balance || 0), 0);
    }
}

AnnualBalance.props = {
    action: { type: Object, optional: true },
    actionId: { type: Number, optional: true },
    className: { type: String, optional: true },
};

registry.category("actions").add("annual_balance", AnnualBalance);
