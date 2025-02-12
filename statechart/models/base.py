# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class Base(models.AbstractModel):
    """The base model, which is implicitly inherited by all models.

    Restore the _patch_method removed in Odoo 18
    """

    _inherit = "base"

    @classmethod
    def _patch_method(cls, name, method):
        origin = getattr(cls, name)
        method.origin = origin
        # propagate decorators from origin to method, and apply api decorator
        wrapped = api.propagate(origin, method)
        wrapped.origin = origin
        setattr(cls, name, wrapped)
