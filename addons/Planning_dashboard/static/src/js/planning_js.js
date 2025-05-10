/* @odoo-module */

import { registry } from '@web/core/registry'
const { Component, onMounted, useState } = owl
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
    groupedByModel: {} // Ajoutez cette ligne
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
        });
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

    // Obtenir le jour actuel
    const today = new Date();
    const currentDay = today.getDate();
    const currentMonth = today.getMonth() + 1; // Les mois commencent à 0 en JavaScript
    const currentYear = today.getFullYear();

    // Calculer le startDay uniquement si c'est le mois actuel et le startDay est à sa valeur par défaut (1)
    let calculatedStartDay = startDay;
    if (selectedMonth === currentMonth && selectedYear === currentYear && startDay === 1) {
        if (currentDay > 15) {
            // Afficher les 15 derniers jours du mois
            const lastDayOfMonth = new Date(currentYear, currentMonth, 0).getDate(); // Dernier jour du mois
            calculatedStartDay = Math.max(1, lastDayOfMonth - 14); // 15 jours incluant le dernier jour
        }
    }

    let currentDayIter = calculatedStartDay;
    let currentMonthIter = selectedMonth;
    let currentYearIter = selectedYear;

    for (let i = 0; i < 15; i++) {
        // Vérifier si on dépasse le dernier jour du mois
        const daysInMonth = new Date(currentYearIter, currentMonthIter, 0).getDate();
        if (currentDayIter > daysInMonth) {
            currentDayIter = 1; // Recommencer à 1
            currentMonthIter += 1; // Passer au mois suivant
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

        currentDayIter += 1; // Passer au jour suivant
    }

    // Mettre à jour l'état startDay uniquement si c'est le mois actuel et le startDay est à sa valeur par défaut (1)
    if (selectedMonth === currentMonth && selectedYear === currentYear && startDay === 1) {
        this.state.startDay = calculatedStartDay;
    }

    this.state.days = days;
}

    switchToNext15Days() {
    let { selectedMonth, selectedYear, startDay } = this.state;

    // Calculer le nouveau startDay
    let newStartDay = startDay + 15;

    // Vérifier si on dépasse la fin du mois
    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
    if (newStartDay > daysInMonth) {
        newStartDay -= daysInMonth; // Ajuster pour le mois suivant
        selectedMonth += 1; // Passer au mois suivant
        if (selectedMonth > 12) {
            selectedMonth = 1;
            selectedYear += 1; // Passer à l'année suivante
        }
    }

    // Mettre à jour l'état
    this.state.startDay = newStartDay;
    this.state.selectedMonth = selectedMonth;
    this.state.selectedYear = selectedYear; // Mettre à jour l'année
    this.state.selectedMonthName = this.getMonthName(selectedMonth);

    // Regénérer les jours et récupérer les disponibilités
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
            selectedYear -= 1; // Passer à l'année précédente
        }
        const daysInPrevMonth = new Date(selectedYear, selectedMonth, 0).getDate();
        newStartDay += daysInPrevMonth;
    }

    this.state.startDay = newStartDay;
    this.state.selectedMonth = selectedMonth;
    this.state.selectedYear = selectedYear; // Mettre à jour l'année
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
    const selectedId = event.target.value; // Récupère la valeur sélectionnée
    this.state.selectedModel = selectedId; // Met à jour l'état avec l'ID du modèle (ou une chaîne vide si "tous les modèles" est sélectionné)

    // Mettre à jour le nom du modèle affiché
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

    updateSelectedModel(event) {
    const selectedId = event.target.value;
    const selectedModel = this.state.models.find(model => model.id == selectedId);

    this.state.selectedModel = selectedModel ? selectedModel.id : "";
    this.state.selectedModelName = selectedModel ? selectedModel.name : "tous les modèles";
}


    onClick() {
    if (!this.state.selectedZone) {
        alert("Veuillez sélectionner une zone avant de continuer !");
        return;
    }

    // Activer l'état isSearchClicked
    this.state.isSearchClicked = true;

    // Mettre à jour le modèle affiché dans le tableau
    if (this.state.selectedModel === "") {
        this.state.displayedModelName = "Tous les modèles";
    } else {
        const selectedModel = this.state.models.find(model => model.id == this.state.selectedModel);
        this.state.displayedModelName = selectedModel ? selectedModel.name : "Aucun modèle sélectionné";
    }

    // Lancer la recherche
    this.fetchAvailabilityPlanning(this.state.selectedZone, this.state.selectedModel);

    // Afficher le tableau
    this.state.showTable = true;

    // Appeler la méthode pour récupérer les réservations des 3 derniers jours
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
            const modeleMatch = line.match(/(.+?) : /); // Capture le nom du modèle
            if (modeleMatch) {
                const modele = modeleMatch[1].trim();
                if (!groupedByModel[modele]) {
                    groupedByModel[modele] = [];
                }

                const vehicules = line.split('},');
                for (const vehicule of vehicules) {
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
                                planning[date1] = {
                                    first: value1,
                                    second: value2
                                };
                            }
                        }

                        groupedByModel[modele].push({
                            id: groupedByModel[modele].length + 1,
                            matricule: `${matriculeMatch[1].trim()} (${numeroMatch[1].trim()})`,
                            planning: planning
                        });
                    }
                }
            }
        }

        this.state.groupedByModel = groupedByModel;
    } catch (error) {
        console.error("Erreur lors de la récupération des disponibilités :", error);
    }
}
}

PlanningDashboardOuest.template = "PlanningDashboardOuest";
registry.category("actions").add("planning_dashboard_ouest", PlanningDashboardOuest);