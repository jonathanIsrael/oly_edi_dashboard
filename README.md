# oly_edi_dashboard

Tablero de estado de documentos electrónicos SRI para Olympo (Odoo 16).

Proyecto personal para fortalecer conocimientos (incluye aprender OWL desde
cero) y aportar valor al producto que Prosaf comercializa. Inspirado
conceptualmente en `l10n_ec_edi_systray` (Trescloud), adaptado a la
arquitectura custom de Olympo — Prosaf no es partner de Odoo y no tiene
acceso a esa funcionalidad en su forma estándar.

## Alcance

- Solo lectura. No modifica el flujo existente de firma/envío al SRI.
- Cubre `bl.invoice` (módulo `oly_base_billing`), `account.retention`
  (módulo `oly_journal`) y `remission.guide.sri` (módulo `oly_asset`).

## Topología de bases de datos (importante)

No todos los clientes tienen los tres módulos fuente en la misma base de
datos:

- Clientes tipo GAD (ej. GADPA): un solo Odoo con todo instalado junto.
- Clientes de servicios (ej. EMSABA): dos bases *separadas* — una
  "comercial"/recaudación (`oly_base_billing`) y otra "financiera"
  (`oly_journal`, `oly_asset`). Son bases Postgres distintas, no solo
  módulos distintos — un `UNION ALL` entre ellas no es posible sin algo
  como `postgres_fdw`.

Por eso el módulo **no declara depends duro** de los tres módulos fuente
(ver `__manifest__.py`). La vista SQL debe verificar en `ir.module.module`
cuáles de los tres están instalados en la base actual y armar el
`UNION ALL` solo con esas tablas. El tablero, entonces, muestra lo que esa
base de datos puede ver — igual que cualquier otro módulo de Odoo.

## Fases

1. Vista SQL (`UNION ALL` de los tres modelos) + vista lista/kanban
   interactiva, con filtros y agrupar por.
2. Systray de alertas (componente OWL) con contador por categoría.

## Decisiones de arquitectura (Fase 0)

- `bl.invoice` y `account.retention` heredan el mixin `electronic.document`
  (`state_ce`, `authorization_ce`, `date_ce`, `key_ce`, `validation_info`).
- `remission.guide.sri` **no** hereda ese mixin — implementación propia,
  duplica los mismos campos SRI excepto `validation_info`, que no existe.
  Su `action_signer()` tampoco captura excepciones. Para guías, la categoría
  "rechazado con motivo" no es posible con los datos actuales.
- No existe un estado "rechazado" explícito en ningún modelo. Se infiere:
  - Autorizado: `state_ce` en (3, 4) y `authorization_ce` con valor.
  - Rechazado / inconsistencia: `state = 'approved'` y `state_ce` no en
    (3, 4) y `validation_info` empieza con `'Tipo de Error:'`
    (evidencia real, ver `INFORMACIÓN DE VALIDACIÓN` en capturas de
    producción — este prefijo lo genera el `except` de `action_signer()`).
  - Pendiente: mismo filtro de estado, pero sin ese prefijo (puede tener el
    dump de la respuesta exitosa del SRI, o "Sin información" por defecto,
    o vacío — ninguno de esos es un error).
- `bl.invoice` agrupa varios tipos de documento SRI bajo un mismo modelo
  (Factura, Nota de Crédito, Nota de Débito), distinguibles por
  `irs_id_code` (`01`, `04`, `05` respectivamente). El tablero debe
  normalizar esto a una columna `tipo_documento` propia, separada del
  modelo de origen.

## Estado actual

Fase 0 (análisis y arquitectura) completa. Siguiente paso: vista SQL.
