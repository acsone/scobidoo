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
        # force two step validation
        self.child1 = self.env['test.inherit.child1'].create(
            {'name': 'child1'})
        self.child2 = self.env['test.inherit.child2'].create(
            {'name': 'child2'})
        self.statechart_grand_parent = self.env.ref(
            'statechart_demo_purchase.statechart_grandparent_demo')
        self.statechart_grand_child2 = self.env.ref(
            'statechart_demo_purchase.statechart_child2_demo')

    def test_statechart(self):
        # check that the statechart is inherited for child1
        self.assertEqual(
            self.child1.sc_interpreter.statechart.name,
            'Statechart Grand Parents'
        )
        self.assertEqual(
            self.child2.sc_interpreter.statechart.name,
            'Statechart Child2'
        )
