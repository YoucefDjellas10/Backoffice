/* @odoo-module */

import { registry } from '@web/core/registry';
import { Component, onMounted, useState } from '@odoo/owl';
import { jsonrpc } from "@web/core/network/rpc_service";

export class KanbanReservationJs extends Component {
    setup() {
        this.today = new Date();
        this.state = useState({
            currentDate: this.getFormattedDate(this.today),
            activeDate: this.today,
            formattedActiveDate: this.formatDateDDMMYYYY(this.today),
            operationsCount: 0,
            models: [],
            zones: [],
            selectedModel: "",
            selectedZone: null,
            reservations: [],
            filteredReservations: [],
            selectedDate: this.getFormattedDateInput(this.today)
        });

        onMounted(async () => {
            await this.fetchZones();
            await this.fetchModels();
            await this.fetchReservationsForDate(this.today);
            document.getElementById('search-date').value = this.state.selectedDate;
            document.getElementById('search-date').addEventListener('change', (e) => this.updateSelectedDate(e));
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

    formatDateDDMMYYYY(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }

    formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${day}/${month}/${year} ${hours}:${minutes}`;
    }

    getFormattedDateInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    changeDate(days) {
        const newDate = new Date(this.state.activeDate);
        newDate.setDate(newDate.getDate() + days);

        this.state.activeDate = newDate;
        this.state.currentDate = this.getFormattedDate(newDate);
        this.state.formattedActiveDate = this.formatDateDDMMYYYY(newDate);
        this.state.selectedDate = this.getFormattedDateInput(newDate);

        document.getElementById('search-date').value = this.state.selectedDate;
        this.fetchReservationsForDate(newDate);
    }

    async fetchReservationsForDate(date) {
    try {
        const formattedDate = this.getFormattedDateInput(date);

        // Récupérer les DÉPARTS (livraisons) pour cette date
        const departures = await jsonrpc("/web/dataset/call_kw/livraison/search_read", {
            model: 'livraison',
            method: 'search_read',
            args: [[
                '&',
                ['lv_type', '=', 'livraison'],
                '&',
                ['date_heure_debut', '>=', `${formattedDate} 00:00:00`],
                ['date_heure_debut', '<=', `${formattedDate} 23:59:59`]
            ]],
            kwargs: {
                fields: [
                    'id', 'name', 'lv_type', 'date_heure_debut', 'lieu_depart',
                    'lieu_retour', 'vehicule', 'matricule', 'stage','duree_dereservation',
                    'create_date', 'livrer_par', 'modele', 'zone'
                ]
            }
        });

        // Récupérer les RETOURS (restitutions) pour cette date
        const returns = await jsonrpc("/web/dataset/call_kw/livraison/search_read", {
            model: 'livraison',
            method: 'search_read',
            args: [[
                '&',
                ['lv_type', '=', 'restitution'],
                '&',
                ['date_heure_fin', '>=', `${formattedDate} 00:00:00`],
                ['date_heure_fin', '<=', `${formattedDate} 23:59:59`]
            ]],
            kwargs: {
                fields: [
                    'id', 'name', 'lv_type', 'date_heure_debut', 'date_heure_fin', 'lieu_depart',
                    'lieu_retour', 'vehicule', 'matricule', 'stage','duree_dereservation',
                    'create_date', 'livrer_par', 'modele', 'zone'
                ]
            }
        });

        // Combiner les deux résultats
        const allReservations = [...departures, ...returns];

        this.state.reservations = allReservations;
        this.state.filteredReservations = allReservations;
        this.state.operationsCount = allReservations.length;
        this.applyFilters();
    } catch (error) {
        console.error("Erreur:", error);
    }
}

    updateSelectedDate(event) {
        const selectedDate = event.target.value;
        if (selectedDate) {
            this.state.selectedDate = selectedDate;
            const dateObj = new Date(selectedDate);
            this.state.activeDate = dateObj;
            this.state.currentDate = this.getFormattedDate(dateObj);
            this.state.formattedActiveDate = this.formatDateDDMMYYYY(dateObj);
            this.fetchReservationsForDate(dateObj);
        }
    }


    printReservations() {
        const printContent = document.querySelector('.card-container');
        if (!printContent) return;

        const printWindow = window.open('', '', 'height=600,width=800');

        printWindow.document.write('<html><head><title>Impression</title>');

        const styles = [...document.querySelectorAll('style, link[rel="stylesheet"]')];
        styles.forEach((style) => {
            printWindow.document.write(style.outerHTML);
        });

        printWindow.document.write(`
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        .entry {
            border: 1px solid #999;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
            page-break-inside: avoid; /* Cette propriété est cruciale */
            break-inside: avoid; /* Version moderne */
        }
        .entry-icon {
            font-weight: bold;
            font-size: 18px;
        }
        @media print {
            .entry {
                page-break-inside: avoid;
                break-inside: avoid;
            }
        }
    </style>
`);

        printWindow.document.write('</head><body>');
        printWindow.document.write(printContent.outerHTML);
        printWindow.document.write('</body></html>');
        printWindow.document.close();

        printWindow.focus();
        printWindow.print();
        printWindow.close();
    }

    async fetchModels() {
        try {
            const models = await jsonrpc("/web/dataset/call_kw/modele/search_read", {
                model: 'modele',
                method: 'search_read',
                args: [[]],
                kwargs: {
                    fields: ['id', 'name']
                }
            });
            this.state.models = models;
        } catch (error) {
            console.error("Erreur:", error);
        }
    }

    async fetchZones() {
        try {
            const zones = await jsonrpc("/web/dataset/call_kw/zone/search_read", {
                model: 'zone',
                method: 'search_read',
                args: [[]],
                kwargs: {
                    fields: ['id', 'name']
                }
            });
            this.state.zones = zones;
        } catch (error) {
            console.error("Erreur:", error);
        }
    }

    updateSelectedModel(event) {
        const selectedId = event.target.value;
        this.state.selectedModel = selectedId;
        this.applyFilters();
    }

    updateSelectedZone(event) {
        const selectedZone = event.target.value;
        this.state.selectedZone = selectedZone;
        this.applyFilters();
    }

    applyFilters() {
        let filtered = this.state.reservations;

        if (this.state.selectedModel) {
            filtered = filtered.filter(r => r.modele && r.modele[0] === parseInt(this.state.selectedModel));
        }

        if (this.state.selectedZone) {
            filtered = filtered.filter(r => r.zone && r.zone[0] === parseInt(this.state.selectedZone));
        }

        this.state.filteredReservations = filtered;
        this.state.operationsCount = filtered.length;
    }

    openReservationForm(reservationId) {
    const actionId = 655; // Nouvel ID de l'action (anciennement 1963)
    const menuId = 271; // Nouvel ID du menu (anciennement 1771)
    const model = 'livraison'; // Ceci reste inchangé

    window.open(
    `https://backoffice.safarelamir.com/web#id=${reservationId}&menu_id=${menuId}&action=${actionId}&model=${model}&view_type=form`,
    '_blank'
);
}
}

KanbanReservationJs.template = "kanbanreservation";
registry.category("actions").add("kanban_reservation_dashboard", KanbanReservationJs);
