from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = ['res.partner']

    x_edi_accounting_id = fields.Char('Accounting ID')
    x_edi_store_number = fields.Char('Store number')
    x_edi_flag = fields.Boolean('EDI Flag')
