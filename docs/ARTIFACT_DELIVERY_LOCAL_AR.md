# Entrega de artefactos Data QA — prototipo local

## Estado
La API autenticada de artefactos está implementada como prototipo en `data_qa_agent/artifact_server.py`. No está desplegada en internet, no tiene una URL HTTPS pública y todavía no se ha validado en CI después de estos cambios. No es todavía una integración de entrega válida para AgenC.

## Qué hace
- Acepta únicamente informes JSON estructurados de Data QA, no archivos fuente del cliente.
- Exige `Authorization: Bearer <token>` para subir, consultar y borrar artefactos.
- Rechaza tokens de configuración demasiado cortos, JSON inválido, esquemas incorrectos y archivos por encima del límite.
- Genera IDs aleatorios no predecibles y calcula el SHA-256 del contenido canónico en el servidor.
- Devuelve una ruta autenticada, un enlace de descarga firmado de corta duración, tamaño, hash y vencimiento; el vencimiento por defecto es 24 horas. El enlace firmado permite que el comprador descargue el informe sin recibir el token de subida.
- Permite borrar un artefacto y limpiar vencidos.
- No registra encabezados de autorización ni contenido de artefactos.
- Por defecto escucha sólo en `127.0.0.1`, no en una interfaz pública.

## Ejecución local

Generá un token aleatorio de al menos 32 caracteres y guardalo sólo en el entorno local. Nunca lo commits ni lo compartas por chat:

```bash
export ARTIFACT_API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ARTIFACT_STORAGE_DIR="$HOME/.local/share/ledger-check/artifacts"
export ARTIFACT_TTL_SECONDS=86400
python3 -m data_qa_agent.artifact_server
```

La API escucha en `127.0.0.1:8080` salvo que se configure otro host/puerto. El servicio no incluye TLS. Los enlaces firmados sólo son seguros para compartir mediante HTTPS; no los envíes por canales inseguros. No configures `ARTIFACT_BIND_HOST=0.0.0.0` para exponerlo directamente a internet.

## Endpoints
- `POST /v1/artifacts`: recibe el cuerpo JSON del informe.
- `GET /v1/artifacts/{artifact_id}`: recupera un artefacto no vencido con bearer token o con el enlace firmado devuelto al subir.
- `DELETE /v1/artifacts/{artifact_id}`: elimina un artefacto.

Todas las rutas requieren token bearer. En producción, un proxy HTTPS administrado debe terminar TLS, aplicar límites de conexiones/tiempo, restringir acceso y proteger el origen. El cliente del marketplace debe construir la URL pública HTTPS a partir de una URL de despliegue verificada; no se debe publicar la ruta relativa como si ya fuera accesible.

## Antes de usarlo con contrataciones reales
1. Ejecutar la suite completa en CI y probar una subida/descarga con autenticación válida e inválida.
2. Añadir control de cuota/rate limit, política de retención, borrado automático programado y monitoreo de espacio.
3. Desplegar sólo detrás de HTTPS con una URL estable; confirmar que el origen no sea accesible directamente.
4. Verificar compatibilidad del formato de prueba/hash requerido por la versión vigente de AgenC.
5. Ejecutar un contrato de prueba autorizado y comprobar que el comprador descarga el informe y que su hash coincide.
6. No aceptar archivos con datos personales, financieros, médicos, credenciales o información confidencial mientras no haya una política adecuada de privacidad y retención.

Este módulo no reclama tareas, no firma transacciones, no procesa pagos y no demuestra ingresos.
