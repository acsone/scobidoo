# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from lxml import etree

from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.exceptions import UserError, MissingError

from .event import Event
from .interpreter import Interpreter
from ..exceptions import NoTransitionError


_logger = logging.getLogger(__name__)


def _sc_make_event_allowed_field_name(event_name):
    # TODO event names must be valid python identifiers
    #      (that must be tested somewhere long before reaching this point)
    return 'sc_' + event_name + '_allowed'


class InterpreterField(fields.Field):
    type = 'sc_interpreter'


class StatechartMixin(models.AbstractModel):

    _name = 'statechart.mixin'
    _description = 'Statechart Mixin'

    # TODO if we want this to be configurable through the Odoo UI
    #      this mixin probably must go away and the register_hook
    #      must run for all models that have a statechart;
    #      this is much easier to do in Odoo 10+ by inheriting
    #      BaseModel though.
    #
    #      That said, if we get rid of this mixin, we must find
    #      a better way to cache interpreters; this is currently
    #      implemented with the sc_interpreter special field.

    sc_state = fields.Char()
    sc_interpreter = InterpreterField(
        compute='_compute_sc_interpreter')
    sc_display_state = fields.Char(
        compute='_compute_sc_display_state')

    @api.model
    def _get_statechart(self, search_parents):
        Statechart = self.env['statechart']
        statechart = Statechart.statechart_for_model(self._model._name)
        if statechart:
            return statechart
        if search_parents:
            for parent in self._inherits:
                statechart = Statechart.statechart_for_model(parent)
                if statechart:
                    return statechart
        return None

    @api.depends('sc_state')
    def _compute_sc_interpreter(self):
        statechart = self._get_statechart(search_parents=False)
        for rec in self:
            _logger.debug("initializing interpreter for %s", rec)
            initial_context = {
                'o': rec,
                # TODO: more action context
            }
            interpreter = Interpreter(
                statechart, initial_context=initial_context)
            if rec.sc_state:
                config = json.loads(rec.sc_state)
                interpreter.restore_configuration(config)
            else:
                interpreter.execute_once()
            rec.sc_interpreter = interpreter

    @api.depends('sc_state')
    def _compute_sc_display_state(self):
        # TODO
        for rec in self:
            rec.sc_display_state = rec.sc_state

    @api.multi
    def _sc_exec_event(self, event_name, *args, **kwargs):
        for rec in self:
            interpreter = rec.sc_interpreter
            event = Event(event_name, args=args, kwargs=kwargs)
            interpreter.queue(event)
            _logger.debug("=> queueing event %s for %s", event, rec)
            if not interpreter.executing:
                steps = interpreter.execute()
                _logger.debug("<= %s", steps)
                if not all([step.transitions for step in steps]):
                    # at least one step had no transition => error
                    raise NoTransitionError(
                        _("Event not allowed.\n\n"
                          "Original event: %s\nSteps: %s") %
                        (event, steps,))
                config = interpreter.save_configuration()
                new_sc_state = json.dumps(config)
                try:
                    # TODO converting to json to determine if sc_state
                    #      has changed is not optimal
                    if new_sc_state != rec.sc_state:
                        rec.write({'sc_state': new_sc_state})
                except MissingError:  # pylint: disable=except-pass
                    # object has been deleted so don't attempt to set its state
                    pass
                if len(self) == 1 and event._return:
                    return event._return

    @classmethod
    def _sc_make_event_method(cls, event_name):
        @api.multi
        def partial(self, *args, **kwargs):
            if event_name == 'write':
                vals = args[0]
                if 'sc_state' in vals:
                    if len(vals) == 1:
                        return self.write.origin(self, vals)
                    else:
                        raise UserError(_(
                            "Cannot write sc_state together "
                            "with other values."))
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
    def _sc_make_event_allowed_field(self, event_name):
        field_name = _sc_make_event_allowed_field_name(event_name)
        field = fields.Boolean(compute='_compute_sc_event_allowed')
        _logger.debug("adding field %s", field_name)
        self._add_field(field_name, field)

    @api.multi
    @api.depends('sc_state')
    def _compute_sc_event_allowed(self):
        # TODO depends() is partial (it does not know the dependencies of
        #      guards): make sure that works in all practical situations
        statechart = self._get_statechart(search_parents=False)
        if not statechart:
            return
        event_names = statechart.events_for()
        for rec in self:
            interpreter = rec.sc_interpreter
            for event_name in event_names:
                field_name = _sc_make_event_allowed_field_name(event_name)
                allowed = interpreter.is_event_allowed(event_name)
                if allowed is None:
                    # None means a guard could not be evaluated: since
                    # we don't know if it's allowed, report it as allowed
                    # and the user may receive an error message later
                    # if he tries to do the action
                    allowed = True
                setattr(rec, field_name, allowed)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        # Override fields_view_get to automatically add
        # the sc_<event>_allowed fields to form view. This is necessary
        # because the views are loaded before _register_hook so our
        # runtime-added fields are not present at that time.
        # This is also a shortcut for the developper who does
        # not need to add them manually in the views.
        # TODO we could go further and automatically make buttons
        #      that trigger events visible or not; this is a bit
        #      more (too much?) magical
        result = super(StatechartMixin, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type != 'form':
            return result
        statechart = self._get_statechart(search_parents=True)
        if not statechart:
            return result
        fields_by_name = result['fields']
        doc = etree.XML(result['arch'])
        form = doc.xpath('/form')[0]
        view = self.env['ir.ui.view'].search([('id', '=', result['view_id'])])
        for event_name in statechart.events_for():
            field_name = _sc_make_event_allowed_field_name(event_name)
            if field_name not in fields_by_name:
                fields_by_name[field_name] = {
                    'string': field_name,
                    'type': 'boolean',
                }
                new_node = etree.Element("field", {
                    "name": field_name,
                    "invisible": "1",
                })
                form.append(new_node)
                view.postprocess(result['model'], new_node, view_id, False,
                                 result['fields'], context=None)
        result['arch'] = etree.tostring(doc)
        return result


@api.model
def _sc_patch(self):
    cls = type(self)
    if getattr(cls, '_sc_patch_done', False):
        return

    if 'statechart' not in self.env:
        return

    Statechart = self.env['statechart']
    statechart = Statechart.statechart_for_model(self._model._name)
    if statechart:
        _logger.debug("_sc_patch for model %s", self._model)
        event_names = statechart.events_for()
        _logger.debug("events: %s", event_names)
        for event_name in event_names:
            self._sc_make_event_method(event_name)
            self._sc_make_event_allowed_field(event_name)

    for parent in self._inherits:
        _sc_patch(self.env[parent])
    self._add_inherited_fields()

    # in v9 this method does everything needed for the
    # additional non-stored computed fields we have added,
    # and does nothing on existing fields
    # (it has been invoked in registry.setup_models before)
    self._setup_fields(False)

    cls._sc_patch_done = True


def _register_hook(self, cr):
    res = _register_hook.origin(self, cr)
    _sc_patch(self, cr, SUPERUSER_ID)
    return res


models.BaseModel._patch_method('_register_hook', _register_hook)
