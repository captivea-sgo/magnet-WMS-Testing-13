# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
DOC_PREFIX_PO = '850'  # Prefix for Purchase Order Document
DOC_PREFIX_POC = '860'  # Prefix for Purchase Order Change Document
DOC_PREFIX_POA = '855'  # Prefix for Purchase Order Aknowledgment Document
DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
DOC_PREFIX_INV = '846'  # Prefix for Inventory Document

POA_FIELDS = ['TRANSACTION ID', 'ACCOUNTING ID', 'PURPOSE', 'TYPE STATUS',
              'PO #', 'PO DATE', 'RELEASE NUMBER', 'REQUEST REFERENCE NUMBER',
              'CONTRACT NUMBER', 'SELLING PARTY NAME',
              'SELLING PARTY ADDRESS 1', 'SELLING PARTY ADDRESS 2',
              'SELLING PARTY CITY', 'SELLING PARTY STATE', 'SELLING PARTY ZIP',
              'ACCOUNT NUMBER - VENDOR NUMBER', 'WAREHOUSE ID', 'LINE #',
              'PO LINE #', 'VENDOR PART #', 'UPC', 'SKU', 'QTY', 'UOM',
              'PRICE', 'SCHEDULED DELIVERY DATE', 'SCHEDULED DELIVERY TIME',
              'ESTIMATED DELIVERY DATE', 'ESTIMATED DELIVERY TIME',
              'PROMISED DATE', 'PROMISED TIME', 'STATUS', 'STATUS QTY',
              'STATUS UOM']
ASN_FIELDS = ['TRANSACTION TYPE', 'ACCOUNTING ID', 'SHIPMENT ID', 'SCAC',
              'CARRIER PRO NUMBER', 'BILL OF LADING', 'SCHEDULED DELIVERY',
              'SHIP DATE', 'SHIP TO NAME', 'SHIP TO ADDRESS - LINE ONE',
              'SHIP TO ADDRESS - LINE TWO', 'SHIP TO CITY', 'SHIP TO STATE',
              'SHIP TO ZIP', 'SHIP TO COUNTRY', 'SHIP TO ADDRESS CODE',
              'SHIP VIA', 'SHIP TO TYPE', 'PACKAGING TYPE', 'GROSS WEIGHT',
              'GROSS WEIGHT UOM', 'NUMBER OF CARTONS SHIPPED',
              'CARRIER TRAILER NUMBER', 'TRAILER INITIAL', 'SHIP FROM NAME',
              'SHIP FROM ADDRESS - LINE ONE', 'SHIP FROM ADDRESS - LINE TWO',
              'SHIP FROM CITY', 'SHIP FROM STATE', 'SHIP FROM ZIP',
              'SHIP FROM COUNTRY', 'SHIP FROM ADDRESS CODE', 'VENDOR NUMBER',
              'DC CODE', 'TRANSPORTATION METHOD', 'PRODUCT GROUP', 'STATUS',
              'TIME SHIPPED', 'PO NUMBER', 'PO DATE', 'INVOICE NUMBER',
              'ORDER WEIGHT', 'STORE NAME', 'STORE NUMBER', 'MARK FOR CODE',
              'DEPARTMENT NUMBER', 'ORDER LADING QUANTITY', 'PACKAGING TYPE',
              'UCC-128', 'PACK SIZE', 'INNER PACK PER OUTER PACK',
              'PACK HEIGHT', 'PACK WIDTH', 'PACK WEIGHT',
              'QTY OF UPCS WITHIN PACK', 'UOM OF UPCS', 'STORE NAME',
              'STORE NUMBER', 'LINE NUMBER', 'VENDOR PART NUMBER',
              'BUYER PART NUMBER', 'UPC NUMBER', 'ITEM DESCRIPTION',
              'QUANTITY SHIPPED', 'UOM', 'QUANTITY ORDERED', 'UNIT PRICE',
              'PACK SIZE', 'PACK UOM', 'INNER PACKS PER OUTER PACK']

