# Copyright 2016-2017 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class PurchaseOrderDelegated(models.Model):

    _name = 'purchase.order.delegated'

    po_id = fields.Many2one(
        comodel_name='purchase.order',
        required=True,
        ondelete='restrict',
        index=True,
        auto_join=True,
        delegate=True,
    )
