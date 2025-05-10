/** @odoo-module */
import {useService} from "@web/core/utils/hooks";
import {Component, onWillStart, useState} from "@odoo/owl";
import {DateTimeInput} from "@web/core/datetime/datetime_input";

export class DateSearch extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            startDate: false,
            endDate: false
        })
    }

    onStartDateChanged(date) {
        if(date){
            this.state.startDate = this.formatDate(date)
        }else{
            this.state.startDate = false
        }
        const {
            context,
            domain
        } = this.loadContextAndDomain()
        this.env.searchModel._domain = domain
        this.env.searchModel._context = context
        this.env.searchModel.search()
    }

    formatDate(date) {
        let year = date.c.year.toString()
        let month = date.c.month.toString().padStart(2, '0'); // The month starts at 0.
        let day = date.c.day.toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    getOriginDomain(domain) {
        let data = []
        for (let item of domain) {
            if (item !== "&" && item !== "|") {
                if (item[0] !== 'create_date') {
                    data.push(item)
                }
            }
        }
        return this.removeFirstDuplicate(data)
    }

    removeFirstDuplicate(arr) {
        const seen = new Set();
        const result = [];
        for (const item of arr) {
            const key = JSON.stringify(item); // Convert array elements to strings for comparison.
            if (!seen.has(key)) {
                seen.add(key);
                result.push(item);
            }
        }
        return result;
    }

    loadContextAndDomain() {
        let domain = []
        let context = {
            ...this.props.context,
            startDate:false,
            endDate:false

        }
        if (this.state.startDate) {
            domain.push(['create_date', '>=', this.state.startDate])
            context = {
                ...this.props.context,
                startDate: this.state.startDate

            }
        }
        if (this.state.endDate) {
            domain.push(['create_date', '<=', this.state.endDate])
            context = {
                ...context,
                endDate: this.state.endDate

            }
        }
        const originDomain = this.getOriginDomain(this.props.domain)
        domain = [...domain, ...originDomain]
        return {
            domain,
            context
        }
    }

    onEndDateChanged(date) {
        if(date){
            this.state.endDate = this.formatDate(date)
        }else{
            this.state.endDate = false
        }

        const {
            context,
            domain
        } = this.loadContextAndDomain()
        this.env.searchModel._domain = domain
        this.env.searchModel._context = context
        this.env.searchModel.search()

    }

}

DateSearch.components = {DateTimeInput}
DateSearch.template = "web.DateSearch";