import csv
import pysftp
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    x_edi_reference = fields.Char('EDI Reference')
    x_edi_accounting_id = fields.Char('Accounting ID')
    x_edi_store_number = fields.Char('Store number')
    x_edi_flag = fields.Boolean('EDI Flag')
    poack_created = fields.Boolean()
    customer_po_ref = fields.Many2one('setu.edi.log')
    poack_ref = fields.Many2one('setu.edi.log')

    def create_poack_export_log(self, DOC_PREFIX_POA):
        log_id = self.env['setu.edi.log'].create_poack_export_log(self.id)
        self.poack_ref = log_id
        res = self.poack_export(log_id, DOC_PREFIX_POA)
        if res:
            log_id.status = 'success'

    def poack_export(self, log_id, DOC_PREFIX_POA):

        company = self.company_id
        sftp_conf = self.env['setu.sftp'].search([('company_id', '=', company.id)])
        ftpserver = sftp_conf['ftp_server']
        ftpport = sftp_conf['ftp_port']
        ftpuser = sftp_conf['ftp_user']
        ftpsecret = sftp_conf['ftp_secret']
        ftpdpath = sftp_conf['ftp_poack_dpath']

        file_name = '/tmp/' + str(DOC_PREFIX_POA) + '_' + str(self.x_edi_reference) + str(self.partner_id.name) + \
                    '_' + '.csv'  # TO DO COMPLETE FILE NAME WITH CUSTOMER NAME
        with open(file_name, 'w+') as file_pointer:
            cvs_rows = []
            writer = csv.DictWriter(file_pointer, fieldnames=POA_FIELDS)
            writer.writeheader()
            for row in log_id.edi_855_log_lines:
                cvs_rows.append({
                    'TRANSACTION ID': DOC_PREFIX_POA,
                    'ACCOUNTING ID': row.accounting_id,
                    'PURPOSE': 'null',  # ASK TIM FOR VALUE
                    'TYPE STATUS': 'null',
                    'PO #': row.po_number,
                    'PO DATE': row.po_date,
                    'RELEASE NUMBER': 'null',
                    'REQUEST REFERENCE NUMBER': row.po_number,
                    'CONTRACT NUMBER': 'null',
                    'SELLING PARTY NAME': company.name,
                    'SELLING PARTY ADDRESS 1': company.street and
                                               company.street or 'null',
                    'SELLING PARTY ADDRESS 2': company.street2 and
                                               company.street2 or 'null',
                    'SELLING PARTY CITY': company.city and
                                          company.city or 'null',
                    'SELLING PARTY STATE': company.state_id and
                                           company.state_id.name or 'null',
                    'SELLING PARTY ZIP': company.zip and
                                         company.zip or 'null',
                    'ACCOUNT NUMBER - VENDOR NUMBER': 'null',
                    'WAREHOUSE ID': 'null',
                    'LINE #': 'null',
                    'PO LINE #': row.line_num and
                                 row.line_num or 'null',
                    'VENDOR PART #': row.product_template_id.default_code or 'null',

                    'UPC': row.upc_num and
                           row.upc_num or 'null',
                    'SKU': 'null',
                    'QTY': row.qty and row.qty or 'null',
                    'UOM': row.uom.name and row.uom.name or 'null',
                    'PRICE': row.price_unit and row.price_unit or 0.0,
                    'SCHEDULED DELIVERY DATE': 'null',
                    'SCHEDULED DELIVERY TIME': 'null',
                    'ESTIMATED DELIVERY DATE': 'null',
                    'ESTIMATED DELIVERY TIME': 'null',
                    'PROMISED DATE': 'null',
                    'PROMISED TIME': 'null',
                    'STATUS': row.x_edi_status,
                    'STATUS QTY': row.product_uom_qty,
                    'STATUS UOM': row.product_uom.name
                })
            writer.writerows(cvs_rows)
            file_pointer.close()
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=22, cnopts=cnopts)
            if sftp:
                sftp.cwd(ftpdpath)
                sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_POA) + '_' + str(self.x_edi_reference) + '_.csv')
                sftp.close()
                self.poack_created = True
                return True

            else:
                return False
        except Exception as e:
            if len(e.args) > 1:
                if e.args[1] == 22:
                    raise Warning('Invalid Server Details')
                raise Warning(e.args[1])
            else:
                raise Warning(e.args[0])

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if res and self.customer_po_ref:
            self.create_poack_export_log(DOC_PREFIX_POA)
            if self.picking_ids:
                self.picking_ids.x_edi_accounting_id = self.x_edi_accounting_id


