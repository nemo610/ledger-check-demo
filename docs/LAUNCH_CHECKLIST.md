# Lista de lanzamiento y monetización responsable

## Antes de buscar comisiones
1. Elegir un nicho y comprobar demanda con entrevistas o contenido orgánico útil.
2. Revisar los términos oficiales del programa de afiliados y solicitar aprobación.
3. Sustituir el catálogo de ejemplo por ofertas aprobadas y enlaces propios HTTPS.
4. Confirmar restricciones de marca, países admitidos, cookies, atribución y métodos de cobro.
5. Publicar la divulgación de afiliación de forma visible en cada canal.
6. Revisar manualmente cada borrador; no enviar spam ni publicar automáticamente.
7. Importar periódicamente reportes oficiales CSV para comparar clics, conversiones y comisiones pendientes/aprobadas/pagadas.
8. Verificar las reglas fiscales y bancarias argentinas con fuentes oficiales y un profesional local.

## Estado real
- Este proyecto genera borradores y resume CSVs locales.
- No raspa sitios, no envía mensajes, no crea cuentas, no ejecuta compras ni procesa pagos.
- No incluye enlaces de afiliación aprobados. El catálogo de ejemplo está intencionalmente bloqueado.
- No se garantizan conversiones ni ingresos. Las comisiones dependen de aprobación, tráfico, términos del programa y ventas válidas.

## Primera prueba
```bash
python -m unittest discover -s tests -v
python -m commission_bot drafts --offers data/offers.approved.json --out output/campaign_drafts.md --channel social
python -m commission_bot report --events data/exported_events.csv --out output/commission_report.json
```
