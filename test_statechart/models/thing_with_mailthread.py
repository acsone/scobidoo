# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models


class ThingWithMailthread(models.Model):

    _name = 'thing.with.mailthread'
    _description = "Thing with mail thread"
    _inherit = ['mail.thread', 'statechart.mixin']
    _statechart_file = 'test_statechart/models/simple_statechart.yml'
