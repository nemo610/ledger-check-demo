# Fábrica de 12.000 bots de comisiones

## Alcance implementado

- Generador de hasta 12.000 identificadores lógicos únicos.
- Cinco roles reutilizables: búsqueda de oportunidades, enrutamiento de referidos, verificación de conversiones, auditoría de comisiones y conciliación de liquidaciones.
- Pruebas unitarias para unicidad, límites, serialización y bloqueo seguro.
- Ejecución deshabilitada por defecto. No crea cuentas falsas, no envía spam, no hace auto-referidos y no mueve fondos.

## Ejecutar

```bash
python -m agent_economy.bot_factory --count 12000 --out output/bot_registry.json
python -m unittest discover -s tests -v
```

## Importante: configuración no equivale a ingresos

Los 12.000 slots no son 12.000 procesos desplegados, integraciones aprobadas ni fuentes de ingresos. Para recibir comisiones se necesitan proveedores reales compatibles, términos vigentes, atribución válida, eventos autenticados, conciliación, infraestructura y un método de cobro disponible en Argentina. Ningún ingreso se considera real hasta comprobar una liquidación.

## Siguiente etapa para que funcionen

1. Elegir un proveedor que permita explícitamente el modelo de referidos automatizados.
2. Integrar el contrato oficial de eventos en modo lectura.
3. Probar atribución, deduplicación, cancelaciones y conciliación.
4. Ejecutar un piloto limitado y medir conversiones reales.
5. Desplegar workers por lotes solo si el piloto demuestra ingresos netos positivos.

No se proyectan ingresos a partir de clicks, tareas listadas o comisiones calculadas.
