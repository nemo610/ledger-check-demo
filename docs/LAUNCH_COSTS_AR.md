# Costes y autorización de lanzamiento — Nemo Agent Store

**Fecha de revisión:** 2026-10-23  
**Rama de trabajo:** `agent-to-agent-monetization-v1`  
**Estado:** preparación técnica; NO desplegado ni registrado en mainnet.

## Estrategia de salida recomendada

Lanzar primero una tienda de referidos para mostrar servicios ya disponibles en AgenC. La tienda usa una wallet pública como destino de comisiones y una tarifa inicial propuesta de 2.5% por contratación referida. Después, si el coste total resulta aceptable, publicar un servicio propio CSV/JSON QA con operador al 5%; cuando una contratación aplique ambos legs, la misma wallet recibiría 7.5% del importe bruto entre referidor y operador. La comisión de protocolo vigente publicada es 5%, así que la carga total típica sería 12.5% y el proveedor que realiza el trabajo conservaría 87.5%. En servicios de terceros donde sólo aplique el referidor, el ingreso propuesto sería 2.5% del importe liquidado.

Son tarifas configurables y propuestas, no ingresos asegurados. No se generan comisiones por visitas, despliegues o listings sin contrataciones que lleguen a liquidarse.

## Costes identificados

| Concepto | Evidencia actual | Qué falta antes de pagar |
|---|---|---|
| Hosting de la tienda | La tienda es una app Next.js; el repositorio no está desplegado. Puede evaluarse un plan gratuito, pero no se ha contratado ningún proveedor. | Elegir proveedor y verificar límites/precio vigente; no comprar dominio de pago en el primer intento si una URL HTTPS gratuita sirve. |
| RPC Solana mainnet | La documentación oficial recomienda un RPC propio; no se ha configurado uno. | Elegir endpoint y confirmar si tiene plan gratuito, límites y cargos. No guardar URL con token en logs o Git. |
| Registro de agente proveedor | La documentación oficial publica un stake mínimo de referencia de **0.01 SOL**; hay que leer `ProtocolConfig.minAgentStake` en vivo antes de la transacción. | Confirmar el valor en mainnet, el tratamiento/retiro del stake y autorizar expresamente la firma. |
| Listing de servicio | Requiere una cuenta on-chain y por tanto rent-exemption y fee de transacción. | Consultar el tamaño real de cuenta, rent-exemption actual y simulación de la transacción; importe aún no confirmado. |
| Wallet receptora de comisiones | Los destinatarios de legs SOL deben mantener al menos **890,880 lamports** (0.00089088 SOL) para rent exemption, según la documentación actual. | Verificar el saldo actual de la wallet pública y si hace falta un pequeño fondeo. |
| Fee de protocolo | La documentación pública indica **5% (500 bps) hoy**, sujeto a la configuración vigente. | Releer configuración live antes de cualquier transacción o publicación. |
| Comisiones propias | Configuración de lanzamiento propuesta: **2.5% referrer + 5% operator**. | Aprobar la política comercial y comprobar que la combinación aplica al tipo de contratación. |
| Costes de compra/venta y transacciones | Los paga la wallet que firma la acción correspondiente; el RPC/hosting pueden añadir cargos. | Estimar en simulación y revisar cada transacción antes de firmar. |

Fuentes oficiales para revalidar:  
- https://agenc.ag/docs/launch-a-marketplace  
- https://agenc.ag/docs/agent-briefs/sell-a-service  
- https://agenc.ag/protocol  
- https://agenc.ag/docs/wallet-setup

## Separar los dos caminos

### A. Referidos primero — menor compromiso inicial

1. Confirmar wallet pública receptora (dirección solamente; nunca seed phrase ni clave privada).
2. Elegir hosting con URL HTTPS y confirmar coste real.
3. Generar y compilar la tienda con fee de referidor 2.5%.
4. Revisar y aprobar publicación/registro de la tienda si la plataforma lo exige; antes de firmar, mostrar el resumen exacto de la transacción y su coste.
5. Verificar el listing/storefront público, el flujo de contratación y la lectura del endpoint de earnings.
6. Promocionar servicios relevantes de forma legítima; medir clics y contrataciones, pero contabilizar ingresos sólo con settlement confirmado.

### B. Servicio propio + operador — requiere presupuesto on-chain

Además del camino A: registrar el agente (stake mínimo de referencia 0.01 SOL), publicar la oferta, alojar el JSON de especificación con hash verificable, pasar moderación, desplegar el endpoint de entrega con HTTPS y probar aceptación. El coste de rent, RPC, hosting y transacciones se debe mostrar antes de autorizar cada firma.

## Bloqueos de seguridad

- No se guardará ninguna clave privada, seed phrase ni token de RPC en GitHub, Jules, logs o chat.
- No se usará la wallet principal como signer automatizado. Si se activa una wallet de operación, será de bajo saldo y con límites explícitos.
- No habrá claims automáticos, transacciones firmadas, publicación de mainnet ni transferencias sin aprobación concreta de los costes y la acción.
- El saldo de una tarea publicada no se cuenta como ingreso. Sólo un recibo de liquidación confirmado cuenta como comisión.
- El código actual del auditor de tareas es de sólo lectura y mantiene `live_execution_enabled=false`; aún no prueba derivación canónica de PDA ni vínculo on-chain del hash de especificación.

## Decisiones que necesitará confirmar el titular

Se pedirán únicamente cuando estén listos los previews técnicos:
1. Dirección pública de la wallet de comisiones (si no está ya configurada en el entorno local).
2. URL/hosting seleccionado y coste mensual exacto (idealmente cero al inicio).
3. Presupuesto máximo en SOL para stake, rent y fees de transacción.
4. Aprobación de las tarifas de 2.5% referidor y 5% operador.
5. Aprobación separada de cada transacción de registro/publicación en mainnet.

**No se puede prometer que haya ganancias hoy.** El objetivo realista es llegar a una tienda publicada y verificable o, si el hosting/RPC/on-chain requiere un gasto aún no aprobado, dejarla lista para que el titular apruebe exactamente ese coste.
