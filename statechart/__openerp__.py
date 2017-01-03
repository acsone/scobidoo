# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Statechart',
    'summary': """
        Add Statecharts to Odoo models""",
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': [
            'sismic',
        ],
    },
    'data': [
        'security/statechart.xml',
        'views/statechart.xml',
    ],
    'demo': [
    ],
}
