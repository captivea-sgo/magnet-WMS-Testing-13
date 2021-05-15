# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    max_weight = fields.Float("Weight (lb)")
    # lngth IS NOT A TYPO https://github.com/odoo/odoo/issues/41353
    lngth = fields.Integer("Length (in)", help="length in inches
    # Although it feels weird to use Integer in millimeters, we use Int to
    # override the fields from delivery module instead of defining new ones
    width = fields.Integer("Width (in)", help="width in inches
    height = fields.Integer("Height (in)", help="height in inches")
    volume = fields.Float(
        "Volume (ft³)",
        digits=(8, 4),
        compute="_compute_volume",
        readonly=True,
        store=False,
        help="volume in cubic feet",
    )

    @api.depends("lngth", "width", "height")
    def _compute_volume(self):
        for pack in self:
            pack.volume = (pack.lngth * pack.width * pack.height) / 1728.0 ** 3
