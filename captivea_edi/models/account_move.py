# -*- coding: utf-8 -*-

import csv
import ssl
import ftplib
import pysftp
from ftplib import FTP, FTP_TLS

from odoo import api, fields, models, _

# forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')

# EDI Block
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
BIL_FIELDS = ['TRANSACTION ID', 'ACCOUNTING ID', 'INVOICE #', 'INVOICE DATE',
              'PO #', 'PO DATE', 'DEPT #', 'BILL OF LADING', 'CARRIER PRO #',
              'SCAC', 'SHIP VIA', 'SHIP TO NAME', 'SHIP TO ADDRESS 1',
              'SHIP TO ADDRESS 2', 'SHIP TO CITY', 'SHIP TO STATE',
              'SHIP TO ZIP CODE', 'SHIP TO COUNTRY', 'STORE #', 'BILL TO NAME',
              'BILL TO ADDRESS 1', 'BILL TO ADDRESS 2', 'BILL TO CITY',
              'BILL TO STATE', 'BILL TO ZIP CODE', 'BILL TO COUNTRY',
              'BILL TO CODE', 'SHIP DATE', 'TERMS DESCRIPTION', 'NET DAYS DUE',
              'DISCOUNT DAYS DUE', 'DISCOUNT PERCENT', 'NOTE', 'WEIGHT',
              'TOTAL CASES SHIPPED', 'TAX AMOUNT', 'CHARGE AMOUNT 1',
              'CHARGE AMOUNT 2', 'ALLOWANCE PERCENT 1', 'ALLOWANCE AMOUNT 1',
              'ALLOWANCE PERCENT 2', 'ALLOWANCE AMOUNT 2', 'LINE #',
              'VENDOR PART #', 'BUYER PART #', 'UPC #', 'DESCRIPTION',
              'QUANTITY SHIPPED', 'UOM', 'UNIT PRICE', 'QUANTITY ORDERED',
              'PACK SIZE', '# OF INNER PACKS', 'ITEM ALLOWANCE PERCENT',
              'ITEM ALLOWANCE AMOUNT']


