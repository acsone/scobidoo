# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from odoo.tests import common


class TestBasic(common.TransactionCase):
    def assertScState(self, sc_state, expected_config):
        if not expected_config:
            self.assertFalse(sc_state)
        else:
            config = json.loads(sc_state)
            self.assertEqual(set(config["configuration"]), set(expected_config))

    def test_basic(self):
        model = self.env["scobidoo.test.model"]
        record = model.create({"amount": 200})
        record.confirm1()
        self.assertScState(record.sc_state, ["confirmed1", "root"])
        # big amount, confirm manually
        record.confirm2()
        self.assertScState(record.sc_state, ["confirmed2", "root"])

    def test_automatic_transition(self):
        model = self.env["scobidoo.test.model"]
        record = model.create({"amount": 50})
        record.confirm1()
        # small amount, step 2 done automatically
        self.assertScState(record.sc_state, ["confirmed2", "root"])

    def test_automatic_transition_on_create(self):
        model = self.env["scobidoo.test.model"]
        record = model.create({"amount": 0.5})
        # very small amount, step 1 and 2 done automatically
        self.assertScState(record.sc_state, ["confirmed2", "root"])

    def test_get_sc_event_allowed_field_names(self):
        """
        Test that we can ignore certain events based on a context
        key (ignore_for_has_allowed_events)
        """
        model = self.env["scobidoo.test.model"]
        record = model.create({"amount": 200})
        record.confirm1()
        self.assertScState(record.sc_state, ["confirmed1", "root"])

        # 2 events are allowed: confirmed2 and cancel
        self.assertEqual(record.sc_has_allowed_events, True)

        # 1 event is allowed: confirmed2
        record.invalidate_cache()
        self.assertEqual(
            record.with_context(
                ignore_for_has_allowed_events=["cancel"]
            ).sc_has_allowed_events,
            True,
        )

        # no event allowed
        record.invalidate_cache()
        self.assertEqual(
            record.with_context(
                ignore_for_has_allowed_events=["cancel", "confirm2"]
            ).sc_has_allowed_events,
            False,
        )
