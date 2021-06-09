from odoo import fields, models, api


class POACKExport(models.Model):
    _name = 'setu.poack.export.log.line'

    accounting_id = fields.Char('Accounting ID')
    po_number = fields.Char('EDI Ref')
    po_date = fields.Char('PO Date')
    company_id = fields.Many2one('res.company', string='Selling Party Name')
    street = fields.Char(related='company_id.street', string='Selling Party Address 1')
    street2 = fields.Char(related='company_id.street2', string='Selling Party Address 2')
    city = fields.Char(related='company_id.city', string='Selling Party City')
    state = fields.Many2one(related='company_id.state_id', string='Selling Party State')
    country = fields.Many2one(related='company_id.country_id', string='Selling Party Country')
    zip = fields.Char(related='company_id.zip', string='Selling Party Zip')
    x_edi_po_line_number = fields.Char('PO Line #')
    product_template_id = fields.Many2one('product.template', 'Vendor Part #')
    qty = fields.Float('Qty')
    uom = fields.Many2one('uom.uom', 'UOM')
    price_unit = fields.Float('Price')
    commitment_date = fields.Char(string='Scheduled Delivery Date')
    x_edi_status = fields.Selection([('accept', 'Accept'), ('reject', 'Reject')], string='Status')
    product_uom_qty = fields.Float('Status Qty')
    product_uom = fields.Many2one('uom.uom', 'Status UOM')
    edi_log_id = fields.Many2one('setu.edi.log')
    log_type = fields.Selection([('success', 'Success'),
                                 ('fail', 'Failure')], default='fail')
    upc_num = fields.Char('Barcode')
    transaction_id = fields.Char('Transaction ID')
    store_number = fields.Char('Store number')
    line_num = fields.Char('PO Line #')


class SHIPACKExport(models.Model):
    _name = 'setu.shipack.export.log.line'

    edi_log_id = fields.Many2one('setu.edi.log', 'Log Id')
    accounting_id = fields.Char('Accounting ID')
    shipment_id = fields.Char('Shipment ID')
    x_studio_scac = fields.Char('SCAC')
    carrier_tracking_ref = fields.Char('Carrier Pro #')
    origin_sale_order = fields.Many2one('sale.order', 'Bill of Lading')
    date_done = fields.Char(string='Ship Date')
    store_number = fields.Char('Store number')

    ship_to_name = fields.Char('Ship To Name')
    ship_to_address_1 = fields.Char('Ship To Address – Line One')
    ship_to_address_2 = fields.Char('Ship To Address – Line Two')
    ship_to_city = fields.Char('Ship to city')
    ship_to_state = fields.Char('Ship to state')
    ship_to_zip = fields.Char('Ship to zip')
    ship_to_country = fields.Char('Ship to country')

    carrier_id = fields.Many2one('delivery.carrier', 'Ship via')
    x_studio_packaging_type = fields.Char('Packaging Type')
    weight = fields.Float('Gross Weight')
    weight_uom_name = fields.Char('')
    x_package_count = fields.Integer('# of Cartons Shipped')

    ship_from_company_id = fields.Many2one('res.company', 'Ship From Name')
    ship_from_street = fields.Char(related='ship_from_company_id.street', string='Ship From Address – Line One')
    ship_from_street2 = fields.Char(related='ship_from_company_id.street', string='Ship From Address – Line Two')
    ship_from_city = fields.Char(related='ship_from_company_id.city', string='Ship From City')
    ship_from_state = fields.Many2one(related='ship_from_company_id.state_id', string='Ship From State')
    ship_from_zip = fields.Char(related='ship_from_company_id.zip', string='Ship From Zip')
    ship_from_country = fields.Many2one(related='ship_from_company_id.country_id', string='Ship From Country')

    vendor_number = fields.Char('Vendor Number')
    uom = fields.Char('UOM')
    status = fields.Selection([('partial', 'Partial Shipment'),
                               ('complete', 'Complete Shipment')])
    po_number = fields.Char('PO Number')
    po_date = fields.Char('PO Date')
    product_id = fields.Char('Vendor Part Number')
    description_sale = fields.Char('Item Description')
    quantity_done = fields.Float('Quantity Shipped')
    product_uom_quantity = fields.Float('Quantity Ordered')



class INVACKExport(models.Model):
    _name = 'setu.invack.export.log.line'

