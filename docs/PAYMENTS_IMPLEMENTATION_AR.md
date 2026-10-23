# Plan de implementación de cobros — Argentina

## Objetivo

Construir un flujo verificable para comisiones entre agentes de software y, más adelante, convertir los fondos a pesos y retirarlos a una cuenta propia. Este repositorio no envía pagos ni firma transacciones.

## Hallazgo principal

El alias bancario `donatonuevaesperanza` es un destino para transferencias locales; no es una dirección de blockchain ni una credencial de API. No hace falta cambiarlo por un CBU para recibir transferencias locales, pero ni alias, CBU ni CVU sustituyen una wallet Solana para liquidaciones del protocolo AgenC.

## Ruta recomendada

1. **Marketplace/referente:** crear una wallet Solana propia y configurar un storefront/handle en AgenC para que las contrataciones originadas allí puedan llevar una comisión de referente.
2. **Agente trabajador (separado):** registrar/configurar un agente capaz de encontrar tareas, revisar condiciones, completar entregables y seguir el flujo de aceptación del marketplace.
3. **Lectura de ingresos:** consultar los endpoints públicos de hires del operador/referente. Guardar wallet, fecha y payload sin secretos. El resultado del endpoint no demuestra por sí solo que se recibió una transferencia.
4. **Verificación de liquidación:** comprobar firma/transacción en cadena, estado confirmado, destinatario, activo, importe neto y posibles reversiones antes de marcar fondos como recibidos.
5. **Conversión a pesos:** elegir después un proveedor disponible en Argentina que admita el activo/red exactos, permita retiro a una cuenta bancaria propia y tenga costes/KYC conocidos. No asumir conversión automática a Mercado Pago o Santander.

## Papel de Mercado Pago

Mercado Pago Argentina ofrece APIs de cobro y Split de Pagos 1:1 para integraciones de marketplace. Eso requiere una aplicación e integración compatibles, OAuth de vendedores y requisitos de cuenta; no permite asumir que un marketplace externo de agentes pueda liquidar comisiones directamente a Mercado Pago sin integración aprobada.

Documentación oficial:
- https://www.mercadopago.com.ar/developers/es
- https://www.mercadopago.com.ar/developers/es/docs/split-payments/split-1-1/overview
- https://www.mercadopago.com.ar/developers/es/docs/split-payments/split-1-1/prerequisites
- https://www.mercadopago.com.ar/developers/es/docs/security/oauth/introduction

## Santander y alias bancario

Santander puede ser el destino final de fondos en pesos, pero no debemos asumir que una cuenta personal dispone de una API adecuada para este flujo. Verificar con el banco los productos habilitados. El alias informado no debe tratarse como API ni como wallet cripto.

## Seguridad

- Nunca guardar ni compartir frase semilla, clave privada, códigos de recuperación o tokens en GitHub, Jules, chat, variables públicas o logs.
- Para consultas de lectura basta con la dirección pública de Solana; nunca compartir secretos.
- No usar endpoints de consulta con cobro por solicitud sin autorización previa.
- No marcar ingresos como recibidos sin conciliar la transacción on-chain.
- No habilitar pagos automáticos ni firmantes sin revisar antes el importe, la red, el destinatario y los límites.

## Estado actual

- Existe un ledger Python de comisiones propuestas con datos sintéticos; no ejecuta pagos.
- Existe un adaptador de lectura AgenC en `agent_economy/agenc_adapter.py`, conectado a una opción explícita del CLI.
- Se añadieron pruebas del adaptador. La primera ejecución de CI detectó un fallo real de validación de la respuesta malformada; la rama incluye una corrección defensiva, pero hay que verificar el nuevo CI antes de declarar la versión estable.
- El workflow de CI ahora incluye esta rama y prueba el CLI correcto (`python -m agent_economy.cli --help`).
- Se añadió `docs/DEPLOYMENT_AND_MARKETPLACE_AR.md` con la ruta de despliegue y los criterios de aceptación.
- Todavía no hay una wallet conectada, un agente registrado, un runtime externo verificado, una tarea completada ni una comisión real conciliada.

## Próximas tareas

1. Confirmar CI verde en la rama.
2. Elegir y configurar la wallet pública y el storefront/referente de AgenC.
3. Preparar un runtime externo y demostrar que sobrevive a reinicios sin depender de la VM.
4. Conectar el agente al flujo de trabajo del marketplace con revisión de permisos y límites.
5. Completar una tarea de prueba y verificar tanto la atribución como la liquidación en cadena.
6. Investigar una rampa fiat compatible con Argentina solo después de comprobar que existen fondos retirables.

## Documentación oficial de referencia

- AgenC marketplace: https://agenc.ag/docs/launch-a-marketplace
- AgenC Marketplace Agent Kit: https://agenc.ag/docs/kit
- AgenC hosted write surfaces: https://agenc.ag/docs/hosted-writes
- AgenC protocol: https://agenc.ag/protocol
