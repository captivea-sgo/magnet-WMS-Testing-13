# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import csv
import pysftp
from odoo import models, fields, api

DOC_PREFIX_POA = '855'
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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def create_edi_poack(self):
        """
        This function create new file based on import that has been log.
        :param current_orders:
        :param DOC_PREFIX_POA:
        :return:
        """
        self.ensure_one()
        company = self.env.company
        ftpserver = company['ftp_server']
        ftpport = company['ftp_port']
        ftpuser = company['ftp_user']
        ftpsecret = company['ftp_secret']
        ftpdpath = company['ftp_dpath']
        if self.edi_reference:
            file_name = '/tmp/' + str(DOC_PREFIX_POA) + '_' + str(self.edi_reference) + \
                        '_' + '.csv' # TO DO COMPLETE FILE NAME WITH CUSTOMER NAME
            with open(file_name, 'w+') as file_pointer:
                cvs_rows = []
                writer = csv.DictWriter(file_pointer, fieldnames=POA_FIELDS)
                writer.writeheader()
                rows = self.env['captivea.edidocumentlog'].sudo().search(
                    [('po_number', '=', self.edi_reference)])
                for row in rows:
                    cvs_rows.append({
                        'TRANSACTION ID': DOC_PREFIX_POA,
                        'ACCOUNTING ID': row.accounting_id,
                        'PURPOSE': 'null', # ASK TIM FOR VALUE
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
                        'VENDOR PART #': row.vendor_part_num and
                                         row.vendor_part_num or 'null',
                        'UPC': row.upc_num and
                               row.upc_num or 'null',
                        'SKU': 'null',
                        'QTY': row.quantity and row.quantity or 'null',
                        'UOM': row.uom and row.uom or 'null',
                        'PRICE': row.unit_price and row.unit_price or 0.0,
                        'SCHEDULED DELIVERY DATE': 'null',
                        'SCHEDULED DELIVERY TIME': 'null',
                        'ESTIMATED DELIVERY DATE': 'null',
                        'ESTIMATED DELIVERY TIME': 'null',
                        'PROMISED DATE': 'null',
                        'PROMISED TIME': 'null',
                        'STATUS': row.state,
                        'STATUS QTY': 'null',
                        'STATUS UOM': 'null'
                    })
                writer.writerows(cvs_rows)
                file_pointer.close()
            try:
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport,
                                         cnopts=cnopts)
                if sftp:
                    sftp.cwd(ftpdpath)
                    sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_POA) + '_' + str(self.edi_reference) + '_.csv')
                    sftp.close()
                else:
                    return False
            except Exception as e:
                if len(e.args) > 1:
                    if e.args[1] == 22:
                        raise Warning('Invalid Server Details')
                    raise Warning(e.args[1])
                else:
                    raise Warning(e.args[0])
