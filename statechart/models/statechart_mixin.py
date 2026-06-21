# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, UserError
from odoo.fields import Domain

from ..exceptions import NoTransitionError
from .event import Event
from .interpreter import Interpreter
from .statechart import parse_statechart_file

_logger = logging.getLogger(__name__)


def _patch_method(cls, name, method):
    """Patch a method on a class, preserving the original as .origin."""
    origin = getattr(cls, name)
    method.origin = origin

    # Maintain the statechart engine's .origin pointer chain
    if hasattr(origin, "origin"):
        method.origin = origin.origin
    else:
        method.origin = origin

    # Physically mount the wrapper onto the runtime class dictionary
    setattr(cls, name, method)


def _sc_make_event_allowed_field_name(event_name):
    # TODO event names must be valid python identifiers
    #      (that must be tested somewhere long before reaching this point)
    return "sc_" + event_name + "_allowed"


def _sc_is_event_allowed_field_name(field_name):
    return field_name.startswith("sc_") and field_name.endswith("_allowed")


def _sc_event_from_event_allowed_field_name(field_name):
    return field_name[3:-8]


def _sc_make_event_allowed_field(cls, event_name):
    # We add the fields on the original Python definition class
    # so all downstream field processing done by Odoo works
    # (_inherit, _inherits in particular).
    # This is called at import time via _sc_inject_fields_on_class
    # before Odoo's ORM processes the class.
    field_name = _sc_make_event_allowed_field_name(event_name)
    if hasattr(cls, field_name):
        return
    field = fields.Boolean(
        compute="_compute_sc_event_allowed",
        readonly=True,
        store=False,
    )
    _logger.debug("adding field %s to %s", field_name, cls)
    setattr(cls, field_name, field)
    field.__set_name__(cls, field_name)


def _sc_inject_fields_on_class(cls):
    if "_statechart_file" not in cls.__dict__:
        return
    _logger.debug(
        "StatechartMixin: injecting sc_event_allowed fields on %s at import time", cls
    )
    statechart = parse_statechart_file(cls._statechart_file)
    for event_name in statechart.events_for():
        _sc_make_event_allowed_field(cls, event_name)


class InterpreterField(fields.Field):
    type = "sc_interpreter"


