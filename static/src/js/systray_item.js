/** @odoo-module **/

import { registry } from "@web/core/registry";
import { HolaMundo } from "./hola_mundo";

registry.category("systray").add("oly_edi_dashboard.HolaMundo", {
    Component: HolaMundo,
}, { sequence: 1 });