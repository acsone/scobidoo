# -*- coding: utf-8 -*-
# Copyright 2016-2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import logging

from sismic.exceptions import StatechartError
from sismic import io as sismic_io

from openerp import api, fields, models
from openerp import tools

_logger = logging.getLogger(__name__)


class Statechart(models.Model):

    _name = 'statechart'
    _description = 'Statechart'

    name = fields.Char(
        readonly=True,
        store=True,
        compute='_compute_name',
    )
    model_ids = fields.One2many(
        comodel_name='ir.model',
        inverse_name='statechart_id',
        string='Models',
        ondelete='restrict',
    )
    yaml = fields.Text(
        help="YAML representation of the state chart."
             "Currently it is the input, to become a computed field "
             "from a future record-based representation of "
             "the statechart.",
    )

    _sql_constraint = [
        ('unique_name',
         'unique(name)',
         u'Statechart name must be unique')
    ]

    @api.depends('yaml')
    def _compute_name(self):
        for rec in self:
            rec.name = self.parse_statechart(rec.yaml).name

    @api.model
    def parse_statechart(self, yaml):
        with io.StringIO(yaml) as f:
            try:
                statechart = sismic_io.import_from_yaml(f)
                _logger.debug("loaded statechart %s", statechart.name)
                return statechart
            except StatechartError:
                _logger.error("error loading statechart", exc_info=True)
                raise

    @api.model
    @tools.ormcache('name')
    def statechart_by_name(self, name):
        """Load and parse the statechart for an Odoo model."""
        # Use SQL because when this is called, this statechart model
        # may not be fully initialized.
        self.env.cr.execute(
            """SELECT yaml FROM statechart WHERE name=%s""",
            (name, )
        )
        r = self.env.cr.fetchone()
        if not r:
            raise RuntimeError("Statechart named %s not found" % name)
        yaml, = r
        _logger.debug(
            "loading statechart named %s...", name,
        )
        return self.parse_statechart(yaml)

    @api.model
    @tools.ormcache('model_name')
    def statechart_for_model(self, model_name):
        """Load and parse the statechart for an Odoo model.

        Return the sismic statechart object or None if there
        is no statechart defined for this model.
        """
        # Use SQL because when this is called, this statechart model
        # may not be fully initialized.
        self.env.cr.execute(
            """
            SELECT statechart.name, statechart.yaml
            FROM ir_model, statechart
            WHERE statechart.id=ir_model.statechart_id
              AND ir_model.model=%s
            """,
            (model_name, )
        )
        r = self.env.cr.fetchone()
        if not r:
            return None
        name, yaml = r
        _logger.debug(
            "loading statechart %s for model %s...", name, model_name,
        )
        return self.parse_statechart(yaml)

    @api.multi
    def write(self, vals):
        self.statechart_by_name.clear_cache(self)
        self.statechart_for_model.clear_cache(self)
        return super(Statechart, self).write(vals)

    @api.multi
    def unlink(self):
        self.statechart_by_name.clear_cache(self)
        self.statechart_for_model.clear_cache(self)
        return super(Statechart, self).unlink()
