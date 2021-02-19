from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "statechart.mixin"]
    _statechart_file = "statechart_demo/models/res_partner_statechart.yml"
