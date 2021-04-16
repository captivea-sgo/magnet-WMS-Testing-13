# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Captivea EDI',
    'version': '13.0.1',
    'author': 'Captivea LLC',
    'summary': 'Handle EDI documents',
    'category': 'Extra Tools',
    'website': 'https://www.captivea.us',
    'depends': ['base_setup', 'sale', 'stock'],
    'data': ['security/captivea_edi_security_groups.xml',
             'security/ir.model.access.csv',
             'views/res_company.xml',
             'views/captivea_edi_views.xml',
             'views/captivea_edi_wizard_views.xml',
             'views/captivea_menu.xml',
             'views/sale_views.xml',
             'data/ir_cron_jobs.xml',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
