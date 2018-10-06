# Copyright 2016-2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from sismic.exceptions import StatechartError
import sismic.io

from odoo import tools

_logger = logging.getLogger(__name__)


def parse_statechart(f):
    try:
        statechart = sismic.io.import_from_yaml(f)
        _logger.debug("loaded statechart %s", statechart.name)
        return statechart
    except StatechartError:
        _logger.error("error loading statechart", exc_info=True)
        raise


def parse_statechart_file(filename):
    _logger.info("loading statechart file %s", filename)
    with tools.file_open(filename, 'r') as f:
        return parse_statechart(f)
