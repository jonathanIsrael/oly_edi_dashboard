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
    # OJO: no se declara depends duro de oly_base_billing / oly_journal / oly_asset.
    # No siempre conviven en la misma base de datos (clientes tipo GAD: sí;
    # clientes con bases separadas "comercial"/"financiera" como EMSABA: no).
    # La vista SQL detecta en tiempo de instalación/actualización, vía
    # ir.module.module, cuáles de los tres módulos fuente están realmente
    # instalados en ESTA base, y arma el UNION ALL solo con esas tablas.
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'views/edi_dashboard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
