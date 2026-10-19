===========
WhatsApp Web
===========

.. |badge1| image:: https://img.shields.io/badge/maturity-Stable-brightgreen
    :target: https://odoo-community.org/page/development-status
    :alt: Stable
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

.. |badge3| image:: https://onlyone.odoo.com/web/image/website/1/logo/OnlyOne%20Soft?unique=dccda5b
    :target: https://onlyone.odoo.com
    :alt: OnlyOne Soft

|badge1| |badge2| |badge3|

This module extends the functionality of Odoo to support sending WhatsApp Web messages directly from Sales Orders, Invoices, and Purchase Orders, allowing you to communicate with customers and suppliers quickly and efficiently.

**Table of contents**

.. contents::
   :local:

Install
=======

This module does not require any special installation steps. Simply install it from the Apps menu in Odoo 18.

Configure
=========

To configure this module, you need to:

1. Go to Settings > Technical > Settings
2. Scroll down to the "WhatsApp" section
3. Configure the default messages for:
   - Sales Orders
   - Invoices
   - Purchase Orders

You can use placeholders in your messages:
- ``#CLIENTE`` - Customer/Partner name
- ``#PROVEEDOR`` - Supplier/Partner name
- ``#ORDEN`` - Sales Order number
- ``#FACTURA`` - Invoice number
- ``#MONTO`` - Total amount
- ``#NUMERO`` - Phone number (automatically replaced)

Usage
=====

1. Open a Sales Order, Invoice, or Purchase Order
2. Click the "Send WhatsApp" button (WhatsApp icon)
3. The system will automatically replace placeholders with actual data
4. WhatsApp Web will open in a new tab with the pre-filled message

Known issues / Roadmap
======================

* None at the moment

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/onlyone-soft/oo_whatsapp_web/issues>`_.

Credits
=======

Authors
~~~~~~~

* Be OnlyOne

Contributors
~~~~~~~~~~~~

* `Be OnlyOne. <https://onlyone.odoo.com/>`_
  
  * Matías Bressanello

Maintainers
~~~~~~~~~~~

This module is maintained by Be OnlyOne
