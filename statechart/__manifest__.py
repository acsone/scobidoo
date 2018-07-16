# Copyright 2016-2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Statechart',
    'description': """
        Add Statecharts to Odoo models""",
    'version': '11.0.1.0.0',
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
        'views/ir_model.xml',
        'security/statechart.xml',
        'views/statechart.xml',
    ],
    'demo': [
    ],
}
