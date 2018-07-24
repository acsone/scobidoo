# -*- coding: utf-8 -*-
# Copyright 2016-2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, models, fields, _
from openerp.exceptions import UserError

from .event import Event
from .statechart import parse_statechart_file
from .statechart_mixin import (
    _sc_make_event_allowed_field_name,
    StatechartMixin,
)

_logger = logging.getLogger(__name__)


class StatechartInjector(models.AbstractModel):
    """ Inject statechart in models.

    Having this in an AbstractModel that is otherwise not used,
    gives us a mechanism to run something only once on all models,
    at different stages in the registry setup process.
    """
    _name = 'statechart.injector'

    def _sc_make_event_method(self, model, event_name):
        if event_name == 'write':
            raise UserError(_("write cannot be a statechart event"))

        method = None

        @api.multi
        def partial(self, *args, **kwargs):
            event = Event(event_name, method, args, kwargs)
            return self._sc_exec_event(event)

        cls = type(model)

        try:
            method = getattr(cls, event_name)
        except AttributeError:
            _logger.debug("adding event method %s to %s", event_name, cls)
            setattr(cls, event_name, partial)
        else:
            if callable(method):
                _logger.debug(
                    "patching event method %s on %s",
                    event_name, cls,
                )
                cls._patch_method(event_name, partial)
            else:
                raise UserError(
                    _("Statechart event %s would mask "
                      "attribute %s of %s") %
                    (event_name, method, cls)
                )

    def _sc_make_event_allowed_field(self, model, event_name):
        # we add the fields in the original python class
        # so all downstream field processing done by Odoo works
        # (_inherit, _inherits in particular)
        model_cls = type(model).__bases__[0]
        field_name = _sc_make_event_allowed_field_name(event_name)
        field = fields.Boolean(
            compute='_compute_sc_event_allowed',
            readonly=True,
            store=False,
        )
        _logger.debug("adding field %s to %s", field_name, model_cls)
        setattr(model_cls, field_name, field)

    @api.model
    def _prepare_setup(self):
        """ Very early, load the statechart, and add the sc_event_allowed
        fields on the model classes provided by the developer.

        Further steps of the regular setup process will then add these fields
        on children models.
        """
        for model_name in self.env:
            model = self.env[model_name]
            model_cls = type(model).__bases__[0]
            if hasattr(model_cls, '_statechart'):
                continue
            if not hasattr(model_cls, '_statechart_file'):
                continue
            if not isinstance(model, StatechartMixin):
                _logger.warning(
                    "ignoring _statechart_file on %s that does not "
                    "inherit from statechart.mixin",
                    model_cls,
                )
            statechart = parse_statechart_file(model_cls._statechart_file)
            _logger.info(
                "storing _statechart %s on model class %s",
                statechart.name,
                model_cls,
            )
            model_cls._statechart = statechart
            for event_name in statechart.events_for():
                self._sc_make_event_allowed_field(model, event_name)
        return super(StatechartInjector, self)._prepare_setup()

    @api.model
    def _setup_complete(self):
        """ Very late, patch the event methods to invoke the statechart.

        Given the Odoo < 10 inheritance model, all children of a class
        that has a statechart are patched.
        """
        for model_name in self.env:
            model = self.env[model_name]
            cls = type(model)
            if not hasattr(cls, '_statechart'):
                continue
            model_cls = type(model).__bases__[0]
            if getattr(model_cls, '_statechart_patched', False):
                continue
            model_cls._statechart_patched = True
            statechart = model._statechart
            for event_name in statechart.events_for():
                self._sc_make_event_method(model, event_name)
        return super(StatechartInjector, self)._setup_complete()
