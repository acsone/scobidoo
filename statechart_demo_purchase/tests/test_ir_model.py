# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.exceptions import ValidationError

# AccountingTestCase runs after register_hook
from openerp.tests import common


# run tests after install so register_hook has run
@common.at_install(False)
@common.post_install(True)
class TestIrModel(common.TransactionCase):

    def setUp(self):
        super(TestIrModel, self).setUp()
        # force two step validation
        self.env.user.company_id.po_double_validation = 'two_step'
        self.statechart = self.env.ref(
            'statechart_demo_purchase.purchase_order_statechart_demo')
        self.ir_model_purchase = self.env.ref('purchase.model_purchase_order')
        self.ir_model_partner = self.env.ref('base.model_res_partner')

    def test_constrains(self):
        # check that a statechart can only be associated to a model that
        # inherit from statechart.mixin
        self.ir_model_purchase.write({
            'statechart_id': False})
        self.ir_model_purchase.write({
            'statechart_id': self.statechart.id})
        self.assertEqual(
            self.ir_model_purchase.statechart_id, self.statechart)
        with self.assertRaises(ValidationError):
            self.ir_model_partner.statechart_id = self.statechart
