# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, UserError

from ..exceptions import NoTransitionError
from .event import Event
from .interpreter import Interpreter
from .statechart import parse_statechart_file

_logger = logging.getLogger(__name__)


def _sc_make_event_allowed_field_name(event_name):
    # TODO event names must be valid python identifiers
    #      (that must be tested somewhere long before reaching this point)
    return "sc_" + event_name + "_allowed"


def _sc_is_event_allowed_field_name(field_name):
    return field_name.startswith("sc_") and field_name.endswith("_allowed")


def _sc_event_from_event_allowed_field_name(field_name):
    return field_name[3:-8]


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
                "initializing interpreter for %s " "with statechart %s",
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
                interpreter.execute_once()
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
                setattr(rec, field_name, allowed)

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
                _logger.debug(
                    "patching event method %s on %s",
                    event_name,
                    cls,
                )
                cls._patch_method(event_name, partial)
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

    def _sc_make_event_allowed_field(self, model_cls, event_name):
        # we add the fields in the original python class
        # so all downstream field processing done by Odoo works
        # (_inherit, _inherits in particular)
        field_name = _sc_make_event_allowed_field_name(event_name)
        if hasattr(model_cls, field_name):
            return
        field = fields.Boolean(
            compute="_compute_sc_event_allowed",
            readonly=True,
            store=False,
        )
        field.name = field_name
        _logger.debug("adding field %s to %s", field_name, model_cls)
        setattr(model_cls, field_name, field)
        model_cls._field_definitions.append(field)

    @api.model
    def _setup_base(self):
        """Very early, load the statechart, and add the sc_event_allowed
        fields on the model classes where the developer has declared
        the _statechart_file attribute.

        This closely emulates what the developer would have done when
        adding such fields manually.

        Further steps of the regular setup process will then add these fields
        on children models.
        """
        model_cls = type(self)
        assert not models.is_definition_class(model_cls)
        for def_cls in model_cls.__bases__:
            if not models.is_definition_class(def_cls):
                continue
            if "_statechart_file" not in def_cls.__dict__:
                continue
            _logger.debug(
                "%s has _statechart_file.",
                def_cls,
            )
            statechart = parse_statechart_file(def_cls._statechart_file)
            _logger.debug(
                "adding sc_event_allowed fields of statechart %s on %s.",
                statechart.name,
                def_cls,
            )
            for event_name in statechart.events_for():
                self._sc_make_event_allowed_field(def_cls, event_name)
        return super()._setup_base()

    @api.model
    def _sc_patch(self):
        cls = type(self)
        if not hasattr(self, "_statechart_file"):
            return
        if self._inherit:
            if isinstance(self._inherit, str):
                parents = [self._inherit]
            else:
                parents = self._inherit
            for parent in parents:
                if parent != self._name:
                    parent_model = self.env[parent]
                    if hasattr(parent_model, "_sc_patch"):
                        parent_model._sc_patch()
        statechart = parse_statechart_file(self._statechart_file)
        _logger.debug(
            "patching/adding event methods of statechart %s on %s.",
            statechart.name,
            cls,
        )
        cls._statechart = statechart
        if not hasattr(cls, "_statechart_patched"):
            cls._statechart_patched = set()
        for event_name in statechart.events_for():
            if event_name not in cls._statechart_patched:
                self._sc_make_event_method(self, event_name)
                cls._statechart_patched.add(event_name)

    @api.model
    def _setup_complete(self):
        """Very late, patch the event methods to invoke the statechart.

        We record a set of event methods already patched, so an inherited
        class can override the statechart with another one adding new events,
        and we will not patch the same method twice.
        """
        res = super()._setup_complete()
        self._sc_patch()
        return res

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
        return []

    @api.model
    def _search_sc_has_allowed_events(self, operator, value):
        if (operator == "=" and value) or operator == "!=" and not value:
            records = self.search(self._get_sc_has_allowed_events_pre_filter())
            return [
                ("id", "in", [rec.id for rec in records if rec.sc_has_allowed_events])
            ]
        return ["!"] + self._search_sc_has_allowed_events("=", True)

    def _get_sc_has_allowed_events_domain(self):
        return [
            ("sc_has_allowed_events", "=", True)
        ] + self._get_sc_has_allowed_events_pre_filter()
