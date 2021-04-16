# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import csv
import ssl
import ftplib
from ftplib import FTP, FTP_TLS

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, Warning

DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
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


class Picking(models.Model):
    _inherit = 'stock.picking'
    
    def action_done(self):
        """
        This function is used to create ASNPn(856) file represent picking and
         its move line data. It will create .csv file into grab folder location
        :return:
        """
        res = super(Picking, self).action_done()
        order = self.sale_id
        if order and order.edi_reference and \
                self.picking_type_id.code == 'outgoing' and \
                self.location_dest_id.usage == 'customer': # IF ORDER HAS REFERENCE TO EDI TRANSACTION THEN CREATE ASN
            # BEGINS CREATE ASN
            company = self.env.company
            ftpserver = company['ftp_server']
            ftpport = company['ftp_port']
            ftpuser = company['ftp_user']
            ftpsecret = company['ftp_secret']
            ftpdpath = company['ftp_dpath']
            #set context for secure conection
            ftpcontext = ssl.create_default_context()
            
            file_name = '/tmp/' + str(DOC_PREFIX_ASN) + '_' + \
                        str(order.name) + '_' + str(order.partner_id.name) \
                        +'.csv' # mayBe Edi_reference is better
            with open(file_name, 'w') as file_pointer:
                cvs_rows = []
                writer = csv.DictWriter(file_pointer, fieldnames=ASN_FIELDS)
                writer.writeheader()
                for row in self.move_line_ids_without_package:
                    cvs_rows.append({
                        'TRANSACTION TYPE': DOC_PREFIX_ASN,
                        'ACCOUNTING ID': order.partner_id.name,
                        'SHIPMENT ID': row.reference,
                        'SCAC': 'null',
                        'CARRIER PRO NUMBER': 'null',
                        'BILL OF LADING': 'null',
                        'SCHEDULED DELIVERY': 'null',
                        'SHIP DATE': 'null',
                        'SHIP TO NAME': row.picking_id.partner_id.name,
                        'SHIP TO ADDRESS - LINE ONE':
                            row.picking_id.partner_id.street and
                            row.picking_id.partner_id.street or 'null',
                        'SHIP TO ADDRESS - LINE TWO':
                            row.picking_id.partner_id.street2 and
                            row.picking_id.partner_id.street2 or 'null',
                        'SHIP TO CITY': row.picking_id.partner_id.city and
                                        row.picking_id.partner_id.city or 'null',
                        'SHIP TO STATE': row.picking_id.partner_id.state_id and
                            row.picking_id.partner_id.state_id.name or 'null',
                        'SHIP TO ZIP': row.picking_id.partner_id.zip and
                                       row.picking_id.partner_id.zip or 'null',
                        'SHIP TO COUNTRY': row.picking_id.partner_id.country_id
                        and row.picking_id.partner_id.country_id.name or 'null',
                        'SHIP TO ADDRESS CODE': 'null',
                        'SHIP VIA': row.picking_id.carrier_id and
                                    row.picking_id.carrier_id.name or 'null',
                        'SHIP TO TYPE': 'null',
                        'PACKAGING TYPE': 'null',
                        'GROSS WEIGHT': 'null',
                        'GROSS WEIGHT UOM': 'null',
                        'NUMBER OF CARTONS SHIPPED': 'null',
                        'CARRIER TRAILER NUMBER': 'null',
                        'TRAILER INITIAL': 'null',
                        'SHIP FROM NAME': company.name,
                        'SHIP FROM ADDRESS - LINE ONE': company.street and
                                                        company.street or 'null',
                        'SHIP FROM ADDRESS - LINE TWO': company.street2 and
                                                        company.street2 or 'null',
                        'SHIP FROM CITY': company.city and company.city or 'null',
                        'SHIP FROM STATE': company.state_id.name and
                                           company.state_id.name or 'null',
                        'SHIP FROM ZIP': company.zip and company.zip or 'null',
                        'SHIP FROM COUNTRY': company.country_id.name and
                                             company.country_id.name or 'null',
                        'SHIP FROM ADDRESS CODE': 'null',
                        'VENDOR NUMBER': 'null',
                        'DC CODE': 'null',
                        'TRANSPORTATION METHOD': 'null',
                        'PRODUCT GROUP': 'null',
                        'STATUS': 'null',
                        'TIME SHIPPED': 'null',
                        'PO NUMBER': order.name,
                        'PO DATE': order.date_order,
                        'INVOICE NUMBER': 'null',
                        'ORDER WEIGHT': 'null',
                        'STORE NAME': 'null',
                        'STORE NUMBER': 'null',
                        'MARK FOR CODE': 'null',
                        'DEPARTMENT NUMBER': 'null',
                        'ORDER LADING QUANTITY': 'null',
                        'PACKAGING TYPE': 'null',
                        'UCC-128': 'null',
                        'PACK SIZE': 'null',
                        'INNER PACK PER OUTER PACK': 'null',
                        'PACK HEIGHT': 'null',
                        'PACK WIDTH': 'null',
                        'PACK WEIGHT': 'null',
                        'QTY OF UPCS WITHIN PACK': 'null',
                        'UOM OF UPCS': 'null',
                        'STORE NAME': 'null',
                        'STORE NUMBER': 'null',
                        'LINE NUMBER': 'null',
                        'VENDOR PART NUMBER': row.product_id.default_code and
                                              row.product_id.default_code or '',
                        'BUYER PART NUMBER': 'null',
                        'UPC NUMBER': 'null',
                        'ITEM DESCRIPTION': row.product_id.name,
                        'QUANTITY SHIPPED': row.qty_done and row.qty_done or 0.0,
                        'UOM': row.product_id.uom_id.name,
                        'QUANTITY ORDERED': row.product_uom_qty and
                                            row.product_uom_qty or 0.0,
                        'UNIT PRICE': 'null',
                        'PACK SIZE': 'null',
                        'PACK UOM': 'null',
                        'INNER PACKS PER OUTER PACK': 'null'
                    })
                writer.writerows(cvs_rows)
            try:
                #connection itself
                if company['ftp_tls']:
                    sftp = FTP_TLS()
                    sftp.context = ftpcontext
                else:
                    sftp = FTP()
                if sftp.connect(ftpserver, ftpport):
                    if sftp.login(ftpuser,ftpsecret):
                        sftp.cwd(ftpdpath) # Path where to get files
                        with open(file_name, 'rb') as fp:
                            sftp.storbinary(
                                "STOR " + file_name.replace('/tmp/',''), fp)
                            sftp.quit()
                    else:
                        raise Warning('FTP Login failed!')
                else:
                    raise Warning('FTP Conection failed!')
            except ftplib.all_errors as e:
                raise Warning(_('FTP error: %s') % e)
            # ENDS ASN
            order._create_invoices() # Create Draft Invoice
        return res
