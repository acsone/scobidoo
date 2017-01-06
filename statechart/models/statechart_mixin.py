# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from contextlib import contextmanager
import logging

from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.exceptions import UserError

from .interpreter import Interpreter, Event


_logger = logging.getLogger(__name__)


# TODO this is a quick hack 
#      better idea is to bind the interpreter
#      to a custom field type, or to use
#      the Odoo ORM cache

_interpreters = {}  # record: interpreter

@contextmanager
def _interpreter_for(rec):
    if rec in _interpreters:
        yield _interpreters[rec]
    else:
        Statechart = rec.env['statechart']
        statechart = Statechart.statechart_for_model(rec._model._name)
        action_context = {
            'o': rec,
            # TODO: more action context
        }
        interpreter = Interpreter(
            statechart, initial_context=action_context)
        if rec.sc_state:
            interpreter.restore_configuration(rec.sc_state)
        _interpreters[rec] = interpreter
        try:
            yield interpreter
            new_sc_state = interpreter.save_configuration()
            if new_sc_state != rec.sc_state:
                rec.sc_state = new_sc_state
        finally:
            del _interpreters[rec]
    

class StatechartMixin(models.AbstractModel):

    _name = 'statechart.mixin'
    _description = 'Statechart Mixin'

    # TODO if we want this to be configurable through the Odoo UI
    #      this mixin probably must go away and the register_hook
    #      must run for all models that have a statechart

    sc_state = fields.Char()
    sc_display_state = fields.Char(
        compute='_compute_sc_display_state')

    @api.depends('sc_state')
    def _compute_sc_display_state(self):
        # TODO
        for rec in self:
            rec.sc_display_state = rec.sc_state

    def _sc_exec_event(self, event_name, *args, **kwargs):
        for rec in self:
            with _interpreter_for(rec) as interpreter:
                event = Event(event_name, args=args, **kwargs)
                interpreter.queue(event)
                _logger.debug("=> queueing event %s for %s", event_name, rec)
                if not interpreter.executing:
                    steps = interpreter.execute()
                    _logger.debug("<= %s", steps)
                    # TODO UserError if nothing done (unhandled event)
                # TODO return value

    @classmethod
    def _sc_make_event_method(cls, event_name):
        @api.multi
        def partial(self, *args, **kwargs):
            return self._sc_exec_event(event_name, *args, **kwargs)
        try:
            m = getattr(cls, event_name)
        except AttributeError:
            _logger.debug("adding event method %s", event_name)
            setattr(cls, event_name, partial)
        else:
            if callable(m):
                _logger.debug("patching event method %s", event_name)
                cls._patch_method(event_name, partial)
            else:
                raise UserError(
                    _("Statechart event %s would mask "
                      "attribute %s of class %s") %
                    (event_name, m, cls))

    @api.model
    def _sc_patch(self):
        Statechart = self.env['statechart']
        statechart = Statechart.statechart_for_model(self._model._name)
        if not statechart:
            return
        event_names = statechart.events_for()
        _logger.debug("events: %s", event_names)
        for event_name in event_names:
            self._sc_make_event_method(event_name)

    # TODO convert to @api.model_cr in v10
    def _register_hook(self, cr):
        super(StatechartMixin, self)._register_hook(cr)
        _logger.debug("StatechartMixin register hook for model %s",
                      self._model)
        self._sc_patch(cr, SUPERUSER_ID)
