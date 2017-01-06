# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

#from datetime import datetime

from openerp import fields
from openerp.tests import common

# AccountingTestCase runs after register_hook
from openerp.addons.account.tests.account_test_classes import AccountingTestCase


class TestPOStatechart(AccountingTestCase):

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
        self.assertFalse(self.env.user.has_group('purchase.group_purchase_manager'))
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

    def test_1(self):
        self.assertEqual(self.po.sc_state, False)
        self.assertEqual(self.po.state, 'draft')
        self.po.do_nothing()
        self.assertEqual(self.po.sc_state, '["draft", "root"]')
        self.assertEqual(self.po.state, 'draft')
        # confirm does the normal Odoo stuff
        self.po.button_confirm()
        self.assertEqual(self.po.sc_state, '["confirmed", "not draft", "root"]')
        self.assertEqual(self.po.state, 'to approve')
        # do_nothing does nothing ;)
        self.po.do_nothing()
        self.assertEqual(self.po.sc_state, '["confirmed", "not draft", "root"]')
        self.assertEqual(self.po.state, 'to approve')
        # button_draft does nothing (it has guard=False)
        self.po.button_draft()
        self.assertEqual(self.po.state, 'to approve')
        # cancel resets to draft too
        self.po.button_cancel()
        self.assertEqual(self.po.sc_state, '["draft", "root"]')
        self.assertEqual(self.po.state, 'draft')

    def test_automatic_transition(self):
        # small amount => automatic approval through eventless transition
        self.po.order_line[0].product_qty = 1
        self.po.button_confirm()
        self.assertEqual(self.po.sc_state, '["approved", "not draft", "root"]')
        self.assertEqual(self.po.state, 'purchase')

    def test_no_write(self):
        self.po.button_confirm()
        self.assertEqual(self.po.sc_state, '["confirmed", "not draft", "root"]')
        self.po.write({'name': 'new ref'})
        self.assertNotEqual(self.po.name, 'new ref')
