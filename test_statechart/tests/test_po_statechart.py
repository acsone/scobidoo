# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from lxml import etree

from odoo import fields
from odoo.exceptions import UserError

# AccountingTestCase runs after register_hook
from odoo.tests import common
from odoo.addons.statechart.exceptions import NoTransitionError


class TestPOStatechart(common.TransactionCase):

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
        self.assertScState(self.po.sc_state, ["draft", "root"])
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

    def test_defaults(self):
        po = self.env['purchase.order'].new()
        self.assertTrue(po.sc_do_nothing_allowed)
        self.assertTrue(po.sc_button_confirm_allowed)
        self.assertFalse(po.sc_button_cancel_allowed)

    def test_default_get(self):
        defaults = self.env['purchase.order'].default_get([
            'sc_do_nothing_allowed',
            'sc_button_confirm_allowed',
            'sc_button_cancel_allowed',
        ])
        self.assertTrue(defaults.get('sc_do_nothing_allowed'))
        self.assertTrue(defaults.get('sc_button_confirm_allowed'))
        self.assertFalse(defaults.get('sc_button_cancel_allowed'))


class TestPODelegatedStatechart(common.TransactionCase):

    def setUp(self):
        super(TestPODelegatedStatechart, self).setUp()
        self.PurchaseOrderDelegated = self.env['purchase.order.delegated']
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product_id_1 = self.env.ref('product.product_product_8')
        self.pod = self.PurchaseOrderDelegated.create({
            'partner_id': self.partner_id.id,
        })

    def test_allowed_field_delegated(self):
        # test sc_allowed field from delegate inherited parent
        self.assertTrue(self.pod.sc_do_nothing_allowed)

    def test_fields_view_get(self):
        arch = self.env['purchase.order.delegated'].fields_view_get()['arch']
        doc = etree.XML(arch)
        field = doc.xpath('//field[@name="sc_do_nothing_allowed"]')
        self.assertTrue(field)


class TestPOInheritedStatechart(common.TransactionCase):

    def setUp(self):
        super(TestPOInheritedStatechart, self).setUp()
        # force two step validation, otherwise button_confirm
        # calls button_approve which creates a reentrency error
        self.env.user.company_id.po_double_validation = 'two_step'
        self.env.user.company_id.po_double_validation_amount = 0
        self.env.user.write({
            'groups_id': [
                (3, self.env.ref('purchase.group_purchase_manager').id, False)
            ],
        })
        self.assertFalse(
            self.env.user.has_group('purchase.group_purchase_manager'))
        # create a dummy PO
        self.PurchaseOrderInherited = self.env['purchase.order.inherited']
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product_id_1 = self.env.ref('product.product_product_8')
        self.poi = self.PurchaseOrderInherited.create({
            'partner_id': self.partner_id.id,
        })

    def test_allowed_field_inherited(self):
        # test sc_allowed field from inherited parent
        self.assertTrue(self.poi.sc_do_nothing_allowed)

    def test_event_method_inherited(self):
        # check a statechart event method has been generated in child class
        self.poi.do_nothing()

    def test_patched_event_method_inherited(self):
        # sanity checks
        self.assertEqual(self.poi.amount_total, 0)
        self.assertNotIn(
            self.env.ref('purchase.group_purchase_manager'),
            self.env.user.groups_id
        )
        # check we actually go through the statechart:
        # if amount < 1000, we transition automatically
        # from confirmed to approved
        self.poi.button_confirm()
        self.assertEqual(self.poi.notes,
                         'Congrats for entering the approved state')
