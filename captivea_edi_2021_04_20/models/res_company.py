# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResCompany(models.Model):    
    _inherit = 'res.company'
    
    ftp_server = fields.Char('FTP Server')
    ftp_port = fields.Integer('FTP Port')
    ftp_user = fields.Char('FTP User')
    ftp_secret = fields.Char('FTP Secret')
    ftp_gpath = fields.Char('FTP Grab Path') # the path where you get from files
    ftp_dpath = fields.Char('FTP Drop Path') # the path where you put to files
    ftp_tls = fields.Boolean('FTP TLS Enabled', default=True)
    enable_cron = fields.Boolean('Enable Automated Process', default=False)
    ir_cron_id = fields.Many2one('ir.cron', string='Configure Automated Process')

    @api.onchange('enable_cron')
    def switch_automated_cron(self):
        cron_id = self.env.ref('captivea_edi.ir_cron_captivea_edi_process_schedule')
        if cron_id and self.enable_cron:
            cron_id.active = True
            self.ir_cron_id = cron_id
        elif cron_id and not self.enable_cron:
            cron_id.active = False
            self.ir_cron_id = False
        elif not cron_id:
            self.ir_cron_id = False
