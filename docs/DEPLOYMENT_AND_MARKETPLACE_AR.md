# Despliegue y actividad comercial: plan ejecutable

## Estado verificado

- El adaptador Python consulta los endpoints públicos de hires de AgenC en modo lectura.
- El ledger de comisiones calcula propuestas; no publica listings, no reclama tareas, no entrega trabajos y no firma transacciones.
- El CI anterior detectó un fallo real de validación de hires; la rama incorpora una corrección defensiva para validar la respuesta también en la frontera del adaptador. Hay que esperar y revisar el nuevo CI antes de declarar la rama estable.
- No hay evidencia de un servicio externo desplegado, un proceso continuo activo, una wallet vinculada, un agente registrado o una comisión liquidada.

## Ruta mínima para monetizar como intermediario

La vía más directa documentada es AgenC. Distinguir dos mecanismos:

1. **Comisión de referente (demanda):** un storefront/handle de AgenC debe originar las contrataciones para que el protocolo adjunte el fee de referente. Consultar el endpoint de ingresos por sí solo no genera ingresos.
2. **Comisión de operador (oferta):** publicar listings propios con términos de operador. Esto requiere crear y moderar listings; no se activa por instalar el ledger.

No configurar tasas ni activar mainnet hasta elegir wallet, confirmar la política vigente y revisar la previsualización exacta de la transacción. Los fees están sujetos a límites del protocolo y al tipo de operación; no hay una comisión garantizada.

## Despliegue y ejecución autónoma

### Primera opción: storefront alojado por AgenC
- Crear/controlar una wallet Solana propia.
- Abrir la sección Store de AgenC y registrar un handle como referente; comprobar en la interfaz la tasa y la wallet beneficiaria antes de confirmar.
- Verificar que una contratación real originada desde ese storefront muestra el fee correspondiente en la transacción y en el endpoint de hires.
- Esto puede evitar mantener un storefront propio al inicio, pero no convierte por sí solo al agente en trabajador autónomo.

### Segunda opción: storefront propio
La documentación oficial describe create-agenc-store y un storefront Next.js desplegable en una plataforma de hosting. Antes de ejecutarlo, verificar versiones publicadas, configuración, wallet beneficiaria y build. Requiere una wallet pública, una plataforma de despliegue y variables de entorno; el RPC debe configurarse como secreto del proveedor, nunca en Git.

### Agente que busca y realiza trabajos
La documentación de AgenC describe un Marketplace Agent Kit/CLI/MCP para encontrar tareas, revisar condiciones, reclamar y entregar trabajo. Sus acciones que mutan estado usan previsualización y aprobación explícita; no debemos llamarlo “totalmente autónomo” hasta definir y probar un entorno de ejecución y una política de firma que no exponga claves. No instalar ni habilitar un firmante sin una wallet del titular y límites de gasto/revisión claros.

## Qué se puede automatizar sin la wallet

- Pruebas unitarias y de integración simuladas.
- Validación de eventos, idempotencia y ledger.
- Construcción de un contenedor/runtime y un procedimiento de despliegue sin credenciales.
- Monitor de lectura de endpoints públicos.

## Qué queda bloqueado hasta el setup del titular

- Asociar el destinatario de comisiones y registrar el storefront.
- Firmar operaciones de registro, publicación, contratación o entrega.
- Ejecutar un agente productivo que pueda reclamar trabajos.
- Confirmar comisiones reales y su liquidación en cadena.

Nunca copiar una frase semilla, clave privada o código de recuperación en GitHub, Jules, variables públicas, chat o logs. Solo se debe compartir la dirección pública de la wallet para consultas de lectura.

## Criterios de aceptación

- CI verde en la rama de trabajo.
- Un runtime externo identificado, con despliegue verificable y logs.
- Una prueba de salud/lectura ejecutándose automáticamente tras reinicio sin depender de la VM.
- Wallet y agente registrados correctamente en el marketplace.
- Una tarea de prueba completada bajo las reglas del protocolo.
- Comisión atribuida y liquidación conciliada con evidencia on-chain.

Hasta cumplir estos puntos, el estado comercial debe figurar como **prototipo en preparación, sin ingresos verificados**.

## Documentación oficial de referencia

- AgenC: https://agenc.ag/docs/launch-a-marketplace
- AgenC Marketplace Agent Kit: https://agenc.ag/docs/kit
- AgenC hosted write surfaces: https://agenc.ag/docs/hosted-writes
- AgenC protocol: https://agenc.ag/protocol
