# Copyright 2017-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# AccountingTestCase runs after register_hook
from odoo.tests import common

from odoo.addons.statechart.exceptions import NoTransitionError


class TestInherit(common.TransactionCase):

    def setUp(self):
        super(TestInherit, self).setUp()
        self.parent = self.env['test.inherit.parent'].create(
            {'name': 'parent'})
        self.child1 = self.env['test.inherit.child1'].create(
            {'name': 'child1'})
        self.child2 = self.env['test.inherit.child2'].create(
            {'name': 'child2'})

    def test_statechart_override_1(self):
        # model test.inherit.child2 has it's own statechart,
        # replacing its parent's
        self.assertEqual(
            self.child2.sc_interpreter.statechart.name,
            'test.inherit.child2'
        )
        self.assertTrue(self.child2.sc_button_child2_allowed)
        self.child2.button_child2()
        # child2 does have elements of it's parent statechart
        # but they are disabled because they are not in child2's statechart
        self.assertFalse(self.child2.sc_button_parent_allowed)
        with self.assertRaises(NoTransitionError):
            self.child2.button_parent()

    def test_statechart_override_2(self):
        # model test.inherit.parent has been overridden by,
        # a subclass that adds event button_parent_override
        self.parent.button_parent_override()
        self.child1.button_parent_override()
        with self.assertRaises(NoTransitionError):
            self.child2.button_parent_override()

    def test_statechart_inherit(self):
        # check that the statechart is inherited for child1
        self.assertEqual(
            self.child1.sc_interpreter.statechart.name,
            'test.inherit.parent'
        )
        self.assertTrue(self.child1.sc_button_parent_allowed)
        self.child1.button_parent()
        # child1 must not have elements of child2's statechart
        self.assertFalse(hasattr(self.child1, 'button_child2'))
        self.assertFalse(hasattr(self.child1, 'sc_button_child2_allowed'))

    def test_statechart_inherit_double_patch(self):
        self.parent.button_parent()
        self.child1.button_parent()
        self.parent.button_parent_method()
        self.child1.button_parent_method()
