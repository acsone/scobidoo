# Copyright 2016-2017 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class GrandParent(models.AbstractModel):
    _name = "test.inherit.grand.parent"
    _description = "Test Inherit Grand Parent"
    _inherit = "statechart.mixin"

    name = fields.Char()


class Parent(models.Model):
    _inherit = "test.inherit.grand.parent"
    _name = "test.inherit.parent"
    _description = "Test Inherit Parent"
    _statechart_file = "test_statechart/models/statechart_parent_demo.yml"

    def button_parent_method(self):
        pass


class ParentOverride(models.Model):
    _inherit = "test.inherit.parent"
    _statechart_file = "test_statechart/models/statechart_parent_override_demo.yml"


class Child1(models.Model):
    _name = "test.inherit.child1"
    _description = "Test Inherit Child1"
    _inherit = "test.inherit.parent"

    def button_parent_method(self):
        return super(Child1, self).button_parent_method()


class Child2(models.Model):
    _name = "test.inherit.child2"
    _description = "Test Inherit Child2"
    _inherit = "test.inherit.parent"
    _statechart_file = "test_statechart/models/statechart_child2_demo.yml"
