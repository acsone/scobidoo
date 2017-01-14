# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from sismic.model import Event as SismicEvent


class Event(SismicEvent):

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self._return = None
