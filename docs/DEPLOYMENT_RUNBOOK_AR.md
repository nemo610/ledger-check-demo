# Guía de despliegue del monitor AgenC (solo lectura)

## Qué se preparó

- `agent_economy/monitor.py`: consulta las dos listas públicas de hires de AgenC y emite un resumen JSON en los logs.
- `Dockerfile`: empaqueta el monitor en Python 3.12, sin dependencias externas adicionales.
- `render.yaml`: plantilla de servicio programado en Render cada seis horas.
- `tests/test_monitor.py`: prueba que exige una wallet pública y que el resultado nunca se declara como liquidación verificada.

Este proceso es un monitor, **no** un agente que reclame o complete tareas. No firma, no publica listings, no reclama trabajos, no hace transferencias y no puede generar comisiones por sí solo.

## Bloqueo deliberado antes de activar

1. Crear una wallet Solana propia en el dispositivo del titular.
2. Copiar únicamente la dirección pública a la variable privada de entorno `AGENC_WALLET` del proveedor de hosting.
3. No introducir nunca seed phrase, clave privada ni código de recuperación en GitHub, Render, el repositorio, los logs o el chat.
4. Revisar el plan y el precio actual del hosting antes de crear el servicio. La plantilla usa `plan: starter`; **no desplegar ni aceptar cargos sin aprobar previamente el coste**.
5. Ejecutar una prueba manual y confirmar que los logs muestran `status: ok`, sin errores, y `settlement_verified: false`.

## Qué verifica y qué no

El monitor cuenta hires reportados por los endpoints públicos de AgenC. Un conteo no demuestra que se haya recibido SOL ni otro activo. La liquidación solo debe marcarse como recibida después de comprobar la transacción y el destinatario en cadena.

## Próximo tramo comercial, separado del monitor

Para cobrar como referente hay que registrar un storefront/handle en AgenC y confirmar sus términos. Para cobrar como operador hay que publicar listings con términos compatibles. Para que el bot gane dinero haciendo tareas, falta integrar y probar el Marketplace Agent Kit, sus flujos de claim/submit y la política de aprobación/firma. Nada de eso se habilita mediante este monitor.

## Validación

El CI debe pasar en la cabeza actual de `agent-to-agent-monetization-v1` antes de desplegar. La PR permanece abierta y sin fusionar; `main` no forma parte de este despliegue experimental.
