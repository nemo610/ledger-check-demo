# Facturación simulada de servicios propios

**Estado:** implementado como cálculo determinista; no cobra ni prueba liquidación.  
**Módulo:** `agent_economy/first_party_billing.py`  
**Pruebas:** `tests/test_first_party_billing.py`

## Separación obligatoria

- `referral_commission`: comisión potencial por derivar demanda hacia un proveedor externo; se calcula en el ledger de comisiones existente.
- `first_party_service_charge`: propuesta por uso de un servicio cuyo proveedor somos nosotros.
- `first_party_service_reversal`: propuesta negativa que referencia un cargo previo; no es un reembolso real ni una transacción.

Estos tipos no se mezclan. Un resultado del módulo no es una factura fiscal, cobro, transferencia, settlement ni ingreso recibido.

## Esquema de política

Cada política de servicio propio requiere `policy_id`, `service_id`, `policy_version`, `currency`, `unit_price` y `enabled`. La política debe permanecer `enabled=false` hasta que se aprueben precio, unidad facturable, alcance, términos, reembolsos y disclosure al cliente. El código no define una tarifa comercial predeterminada.

## Esquema de uso

Cada evento requiere `event_id`, `service_id`, `customer_agent_id`, `provider_agent_id`, `idempotency_key`, `usage_units`, `currency`, `policy_version` y `status`. Se puede aportar `source_reference`; una reversión necesita `reverses_event_id`.

El cálculo se rechaza o deja sin cargo cuando hay política deshabilitada/ambigua, moneda distinta, uso no confirmado, importes/unidades inválidos, auto-cobro o reintentos duplicados. El estado de liquidación es siempre `settlement_verified=false`.

## Ejecutar pruebas

```bash
python -m unittest tests.test_first_party_billing -v
python -m unittest discover -s tests -v
```

## Límites y siguiente paso

El módulo es un libro mayor de propuestas en memoria: no autentica clientes, no comprueba por sí solo que el uso ocurrió, no guarda un registro durable, no emite factura fiscal y no integra un proveedor de pagos. Antes de cobrar se requiere una fuente de uso autorizada, persistencia transaccional con restricción única de idempotencia, términos de servicio, comprobantes y conciliación. Mantener desactivado hasta completar esa integración y revisión comercial/legal.
