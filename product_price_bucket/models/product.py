# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, SUPERUSER_ID


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pricing_bucket_id = fields.Many2one('pricing.bucket', string="Price Class")
