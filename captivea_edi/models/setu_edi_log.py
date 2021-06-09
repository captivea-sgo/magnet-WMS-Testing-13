from odoo import fields, models, api


class EDILog(models.Model):
    _name = 'setu.edi.log'
    _rec_name = 'seq'

    seq = fields.Char(readonly=True)
    edi_log_line_ids = fields.One2many('captivea.edidocumentlog', 'edi_log_id')
    edi_855_log_lines = fields.One2many('setu.poack.export.log.line', 'edi_log_id')
    edi_856_log_lines = fields.One2many('setu.shipack.export.log.line', 'edi_log_id')
    type = fields.Selection([('import', 'Import'), ('export', 'Export')])
    po_number = fields.Char()
    document_type = fields.Selection([('850', '850 Customer PO'),
                                      ('855', '855 POACK'),
                                      ('810', '810 INVACK'),
                                      ('856', '856 SHIPACK')])
    status = fields.Selection([('fail', 'Fail'), ('success', 'Success')],
                              compute='_compute_log_status', store=True)
    parent_log_id = fields.Many2one('setu.edi.log', string='Parent Log')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    picking_id = fields.Many2one('stock.picking', string='Delivery Order')
    invoice_id = fields.Many2one('account.move', string='Invoice')

    @api.model_create_multi
    def create(self, vals_list):
        vals_list[0].update({
            'seq': self.env['ir.sequence'].next_by_code('edi.log.seq')
        })
        return super(EDILog, self).create(vals_list)

    @api.depends('edi_log_line_ids.log_type')
    def _compute_log_status(self):
        for log in self:
            if log.document_type == '850':
                states = log.edi_log_line_ids.mapped('log_type')
                if 'fail' not in states and 'success' in states:
                    log.status = 'success'
                if 'fail' in states:
                    log.status = 'fail'

    def get_edi_status(self, line):
        if line.product_id.qty_available >= line.product_uom_qty:
            return 'accept'
        return 'reject'

    def create_poack_export_log(self, sale_id):
        sale_order = self.env['sale.order'].browse(sale_id)
        log_id = self.create({
            'po_number': sale_order.x_edi_reference,
            'type': 'export',
            'document_type': '855',
            'sale_id': sale_id
        })
        export_log = self.env['setu.poack.export.log.line']
        for line in sale_order.order_line:
            export_log.create({
                'accounting_id': sale_order.x_edi_accounting_id,
                'po_number': sale_order.x_edi_reference,
                'po_date': str(sale_order.date_order),
                'company_id': sale_order.company_id.id,
                'x_edi_po_line_number': line.x_edi_po_line_number,
                'product_template_id': line.product_template_id.id,
                'qty': line.product_uom_qty,
                'uom': line.product_uom.id,
                'price_unit': line.price_unit,
                'commitment_date': str(sale_order.commitment_date),
                'x_edi_status': self.get_edi_status(line),
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'edi_log_id': log_id.id,
                'line_num': line.x_edi_po_line_number,
                'upc_num': line.upc_num
            })
        return log_id
