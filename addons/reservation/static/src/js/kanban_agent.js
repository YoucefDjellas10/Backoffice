/* @odoo-module */

import { registry } from '@web/core/registry';
import { Component, onMounted, useState } from '@odoo/owl';
import { jsonrpc } from "@web/core/network/rpc_service";

class KanbanAgentJs extends Component {
    setup() {
        this.isAgent = false;
        this.userId = null;
        this.userZones = [];

        this.today = new Date();
        this.state = useState({
            currentDate: this.getFormattedDate(this.today),
            activeDate: this.today,
            formattedActiveDate: this.formatDateDDMMYYYY(this.today),
            operationsCount: 0,
            models: [],
            selectedModel: "",
            reservations: [],
            filteredReservations: [],
            selectedDate: this.getFormattedDateInput(this.today),
            accessDenied: false,
            userInfo: null
        });

        onMounted(async () => {
            try {
                const user = await jsonrpc("/web/session/get_session_info", {});
                this.userId = user.uid;
                this.state.userInfo = user;

                // Récupérer les zones de l'utilisateur
                const zones = await jsonrpc("/web/dataset/call_kw/res.users/read", {
                    model: 'res.users',
                    method: 'read',
                    args: [[this.userId], ['zone_ids']],
                    kwargs: { context: {} }
                });

                this.userZones = zones[0].zone_ids || [];

                const isAgent = await jsonrpc("/web/dataset/call_kw/res.users/has_group", {
                    model: 'res.users',
                    method: 'has_group',
                    args: ['access_rights_groups.group_agent'],
                    kwargs: { context: {} }
                });

                this.isAgent = isAgent;

                if (!this.isAgent) {
                    this.state.accessDenied = true;
                    return;
                }

                await this.fetchModels();
                await this.fetchReservationsForDate(this.today);
                document.getElementById('search-date').value = this.state.selectedDate;
                document.getElementById('search-date').addEventListener('change', (e) => this.updateSelectedDate(e));
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

    // Vérifier qu'on ne dépasse pas +3/-3 jours par rapport à aujourd'hui
    const today = new Date();
    const diffDays = Math.floor((newDate - today) / (1000 * 60 * 60 * 24));

    if (diffDays < -3 || diffDays > 3) {
        return; // Bloquer la navigation au-delà de 3 jours
    }

    // Le reste reste identique
    this.state.activeDate = newDate;
    this.state.currentDate = this.getFormattedDate(newDate);
    this.state.formattedActiveDate = this.formatDateDDMMYYYY(newDate);
    this.state.selectedDate = this.getFormattedDateInput(newDate);
    document.getElementById('search-date').value = this.state.selectedDate;
    this.fetchReservationsForDate(newDate);
}
    isDateNavigationDisabled(days) {
    const testDate = new Date(this.state.activeDate);
    testDate.setDate(testDate.getDate() + days);
    const today = new Date();
    const diffDays = Math.floor((testDate - today) / (1000 * 60 * 60 * 24));
    return diffDays < -3 || diffDays > 3;
}
    async fetchReservationsForDate(date) {
        try {
            const formattedDate = this.getFormattedDateInput(date);
            const today = new Date();
            const diffDays = Math.floor((date - today) / (1000 * 60 * 60 * 24));

            const domain = [
                '&',
                ['lv_type', 'in', ['livraison', 'restitution']],
                '&',
                ['action_date', '>=', `${formattedDate} 00:00:00`],
                ['action_date', '<=', `${formattedDate} 23:59:59`],

            ];


//            if (diffDays < 0) {
//                domain.push(['stage', '!=', 'livre']);
//            }

            const reservations = await jsonrpc("/web/dataset/call_kw/livraison/search_read", {
                model: 'livraison',
                method: 'search_read',
                args: [domain],
                kwargs: {
                    fields: [
                        'id', 'name', 'lv_type', 'date_heure_debut', 'date_heure_fin', 'lieu_depart',
                        'lieu_retour', 'vehicule', 'matricule', 'stage', 'duree_dereservation',
                        'create_date', 'livrer_par', 'modele', 'zone','date_de_livraison',
                        'opt_protection', 'opt_carburant', 'siege_bebe', 'action_date'
                    ],
                    order: 'action_date asc'
                }
            });

            this.state.reservations = reservations;
            this.state.filteredReservations = reservations;
            this.state.operationsCount = reservations.length;
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
                    page-break-inside: avoid;
                    break-inside: avoid;
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
            this.state.models = models || [];
        } catch (error) {
            console.error("Erreur:", error);
            this.state.models = [];
        }
    }

    updateSelectedModel(event) {
        const selectedId = event.target.value;
        this.state.selectedModel = selectedId;
        this.applyFilters();
    }

    applyFilters() {
        let filtered = this.state.reservations || [];

        if (this.state.selectedModel) {
            filtered = filtered.filter(r => r.modele && r.modele[0] === parseInt(this.state.selectedModel));
        }

        this.state.filteredReservations = filtered;
        this.state.operationsCount = filtered.length;
    }

    openReservationForm(reservationId) {
        const actionId = 655;
        const menuId = 271;
        const model = 'livraison';

        window.open(
            `https://backoffice.safarelamir.com/web#id=${reservationId}&menu_id=${menuId}&action=${actionId}&model=${model}&view_type=form`,
            '_blank'
        );
    }
}

KanbanAgentJs.template = "kanbanagent";
registry.category("actions").add("kanban_agent_dashboard", KanbanAgentJs);