class AccountMove(models.Model):
    _inherit = "account.move"
    
    def action_post(self):
        """
        This Function is used create Invoice(810-880) file if the entry is
        related to SO. and call invoice action post function that execute
        default behaviour.
        :return:
        """
        res = super(AccountMove,self).action_post()
        order = self.env['sale.order'].sudo().search(
            [('name', '=', str(self.invoice_origin))], limit=1)
        if order.edi_reference: # IF ORDER HAS REFERENCE TO EDI TRANSACTION THEN CREATE EDI INVOICE
            # BEGINS CREATE EDI INVOICE
            company = self.env.company
            ftpserver = company['ftp_server']
            ftpport = company['ftp_port']
            ftpuser = company['ftp_user']
            ftpsecret = company['ftp_secret']
            ftpdpath = company['ftp_dpath']
            file_name = '/tmp/' + str(DOC_PREFIX_BIL) + '_' + \
                        str(order.edi_reference) + '_' + \
                        str(order.partner_id.name) + '.csv'
            with open(file_name, 'w') as file_pointer:
                cvs_rows = []
                writer = csv.DictWriter(file_pointer, fieldnames=BIL_FIELDS)
                writer.writeheader()                        
                for row in self.invoice_line_ids:
                    cvs_rows.append({
                        'TRANSACTION ID': DOC_PREFIX_BIL,
                        'ACCOUNTING ID': order.partner_id.name,
                        'INVOICE #': self.name,
                        'INVOICE DATE': str(self.invoice_date),
                        'PO #': order.name,
                        'PO DATE': order.date_order,
                        'DEPT #': 'null',
                        'BILL OF LADING': 'null',
                        'CARRIER PRO #': 'null',
                        'SCAC': 'null',
                        'SHIP VIA': 'null',
                        'SHIP TO NAME': order.partner_id.name,
                        'SHIP TO ADDRESS 1': order.partner_id.street and
                                             order.partner_id.street or 'null',
                        'SHIP TO ADDRESS 2': order.partner_id.street2 and
                                             order.partner_id.street2 or 'null',
                        'SHIP TO CITY': order.partner_id.city and
                                        order.partner_id.city or 'null',
                        'SHIP TO STATE': order.partner_id.state_id and
                                         order.partner_id.state_id.name or 'null',
                        'SHIP TO ZIP CODE': order.partner_id.zip and
                                            order.partner_id.zip or 'null',
                        'SHIP TO COUNTRY': order.partner_id.country_id and
                                           order.partner_id.country_id.name or 'null',
                        'STORE #': 'null',
                        'BILL TO NAME': order.partner_id.name,
                        'BILL TO ADDRESS 1': order.partner_id.street and
                                             order.partner_id.street or 'null',
                        'BILL TO ADDRESS 2': order.partner_id.street2 and
                                             order.partner_id.street2 or 'null',
                        'BILL TO CITY': order.partner_id.city and
                                        order.partner_id.city or 'null',
                        'BILL TO STATE': order.partner_id.state_id and
                                         order.partner_id.state_id.name or 'null',
                        'BILL TO ZIP CODE': order.partner_id.zip and
                                            order.partner_id.zip or 'null',
                        'BILL TO COUNTRY': order.partner_id.country_id and
                                           order.partner_id.country_id.name or 'null',
                        'BILL TO CODE': 'null',
                        'SHIP DATE': 'null',
                        'TERMS DESCRIPTION': order.payment_term_id and
                                             order.payment_term_id.name or 'null',
                        'NET DAYS DUE': 'null',
                        'DISCOUNT DAYS DUE': 'null',
                        'DISCOUNT PERCENT': 'null',
                        'NOTE': order.note and order.note or '',
                        'WEIGHT': 'null',
                        'TOTAL CASES SHIPPED': 'null',
                        'TAX AMOUNT': order.amount_tax and
                                      order.amount_tax or 0.0,
                        'CHARGE AMOUNT 1': 'null',
                        'CHARGE AMOUNT 2': 'null',
                        'ALLOWANCE PERCENT 1': 'null',
                        'ALLOWANCE AMOUNT 1': 'null',
                        'ALLOWANCE PERCENT 2': 'null',
                        'ALLOWANCE AMOUNT 2': 'null',
                        'LINE #': 'null',
                        'VENDOR PART #': row.product_id.default_code and
                                         row.product_id.default_code or '',
                        'BUYER PART #': 'null',
                        'UPC #': 'null',
                        'DESCRIPTION': row.product_id.name,
                        'QUANTITY SHIPPED': row.quantity and row.quantity or 0.0,
                        'UOM': row.product_id.uom_id.name,
                        'UNIT PRICE': row.price_unit and row.price_unit or 0.0,
                        'QUANTITY ORDERED': 'null',
                        'PACK SIZE': 'null',
                        '# OF INNER PACKS': 'null',
                        'ITEM ALLOWANCE PERCENT': 'null',
                        'ITEM ALLOWANCE AMOUNT': 'null',
                    })                                                    
                writer.writerows(cvs_rows)
            try:
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport,
                                         cnopts=cnopts)
                if sftp:
                    sftp.cwd(ftpdpath)
                    sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_BIL) + '_' + str(order.edi_reference) + '_' \
                             + str(order.partner_id.name) + '.csv')
                    sftp.close()
                else:
                    return False

                #connection itself
                # if company['ftp_tls']:
                #     sftp = FTP_TLS()
                #     sftp.context = ftpcontext
                # else:
                #     sftp = FTP()
                # if sftp.connect(ftpserver, ftpport):
                #     if sftp.login(ftpuser, ftpsecret):
                #         sftp.cwd(ftpdpath) # Path where to get files
                #         with open(file_name, 'rb') as fp:
                #             sftp.storbinary("STOR " + file_name.replace('/tmp/',''), fp)
                #             sftp.quit()
                #     else:
                #         raise Warning('FTP Login failed!')
                # else:
                #     raise Warning('FTP Conection failed!')
            except Exception as e:
                raise Warning(_('FTP error: %s') % e)
            # ENDS EDI INVOICE
        return res
