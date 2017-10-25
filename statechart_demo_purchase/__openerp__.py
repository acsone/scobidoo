# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Statechart Demo Purchase',
    'description': """
        Statechart demo and tests""",
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': [
        'purchase',
        'statechart',
    ],
    'data': [
        'views/purchase_order.xml',
    ],
    'demo': [
        'demo/statechart.xml',
    ],
}
