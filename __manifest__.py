# -*- coding: utf-8 -*-
{
    'name': 'Tablero EDI - Estado de Documentos Electrónicos SRI',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Localization',
    'summary': 'Visibilidad de estado de documentos electrónicos SRI (facturas, retenciones, guías de remisión)',
    'description': """
Tablero de estado de documentos electrónicos SRI para Olympo
==============================================================
Proyecto personal / hobby técnico. Consulta de solo lectura sobre los
documentos electrónicos generados por Olympo (bl.invoice, account.retention,
remission.guide.sri), inspirado conceptualmente en l10n_ec_edi_systray de
Trescloud, adaptado a la arquitectura custom de Olympo/Prosaf.

Fase 1 (MVP): vista SQL de solo lectura + vista lista/kanban interactiva.
Fase 2: systray de alertas (OWL).

No modifica el flujo de emisión/firma existente.
    """,
    'author': 'Jonathan',
    'license': 'LGPL-3',
    'depends': [
        'oly_base_billing',
        'account_journal',
        'oly_asset',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/edi_dashboard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
