# -*- coding: utf-8 -*-
# Copyright 2016-2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from lxml import etree

from openerp import api, fields, models, _
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

    sc_state = fields.Char(
        copy=False,
    )
    sc_interpreter = InterpreterField(
        compute='_compute_sc_interpreter')
    sc_display_state = fields.Char(
        compute='_compute_sc_display_state')

    @api.multi
    def sc_queue(self, event_name, *args, **kwargs):
        for rec in self:
            interpreter = rec.sc_interpreter
            event = Event(event_name, args=args, kwargs=kwargs)
            _logger.debug("=> queueing event %s for %s", event, rec)
            interpreter.queue(event)
            if not interpreter.executing:
                rec._sc_execute(interpreter, event)

    @api.depends('sc_state')
    def _compute_sc_interpreter(self):
        Statechart = self.env['statechart']
        statechart = Statechart.statechart_by_name(self._statechart_name)
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
    def _sc_execute(self, interpreter, orig_event):
        self.ensure_one()
        steps = interpreter.execute()
        _logger.debug("<= %s", steps)
        if not all([step.transitions for step in steps]):
            # at least one step had no transition => error
            raise NoTransitionError(
                _("This action is not allowed in the current state "
                  "or with your access rights.\n\n"
                  "Technical details of the error: %s\nSteps: %s") %
                (orig_event, steps,))
        config = interpreter.save_configuration()
        new_sc_state = json.dumps(config)
        try:
            # TODO converting to json to determine if sc_state
            #      has changed is not optimal
            if new_sc_state != self.sc_state:
                self.write({'sc_state': new_sc_state})
        except MissingError:  # pylint: disable=except-pass
            # object has been deleted so don't attempt to set its state
            pass

    @api.multi
    def _sc_exec_event(self, event_name, *args, **kwargs):
        for rec in self:
            interpreter = rec.sc_interpreter
            if not interpreter.executing:
                event = Event(event_name, args=args, kwargs=kwargs)
                _logger.debug("=> queueing event %s for %s", event, rec)
                interpreter.queue(event)
                rec._sc_execute(interpreter, event)
                if len(self) == 1 and event._return:
                    return event._return
            else:
                event = Event(event_name, args=args, kwargs=kwargs)
                msg = _(
                    "Reentrancy error for %s on %s. "
                    "Please use sc_queue() "
                    "instead of a direct method call. "
                ) % (event, rec)
                raise RuntimeError(msg)
        return None

    @classmethod
    def _sc_make_event_method(cls, event_name):
        if event_name == 'write':
            raise UserError(_("write cannot be a statechart event"))

        @api.multi
        def partial(self, *args, **kwargs):
            return self._sc_exec_event(event_name, *args, **kwargs)

        try:
            m = getattr(cls, event_name)
        except AttributeError:
            _logger.debug("adding event method %s to class %s",
                          event_name, cls)
            setattr(cls, event_name, partial)
        else:
            if callable(m):
                _logger.debug("patching event method %s on class %s",
                              event_name, cls)
                cls._patch_method(event_name, partial)
            else:
                raise UserError(
                    _("Statechart event %s would mask "
                      "attribute %s of class %s") %
                    (event_name, m, cls))

    @api.model
    def _sc_make_event_allowed_field(self, event_name, default):
        field_name = _sc_make_event_allowed_field_name(event_name)
        field = fields.Boolean(
            compute='_compute_sc_event_allowed',
            default=default,
            readonly=True,
            store=False,
        )
        _logger.debug("adding field %s to %s", field_name, self)
        self._add_field(field_name, field)

    @api.depends('sc_state')
    def _compute_sc_event_allowed(self):
        # TODO depends() is partial (it does not know the dependencies of
        #      guards): make sure that works in all practical situations
        Statechart = self.env['statechart']
        statechart = Statechart.statechart_by_name(self._statechart_name)
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
        Statechart = self.env['statechart']
        statechart = Statechart.statechart_by_name(self._statechart_name)
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
                                 result['fields'])
        result['arch'] = etree.tostring(doc)
        return result

    @api.model
    def create(self, vals):
        rec = super(StatechartMixin, self).create(vals)
        # make sure the interpreter is initialized, because
        # merely entering the root state may have side effects
        # (onentry, etc) and we don't want that to occur
        # more than once
        config = rec.sc_interpreter.save_configuration()
        rec.sc_state = json.dumps(config)
        return rec


class StatechartInjector(models.AbstractModel):
    """ Inject statechart logic in all models that need one.

    This is done as an abstract model, as a trick to have something
    executed exactly once at the end of registry initialization.
    """

    _inherit = 'base'
    _name = 'statechart.injector'

    @api.model_cr
    def _register_hook(self):
        Statechart = self.env['statechart']
        statechart_name_by_model = {}
        for statechart in Statechart.search([]):
            for model in statechart.model_ids.mapped('model'):
                statechart_name_by_model[model] = statechart.name

        done = set()

        def patch(model):
            if model in done:
                return
            done.add(model)
            Model = self.env[model]
            # patch parents first (if not done yet)
            parents = []
            if isinstance(Model._inherit, basestring):
                parents.append(Model._inherit)
            elif Model._inherit:
                parents.extend(Model._inherit)
            parents.extend(Model._inherits.keys())
            for parent in parents:
                patch(parent)
            # make/patch event methods on models that have a statechart,
            # they will be inherited
            statechart_name = statechart_name_by_model.get(model)
            if not statechart_name:
                return
            if not isinstance(Model, StatechartMixin):
                _logger.error(
                    "Statechart %s for model %s ignored because "
                    "it does not inherit from StatechartMixin.",
                    statechart_name, model,
                )
                return
            if hasattr(Model, '_statechart_name'):
                _logger.error(
                    "Statechart %s for model %s ignored because "
                    "one of it's parent models already has a "
                    "statechart (%s).",
                    statechart_name, model, Model._statechart_name,
                )
                return
            # now let's patch the model
            _logger.info(
                "Patching model %s with statechart %s",
                model, statechart_name,
            )
            Model.__class__._statechart_name = statechart_name
            statechart = Statechart.statechart_by_name(statechart_name)
            event_names = statechart.events_for()
            _logger.debug("events: %s", event_names)
            # add/patch event method
            for event_name in event_names:
                Model._sc_make_event_method(event_name)
            # add sc_event_allowed fields
            dummy = Model.new()
            dummy_interpreter = dummy.sc_interpreter
            models_to_add_fields = [Model]
            # we need to add sc_event_allowed fields to _inherit children
            # they will be added on _inherits children later with
            # _add_inherited_fields()
            for m in Model._inherit_children:
                models_to_add_fields.append(self.env[m])
            for event_name in event_names:
                # This computation of a default value for the sc_event_allowed
                # fields is necessary because the web ui issues a default_get
                # call when opening a form in create mode instead of doing
                # a new() then reading the fields.
                # CAUTION: because this initialization of the interpreter
                # implies executing the transition to the initial state,
                # it is very important that anything this transition does
                # is idempotent (ie it's associated action, and the on_entry
                # of the initial state must not have side effects) - this
                # is good practice anyway.
                default = dummy_interpreter.is_event_allowed(event_name)
                for m in models_to_add_fields:
                    m._sc_make_event_allowed_field(event_name, default)

        for model in self.env:
            patch(model)
            self.env[model]._add_inherited_fields()
            self.env[model]._setup_fields(False)
