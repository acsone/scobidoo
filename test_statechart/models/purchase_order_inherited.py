# -*- coding: utf-8 -*-
# Copyright 2016-2017 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models


class PurchaseOrderInherited(models.Model):

    _inherit = 'purchase.order'
    _name = 'purchase.order.inherited'
    _table = 'purchase_order'
