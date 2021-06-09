from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    x_edi_mismatch = fields.Boolean('EDI Mismatch')
    x_edi_po_line_number = fields.Char('PO #')
    upc_num = fields.Char()
