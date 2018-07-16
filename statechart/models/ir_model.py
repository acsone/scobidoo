# Copyright 2017-2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrModel(models.Model):

    _inherit = 'ir.model'

    statechart_id = fields.Many2one(
        'statechart',
    )

    @api.constrains('statechart_id')
    def _check_statechart_id(self):

        for rec in self.filtered(lambda a: a.statechart_id):
            if not hasattr(self.env[rec.model], '_sc_make_event_method'):
                # in a perfect world we should check if the model is an
                # instance of 'statechart.mixin' but the pythonic way to check
                # this contrains doesn't work
                # StatechartMixin = type(self.env['statechart.mixin'])
                # if no isinstance(self.env[rec.model], StatechartMixin)
                # TODO in v10, the isinstance method should work
                raise ValidationError(_(
                    "Model %s must inherit from ''statechart.mixin' "
                    "to support statecharts.") % rec.model)
