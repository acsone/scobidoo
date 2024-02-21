# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Statechart",
    "summary": """
        Add Statecharts to Odoo models""",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/acsone/scobidoo",
    "depends": [
        "base",
    ],
    "external_dependencies": {
        "python": [
            "sismic>=1.4.1",
        ],
    },
    "data": [],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "statechart/static/src/core/errors/error_dialogs.esm.js",
        ],
    },
    "installable": True,
}
