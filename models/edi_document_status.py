# -*- coding: utf-8 -*-
from odoo import fields, models, tools

SOURCE_MODULES = ['oly_base_billing', 'oly_journal', 'oly_asset']


class EdiDocumentStatus(models.Model):
    """
    Vista de solo lectura que normaliza el estado SRI de los documentos
    electrónicos de Olympo (bl.invoice, account.retention,
    remission.guide.sri).

    El UNION ALL se arma dinámicamente en init() según qué módulos fuente
    estén REALMENTE instalados en esta base de datos: no todos los
    clientes tienen los tres juntos (ver README.md - topología de bases
    separadas "comercial"/"financiera" vs. bases únicas tipo GAD).

    Simplificaciones conscientes de esta v1, a validar con datos reales:

    - El filtro "es un documento electrónico real" en bl.invoice usa
      `proform = 'FC'` + `state_ce IS NOT NULL` como proxy. El campo real
      `electronic_document` es un compute NO almacenado (depende de
      journal_id.authorization_ids -> authorization_id.is_electronic), y
      esa cadena de relaciones todavía no está mapeada. Si los conteos no
      cuadran con lo que se ve en la UI agrupada por "Estado SRI", este es
      el primer lugar a revisar.
    - Los ids se desplazan por origen (bl.invoice sin desplazar,
      account.retention +1_000_000_000, remission.guide.sri
      +2_000_000_000) para evitar colisión entre los tres orígenes, que
      tienen secuencias de id independientes. Asume que ningún modelo
      individual va a superar ~1000 millones de registros - razonable
      hoy, pero es una simplificación, no una garantía matemática.
    - remission.guide.sri no tiene validation_info (no hereda
      electronic.document - ver README), así que nunca puede caer en la
      categoría "rechazado" con motivo, solo "pendiente" sin detalle.
    """
    _name = 'edi.document.status'
    _description = 'Estado de Documento Electrónico SRI'
    _auto = False
    _order = 'document_date desc'

    res_model = fields.Char(string='Modelo origen', readonly=True)
    res_id = fields.Integer(string='ID del registro', readonly=True)
    document_number = fields.Char(string='Número', readonly=True)
    document_date = fields.Date(string='Fecha', readonly=True)
    partner_name = fields.Char(string='Cliente', readonly=True)
    tipo_documento = fields.Char(string='Tipo de documento', readonly=True)
    business_state = fields.Char(string='Estado', readonly=True)
    state_ce = fields.Char(string='Estado SRI', readonly=True)
    authorization_ce = fields.Char(string='Autorización', readonly=True)
    validation_info = fields.Text(string='Información de validación', readonly=True)
    categoria = fields.Selection([
        ('autorizado', 'Autorizado'),
        ('pendiente', 'Pendiente'),
        ('rechazado', 'Rechazado / Inconsistencia'),
        ('enviado_sin_autorizar', 'Enviado sin autorizar'),
        ('anulado', 'Anulado'),
        ('otro', 'Otro'),
    ], string='Categoría', readonly=True)

    # --- CONSTRUCCIÓN DINÁMICA DE LA VISTA -----------------------------

    def _get_installed_sources(self):
        modules = self.env['ir.module.module'].sudo().search([
            ('name', 'in', SOURCE_MODULES),
            ('state', '=', 'installed'),
        ]).mapped('name')
        return set(modules)

    def _get_excluded_journal_codes(self):
        """
        Diarios a excluir de la vista, configurados por base de datos.

        No es una regla de negocio universal: es un hallazgo de
        calidad de datos específico de cada cliente (diarios de migración
        o carga masiva mal etiquetados). Cada instalación decide su propia
        lista vía parameter, en vez de que el módulo la asuma para
        todos los clientes.

        Vacío por defecto: un cliente nuevo no pierde ningún documento
        hasta que alguien audite su data real y configure explícitamente.
        """
        param = self.env['ir.config_parameter'].sudo().get_param(
            'oly_edi_dashboard.excluded_journal_codes', ''
        )
        return [c.strip() for c in param.split(',') if c.strip()]

    def _select_bl_invoice(self):
        excluded = self._get_excluded_journal_codes()
        journal_filter = ""
        if excluded:
            codes = ", ".join("'%s'" % c.replace("'", "''") for c in excluded)
            journal_filter = "AND (aj.code IS NULL OR aj.code NOT IN (%s))" % codes

        return """
            SELECT
                bi.id AS id,
                'bl.invoice' AS res_model,
                bi.id AS res_id,
                bi.invoice_number AS document_number,
                bi.date_invoice AS document_date,
                rp.name AS partner_name,
                CASE
                    WHEN bi.irs_id_code = '01' AND bi.type = 'out_invoice' THEN 'Factura'
                    WHEN bi.irs_id_code = '04' AND bi.type = 'out_refund'  THEN 'Nota de Crédito'
                    WHEN bi.irs_id_code = '05' AND bi.type = 'out_invoice' THEN 'Nota de Débito'
                    ELSE 'Otro (irs_id_code=' || COALESCE(bi.irs_id_code, '?') || ', type=' || COALESCE(bi.type, '?') || ')'
                END AS tipo_documento,
                bi.state AS business_state,
                bi.state_ce AS state_ce,
                bi.authorization_ce AS authorization_ce,
                bi.validation_info AS validation_info
            FROM bl_invoice bi
            LEFT JOIN res_partner rp ON rp.id = bi.partner_id
            LEFT JOIN account_journal aj ON aj.id = bi.journal_id
            WHERE bi.proform = 'FC' AND bi.state_ce IS NOT NULL
                %s
        """ % journal_filter

    def _select_account_retention(self):
        return """
            SELECT
                (ar.id + 1000000000) AS id,
                'account.retention' AS res_model,
                ar.id AS res_id,
                ar.retention_number AS document_number,
                ar.date AS document_date,
                rp.name AS partner_name,
                'Retención' AS tipo_documento,
                ar.state AS business_state,
                ar.state_ce AS state_ce,
                ar.authorization_ce AS authorization_ce,
                ar.validation_info AS validation_info
            FROM account_retention ar
            LEFT JOIN res_partner rp ON rp.id = ar.partner_id
            WHERE ar.state_ce IS NOT NULL
        """

    def _select_remission_guide(self):
        return """
            SELECT
                (rg.id + 2000000000) AS id,
                'remission.guide.sri' AS res_model,
                rg.id AS res_id,
                rg.guide_number AS document_number,
                rg.guide_date AS document_date,
                rg.receipt_name AS partner_name,
                'Guía de Remisión' AS tipo_documento,
                rg.state AS business_state,
                rg.state_ce AS state_ce,
                rg.authorization_ce AS authorization_ce,
                NULL::text AS validation_info
            FROM remission_guide_sri rg
            WHERE rg.state_ce IS NOT NULL
        """

    def _select_empty(self):
        # Ninguno de los tres módulos fuente está instalado en esta base:
        # la vista queda vacía en vez de romper la instalación del módulo.
        return """
            SELECT
                NULL::integer AS id,
                NULL::varchar AS res_model,
                NULL::integer AS res_id,
                NULL::varchar AS document_number,
                NULL::date AS document_date,
                NULL::varchar AS partner_name,
                NULL::varchar AS tipo_documento,
                NULL::varchar AS business_state,
                NULL::varchar AS state_ce,
                NULL::varchar AS authorization_ce,
                NULL::text AS validation_info
            WHERE false
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        installed = self._get_installed_sources()
        branches = []
        if 'oly_base_billing' in installed:
            branches.append(self._select_bl_invoice())
        if 'oly_journal' in installed:
            branches.append(self._select_account_retention())
        if 'oly_asset' in installed:
            branches.append(self._select_remission_guide())
        if not branches:
            branches.append(self._select_empty())

        union_sql = " UNION ALL ".join(branches)

        sql = ("""SELECT
                    src.*,
                    CASE
                        WHEN src.state_ce IN ('3', '4')
                             AND src.authorization_ce IS NOT NULL
                             AND src.authorization_ce != ''
                            THEN 'autorizado'
                        WHEN src.business_state = 'approved'
                             AND src.state_ce = '4'
                             AND (src.authorization_ce IS NULL OR src.authorization_ce = '')
                            THEN 'enviado_sin_autorizar'
                        WHEN src.business_state = 'approved'
                             AND (src.state_ce IS NULL OR src.state_ce NOT IN ('3', '4'))
                             AND src.validation_info LIKE 'Tipo de Error:%%'
                            THEN 'rechazado'
                        WHEN src.business_state = 'approved'
                             AND (src.state_ce IS NULL OR src.state_ce NOT IN ('3', '4'))
                            THEN 'pendiente'
                        WHEN src.business_state = 'cancel'
                            THEN 'anulado'
                        ELSE 'otro'
                    END AS categoria
                FROM (%s) src""") % union_sql
        print(sql)

        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    src.*,
                    CASE
                        WHEN src.state_ce IN ('3', '4')
                             AND src.authorization_ce IS NOT NULL
                             AND src.authorization_ce != ''
                            THEN 'autorizado'
                        WHEN src.business_state = 'approved'
                             AND src.state_ce = '4'
                             AND (src.authorization_ce IS NULL OR src.authorization_ce = '')
                            THEN 'enviado_sin_autorizar'
                        WHEN src.business_state = 'approved'
                             AND (src.state_ce IS NULL OR src.state_ce NOT IN ('3', '4'))
                             AND src.validation_info LIKE 'Tipo de Error:%%'
                            THEN 'rechazado'
                        WHEN src.business_state = 'approved'
                             AND (src.state_ce IS NULL OR src.state_ce NOT IN ('3', '4'))
                            THEN 'pendiente'
                        WHEN src.business_state = 'cancel'
                            THEN 'anulado'
                        ELSE 'otro'
                    END AS categoria
                FROM (%s) src
            )
        """ % (self._table, union_sql))
