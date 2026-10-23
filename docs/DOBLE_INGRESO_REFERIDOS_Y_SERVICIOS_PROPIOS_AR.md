# Modelo de doble ingreso: referidos + servicios propios cobrados a agentes

**Estado:** diseño comercial/ingeniería; no hay cobros activos ni ingresos verificados.  
**Rama:** `agent-to-agent-monetization-v1`.

## Decisión

El proyecto debe separar dos flujos que pueden coexistir, pero no deben confundirse ni cobrarse dos veces por el mismo concepto sin disclosure:

1. **Ingreso por referidos (demanda):** si un comprador llega a un servicio de un tercero por nuestra tienda y completa una contratación atribuida, la plataforma puede liquidar una comisión de referidor a nuestra wallet. La configuración actual reserva un 2,5% (250 bps). Depende de atribución y settlement real; no es un ingreso garantizado.
2. **Ingreso por nuestros propios servicios/agentes (oferta):** cuando un bot cliente contrata un servicio publicado por uno de nuestros agentes, el proyecto debe cobrar por el servicio que ofrecemos. En AgenC, el mecanismo nativo para una tarifa de operador es el `operator` leg de los listings/terms creados con esa configuración. La documentación de AgenC indica que la tarifa de operador y la de referidor son legs diferentes, se fijan en la contratación y se pagan en settlement; hay límites de tarifa combinada. No activar esa tarifa en la tienda actual hasta decidir qué servicio propio publicamos, su precio y el porcentaje, porque el config actual está intencionalmente limitado a referidos.
3. **Cobro directo por uso de nuestro software/API (futuro, independiente):** si otros bots usan nuestro SDK/API/worker como producto, necesitamos una política de precios propia (por tarea, uso o suscripción), un identificador idempotente por operación, evidencia de uso, autorización contractual, factura/recibo y reconciliación. El ledger actual solo calcula propuestas; no autentica clientes ni ejecuta cobros. No presentar ese mecanismo como implementado.

## Reglas de cobro

- No activar una tarifa ni inventar un porcentaje comercial hasta que exista definición de servicio, unidad facturable, moneda, política de reembolso y disclosure visible al cliente.
- No cobrar una comisión de operador sobre un servicio ajeno salvo que la plataforma y los términos permitan ese rol y la contratación lo refleje.
- No duplicar una tarifa directa de API y una tarifa on-chain por la misma prestación sin comunicar claramente ambas y verificar que los términos lo permiten.
- Cada evento debe estar ligado a una fuente verificable, una política versionada y un ID idempotente; self-referral, replays, eventos no confirmados, reversiones y políticas ambiguas deben fallar cerrados.
- Las tarifas de prueba en JSON son fixtures sintéticos y permanecen deshabilitadas. Un cálculo de comisión no equivale a un cobro ni a un settlement.
- No ejecutar pagos, claims, firmas, registro on-chain, despliegues pagos o activación de políticas en automático.

## Orden eficiente de implementación

1. Mantener el canal de referidos en preparación con 2,5%, sin operator leg, hasta que el registro, hosting, saldo receptor y coste total estén verificados.
2. Elegir el primer servicio propio vendible (por ejemplo, inspección/QA de archivos y entrega de reporte) y describir exactamente qué recibe el bot comprador.
3. Implementar una política de facturación separada de `agenc-demo-fee-v1`: `service_id`, `customer_agent_id`, `idempotency_key`, `usage_units`, `gross_amount`, `currency`, `policy_version`, `source_reference`, `status`, `refund/reversal` y estado de liquidación. Primero en modo simulado.
4. Probar con eventos sintéticos y fallos de red/reintentos; impedir doble cobro y nunca considerar pagada una factura sin confirmación de la fuente.
5. Comparar el cobro directo del servicio con el mecanismo operator de AgenC para elegir una sola ruta inicial o documentar claramente ambas.
6. Solo después de un piloto gratuito/sandbox y revisión de costes, presentar el porcentaje/precio y solicitar autorización concreta para activar cualquier cobro real.

## Criterios para afirmar que genera ingresos

Solo se informa ingreso cuando hay evidencia independiente de una contratación/uso facturable confirmado y un settlement o pago conciliado. Visitas, listings, tareas encontradas, comisiones calculadas, saldo informado por un endpoint sin conciliación y builds verdes no son ingresos.
