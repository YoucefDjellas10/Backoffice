/* @odoo-module */

import { registry } from '@web/core/registry'
const { Component, onMounted, useState, onPatched } = owl
import { jsonrpc } from "@web/core/network/rpc_service"

export class PlanningDashboardOuest extends Component {
    setup() {
        this.state = useState({
            matricules: [],
            zones: [],
            models: [],
            vehicules: [],
            selectedModel: "",
            selectedZone: null,
            selectedMonth: new Date().getMonth() + 1,
            selectedYear: new Date().getFullYear(),
            days: [],
            selectedMonthName: this.getMonthName(new Date().getMonth() + 1),
            updateTime: this.getCurrentTime(),
            startDay: 1,
            showTable: false,
            displayedModelName: "Aucun modèle sélectionné",
            displayedMatricules: [],
            isSearchClicked: false,
            groupedByModel: {},
            blockedVehicles: {} // NOUVEAU : pour stocker les véhicules bloqués
        });

        this.months = [
            { id: 1, name: "Jan" }, { id: 2, name: "Fév" }, { id: 3, name: "Mar" },
            { id: 4, name: "Avr" }, { id: 5, name: "Mai" }, { id: 6, name: "Juin" },
            { id: 7, name: "Juil" }, { id: 8, name: "Août" }, { id: 9, name: "Sep" },
            { id: 10, name: "Oct" }, { id: 11, name: "Nov" }, { id: 12, name: "Déc" },
        ];

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchModele();
            await this.fetchMatricules();
            await this.fetchVehicule();
            this.generateDays();
            this.updateCurrentTime();
            this.addBlockedVehicleCSS(); // NOUVEAU
        });
        onPatched(() => {
            this.applyBlockedVehicleStyles();
        });
    }

    addBlockedVehicleCSS() {
        if (document.querySelector('#blocked-vehicle-styles')) {
            return;
        }

        const cssStyles = `
            <style id="blocked-vehicle-styles">
                .BLOQUE,
                .planning-cell-blocked,
                .blocked-vehicle,
                td.BLOQUE,
                span.BLOQUE {
                    background-color: #edf37d !important;
                    color: #748b1a !important;
                    font-weight: 500 !important;
                    box-shadow: inset 1px 1px 2px rgba(100, 100, 100, 0.2),
                                inset -1px -1px 2px rgba(255, 255, 255, 0.5),
                                -5px 1px 0px -3px rgba(255, 255, 255, 0.75) inset;
                                -webkit-box-shadow: -5px 1px 0px -3px rgba(255, 255, 255, 0.75) inset;
                                -moz-box-shadow: -5px 1px 0px -3px rgba(255, 255, 255, 0.75) inset;
                text-shadow: 0px 0px 2px rgba(51, 51, 51, 0.1);
                text-align: center;
                padding: 4px;
                border: none !important;
                }
            </style> `;

        document.head.insertAdjacentHTML('beforeend', cssStyles);
    }

    // NOUVEAU : Appliquer les styles aux éléments contenant "BLOQUE"
    applyBlockedVehicleStyles() {
        setTimeout(() => {
            const cells = document.querySelectorAll('td, span, div');

            cells.forEach(cell => {
                const text = cell.textContent || cell.innerText;
                if (text && text.includes('BLOQUE')) {
                    cell.classList.add('BLOQUE');
                    cell.style.backgroundColor = '#ffc107';
                    cell.style.color = '#000000';
                    cell.style.fontWeight = 'bold';
                    cell.style.border = '2px solid #ffb300';
                    cell.style.textAlign = 'center';
                    cell.style.padding = '4px';
                    cell.style.borderRadius = '4px';

                    if (!cell.hasAttribute('title')) {
                        cell.setAttribute('title', 'Véhicule bloqué - Non disponible');
                    }
                }
            });
        }, 100);
    }

    // NOUVEAU : Récupérer les véhicules bloqués pour une période
    async fetchBlockedVehicles() {
        try {
            const startDate = new Date(this.state.selectedYear, this.state.selectedMonth - 1, this.state.startDay);
            const endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 14);

            const response = await jsonrpc("/web/dataset/call_kw/planning.dashboard/get_blocked_vehicles_for_period", {
                model: 'planning.dashboard',
                method: 'get_blocked_vehicles_for_period',
                args: [startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]],
                kwargs: {}
            });

            this.state.blockedVehicles = response || {};
            console.log("Véhicules bloqués récupérés:", this.state.blockedVehicles);
        } catch (error) {
            console.error("Erreur lors de la récupération des véhicules bloqués:", error);
            this.state.blockedVehicles = {};
        }
    }

    async fetchMatricules() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/planning.dashboard/get_all_matricules", {
                model: 'planning.dashboard',
                method: 'get_all_matricules',
                args: [{}],
                kwargs: {}
            });
            this.state.matricules = response || [];
        } catch (error) {
            console.error("Erreur lors de la récupération des matricules :", error);
        }
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

    async fetchVehicule() {
        const models = await jsonrpc("/web/dataset/call_kw/reservation/get_all_modele", {
            model: 'reservation',
            method: 'get_all_modele',
            args: [{}],
            kwargs: {}
        });
        this.state.models = models.map(modele => ({ id: modele.id, name: modele.name }));
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString('fr-FR', { hour12: false });
    }

    updateCurrentTime() {
        this.state.updateTime = this.getCurrentTime();
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

    generateDays() {
        const { selectedMonth, selectedYear, startDay } = this.state;
        const dayNames = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
        let days = [];

        const today = new Date();
        const currentDay = today.getDate();
        const currentMonth = today.getMonth() + 1;
        const currentYear = today.getFullYear();

        let calculatedStartDay = startDay;
        if (selectedMonth === currentMonth && selectedYear === currentYear && startDay === 1) {
            if (currentDay > 15) {
                const lastDayOfMonth = new Date(currentYear, currentMonth, 0).getDate();
                calculatedStartDay = Math.max(1, lastDayOfMonth - 14);
            }
        }

        let currentDayIter = calculatedStartDay;
        let currentMonthIter = selectedMonth;
        let currentYearIter = selectedYear;

        for (let i = 0; i < 15; i++) {
            const daysInMonth = new Date(currentYearIter, currentMonthIter, 0).getDate();
            if (currentDayIter > daysInMonth) {
                currentDayIter = 1;
                currentMonthIter += 1;
                if (currentMonthIter > 12) {
                    currentMonthIter = 1;
                    currentYearIter += 1;
                }
            }

            const date = new Date(currentYearIter, currentMonthIter - 1, currentDayIter);
            const dayName = dayNames[date.getDay()];
            const formattedDay = currentDayIter.toString().padStart(2, "0");
            const formattedMonth = currentMonthIter.toString().padStart(2, "0");

            days.push({ label: `${dayName}. ${formattedDay}/${formattedMonth}` });

            currentDayIter += 1;
        }

        if (selectedMonth === currentMonth && selectedYear === currentYear && startDay === 1) {
            this.state.startDay = calculatedStartDay;
        }

        this.state.days = days;
    }

    switchToNext15Days() {
        let { selectedMonth, selectedYear, startDay } = this.state;

        let newStartDay = startDay + 15;

        const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
        if (newStartDay > daysInMonth) {
            newStartDay -= daysInMonth;
            selectedMonth += 1;
            if (selectedMonth > 12) {
                selectedMonth = 1;
                selectedYear += 1;
            }
        }

        this.state.startDay = newStartDay;
        this.state.selectedMonth = selectedMonth;
        this.state.selectedYear = selectedYear;
        this.state.selectedMonthName = this.getMonthName(selectedMonth);

        this.generateDays();
        this.fetchAvailabilityPlanning(this.state.selectedZone, this.state.selectedModel);
    }

    switchToPrevious15Days() {
        let { selectedMonth, selectedYear, startDay } = this.state;

        let newStartDay = startDay - 15;

        if (newStartDay < 1) {
            selectedMonth -= 1;
            if (selectedMonth < 1) {
                selectedMonth = 12;
                selectedYear -= 1;
            }
            const daysInPrevMonth = new Date(selectedYear, selectedMonth, 0).getDate();
            newStartDay += daysInPrevMonth;
        }

        this.state.startDay = newStartDay;
        this.state.selectedMonth = selectedMonth;
        this.state.selectedYear = selectedYear;
        this.state.selectedMonthName = this.getMonthName(selectedMonth);

        this.generateDays();
        this.fetchAvailabilityPlanning(this.state.selectedZone, this.state.selectedModel);
    }

    selectMonth(month) {
        this.state.selectedMonth = month;
        this.state.selectedMonthName = this.getMonthName(month);
        this.state.startDay = 1;
        this.generateDays();
        this.updateCurrentTime();
    }

    getMonthName(month) {
        const months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"];
        return months[month - 1];
    }

    updateSelectedModel(event) {
        const selectedId = event.target.value;
        this.state.selectedModel = selectedId;

        if (selectedId === "") {
            this.state.selectedModelName = "Tous les modèles";
        } else {
            const selectedModel = this.state.models.find(model => model.id == selectedId);
            this.state.selectedModelName = selectedModel ? selectedModel.name : "Aucun modèle sélectionné";
        }
    }

    updateSelectedZone(event) {
        const selectedZone = event.target.value;
        this.state.selectedZone = selectedZone;
        console.log("Zone sélectionnée :", selectedZone);
        this.fetchMatricules(selectedZone);
    }

    async onClick() {
        if (!this.state.selectedZone) {
            alert("Veuillez sélectionner une zone avant de continuer !");
            return;
        }

        this.state.isSearchClicked = true;

        if (this.state.selectedModel === "") {
            this.state.displayedModelName = "Tous les modèles";
        } else {
            const selectedModel = this.state.models.find(model => model.id == this.state.selectedModel);
            this.state.displayedModelName = selectedModel ? selectedModel.name : "Aucun modèle sélectionné";
        }

        // NOUVEAU : Récupérer les véhicules bloqués avant le planning
        await this.fetchBlockedVehicles();

        this.fetchAvailabilityPlanning(this.state.selectedZone, this.state.selectedModel);
        this.state.showTable = true;
        this.fetchReservationsLast3Days();
    }

    async fetchReservationsLast3Days() {
        try {
            const response = await jsonrpc("/web/dataset/call_kw/planning.dashboard/action_get_reservations_last_3_days", {
                model: 'planning.dashboard',
                method: 'action_get_reservations_last_3_days',
                args: [{}],
                kwargs: {}
            });

            console.log("Réservations des 3 derniers jours :", response);
        } catch (error) {
            console.error("Erreur lors de la récupération des réservations des 3 derniers jours :", error);
        }
    }

    async fetchAvailabilityPlanning(zone_id = null, model_id = null) {
        try {
            const kwargs = {
                zone_id: zone_id,
                selected_month: this.state.selectedMonth,
                selected_year: this.state.selectedYear,
                start_day: this.state.startDay
            };

            if (model_id !== "") {
                kwargs.model_id = model_id;
            }

            const response = await jsonrpc("/web/dataset/call_kw/planning.dashboard/get_availibality_planning", {
                model: 'planning.dashboard',
                method: 'get_availibality_planning',
                args: [{}],
                kwargs: kwargs
            });

            const groupedByModel = {};
            const lines = response.split('\n');

            for (const line of lines) {
                const modeleMatch = line.match(/(.+?) : /);
                if (modeleMatch) {
                    const modele = modeleMatch[1].trim();
                    if (!groupedByModel[modele]) {
                        groupedByModel[modele] = [];
                    }

                    const vehicules = line.split('},');
                    for (const vehicule of vehicules) {
                        const vehiculeIdMatch = vehicule.match(/id = ([^,]+)/);
                        const matriculeMatch = vehicule.match(/matricule = ([^,]+)/);
                        const numeroMatch = vehicule.match(/Numero = ([^,]+)/);
                        const planningMatch = vehicule.match(/\[(.+?)\]/g);

                        if (matriculeMatch && numeroMatch && planningMatch) {
                            const planning = {};

                            for (const block of planningMatch) {
                                const entries = block.slice(1, -1).split(',');
                                const [firstEntry, secondEntry] = entries.map(entry => entry.trim());

                                const [date1, value1] = firstEntry.split('=').map(s => s.trim());
                                const [date2, value2] = secondEntry.split('=').map(s => s.trim());

                                if (date1 === date2) {
                                    let finalValue1 = value1;
                                    let finalValue2 = value2;

                                    // NOUVEAU : Vérifier si le véhicule est bloqué ce jour-là
                                    const vehiculeId = vehiculeIdMatch ? parseInt(vehiculeIdMatch[1].trim()) : null;
                                    if (vehiculeId && this.state.blockedVehicles[vehiculeId]) {
                                        const [day, month] = date1.split('/');
                                        const checkDate = `${this.state.selectedYear}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;

                                        for (const block of this.state.blockedVehicles[vehiculeId]) {
                                            if (checkDate >= block.date_from && checkDate <= block.date_to) {
                                                finalValue1 = "BLOQUE";
                                                finalValue2 = "BLOQUE";
                                                break;
                                            }
                                        }
                                    }

                                    planning[date1] = {
                                        first: finalValue1,
                                        second: finalValue2,
                                        isBlocked: finalValue1 === "BLOQUE" || finalValue2 === "BLOQUE"
                                    };
                                }
                            }

                            groupedByModel[modele].push({
                                id: vehiculeIdMatch ? parseInt(vehiculeIdMatch[1].trim()) : groupedByModel[modele].length + 1,
                                matricule: `${matriculeMatch[1].trim()} (${numeroMatch[1].trim()})`,
                                planning: planning
                            });
                        }
                    }
                }
            }

            this.state.groupedByModel = groupedByModel;

            // NOUVEAU : Appliquer les styles après la mise à jour des données
            setTimeout(() => this.applyBlockedVehicleStyles(), 200);

        } catch (error) {
            console.error("Erreur lors de la récupération des disponibilités :", error);
        }
    }
}

PlanningDashboardOuest.template = "PlanningDashboardOuest";
registry.category("actions").add("planning_dashboard_ouest", PlanningDashboardOuest);
