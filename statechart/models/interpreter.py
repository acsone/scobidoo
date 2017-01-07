# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json

from sismic.interpreter import Interpreter as SismicInterpreter
from sismic.model import Event


class Interpreter(SismicInterpreter):

    def __init__(self, *args, **kwargs):
        super(Interpreter, self).__init__(
            *args, ignore_contract=True, **kwargs)
        self._in_execute_once = False

    @property
    def executing(self):
        return self._in_execute_once

    def execute_once(self):
        if self._in_execute_once:
            raise RuntimeError("Cannot reenter execute_once")
        try:
            self._in_execute_once = True
            return super(Interpreter, self).execute_once()
        finally:
            self._in_execute_once = False

    def save_configuration(self):
        # TODO memory, something else?
        # TODO: the sorted is here to ease tests asserts only
        config = sorted(list(self._configuration))
        return json.dumps(config)

    def restore_configuration(self, config):
        # TODO memory, something else?
        config = json.loads(config)
        self._configuration = set(config)
        self._initialized = True

    def is_event_allowed(self, event_name):
        # type: (str) -> List[model.Transition]
        """
        Return True if there is at least one transition for the event,
        False if there is no transition for the event,
        None in case a there is a transition whose guard could not be
        evaluated.

        :param event_name: event to consider
        :return: True|False|None
        """
        # Retrieve the firable transitions for all active state
        for transition in self._statechart.transitions:
            if transition.event == event_name and transition.source in self._configuration:
                if transition.guard is None:
                    return True
                try:
                    if self._evaluator.evaluate_guard(transition, Event(event_name)):
                        return True
                except:
                    return None
        return False
