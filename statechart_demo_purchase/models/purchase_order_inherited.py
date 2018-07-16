# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrderInherited(models.Model):

    _inherit = 'purchase.order'
    _name = 'purchase.order.inherited'
