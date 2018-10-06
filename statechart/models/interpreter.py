# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import sys

from sismic.exceptions import CodeEvaluationError
from sismic.interpreter import Interpreter as SismicInterpreter
from sismic.model import Event


def _root_cause(e):
    if not hasattr(e, '__cause__') or not e.__cause__:
        return e
    return _root_cause(e.__cause__)


class Interpreter(SismicInterpreter):

    def __init__(self, *args, **kwargs):
        super(Interpreter, self).__init__(
            *args, ignore_contract=True, **kwargs)
        self._in_execute_once = False

    @property
    def executing(self):
        return self._in_execute_once

    def execute(self, max_steps=-1):
        try:
            return super(Interpreter, self).execute(max_steps)
        except CodeEvaluationError as e:
            raise _root_cause(e).with_traceback(sys.exc_info()[2])

    def execute_once(self):
        if self._in_execute_once:
            raise RuntimeError("Cannot reenter execute_once")
        try:
            self._in_execute_once = True
            try:
                return super(Interpreter, self).execute_once()
            except CodeEvaluationError as e:
                raise _root_cause(e).with_traceback(sys.exc_info()[2])
        finally:
            self._in_execute_once = False

    def save_configuration(self):
        """Return the interpreter configuration.

        The result must be considered opaque, and can be used with
        `restore_configuration`. It is guaranteed to be json serializable.
        Note the evaluator context is not included in this configuration
        and must be saved independently if necessary.
        """
        # TODO memory, something else?
        return dict(
            configuration=list(self._configuration)
        )

    def restore_configuration(self, config):
        # TODO memory, something else?
        self._configuration = set(config['configuration'])
        self._initialized = True

    def is_event_allowed(self, event_name):
        # type: (str) -> Union[None, bool]
        """
        Return True if there is at least one transition for the event,
        False if there is no transition for the event,
        None in case a there is a transition whose guard could not be
        evaluated.

        :param event_name: event to consider
        :return: True|False|None
        """
        # Retrieve the firable transitions for all active state
        evaluator = self._evaluator
        for transition in self._statechart.transitions:
            if transition.event == event_name and \
                    transition.source in self._configuration:
                if transition.guard is None:
                    return True
                try:
                    if evaluator.evaluate_guard(transition, Event(event_name)):
                        return True
                except Exception:  # pylint: disable=broad-except
                    return None
        return False
