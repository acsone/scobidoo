# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Statechart Demo Purchase',
    'description': """
        Statechart demo and tests""",
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': [
        'purchase',
        'statechart',
    ],
    'data': [
        'views/purchase_order.xml',
        'security/purchase_order_delegated.xml',
        'security/thing_with_mailthread.xml',
    ],
    'demo': [
    ],
}
