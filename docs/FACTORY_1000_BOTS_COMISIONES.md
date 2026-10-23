# Fábrica escalable de bots de comisiones

## Entregado en esta rama

- Generador determinista de hasta 1.000 identificadores lógicos de bots.
- Cinco roles reutilizables: búsqueda de oportunidades, enrutamiento de referidos, verificación de conversiones, auditoría de comisiones y conciliación de liquidaciones.
- Pruebas unitarias para unicidad, límites, serialización y bloqueo seguro.
- Ejecución deshabilitada por defecto. No crea cuentas falsas, no envía spam, no hace auto-referidos y no mueve fondos.

## Ejecutar

```bash
python -m agent_economy.bot_factory --count 1000 --out output/bot_registry.json
python -m unittest discover -s tests -v
```

## Estado de ingresos

Los 1.000 slots son configuraciones lógicas, no 1.000 procesos desplegados ni 1.000 fuentes de ingresos. Para generar ingresos hacen falta proveedores compatibles y aprobados, términos vigentes, atribución válida, eventos autenticados, conciliación y un método de cobro disponible en Argentina. Hasta demostrarlo, no se deben activar bots ni informar ingresos.

## Siguiente orden de trabajo

1. Elegir un proveedor que permita explícitamente referidos automatizados.
2. Integrar su contrato oficial de eventos en modo lectura.
3. Probar atribución, deduplicación, cancelaciones y conciliación.
4. Ejecutar un piloto pequeño y medir conversiones reales antes de escalar workers.
5. Escalar solo si el piloto demuestra conversiones y el coste operativo queda por debajo de la comisión.

No se proyectan ingresos a partir de clicks, tareas listadas o comisiones calculadas.
