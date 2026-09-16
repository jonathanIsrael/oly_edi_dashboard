/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

export class HolaMundo extends Component {
    static template = "oly_edi_dashboard.HolaMundo";

    setup() {
        this.state = useState({ contador: 0 });
    }

    incrementar() {
        this.state.contador++;
    }
}
