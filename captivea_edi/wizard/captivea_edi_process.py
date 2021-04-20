# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import csv
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
import pysftp

DOC_PREFIX_PO = '850' # Prefix for Purchase Order Document
DOC_PREFIX_POC = '860' # Prefix for Purchase Order Change Document
DOC_PREFIX_POA = '855' # Prefix for Purchase Order Aknowledgment Document
DOC_PREFIX_ASN = '856' # Prefix for Advanced Ship Notice Document
DOC_PREFIX_BIL = '810' # Prefix for Invoice Document
DOC_PREFIX_INV = '846' # Prefix for Inventory Document
CURRENT_ORDERS = list() # Current Processed Orders REMOVE THIS LATER NOT NEEDED ANYMORE
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


class CaptiveaEdiProcess(models.TransientModel):
    _name = 'captivea.ediprocess'
    _description = 'EDI manual handler model'

    active = fields.Boolean('Active?', default=True)
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='State', readonly=True, default='init')

    @api.model
    def _write_edi_doclog(self,vals):
        try:
            doclog = self.env['captivea.edidocumentlog']
            doclog.sudo().create(vals)            
            return True
        except:
            raise Warning('Error writing logdoc!')
            return False
    
    def _validate_order(self, vals):
        """
        Function validate the request qty, product, customer, etc.
        :param vals:
        :return: status / validation msg
        """
        #Partner Validation
        if not self.env['res.partner'].sudo().search(
                [('name','=',vals['accounting_id'])]):
            validation_msg = "Failed! Customer does not exists."
        else:
            #Product Validation
            if not self.env['product.product'].sudo().search(
                    [('default_code','=',vals['vendor_part_num'])]):
                validation_msg = "Failed! Product does not exists."
            else:
                #Stock Validation
                qty = self.env['product.product'].sudo().search(
                    [('default_code','=',vals['vendor_part_num'])], limit=1)
                if not (qty.qty_available > float(vals['quantity'])):
                    validation_msg = "Failed! Not enough stock"
                else:
                    validation_msg = "Pass"
        return validation_msg

    def _grab_ftp_files(self):
        """
        This function check the connection and check for any new file if exist
        it will read and create log entry based on data. and if data is proper
        from log create funtion SO will also be created.
        :return:
        """
        current_orders = list()
        company = self.env.company
        ftpserver = company['ftp_server']
        if not ftpserver:
            raise Warning('FTP Host parameter missed!')
        ftpport = company['ftp_port']
        if not ftpport:
            raise Warning('FTP Port parameter missed!')
        ftpuser = company['ftp_user']
        if not ftpuser:
            raise Warning('FTP User parameter missed!')
        ftpsecret = company['ftp_secret']
        if not ftpsecret:
            raise Warning('FTP password parameter missed!')
        ftpgpath = company['ftp_gpath']
        if not ftpgpath:
            raise Warning('FTP GrabPath parameter missed!')
        ftpdpath = company['ftp_dpath']
        if not ftpdpath:
            raise Warning('FTP DropPath parameter missed!')
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        try:
            sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport, cnopts=cnopts)
            if sftp:
                sftp.cwd(ftpgpath)
                directory_structure = sftp.listdir_attr()
                for attr in directory_structure:
                    file_path = ftpgpath + '/' + attr.filename
                    if sftp.isfile(file_path):
                        csvfile = sftp.open(file_path)
                        csvdata = csv.DictReader(csvfile)
                        vals = {}
                        for row in csvdata: # Processing file begins here.
                            vals = {'create_date': datetime.now(),
                                    'transaction_id': row["TRANSACTION ID"],
                                    'accounting_id': row["ACCOUNTING ID"],
                                    'po_number': row["PURCHASE ORDER NUMBER"],
                                    'po_date': row["PO DATE"],
                                    'ship_to_name': row["SHIP TO NAME"],
                                    'ship_to_address_1': row["SHIP TO ADDRESS 1"],
                                    'ship_to_address_2': row["SHIP TO ADDRESS 2"],
                                    'ship_to_city': row["SHIP TO CITY"],
                                    'ship_to_state': row["SHIP TO STATE"],
                                    'ship_to_zip': row["SHIP TO ZIP"],
                                    'ship_to_country': row["SHIP TO COUNTRY"],
                                    'store_number': row["STORE NUMBER"],
                                    'bill_to_name': row["BILL TO NAME"],
                                    'bill_to_address_1': row["BILL TO ADDRESS 1"],
                                    'bill_to_address_2': row["BILL TO ADDRESS 2"],
                                    'bill_to_city': row["BILL TO CITY"],
                                    'bill_to_state': row["BILL TO STATE"],
                                    'bill_to_zip': row["BILL TO ZIP"],
                                    'bill_to_country': row["BILL TO COUNTRY"],
                                    'bill_to_code': row["BILL TO CODE"],
                                    'ship_via': row["SHIP VIA"],
                                    'ship_date': row["SHIP DATE"],
                                    'terms': row["TERMS"],
                                    'note': row["NOTE"],
                                    'department_number': row["DEPARTMENT NUMBER"],
                                    'cancel_date': row["CANCEL DATE"],
                                    'do_not_ship_before': row[
                                        "DO NOT SHIP BEFORE"],
                                    'do_not_ship_after': row["DO NOT SHIP AFTER"],
                                    'allowance_percent_1': row[
                                        "ALLOWANCE PERCENT 1"],
                                    'allowance_amount_1': row[
                                        "ALLOWANCE AMOUNT 1"],
                                    'allowance_percent_2': row[
                                        "ALLOWANCE PERCENT 2"],
                                    'allowance_amount_2': row[
                                        "ALLOWANCE AMOUNT 2"],
                                    'line_num': row["LINE #"],
                                    'vendor_part_num': row["VENDOR PART #"],
                                    'buyers_part_num': row["BUYERS PART #"],
                                    'upc_num': row["UPC #"],
                                    'description': row["DESCRIPTION"],
                                    'quantity': row["QUANTITY"],
                                    'uom': row["UOM"],
                                    'unit_price': row["UNIT PRICE"],
                                    'pack_size': row["PACK SIZE"],
                                    'num_of_inner_packs': row["# OF INNER PACKS"],
                                    'item_allowance_percent': row[
                                        "ITEM ALLOWANCE PERCENT"],
                                    'item_allowance_amount': row[
                                        "ITEM ALLOWANCE AMOUNT"],
                                    'state': "Testing",
                                    }
                            # DO VALIDATIONS
                            STATE = self.env['captivea.ediprocess']._validate_order(vals)
                            vals['state'] = STATE
                            res = self.env['captivea.ediprocess']._write_edi_doclog(vals)

                            if not vals['po_number'] in current_orders:
                                current_orders.append(vals['po_number'])
                            if not res:
                                return False
                # Delete files once processed
                ##### This code is commented for testing purpose as we dont need to remove the file.
                # for attr in directory_structure:
                #     file_path = ftpgpath + '/' + attr.filename
                #     if sftp.isfile(file_path):
                #         try:
                #             sftp.remove(file_path)
                #         except:
                #             continue
                sftp.close()
                return current_orders
            else:
                return False
        except Exception as e:
            if len(e.args) > 1:
                if e.args[1] == 22:
                    raise Warning('Invalid Server Details')
                raise Warning(e.args[1])
            else:
                raise Warning(e.args[0])

    def _create_edi_poack(self, current_orders, DOC_PREFIX_POA):
        """
        This function create new file based on import that has been log.
        :param current_orders:
        :param DOC_PREFIX_POA:
        :return:
        """
        company = self.env.company
        ftpserver = company['ftp_server']
        ftpport = company['ftp_port']
        ftpuser = company['ftp_user']
        ftpsecret = company['ftp_secret']
        ftpdpath = company['ftp_dpath']
        for order in current_orders:
            file_name = '/tmp/' + str(DOC_PREFIX_POA) + '_' + str(order) + \
                        '_' + '.csv' # TO DO COMPLETE FILE NAME WITH CUSTOMER NAME
            with open(file_name, 'w+') as file_pointer:
                cvs_rows = []
                writer = csv.DictWriter(file_pointer, fieldnames=POA_FIELDS)
                writer.writeheader()
                rows = self.env['captivea.edidocumentlog'].sudo().search(
                    [('po_number', '=', order)])
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
                sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=22, cnopts=cnopts)
                if sftp:
                    sftp.cwd(ftpdpath)
                    sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_POA) + '_' + str(order) + '_.csv')
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

    def run_edi_process(self):
        current_orders = self._grab_ftp_files()
        if current_orders:
            # Write POA File to FTP
            self._create_edi_poack(current_orders, DOC_PREFIX_POA)
            self.state = 'done'
            return {
                'name': _('EDI Process Completed'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'captivea.ediprocess',
                'domain': [],
                'context': dict(self._context, active_ids=self.ids),
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self.id,
            }
        else:
            raise Warning('There are no files to process, or the logging or '
                          'connection have failed!')

    def reload(self):
        """
        Reload the page
        :return:
        """
        return {'type': 'ir.actions.client', 'tag': 'reload'}
