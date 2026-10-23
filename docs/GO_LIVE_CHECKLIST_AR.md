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
| Worker local CSV/JSON | Implementado en el repositorio |
| Generación de informe con hash | Implementada; límites locales de tamaño y escritura atómica |
| API de artefactos con bearer token, tamaño limitado, hash calculado por servidor, TTL y enlace firmado temporal | Prototipo local; CI verde con pruebas HTTP/auth/hash/enlace firmado |
| HTTPS público estable | Pendiente; el servidor escucha en loopback y no incluye TLS |
| Pruebas automatizadas en CI | CI verde: 56 tests y build Docker OK en commit `5490ad8131b852b3e568444638780048095f47fa` |
| Especificación de oferta | Preparada en `data_qa_agent/listing_spec.json` |
| Detección pública de tareas | Cliente read-only implementado; consulta real todavía pendiente de ejecución desde un entorno con acceso a la API |
| Registro on-chain del agente | No realizado |
| Publicación de listing | No realizada |
| Moderación CLEAN | No realizada |
| Bucle de ejecución con firma | Deshabilitado/no implementado como proceso operativo |
| Contrato, liquidación e ingresos | Ninguno demostrado |

## Bloqueantes para publicar y cobrar

1. **Aprobación explícita de presupuesto:** el registro en mainnet requiere una participación de referencia de 0.01 SOL por agente; también hay rent, comisiones de red y posible coste de hosting/RPC. Leer el valor vigente de `ProtocolConfig.minAgentStake` antes de operar. No financiar ni firmar hasta que el titular lo apruebe.
2. **Billetera:** el titular debe elegir y configurar localmente la billetera pública y el mecanismo de firma. Nunca compartir seed phrase ni clave privada por chat ni guardarlas en GitHub.
3. **Oferta alojada:** publicar el JSON canónico en una URL HTTPS estable y comprobar que el contenido y su hash coinciden exactamente.
4. **Registro y listing:** registrar el agente y publicar el listing usando la versión vigente documentada del SDK; revalidar la matriz oficial antes de instalar.
5. **Moderación:** solicitar la atestación y confirmar que el resultado sea `clean`; no asumir que una oferta publicada ya es contratable.
6. **Entrega segura:** validar el prototipo local, desplegarlo detrás de HTTPS, asegurar la autenticación, límites, vencimiento y borrado, y probar descarga real desde fuera del entorno local. No exponer directamente el servidor HTTP.
7. **Ciclo de contratación:** probar en entorno de ensayo o con un trabajo autorizado el descubrimiento de hires propios, verificación del hash del job spec, claim, ejecución aislada, alojamiento del artefacto, envío del hash y aceptación por el comprador.
8. **Conciliación:** contar ingreso sólo cuando exista recibo de liquidación verificable on-chain; el snapshot de una API no es suficiente por sí solo.

## Pasos operativos, en orden

1. Ejecutar las pruebas del repositorio y una muestra sintética de CSV y JSON; confirmar CI tras los commits recientes.
2. Probar localmente el API de artefactos, incluida autorización correcta/incorrecta, tamaño límite, hash, vencimiento y borrado.
3. Ejecutar el descubridor read-only y guardar el snapshot; revisar cada especificación, deadline, reward, requisitos y costes.
4. Desplegar una URL HTTPS estable sólo cuando se conozcan y aprueben los costes; comprobar TLS, autenticación y descarga desde un cliente externo.
5. Revisar fees, wallet de cobro, rent y costes; solicitar autorización del titular antes de cualquier firma o gasto.
6. Registrar agente y publicar listing; verificar visibilidad en la API pública y la moderación.
7. Mantener la ejecución desactivada hasta que el titular apruebe expresamente claims y envíos automáticos.
8. Completar el primer trabajo, lograr aceptación y verificar la transacción de liquidación.
9. Sólo después del primer pago confirmado, decidir si conviene añadir más agentes o una tienda propia.

## Fuentes oficiales a revalidar el día del lanzamiento

- [AgenC: vender servicios como proveedor](https://agenc.ag/docs/quickstart-providers)
- [AgenC: brief canónico para vender un servicio](https://agenc.ag/docs/agent-briefs/sell-a-service)
- [AgenC: API REST](https://agenc.ag/docs/api)
- [AgenC: mainnet quickstart](https://agenc.ag/docs/quickstart-mainnet)

**Regla de salida:** no anunciar que estamos “en vivo” hasta que el listing sea visible, la moderación sea CLEAN y la ruta de entrega haya sido probada. No anunciar ingresos hasta verificar un recibo de liquidación.
