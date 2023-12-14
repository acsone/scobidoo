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
            self.assertEqual(set(config['configuration']),
                             set(expected_config))

    def test_basic(self):
        """
        Test that we can create a model with a statechart and that the
        statechart is correctly initialized
        """
        model = self.env['scobidoo.test.model']
        record = model.create({'amount': 200})
        record.confirm1()
        self.assertScState(record.sc_state, ["confirmed1", "root"])
        # big amount, confirm manually
        record.confirm2()
        self.assertScState(record.sc_state, ["confirmed2", "root"])

    def test_automatic_transition(self):
        """
        Test that we can create a model with a statechart and that the
        statechart is correctly initialized
        """
        model = self.env['scobidoo.test.model']
        record = model.create({'amount': 50})
        record.confirm1()
        # small amount, step 2 done automatically
        self.assertScState(record.sc_state, ["confirmed2", "root"])
