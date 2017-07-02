# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from openerp import fields
from openerp.exceptions import UserError

# AccountingTestCase runs after register_hook
from openerp.addons.account.tests.account_test_classes \
    import AccountingTestCase
from openerp.addons.statechart.exceptions import NoTransitionError


class TestPOStatechart(AccountingTestCase):

    def assertScState(self, sc_state, expected_config):
        if not expected_config:
            self.assertFalse(sc_state)
        else:
            config = json.loads(sc_state)
            self.assertEqual(set(config['configuration']),
                             set(expected_config))

    def setUp(self):
        super(TestPOStatechart, self).setUp()
        # force two step validation
        self.env.user.company_id.po_double_validation = 'two_step'
        self.env.user.company_id.po_double_validation_amount = 0
        self.env.user.write({
            'groups_id': [
                (3, self.env.ref('purchase.group_purchase_manager').id, False)
            ],
        })
        self.assertFalse(
            self.env.user.has_group('purchase.group_purchase_manager'))
        # create a PO
        self.PurchaseOrder = self.env['purchase.order']
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product_id_1 = self.env.ref('product.product_product_8')
        self.po = self.PurchaseOrder.create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_id_1.name,
                    'product_id': self.product_id_1.id,
                    'product_qty': 5.0,
                    'product_uom': self.product_id_1.uom_po_id.id,
                    'price_unit': 500.0,
                    'date_planned': fields.Date.today(),
                }),
            ],
        })
        self.po2 = self.PurchaseOrder.create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_id_1.name,
                    'product_id': self.product_id_1.id,
                    'product_qty': 5.0,
                    'product_uom': self.product_id_1.uom_po_id.id,
                    'price_unit': 500.0,
                    'date_planned': fields.Date.today(),
                }),
            ],
        })

    def test_1(self):
        self.assertScState(self.po.sc_state, False)
        self.assertEqual(self.po.state, 'draft')
        self.assertTrue(self.po.sc_do_nothing_allowed)
        self.assertTrue(self.po.sc_button_confirm_allowed)
        self.assertFalse(self.po.sc_button_approve_allowed)
        self.assertFalse(self.po.sc_button_cancel_allowed)
        self.assertFalse(self.po.sc_button_draft_allowed)
        self.po.do_nothing()
        self.assertScState(self.po.sc_state, ["draft", "root"])
        self.assertEqual(self.po.state, 'draft')
        # confirm does the normal Odoo stuff
        self.po.button_confirm()
        self.assertScState(self.po.sc_state,
                           ["confirmed", "not draft", "root"])
        self.assertEqual(self.po.state, 'to approve')
        self.assertEqual(self.po.notes, 'Congrats for exiting the draft state')
        # do_nothing does nothing ;)
        self.po.do_nothing()
        self.assertScState(self.po.sc_state,
                           ["confirmed", "not draft", "root"])
        self.assertEqual(self.po.state, 'to approve')
        self.assertTrue(self.po.sc_button_approve_allowed)
        # button_draft does nothing (it has guard=False)
        with self.assertRaises(NoTransitionError):
            self.po.button_draft()
        # cancel resets to draft too
        self.po.button_cancel()
        self.assertScState(self.po.sc_state,
                           ["draft", "root"])
        self.assertEqual(self.po.state, 'draft')

    def test_automatic_transition(self):
        # small amount => automatic approval through eventless transition
        self.po.order_line[0].product_qty = 1
        self.assertFalse(self.po.sc_button_approve_allowed)
        self.po.button_confirm()
        self.assertScState(self.po.sc_state,
                           ["approved", "not draft", "root"])
        self.assertEqual(self.po.state, 'purchase')
        # TODO this test is currently failing because _compute_sc_interpreter
        #      create a new interpreter instance while another one is already
        #      executing for the same record... need to find something better
        #      than a computed field to manage the lifecycle of interpreter
        #      instances
        self.assertEqual(self.po.notes,
                         'Congrats for entering the approved state')
        self.assertFalse(self.po.sc_button_approve_allowed)

    def test_no_write(self):
        self.po.button_confirm()
        self.assertScState(self.po.sc_state,
                           ["confirmed", "not draft", "root"])
        with self.assertRaises(NoTransitionError):
            self.po.write({'name': 'new ref'})

    def test_two_interpreters(self):
        self.po.button_confirm()
        self.assertScState(self.po.sc_state,
                           ["confirmed", "not draft", "root"])
        self.po2.button_confirm()
        self.assertScState(self.po2.sc_state,
                           ["confirmed", "not draft", "root"])

    def test_return(self):
        res = self.po.compute_something()
        self.assertEqual(res, 'something')

    def test_unlink(self):
        po_id = self.po.id
        self.po.unlink()
        self.assertFalse(self.PurchaseOrder.search([('id', '=', po_id)]))

    def test_deep_user_error(self):
        with self.assertRaises(UserError):
            self.po.raise_user_error()
