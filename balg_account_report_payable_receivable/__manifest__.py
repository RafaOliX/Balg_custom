# Copyright (C) 2024 Bryan Gomez
#  (<Bryan.gomez1311@gmail.com>)
# Licencia: Propietaria. Todos los derechos reservados.
# Este archivo forma parte de un módulo personalizado para Odoo.
{
    "name": "Venezuela - Report Payable Receivable Balg",
    "version": "16.0.4.1.1",
    "author": "Holos",
    "countries": ['ve'],
    "contributors": [
        "Bryan Gomez <bryam.gomez1311@gmail.com>",
        "Rafael Olivares <rafaolix59@gmail.com>",
    ],
    "maintainers": [
        "Bryan Gomez <bryam.gomez1311@gmail.com>",
        "Rafael Olivares <rafaolix59@gmail.com>",
    ],
    "summary": "Account Payable Receivable Balg",
    "category": "Accounting/Localizations/Account Charts",
    "website": "",
    "depends": ['l10n_ve_account_sequence_number', 'report_xlsx'],
    "data": [
        "security/ir.model.access.csv",
        "report/ir_action_report.xml",
        "views/report_account_payable_receivable.xml",
        "wizard/account_payable_receivable_wizard_view.xml",
        "views/menuitem.xml"
    ],
    'license': 'LGPL-3',
    "installable": True,
    "application": False,
    "auto_install": False
}
