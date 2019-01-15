# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class ThingWithMailthread(models.Model):

    _name = 'thing.with.mailthread'
    _description = "Thing with mail thread"
    _inherit = ['mail.thread', 'statechart.mixin']
    _statechart_file = 'statechart_demo_purchase/models/simple_statechart.yml'
