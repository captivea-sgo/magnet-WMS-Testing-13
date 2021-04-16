# -*- coding: utf-8 -*-

{
    "name": "Product Pricing Bucket", 
    "version": "13.0.0.2",
    "author": "", 
    "category": "Product", 
    "description": """

    """,
    "website": "", 
    "license": "Other proprietary", 
    "depends": [
        "base", "sale_management", "account", "stock"
    ], 
    "demo": [], 
    "data": [
        "security/ir.model.access.csv", 
        "views/pricing_bucket_views.xml",
        "views/product_product_view.xml",
        "views/product_pricelist_views.xml",
    ],
    "images": ['static/description/icon.png'],
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False,
    "active": False,
    'price': 29.99,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
