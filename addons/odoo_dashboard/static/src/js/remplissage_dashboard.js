/** @odoo-module */

import {registry} from '@web/core/registry'

const {Component, onMounted, useState, useRef} = owl

import {jsonrpc} from "@web/core/network/rpc_service"
import {useService} from "@web/core/utils/hooks";

export class RemplissagetDashboard extends Component {

    setup() {
        this.action = useService("action")
        this.remplissage_chart = useRef("remplissage_chart")
        this.champ1 = useRef("champ1");
        this.state = useState({
            zones: [],
            categories: [],
            models: []
        });

        onMounted(this.onMounted);
    }

    async onMounted() {
        await this.fetchZones();
        await this.fetchCategorie();
        await this.fetchModele();
        await this.render_remplissage_chart();

        this.setTodayDateToChamp1();

    }

    async fetchModele() {
        const models = await jsonrpc("/web/dataset/call_kw/reservation/get_all_modele", {
            model: 'reservation',
            method: 'get_all_modele',
            args: [{}],
            kwargs: {}
        });

        this.state.models = models.map(modele => ({ id: modele.id, name: modele.name }));


    }


    async fetchCategorie() {
        const categories = await jsonrpc("/web/dataset/call_kw/reservation/get_all_categories", {
            model: 'reservation',
            method: 'get_all_categories',
            args: [{}],
            kwargs: {}
        });

        this.state.categories = categories.map(categorie => ({ id: categorie.id, name: categorie.name }));


    }


    async fetchZones() {
        const zones = await jsonrpc("/web/dataset/call_kw/reservation/get_all_zones", {
            model: 'reservation',
            method: 'get_all_zones',
            args: [{}],
            kwargs: {}
        });

        this.state.zones = zones.map(zone => ({ id: zone.id, name: zone.name }));

    }

    async render_remplissage_chart(){
        var result_data = await this.fetchRemplissageChart()
        var $remplissage_chart_bar = $(this.remplissage_chart.el)
        var bar_data = this.prepareChartData(result_data)
        var options_data  = {}
        this.createChart($remplissage_chart_bar,"bar",bar_data)
    }

    fetchRemplissageChart(){
        return jsonrpc("web/dataset/call_kw/reservation/remplissage_action_chart", {
            model: 'reservation',
            method: 'remplissage_action_chart',
            args: [{}],
            kwargs: {}
        });
    }


    prepareChartData(result_data) {
        const labels = result_data[1]
        const data = result_data[0]
        const colors = generateDynamicColors(labels.length)
        return {
            labels: labels,
            datasets: [
                {
                    label: "Pourcentage",
                    data: data,
                    backgroundColor: colors,
                    borderColor: colors.map(color => color.replace('50%', '40%')),
                    borderWidth:3
                }
            ]
        }
    }


    createChart(element, type, data, options={}) {
        new Chart(element, {
            type: type,
            data: data,
            options : options
        })
    }

     setTodayDateToChamp1() {
        const today = this.getTodayDate();
        if (this.champ1.el) {
            this.champ1.el.value = today;
        }
    }

    // Fonction utilitaire pour obtenir la date d'aujourd'hui au format YYYY-MM-DD
    getTodayDate() {
        const today = new Date();
        const day = String(today.getDate()).padStart(2, '0');
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const year = today.getFullYear();
        return `${year}-${month}-${day}`;
    }



}

RemplissagetDashboard.template = "RemplissageDashBoardMain"
registry.category("actions").add("remplissage_dashboard_main", RemplissagetDashboard)