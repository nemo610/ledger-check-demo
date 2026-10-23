# Preparación del trabajador autónomo AgenC — antes de wallet

## Objetivo

Este documento separa tres componentes que no deben confundirse:

1. **Monitor de ingresos** (`agent_economy/monitor.py`): solo lectura, no produce ingresos.
2. **Referente/operador**: storefront o listings de AgenC que atribuyen una comisión al titular bajo las reglas del protocolo.
3. **Trabajador autónomo**: agente registrado que descubre tareas, verifica el job spec, reclama una tarea, produce un entregable y lo envía para revisión/aceptación.

## Integración oficial investigada

La documentación oficial consultada describe el paquete `@tetsuo-ai/agenc-worker@^0.2.0` como la ruta de cero código para el ciclo de trabajo y la CLI `agenc-marketplace` como la herramienta para operar el marketplace con previsualizaciones y controles de firma.

Referencias:
- Kit oficial: https://agenc.ag/docs/kit
- Brief oficial para conectar un worker: https://agenc.ag/docs/agent-briefs/wire-a-worker
- Configuración de wallet: https://agenc.ag/docs/wallet-setup
- Integración y controles de firma: https://agenc.ag/integrations

## Requisitos antes de activarlo

- Crear la wallet personalmente y mantener su frase semilla/clave privada fuera del chat, GitHub, Jules y logs.
- Leer el mínimo de stake vigente desde el protocolo antes de registrar el agente; no asumir que el importe no cambió.
- La guía oficial consultada indica aproximadamente 0,021 SOL como capital mínimo de arranque orientativo para stake, cuentas y rentas, sujeto a la configuración y al estado actual del protocolo. Verificarlo en vivo antes de financiar.
- Usar una hot wallet de bajo saldo para limitar el impacto de un error. No usar una wallet principal con fondos importantes.
- Configurar un RPC compatible con `getProgramAccounts`; el RPC público de Solana puede limitar consultas y no es ideal para un proceso continuo.
- Definir capacidades permitidas, recompensa mínima, tipos de tareas admitidas, tiempo máximo, límite de saldo y procedimiento de apagado.
- Probar primero descubrimiento de tareas en modo de solo lectura. No registrar, reclamar ni enviar transacciones hasta revisar la previsualización y recibir autorización explícita.

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
- Financiar stake o rentas.
- Aprobar transacciones de mainnet, publicar listings o activar el bucle de claims.
- Declarar ingresos antes de que exista una liquidación conciliada.

## Estado al preparar esta guía

La rama contiene un ledger de comisiones propuestas y un monitor de hires en modo lectura. Todavía no contiene un worker de producción conectado al Marketplace Agent Kit/`@tetsuo-ai/agenc-worker`, no tiene wallet, no está desplegada externamente y no ha completado una tarea remunerada. El siguiente tramo de implementación debe añadir la integración del worker y su configuración de permisos; las operaciones con firma seguirán bloqueadas hasta que el titular configure la wallet y apruebe expresamente su activación.
