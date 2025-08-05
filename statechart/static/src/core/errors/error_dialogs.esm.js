import {WarningDialog, odooExceptionTitleMap} from "@web/core/errors/error_dialogs";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

registry
    .category("error_dialogs")
    .add("odoo.addons.statechart.exceptions.NoTransitionError", WarningDialog);

odooExceptionTitleMap["odoo.addons.statechart.exceptions.NoTransitionError"] =
    _t("Transition Error");
