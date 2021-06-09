# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import csv
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
import pysftp

DOC_PREFIX_PO = '850'  # Prefix for Purchase Order Document
DOC_PREFIX_POC = '860'  # Prefix for Purchase Order Change Document
DOC_PREFIX_POA = '855'  # Prefix for Purchase Order Aknowledgment Document
DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
DOC_PREFIX_INV = '846'  # Prefix for Inventory Document
CURRENT_ORDERS = list()  # Current Processed Orders REMOVE THIS LATER NOT NEEDED ANYMORE
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

    sftp_instance = fields.Many2one('setu.sftp', 'Instance', domain=[('instance_active', '=', True)])
    active = fields.Boolean('Active?', default=True)
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='State', readonly=True, default='init')
    notification = fields.Text()
    import_850 = fields.Boolean()
    export_855 = fields.Boolean()

    def reload(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_execute(self):
        if self.import_850:
            res = self.run_edi_process()
        elif self.export_855:
            self.manual_export_poack()
            res = self.reload()

        return res

    def manual_export_poack(self):
        sales = self.env['sale.order'].search([('poack_created', '=', False),
                                               ('customer_po_ref', '!=', False),
                                               ('state', '=', 'sale')])
        for sale in sales:
            sale.poack_export(sale.poack_ref, '855')

    @api.model
    def _write_edi_doclog(self, vals, log_id):
        try:
            doclog = self.env['captivea.edidocumentlog']
            log = doclog.sudo().create_and_add(vals, log_id)
            return log
        except:
            pass

    def _validate_order(self, vals):
        """
        Function validate the request qty, product, customer, etc.
        :param vals:
        :return: status / validation msg
        """
        # Partner Validation

        if not self.env['res.partner'].sudo().search(
                [('name', '=', vals['accounting_id']),
                 ('x_edi_flag', '=', True)]):
            validation_msg = "Failed! Customer does not exists."
        else:
            # Product Validation
            if not self.env['product.product'].sudo().search(
                    [('default_code', '=', vals['vendor_part_num'].strip())]):
                validation_msg = "Failed! Product does not exists."
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
        failed_log_ids = self.env['setu.edi.log']
        files_to_remove = list()
        # company = self.env.company
        # sftp_conf = self.env['setu.sftp'].search([('company_id', '=', company.id)])
        sftp_conf = self.sftp_instance
        ftpserver = sftp_conf['ftp_server']
        if not ftpserver:
            raise Warning('FTP Host parameter missed!')
        ftpport = sftp_conf['ftp_port']
        if not ftpport:
            raise Warning('FTP Port parameter missed!')
        ftpuser = sftp_conf['ftp_user']
        if not ftpuser:
            raise Warning('FTP User parameter missed!')
        ftpsecret = sftp_conf['ftp_secret']
        if not ftpsecret:
            raise Warning('FTP password parameter missed!')
        ftpgpath = sftp_conf['ftp_gpath']
        if not ftpgpath:
            raise Warning('FTP GrabPath parameter missed!')
        ftpdpath = sftp_conf['ftp_poack_dpath']
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
                        log_id = False
                        log_ids = self.env['setu.edi.log']
                        for row in csvdata:  # Processing file begins here.
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
                                    'vendor_part_num': row["VENDOR PART #"].strip(),
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
                            log_id = self.env['setu.edi.log'].search([('po_number', '=', vals['po_number']),
                                                                      ('type', '=', 'import'),
                                                                      ('document_type', '=', '850')])
                            if not log_id:
                                log_id = self.env['setu.edi.log'].create({
                                    'po_number': vals['po_number'],
                                    'type': 'import',
                                    'document_type': '850'
                                })
                            log_ids |= log_id

                            STATE = self.env['captivea.ediprocess']._validate_order(vals)
                            vals['state'] = STATE
                            self.env['captivea.ediprocess']._write_edi_doclog(vals, log_id)

                        success_log_ids = log_ids.filtered(lambda l: l.status == 'success')
                        failed_log_ids = log_ids.filtered(lambda l: l.status != 'success')
                        if success_log_ids:
                            for log in success_log_ids:
                                current_orders.append(log_id.po_number)
                                order = self.env['captivea.edidocumentlog']._create_sale_order(log)
                                log.sale_id = order
                                file_path = ftpgpath + '/' + attr.filename
                                files_to_remove.append(file_path)
                                # if sftp.isfile(file_path):
                                #     try:
                                #         # sftp.remove(file_path)
                                #         sftp.remove(file_path)
                                #     except Exception as e:
                                #         continue
                # for file_path in files_to_remove:
                #     if sftp.isfile(file_path):
                #         try:
                #             # sftp.remove(file_path)
                #             sftp.remove(file_path)
                #         except Exception as e:
                #             continue
                sftp.close()

            sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport,
                                     cnopts=cnopts)
            if sftp:
                for file_path in files_to_remove:
                    if sftp.isfile(file_path):
                        try:
                            sftp.remove(file_path)
                        except Exception as e:
                            continue

                return current_orders, failed_log_ids
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
        current_orders, failed_log_ids = self._grab_ftp_files()
        if failed_log_ids:
            log_names = " ,".join(failed_log_ids.mapped('seq'))
        if current_orders and not failed_log_ids:
            self.notification = 'All files processed successfully.'
        elif current_orders and failed_log_ids:
            self.notification = 'Operation completed successfully but some of the files could not process. Please ' \
                                'check log of ' + log_names
        elif failed_log_ids and not current_orders:
            self.notification = 'All files failed processing. Please check log of ' + log_names
        else:
            self.notification = 'No files found to process.'

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
