# MVP del worker proveedor AgenC (CSV/JSON)

## Estado honesto
Este cambio prepara un servicio HTTP sin estado, Docker y una configuración inicial para Render. **No crea una URL pública ni registra/publica al agente en Solana.** Para HTTPS real hay que crear el servicio de hosting y comprobar la URL asignada desde fuera.

## Servicio
- `GET /health` y `GET /healthz`: estado y límites.
- `POST /v1/validate`: JSON con `filename`, `format` (`csv` o `json`) y `content` como texto UTF-8.
- Límite del cuerpo HTTP: 256 KiB; contenido: 192 KiB.
- CSV: cabeceras vacías/duplicadas, filas de ancho desigual y ausencia de filas de datos.
- JSON: sintaxis y tipo raíz.
- Devuelve SHA-256, hallazgos, `stored:false`; no persiste archivos, ejecuta código, firma ni mueve fondos.
- Límite por IP en memoria: básico, no sustituye rate limiting distribuido de producción.

## Petición de ejemplo
```json
{"filename":"dataset.csv","format":"csv","content":"id,name\n1,Ada\n"}
```

## Pruebas
`python -m unittest discover -s tests -v`

## HTTPS y despliegue
El `provider_service/Dockerfile` y `provider_service/render.yaml` preparan el servicio para desplegarse por separado del monitor existente. El proveedor de hosting termina TLS y entrega una URL HTTPS. `autoDeploy: false` evita desplegar automáticamente cambios sin revisión. No se ha creado ni activado un servicio externo; aún no existe endpoint público verificado.

## Bloqueos reales antes de aceptar tareas pagas
1. Esto es el validador, **no el worker AgenC completo**: aún no escucha/recoge jobs, verifica claims, recupera job specs on-chain, aloja artefactos ni envía submit/settlement.
2. No enviar datos personales, médicos, financieros, secretos ni documentos confidenciales.
3. Mantener `settlement_verified:false` hasta verificar liquidación on-chain de forma independiente.
4. Registro y publicación requieren transacciones Solana firmadas por el titular. Revisar el coste real en la cartera antes de aprobar; nunca compartir seed phrase ni clave privada.

## Checklist de habilitación
- [ ] Pruebas del servicio pasan en CI.
- [ ] Despliegue autorizado y URL HTTPS pública comprobada externamente.
- [ ] Prueba externa de `/health` y `POST /v1/validate` con datos sintéticos.
- [ ] Integrar polling/claim/submit con SDK AgenC oficial, sin custodiar claves.
- [ ] AgentRegistration verificado en el indexador y contra cuenta on-chain.
- [ ] ServiceListing vinculado al PDA del agente y especificación canónica accesible por HTTPS.
- [ ] Moderación CLEAN confirmada para el listing.
- [ ] Job de prueba, entrega, aceptación y receipt/liquidación verificados en Solana.

## Fuentes oficiales
- https://agenc.ag/docs/quickstart-workers
- https://agenc.ag/docs/quickstart-providers
- https://agenc.ag/docs/sdk
- https://agenc.ag/docs/hosted-writes
- https://agenc.ag/trust
