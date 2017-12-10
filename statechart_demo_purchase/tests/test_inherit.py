# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# AccountingTestCase runs after register_hook
from openerp.tests import common


# run tests after install so register_hook has run
@common.at_install(False)
@common.post_install(True)
class TestInherit(common.TransactionCase):

    def setUp(self):
        super(TestInherit, self).setUp()
        self.child1 = self.env['test.inherit.child1'].create(
            {'name': 'child1'})
        self.child2 = self.env['test.inherit.child2'].create(
            {'name': 'child2'})

    def test_statechart_override(self):
        # child2 has it's own statechart, replaceing its parent's
        self.assertEqual(
            self.child2.sc_interpreter.statechart.name,
            'test.inherit.child2'
        )
        self.assertTrue(self.child2.sc_button_child2_allowed)
        self.child2.button_child2()
        # child2 does not have elements of it's parent statechart
        self.assertFalse(hasattr(self.child2, 'button_parent'))
        self.assertFalse(hasattr(self.child2, 'sc_button_parent_allowed'))

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
