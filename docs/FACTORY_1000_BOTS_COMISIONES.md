# Fábrica escalable de bots de comisiones

## Entregado en esta rama

- Generador determinista de hasta 1.000 identificadores lógicos de bots.
- Cinco roles reutilizables: búsqueda de oportunidades, enrutamiento de referidos, verificación de conversiones, auditoría de comisiones y conciliación de liquidaciones.
- Pruebas unitarias para unicidad, límites, serialización y bloqueo seguro.
- Ejecución en modo deshabilitado por defecto. No crea cuentas falsas, no envía spam, no hace auto-referidos y no mueve fondos.

## Ejecutar

```bash
python -m agent_economy.bot_factory --count 1000 --out output/bot_registry.json
python -m unittest discover -s tests -v
```

## Lo que falta para producir ingresos reales

Los 1.000 slots son configuraciones lógicas, no 1.000 procesos desplegados ni 1.000 fuentes de ingresos. Para cada canal hacen falta: proveedor real compatible, aprobación/cuenta cuando corresponda, términos vigentes, atribución válida, eventos autenticados, conciliación y método de cobro disponible en Argentina. Hasta demostrar esos puntos, no se deben activar bots ni informar ingresos.

## Orden de implementación recomendado

1. Elegir un proveedor con programa de comisiones y aceptación explícita de tráfico automatizado.
2. Integrar su contrato de eventos oficial en modo lectura.
3. Probar atribución, deduplicación, cancelaciones y conciliación.
4. Ejecutar un piloto pequeño y medir conversiones reales antes de escalar el número de workers.
5. Desplegar workers en lotes solo cuando el piloto muestre conversiones y el costo operativo sea inferior a la comisión cobrada.

No se proyectan ingresos ni se da por verificada una liquidación a partir de clicks, tareas listadas o comisiones calculadas.
