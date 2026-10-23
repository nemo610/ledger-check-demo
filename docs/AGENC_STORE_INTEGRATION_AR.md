# Integración AgenC — tienda y comisiones iniciales

## Configuración preparada

El archivo `agenc.config.ts` usa la API oficial `defineStore` de
`@tetsuo-ai/store-core/config` y configura la wallet pública indicada por el titular:

`CG8BV7x2jWnFkfnV4WMkjLLi3aj6Q2Hu5M8t98MLA391`

- **Referrer: 5% (500 bps)** para contrataciones atribuidas a nuestra superficie.
- **Operator: 5% (500 bps)** para servicios/listings que publiquemos con estos términos.
- **Protocolo AgenC: 5%**, aplicado por el protocolo y no configurable por nosotros.
- **Ejemplo de reparto cuando aplican las tres patas:** trabajador 85%, operador 5%, referidor 5%, protocolo 5%.

La tarifa no se suma al precio del trabajo: se distribuye desde la recompensa según las reglas de AgenC. La comisión de referidor depende de que la contratación esté correctamente atribuida a nuestra tienda. La comisión de operador solo aplica a listings creados con esos términos; no se puede imponer retroactivamente a tareas de terceros.

## Estado y activación

Este repositorio es un prototipo Python, no una tienda Next.js completa. El archivo de configuración es el punto de partida para copiar dentro de un scaffold oficial; por sí solo no publica ni registra una tienda. Próximos pasos técnicos:

1. Crear el proyecto de tienda con la plantilla oficial de AgenC.
2. Instalar las versiones compatibles publicadas de `@tetsuo-ai/store-core`, `@tetsuo-ai/marketplace-react` y `@tetsuo-ai/marketplace-sdk`.
3. Copiar esta configuración al proyecto scaffold y ejecutar `npm run typecheck` y `npm run build`.
4. Inspeccionar el preflight de tarifas y confirmar que la wallet de referidor/operador sea la correcta.
5. Desplegar solo después de revisar hosting, dominio, costes y las transacciones de registro requeridas.
6. Verificar una contratación de prueba y conciliar el recibo on-chain antes de declarar ingresos.

## Seguridad/costos

- No se guarda ninguna clave privada ni frase semilla.
- No se ha firmado ninguna transacción, registrado una tienda, desplegado una web ni movido SOL.
- `allowMainnet: true` indica opt-in explícito a mainnet en la configuración; **no** autoriza por sí mismo una transacción ni significa que la tienda esté activa.
- El despliegue puede requerir firma de wallet y costes de infraestructura/rent. No se financia ni se incurre en costes de hosting sin aprobación explícita.
- La comisión solo se cobra cuando una contratación válida se liquida y la transacción reparte la comisión a la wallet configurada.

## Documentación oficial

- Lanzar una tienda: https://agenc.ag/docs/launch-a-marketplace
- Economía y límites: https://agenc.ag/trust
- Protocolo y reparto: https://agenc.ag/protocol
