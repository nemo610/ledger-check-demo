# Preparación del trabajador autónomo AgenC — antes de wallet

## Objetivo
Este documento separa tres componentes que no deben confundirse:

1. **Monitor de ingresos** (`agent_economy/monitor.py`): solo lectura, no produce ingresos.
2. **Referente/operador**: storefront o listings de AgenC que atribuyen una comisión al titular bajo las reglas del protocolo.
3. **Trabajador autónomo**: agente registrado que descubre tareas, verifica el job spec, reclama una tarea, produce un entregable y lo envía para revisión/aceptación.

## Integración oficial investigada

La documentación oficial distingue el Marketplace Agent Kit (CLI/MCP/controles de firma), el SDK para integrar operaciones en código y el paquete worker `@tetsuo-ai/agenc-worker`. Antes de instalar o conectar un worker hay que verificar la versión coordinada actual en `https://api.agenc.ag/api/versions` y la versión exacta publicada del paquete; no instalar una versión aproximada con `^` para una operación de mainnet.

Referencias:
- Kit oficial: https://agenc.ag/docs/kit
- Brief oficial para conectar un worker: https://agenc.ag/docs/agent-briefs/wire-a-worker
- Configuración de wallet: https://agenc.ag/docs/wallet-setup
- Integración y controles de firma: https://agenc.ag/integrations
- Costos y distribución de comisiones: https://agenc.ag/docs/fees
- Venta de servicios como proveedor: https://agenc.ag/docs/quickstart-providers

## Modelo de ingresos: distinguir las dos vías

- **Ingreso por trabajo:** el agente ejecuta una tarea remunerada y cobra la parte asignada al worker después de la aceptación/liquidación.
- **Comisión de operador o referidor:** una listing/store puede recibir una parte de la liquidación si la contratación atribuye correctamente ese rol y los porcentajes quedaron fijados al crear la listing/contratación. No se cobra automáticamente una comisión por cualquier operación de cualquier bot.
- El protocolo cobra actualmente una comisión de referencia del 5%; la comisión de operador puede llegar hasta 20% y la de referidor hasta 20%, con un máximo combinado de 40% para las partes distintas del worker. El worker conserva al menos 60% del importe de la tarea. Verificar siempre la política vigente y las condiciones de cada flujo.

## Costos: el stake no es el presupuesto total

- **Registro:** la documentación oficial indica un stake de referencia de 0.01 SOL para registrar un agente. Antes de operar hay que leer en vivo `ProtocolConfig.minAgentStake`; no se debe hardcodear ni financiar por adelantado.
- **Renta de cuentas y comisiones de red:** el registro crea una cuenta de agente y cada tarea puede crear cuentas adicionales. Los importes de rent exemption se consultan en la red y pueden variar con el tamaño de cuenta/protocolo.
- **Claims:** el worker oficial verifica el saldo antes de reclamar; puede necesitar renta de cuentas de claim y submission, margen de comisiones de transacción y, para tareas de tipo contest, un depósito reembolsable de 0.01 SOL.
- **Wallet receptora de comisiones:** cada wallet que vaya a recibir una comisión de operador/referidor debe tener al menos 890.880 lamports (0.00089088 SOL) para rent exemption de una cuenta de sistema de cero datos; una wallet nueva con saldo cero puede hacer fallar la liquidación.
- **Hosting/RPC:** la ejecución puede requerir una URL HTTPS pública y un RPC. Se priorizarán opciones gratuitas, pero el precio y los límites se deben verificar antes de desplegar. No se ha contratado ni activado ningún servicio pago.

Por lo tanto, **0.01 SOL es el stake de registro de referencia, no una garantía de que alcanza para registrar, publicar, reclamar y completar trabajos**. El monto total debe calcularse con los requisitos actuales que muestre el preflight, sin añadir fondos automáticamente.

## Requisitos antes de activarlo

- El titular debe configurar la wallet y custodiar localmente la frase semilla/clave privada. Nunca compartirla por chat ni guardarla en GitHub, Jules, logs o archivos del proyecto.
- Leer el mínimo de stake vigente desde el protocolo y consultar los requisitos de rent/fees antes de registrar.
- Usar una hot wallet de bajo saldo para limitar el impacto de un error. No usar una wallet principal con fondos importantes.
- Configurar un RPC compatible con las consultas requeridas; el RPC público puede limitar consultas y no es ideal para un proceso continuo.
- Definir capacidades permitidas, recompensa mínima, tipos de tareas admitidas, tiempo máximo, límite de saldo y procedimiento de apagado.
- Probar primero el descubrimiento en modo de solo lectura. No registrar, reclamar ni enviar transacciones hasta revisar la previsualización y recibir autorización explícita.

## Secuencia de trabajo preparada

1. **Descubrimiento sin firma:** listar tareas públicas y filtrar por capacidades, recompensa y criterios de seguridad.
2. **Validación:** recuperar el job spec fijado en cadena y verificar su hash antes de reclamar.
3. **Registro:** operación on-chain de una sola vez, con stake; bloqueada hasta la aprobación del titular.
4. **Claim:** previsualizar la transacción exacta y revisar coste/cuenta/destino antes de autorizarla.
5. **Ejecución:** correr solo tareas que el agente pueda completar; no aceptar tareas con requisitos de secretos, gastos externos o acciones irreversibles sin aprobación.
6. **Entrega:** alojar el artefacto, calcular su SHA-256 y previsualizar el envío.
7. **Cobro:** esperar aceptación/settlement y verificar el recibo público en cadena; un envío no equivale a un pago recibido.

## Lo que no se hará automáticamente

- Crear o custodiar una wallet por el titular.
- Pedir o almacenar una frase semilla en este repositorio.
- Financiar stake, rentas o comisiones.
- Aprobar transacciones de mainnet, publicar listings o activar el bucle de claims.
- Declarar ingresos antes de que exista una liquidación conciliada.

## Estado al preparar esta guía

La rama contiene un ledger de comisiones propuestas y un monitor de hires en modo lectura. También contiene un worker simulado que valida envelopes normalizados, atribución, hash, recompensa, deadline, capacidades y duplicados; todavía no está conectado al Marketplace Agent Kit/worker oficial ni procesa tareas reales. El proyecto no tiene una wallet cargada, no está desplegado externamente y no ha completado una tarea remunerada. El siguiente tramo debe integrar la versión oficial verificada, terminar el servicio HTTPS de artefactos y ensayar el ciclo completo en modo simulado. Las operaciones con firma seguirán bloqueadas hasta que el titular configure la wallet y apruebe expresamente su activación.
