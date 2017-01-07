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
