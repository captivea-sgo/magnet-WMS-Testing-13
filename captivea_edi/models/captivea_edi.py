# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    edi_reference = fields.Char('EDI Reference')


class CaptiveaEdiDocumentLog(models.Model):
    _name = 'captivea.edidocumentlog'
    _description = 'EDI processed log document'

    active = fields.Boolean('Active?', default=True)
    transaction_id = fields.Char('Transaction ID')
    accounting_id = fields.Char('Accounting ID')
    po_number = fields.Char('PO Number')
    po_date = fields.Char('PO Date')
    ship_to_name = fields.Char('Ship to name')
    ship_to_address_1 = fields.Char('Ship to address 1')
    ship_to_address_2 = fields.Char('Ship to address 2')
    ship_to_city = fields.Char('Ship to city')
    ship_to_state = fields.Char('Ship to state')
    ship_to_zip = fields.Char('Ship to zip')
    ship_to_country = fields.Char('Ship to country')
    store_number = fields.Char('Store number')
    bill_to_name = fields.Char('Bill to name')
    bill_to_address_1 = fields.Char('Bill to address 1')
    bill_to_address_2 = fields.Char('Bill to address 2')
    bill_to_city = fields.Char('Bill to city')
    bill_to_state = fields.Char('Bill to state')
    bill_to_zip = fields.Char('Bill to zip')
    bill_to_country = fields.Char('Bill to country')
    bill_to_code = fields.Char('Bill to code')
    ship_via = fields.Char('Ship via')
    ship_date = fields.Char('Ship date')
    terms = fields.Char('Terms')
    note = fields.Char('Note')
    department_number = fields.Char('Department number')
    cancel_date = fields.Char('Cancel date')
    do_not_ship_before = fields.Char('Do not ship before')
    do_not_ship_after = fields.Char('Do not ship after')
    allowance_percent_1 = fields.Char('Allowance percent 1')
    allowance_amount_1 = fields.Char('Allowance amount 1')
    allowance_percent_2 = fields.Char('Allowance percent 2')
    allowance_amount_2 = fields.Char('Allowance amount 2')
    line_num = fields.Char('Line #')
    vendor_part_num = fields.Char('Vendor part #')
    buyers_part_num = fields.Char('Buyers part #')
    upc_num = fields.Char('UPC #')
    description = fields.Char('Description')
    quantity = fields.Float('Quantity')
    uom = fields.Char('UOM')
    unit_price = fields.Float('Unit price')
    pack_size = fields.Float('Pack size')
    num_of_inner_packs = fields.Float('# of inner packs')
    item_allowance_percent = fields.Char('Item allowance percent')
    item_allowance_amount = fields.Char('Item allowance amount')
    state = fields.Char('Document State')

    # TO DO
    def _create_edi_poack(self):
        return True

    # TO DO
    def _create_edi_asn(self):
        return True

    # TO DO
    def _create_edi_invoice(self):
        return True

    @api.model
    def create(self, vals):
        # Create log register...
        new_record = super(CaptiveaEdiDocumentLog, self).create(vals)
        # ... then Sale Order
        so_vals = {}
        # PARA HACER PROCESAR POR NUMERO DE ORDEN AÑADIR LAS LINEAS.
        if new_record.state == 'Pass':
            order = self.env['sale.order'].sudo().search(
                [('edi_reference', '=', new_record.po_number)], limit=1)
            product = self.env['product.product'].sudo().search(
                [('default_code', '=', new_record.vendor_part_num)],
                limit=1)
            if not order:
                # Order Header
                partner = self.env['res.partner'].sudo().search(
                    [('name', '=', new_record.accounting_id)], limit=1)
                so_vals.update({'partner_id': partner.id})
                so_vals.update({'edi_reference': new_record.po_number})
                order = self.env['sale.order'].sudo().create(so_vals)

                new_order_line = {'order_id': order.id,
                                  'product_id': product.id,
                                  'product_uom_qty':
                                      float(new_record.quantity)}
                self.env['sale.order.line'].sudo().create(new_order_line)
            else:
                # The order already exists
                order_line = self.env['sale.order.line'].sudo().search(
                    [('order_id', '=', order.id),
                     ('product_id', '=', product.id)], limit=1)
                if not order_line:
                    new_order_line = {'order_id': order.id,
                                      'product_id': product.id,
                                      'product_uom_qty': float(
                                          new_record.quantity)}
                    sale_order_line = self.env['sale.order.line']
                    sale_order_line.sudo().create(new_order_line)
                else:
                    # update amount on same product line
                    current_qty = order_line.product_uom_qty
                    order_line.write(
                        {'product_uom_qty': current_qty +
                                            float(new_record.quantity)})
        return new_record
