# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _name = 'setu.sftp'
    _rec_name = 'company_id'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    ftp_server = fields.Char('FTP Server', required=True)
    ftp_port = fields.Integer('FTP Port', required=True)
    ftp_user = fields.Char('FTP User', required=True)
    ftp_secret = fields.Char('FTP Secret', required=True)
    ftp_gpath = fields.Char('FTP 850 Path', required=True)  # the path where you get from files
    ftp_poack_dpath = fields.Char('FTP 855 Drop Path', required=True)  # the path where you put to files
    ftp_shipack_dpath = fields.Char('FTP 856 Drop Path', required=True)
    ftp_invack_dpath = fields.Char('FTP 810 Drop Path', required=True)
    ftp_tls = fields.Boolean('FTP TLS Enabled', default=True)
    enable_cron = fields.Boolean('Enable Automated Process', default=False)
    ir_cron_id = fields.Many2one('ir.cron', string='Configure Automated Process')

    @api.constrains('company_id')
    def validate_company(self):
        if self.search(
                [('id', '!=', self.id), ('company_id', '=', self.company_id.id), ('ftp_server', '=', self.ftp_server)]):
            raise ValidationError(_('Company Configuration already exists.'))

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
