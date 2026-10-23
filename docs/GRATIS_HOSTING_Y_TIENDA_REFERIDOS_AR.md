# Plan de tienda de referidos con alojamiento gratuito

**Proyecto:** Nemo Agent Store  
**Rama:** `agent-to-agent-monetization-v1`  
**Estado:** preparación solamente; no desplegado, no registrado y sin transacciones firmadas.

## Decisión de alojamiento

Primera opción a evaluar: **Cloudflare Workers Free**, con la ruta oficial de Cloudflare para aplicaciones Next.js (actualmente recomienda `vinext` para proyectos nuevos). El plan gratuito documenta 100.000 solicitudes por día y límites de CPU/recursos. No contratar plan pago ni activar facturación. Si la cuenta o el despliegue propone un upgrade, detenerse.

Fuentes oficiales:
- Cloudflare Next.js / Workers: https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/
- Límites Workers: https://developers.cloudflare.com/workers/platform/limits/
- Precios Workers: https://developers.cloudflare.com/workers/platform/pricing/

No elegir Vercel Hobby para una tienda comercial: sus condiciones publicadas limitan ese plan a uso personal/no comercial. Fuente: https://vercel.com/docs/plans/hobby

## Qué puede ser gratuito y qué no está confirmado

| Elemento | Estado | Regla de seguridad |
|---|---|---|
| Código y repositorio | Ya preparado en la rama del PR | Mantener PR #3 abierto y en draft; no tocar `main`. |
| Hosting | Cloudflare Workers Free es candidato; aún no se creó cuenta ni desplegó nada | No activar plan pago ni introducir método de pago para continuar. |
| Subdominio HTTPS del proveedor | Se espera usar el subdominio gratuito del proveedor | No comprar dominio propio. |
| Registro/handle en AgenC | La documentación describe `POST /api/stores` como una operación firmada con wallet en la web de AgenC; no publica en esa página un coste total concluyente | No registrar ni firmar hasta comprobar la pantalla de confirmación y los requisitos actuales. |
| Wallet receptora de comisiones | La documentación de AgenC dice que cada destinatario de un pago SOL debe tener al menos 890.880 lamports (0,00089088 SOL) para rent-exemption | No fondear con dinero personal. Si la wallet no cumple el mínimo, pausar y reportar el bloqueo. |
| Comisión | Solo referidor: 250 bps = 2,5 % | No activar tarifa de operador. La comisión no está garantizada y solo cuenta después de un settlement verificado. |
| RPC / variables | Sin secretos incorporados al repositorio | No pegar claves privadas, seed phrase ni tokens en GitHub, logs o chat. |

Fuente oficial AgenC para los flujos de tienda y firma:
https://agenc.ag/docs/hosted-writes
https://agenc.ag/docs/launch-a-marketplace

## Por qué empezamos por referidos

La configuración de `agenc-store/agenc.config.ts` queda limitada a la comisión referrer del 2,5 %. Se quitó la comisión operator del primer lanzamiento para evitar cobrar una tarifa de venta propia cuando el plan inicial es solo referir servicios de terceros. No se publican listings propios ni se registra un agente proveedor en esta etapa.

La tienda propia autoalojada y la tienda alojada/registrada en agenc.ag son caminos distintos. El primero exige desplegar y mantener una aplicación; el segundo usa la interfaz y registro de la plataforma. Ninguno se considera activo por compilar el proyecto.

## Pasos siguientes, sin gasto

1. Revisar que el cambio de configuración siga compilando en CI.
2. Preparar el despliegue para Cloudflare Workers Free en una rama de trabajo, sin credenciales y sin ejecutar `deploy`.
3. Hacer un build y un preview local/sandbox si el entorno lo permite.
4. Confirmar la URL HTTPS gratuita disponible y comprobar que no se active facturación.
5. Investigar el flujo actual de registro del handle en AgenC y anotar el coste exacto mostrado antes de cualquier firma.
6. Verificar de forma read-only el saldo de la wallet pública y el endpoint de earnings. No mover fondos.
7. Detenerse antes de cualquier registro, firma, publicación pública o gasto; presentar el coste total y pedir autorización específica.

## Criterios de salida

La tienda solo se considerará publicada cuando exista una URL pública comprobada, el handle/manifest esté accesible, la tarifa referrer sea 2,5 %, y el endpoint de earnings responda. Solo se considerará que genera ingresos cuando exista evidencia de una contratación liquidada y de la comisión recibida.

**No se promete ingreso, no se autoriza gastar SOL y no se habilita despliegue automático.**
