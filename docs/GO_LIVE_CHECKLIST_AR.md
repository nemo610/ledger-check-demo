# Plan de salida a mercado — Data QA en AgenC

**Estado:** preparado para revisión; todavía NO publicado, contratado ni cobrado.  
**Rama:** `agent-to-agent-monetization-v1`

## Servicio inicial

- **Nombre corto:** CSV/JSON Data Quality Check (menos de 32 bytes para el nombre on-chain).
- **Precio inicial propuesto:** 0.01 SOL por archivo pequeño. Es una hipótesis de lanzamiento, no un precio validado por ventas.
- **Entrega:** informe JSON descargable con estado, métricas disponibles, hallazgos codificados, severidad y limitaciones.
- **Alcance:** un archivo CSV o JSON no sensible por contratación; validaciones estructurales deterministas. No incluye conciliación contable, validación fiscal, interpretación de negocio ni corrección automática.
- **Privacidad:** no aceptar datos personales, bancarios, médicos, credenciales ni información confidencial. Usar datos sintéticos hasta que exista un proceso de protección y borrado acordado.
- **Criterio de aceptación:** el archivo de salida se puede descargar, es JSON válido, coincide con el hash SHA-256 declarado y enumera los checks ejecutados y las limitaciones.
- **Límite de honestidad:** no prometer exactitud fiscal ni ausencia de errores no detectados.

## Estado real

| Componente | Estado |
| --- | --- |
| Worker local CSV/JSON | Implementado en el repositorio; no está conectado a un ciclo real de contratación |
| Generación de informe con hash | Implementada; límites locales de tamaño y escritura atómica |
| API de artefactos con bearer token, tamaño limitado, hash calculado por servidor, TTL y enlace firmado temporal | Prototipo local; incluye pruebas unitarias y HTTP en CI |
| CI del commit actual | Verificado: `Commission Bot CI` y `AgenC store build preflight` finalizaron con éxito en el commit auditado. El preflight de la tienda valida pasos de preparación, no publica ni despliega la oferta |
| HTTPS público estable | Pendiente; el servidor escucha en loopback y no incluye TLS |
| Especificación de oferta | Preparada en `data_qa_agent/listing_spec.json` |
| Detección pública de tareas | Cliente read-only implementado; consulta real todavía pendiente de ejecución desde un entorno con acceso a la API; filtra tareas y exige URL HTTPS y hash SHA-256 del job spec |
| Validación y ejecución segura de job specs en un worker aislado | Pendiente; no se debe tratar una tarea descubierta como autorizada para ejecutar |
| Registro on-chain del agente | No realizado |
| Publicación de listing | No realizada |
| Moderación CLEAN | No realizada |
| Claims, firmas y envíos de entrega | Deshabilitados/no implementados como proceso operativo |
| Contrato, liquidación e ingresos | Ninguno demostrado |

## Bloqueantes para publicar y cobrar

1. **Aprobación explícita de presupuesto:** el registro en mainnet requiere una participación de referencia de 0.01 SOL por agente; también hay rent, comisiones de red y posible coste de hosting/RPC. Leer el valor vigente de `ProtocolConfig.minAgentStake` antes de operar. No financiar ni firmar hasta que el titular lo apruebe.
2. **Billetera:** el titular debe elegir y configurar localmente la billetera pública y el mecanismo de firma. Nunca compartir seed phrase ni clave privada por chat ni guardarlas en GitHub.
3. **Oferta alojada:** publicar el JSON canónico en una URL HTTPS estable y comprobar que el contenido y su hash coinciden exactamente.
4. **Registro y listing:** registrar el agente y publicar el listing usando la versión vigente documentada del SDK; revalidar la matriz oficial antes de instalar.
5. **Moderación:** solicitar la atestación y confirmar que el resultado sea `CLEAN`; no asumir que una oferta publicada ya es contratable.
6. **Entrega segura:** validar el prototipo local, desplegarlo detrás de HTTPS, asegurar autenticación, límites, vencimiento y borrado, y probar descarga real desde un cliente externo. No exponer directamente el servidor HTTP.
7. **Ciclo de contratación:** implementar y probar en modo simulado un worker que compruebe atribución del trabajo, hash íntegro del job spec, deadline, reward, capacidades, límites de archivo, instrucciones no confiables, idempotencia y aceptación. El worker no debe reclamar ni firmar.
8. **Prueba end-to-end:** demostrar descubrimiento, validación, procesamiento sintético, creación/subida del informe, hash/pointer de entrega y expiración; los claims y las transacciones deben seguir desactivados por defecto.
9. **Conciliación:** contar ingreso sólo cuando exista recibo de liquidación verificable on-chain; el snapshot de una API no es suficiente por sí solo.

## Pasos operativos, en orden

1. Mantener CI verde y ejecutar las pruebas localmente en un entorno controlado; guardar evidencia reproducible.
2. Probar el API de artefactos, incluida autorización correcta/incorrecta, tamaño límite, hash, vencimiento, borrado y fallas de almacenamiento.
3. Completar el worker aislado y pruebas de especificación maliciosa, hash incorrecto, tarea no atribuida, duplicados e idempotencia.
4. Ejecutar el descubridor read-only y guardar el snapshot; revisar cada especificación, deadline, reward, requisitos y costes.
5. Desplegar una URL HTTPS estable sólo cuando se conozcan y aprueben los costes; comprobar TLS, autenticación y descarga desde un cliente externo.
6. Revisar fees, billetera de cobro, rent y costes; solicitar autorización del titular antes de cualquier firma o gasto.
7. Registrar agente y publicar listing sólo después de la autorización explícita; verificar visibilidad en la API pública y moderación `CLEAN`.
8. Mantener claims, firmas y envíos desactivados hasta aprobación expresa del titular.
9. Completar el primer trabajo autorizado, lograr aceptación y verificar la transacción de liquidación.
10. Sólo después del primer pago confirmado, decidir si conviene añadir más agentes o una tienda propia.

## Fuentes oficiales a revalidar el día del lanzamiento

- [AgenC: vender servicios como proveedor](https://agenc.ag/docs/quickstart-providers)
- [AgenC: brief canónico para vender un servicio](https://agenc.ag/docs/agent-briefs/sell-a-service)
- [AgenC: API REST](https://agenc.ag/docs/api)
- [AgenC: mainnet quickstart](https://agenc.ag/docs/quickstart-mainnet)

**Regla de salida:** no anunciar que estamos “en vivo” hasta que el listing sea visible, la moderación sea CLEAN y la ruta de entrega haya sido probada. No anunciar ingresos hasta verificar un recibo de liquidación.
