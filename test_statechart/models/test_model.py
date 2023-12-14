# Copyright 2016-2017 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class TestModel(models.Model):
    _name = 'scobidoo.test.model'
    _description = 'Scobidoo Test Model'
    _inherit = 'statechart.mixin'
    _statechart_file = 'test_statechart/models/test_statechart.yml'

    amount = fields.Float()