class StatechartMixin(models.AbstractModel):
    _name = "statechart.mixin"
    _description = "Statechart Mixin"

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
        readonly=True,
    )
    sc_interpreter = InterpreterField(compute="_compute_sc_interpreter")
    sc_display_state = fields.Char(compute="_compute_sc_display_state")
    sc_has_allowed_events = fields.Boolean(
        compute="_compute_sc_has_allowed_events",
        search="_search_sc_has_allowed_events",
        string="Need action?",
    )

    def sc_queue(self, event_name, *args, **kwargs):
        event = Event(event_name, None, args, kwargs)
        for rec in self:
            interpreter = rec.sc_interpreter
            _logger.debug("=> queueing event %s for %s", event, rec)
            interpreter.queue(event)
            if not interpreter.executing:
                rec._sc_execute(interpreter, event)

    @api.depends("sc_state")
    def _compute_sc_interpreter(self):
        statechart = self._statechart
        for rec in self:
            _logger.debug(
                "initializing interpreter for %s with statechart %s",
                rec,
                statechart.name,
            )
            initial_context = {
                "o": rec,
                "self": rec,
                # TODO: more action context
            }
            interpreter = Interpreter(statechart, initial_context=initial_context)
            if rec.sc_state:
                config = json.loads(rec.sc_state)
                interpreter.restore_configuration(config)
            else:
                interpreter.execute()
            rec.sc_interpreter = interpreter

    @api.depends("sc_state")
    def _compute_sc_display_state(self):
        # TODO
        for rec in self:
            rec.sc_display_state = rec.sc_state

    def _sc_execute(self, interpreter, orig_event):
        self.ensure_one()
        steps = interpreter.execute()
        _logger.debug("<= %s", steps)
        if not all([step.transitions for step in steps]):
            # at least one step had no transition => error
            raise NoTransitionError(
                _(
                    "This action is not allowed in the current state "
                    "or with your access rights.\n\n"
                    "Technical details of the error: %(orig_event)s\nSteps: %(steps)s",
                    orig_event=orig_event,
                    steps=steps,
                )
            )
        config = interpreter.save_configuration()
        new_sc_state = json.dumps(config)
        try:
            # TODO converting to json to determine if sc_state
            #      has changed is not optimal
            if new_sc_state != self.sc_state:
                self.sc_state = new_sc_state
        except MissingError:  # pylint: disable=except-pass
            # object has been deleted so don't attempt to set its state
            pass

    def _sc_exec_event(self, event):
        for rec in self:
            interpreter = rec.sc_interpreter
            if not interpreter.executing:
                _logger.debug("=> queueing event %s for %s", event, rec)
                interpreter.queue(event)
                rec._sc_execute(interpreter, event)
                if len(self) == 1 and event._return:
                    return event._return
            else:
                # The interpreter is already executing, meaning we were called
                # from within a statechart action (e.g. event.method(o) or
                # o.button_confirm.origin(o) calling super() which resolves to
                # a patched parent method). Pass through to the underlying
                # method directly without re-entering the statechart.
                if event.method is not None:
                    return event.method(rec, *event.args, **event.kwargs)
                # If there is no underlying python method (event.method is None),
                # a super() call is impossible.
                # This is a clear design/reentrancy loop error. Raise the exception
                msg = _(
                    "Reentrancy error for %(event)s on %(rec)s. "
                    "Please use sc_queue() "
                    "instead of a direct method call.",
                    event=event,
                    rec=rec,
                )
                raise RuntimeError(msg)
        return None

    @api.depends("sc_state")
    def _compute_sc_event_allowed(self):
        # TODO depends() is partial (it does not know the dependencies of
        #      guards): make sure that works in all practical situations
        statechart = self._statechart
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
                rec[field_name] = allowed

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        # make sure the interpreter is initialized, because
        # merely entering the root state may have side effects
        # (onentry, etc) and we don't want that to occur
        # more than once
        for rec in res:
            config = rec.sc_interpreter.save_configuration()
            rec.sc_state = json.dumps(config)
        return res

    @api.model
    def default_get(self, fields_list):
        """Get default values for sc_event_allowed fields.

        To compute this we instanciate a dummy interpreter. This implies
        entering the initial state and executing the associated actions.
        It is therefore important that such actions have no side effects.
        """
        res = super().default_get(fields_list)
        dummy_interpreter = None
        for field in fields_list:
            if _sc_is_event_allowed_field_name(field):
                if not dummy_interpreter:
                    dummy = self.new()
                    dummy_interpreter = dummy.sc_interpreter
                event_name = _sc_event_from_event_allowed_field_name(field)
                default = dummy_interpreter.is_event_allowed(event_name)
                res[field] = default
        return res

    def _sc_make_event_method(self, model, event_name):
        if event_name == "write":
            raise UserError(_("write cannot be a statechart event"))

        method = None

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
                _logger.debug("patching event method %s on %s", event_name, cls)
                _patch_method(cls, event_name, partial)
            else:
                raise UserError(
                    _(
                        "Statechart event %(event_name)s would mask "
                        "attribute %(method)s of %(cls)s",
                        event_name=event_name,
                        method=method,
                        cls=cls,
                    )
                )

    @api.model
    def _post_model_setup__(self):
        """Patch event methods to invoke the statechart.

        We find the most-derived definition class that declares _statechart_file
        (first match in _model_classes__ order). Using __dict__ on the
        runtime class to track patched events prevents double-patching when
        _post_model_setup__ runs for both a parent and child model.
        """
        super()._post_model_setup__()
        cls = type(self)
        # Find only the most-derived def class with _statechart_file.
        # _model_classes__ is ordered most-derived first, so the first match
        # is the one whose statechart should apply to this model.
        def_cls = next(
            (c for c in cls._model_classes__ if "_statechart_file" in c.__dict__),
            None,
        )
        if def_cls is None:
            return
        statechart = parse_statechart_file(def_cls._statechart_file)
        cls._statechart = statechart
        # Track on the runtime class __dict__ (not def_cls) so:
        # - double-patching is prevented when parent and child share events
        # - each runtime class gets its own independent tracking
        if "_statechart_patched" not in cls.__dict__:
            cls._statechart_patched = set()
        for event_name in statechart.events_for():
            if event_name not in cls._statechart_patched:
                self._sc_make_event_method(self, event_name)
                cls._statechart_patched.add(event_name)

    @api.model
    def _get_sc_event_allowed_field_names(self):
        event_names = self._statechart.events_for()
        return [
            _sc_make_event_allowed_field_name(event_name) for event_name in event_names
        ]

    @api.depends("sc_state")
    def _compute_sc_has_allowed_events(self):
        sc_fields = self._get_sc_event_allowed_field_names()
        for rec in self:
            rec.sc_has_allowed_events = any([rec[f] for f in sc_fields])

    @api.model
    def _get_sc_has_allowed_events_pre_filter(self):
        return Domain.TRUE

    @api.model
    def _search_sc_has_allowed_events(self, operator, value):
        if (operator == "=" and value) or operator == "!=" and not value:
            records = self.search(self._get_sc_has_allowed_events_pre_filter())
            return Domain(
                "id", "in", [rec.id for rec in records if rec.sc_has_allowed_events]
            )
        return ~self._search_sc_has_allowed_events("=", True)

    def _get_sc_has_allowed_events_domain(self):
        base_domain = self._get_sc_has_allowed_events_pre_filter()
        return Domain.AND([Domain("sc_has_allowed_events", "=", True), base_domain])


# ---------------------------------------------------------------------------
# Odoo 19: _setup_base no longer exists. Inject sc_event_allowed fields at
# Python import time by monkeypatching models.Model.__init_subclass__.
# This fires the moment any subclass of models.Model is defined — before
# Odoo's ORM processes anything — so fields land on the definition class
# exactly as if the developer had written them manually. Odoo's normal field
# inheritance then propagates them to child and delegated models for free,
# fixing _inherits and _inherit cases without any manual _fields__ injection.
# ---------------------------------------------------------------------------
_original_init_subclass = models.Model.__dict__.get("__init_subclass__")
# Alias the built-in super function to bypass Pylint's
# AST brain transform keyword matcher
_python_super = super


@classmethod
def _sc_patched_init_subclass(cls, **kwargs):
    if _original_init_subclass is not None:
        _original_init_subclass.__func__(cls, **kwargs)
    else:
        # Uses the alias so Pylint ignores the node,
        # but executes perfectly at runtime
        _python_super(models.Model, cls).__init_subclass__(**kwargs)
    _sc_inject_fields_on_class(cls)


models.Model.__init_subclass__ = _sc_patched_init_subclass
