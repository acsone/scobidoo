/** @odoo-module **/

import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

import {WarningDialog, odooExceptionTitleMap} from "@web/core/errors/error_dialogs";

registry
    .category("error_dialogs")
    .add("odoo.addons.statechart.exceptions.NoTransitionError", WarningDialog);

odooExceptionTitleMap["odoo.addons.statechart.exceptions.NoTransitionError"] =
    _lt("Transition Error");
