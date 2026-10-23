# AgenC: descubrimiento y monetización sin financiar una wallet

## Qué queda preparado

El módulo `agent_economy.discover_agenc` ejecuta únicamente la consulta de lectura documentada para listar hasta diez tareas disponibles:

```bash
agenc-marketplace --network mainnet --json tasks list-claimable --limit 10 --compact
```

La herramienta `python -m agent_economy.discover_agenc` guarda una captura JSON en `output/agenc_claimable_tasks.json`. No reclama tareas, no envía entregas, no firma transacciones y no necesita la clave privada. Requiere que el kit oficial `agenc-marketplace` esté instalado localmente y que su consulta de lectura funcione.

## Cómo encaja el cobro de comisiones

La documentación oficial de AgenC describe dos vías relevantes:
- **Operator fee:** comisión para el operador de la tienda/superficie que origina la contratación.
- **Referrer fee:** comisión para el referente que deriva al comprador.

Ambas forman parte del reparto de una liquidación; no son una tarifa arbitraria que podamos imponer a cualquier bot. Las condiciones y porcentajes tienen que quedar incluidos en la contratación según las reglas y topes del protocolo. La documentación de confianza de AgenC indica que las comisiones se descuentan de la participación del trabajador y que este conserva un mínimo protegido. Consultar la política y el programa desplegado antes de configurar porcentajes.

Referencias oficiales:
- Lanzar un marketplace: https://agenc.ag/docs/launch-a-marketplace
- Kit del marketplace: https://agenc.ag/docs/kit
- Guía de worker: https://agenc.ag/docs/agent-briefs/wire-a-worker
- Configuración de wallet: https://agenc.ag/docs/wallet-setup
- Transparencia y economía: https://agenc.ag/trust

## Por qué no se activa el worker automáticamente

El ciclo de trabajo que puede generar ingresos requiere instalar y configurar el worker oficial, seleccionar tareas compatibles, verificar el job spec, registrar la identidad del agente si corresponde, reclamar, entregar el resultado y esperar la aceptación/liquidación. Algunas de esas acciones son transacciones en Solana y pueden requerir stake, rentas de cuentas, RPC compatible y credenciales del ejecutor. No hay que asumir que todo el flujo puede funcionar sin fondos ni credenciales.

El monitor de ingresos y el lector de tareas son solo de lectura. No equivalen a un worker activo ni demuestran ingresos.

## Pasos de activación, en orden

1. Instalar el kit oficial en una máquina controlada por el titular.
2. Ejecutar el lector de tareas y comprobar que devuelve JSON válido.
3. Evaluar manualmente tareas públicas: especificación, recompensa, plazo, coste de ejecución, riesgos y criterios de aceptación.
4. Preparar el worker en modo de prueba/dry-run si la versión instalada lo soporta; verificar esa opción en la ayuda de la versión concreta, sin inventar flags.
5. Antes de cualquier operación on-chain, consultar los requisitos actuales de stake y rentas directamente en el protocolo. No tomar como vigente una cifra antigua de SOL.
6. Revisar y aprobar de forma explícita cada tipo de operación de escritura. Mantener la clave privada fuera del chat, GitHub, logs y variables públicas.
7. Solo después de confirmar la configuración real de fees, probar una contratación y conciliar el evento de liquidación con una transacción on-chain. La API de hires es una fuente de datos del proveedor, no prueba suficiente por sí sola de fondos recibidos.

## Restricciones de seguridad y costo

- No se crea, financia ni firma ninguna wallet desde este repositorio.
- No se despliega un servicio con costo sin aprobación explícita del titular.
- No se reclama una tarea ni se ejecuta código de un tercero automáticamente.
- No se marca una comisión como cobrada hasta verificar la liquidación on-chain.
- No habilitar la política sintética de `data/fee_policies.example.json`: su tasa es una fixture de prueba, no una recomendación ni una tarifa oficial.
- La implementación actual no está conectada a un worker activo y no garantiza ingresos.

## Validación local

```bash
python -m unittest discover -s tests -v
python -m agent_economy.discover_agenc --out output/agenc_claimable_tasks.json
```

El segundo comando requiere el CLI oficial instalado y solo realiza lectura. No ejecutarlo con credenciales de firma si no se revisó previamente la configuración de la CLI.
