# -*- coding: utf-8 -*-
# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class GrandParent(models.AbstractModel):
    _name = 'test.inherit.grand.parent'
    _inherit = 'statechart.mixin'
    name = fields.Char()


class Parent(models.AbstractModel):
    _inherit = 'test.inherit.grand.parent'
    _name = 'test.inherit.parent'


class Child1(models.Model):
    _name = 'test.inherit.child1'
    _inherit = 'test.inherit.parent'


class Child2(models.Model):
    _name = 'test.inherit.child2'
    _inherit = 'test.inherit.parent'
