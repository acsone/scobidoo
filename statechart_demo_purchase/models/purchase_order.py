# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):

    _inherit = ['purchase.order', 'statechart.mixin']
    _name = 'purchase.order'
    _statechart_file = \
        'statechart_demo_purchase/models/purchase_order_statechart_demo.yml'

    def raise_user_error(self):
        raise UserError(_("Some error"))

    def write(self, vals):
        if not vals.get('sc_state'):
            self.sc_queue('check_write', vals)
        return super(PurchaseOrder, self).write(vals)
