# Ejecución de las cuatro fases — Ledger Check / AgenC

Fecha de revisión: 2026-10-23. Rama de trabajo: `agent-to-agent-monetization-v1`.

## Fase A — Seguridad y preparación
- El trabajo permanece aislado en una rama y en la PR #3; no se fusionó a `main`.
- El ledger usa eventos de prueba y no ejecuta transferencias.
- Las consultas de ingresos se marcan como reportadas por el proveedor, no como fondos recibidos verificados.
- CI pasó en el commit `ecd7ad111f3b39ff69e3cb01f0c9ecd9c22bdd9e`.
- No se configuraron claves privadas, no se firmaron transacciones, no se desplegó a mainnet y no se activó hosting pago.

## Fase B — Descubrimiento de demanda
- Fuente validada en documentación oficial: API pública GET `https://api.agenc.ag/api/tasks`, filtros `status=open` y `actionable=true`, con paginación `page/pageSize`.
- Se añadió `agent_economy/task_discovery.py`: obtiene una instantánea de solo lectura, exige tareas abiertas con recompensa SOL positiva, deadline futuro, especificación HTTPS fijada por hash y verificación pública aprobada; ordena candidatos por una cota superior del pago al trabajador.
- La estimación resta solamente el 5% de tarifa de protocolo documentada. No resta comisiones opcionales de operador/referente ni costes; por eso se etiqueta expresamente como cota superior, no beneficio neto.
- El escaneo no reclama tareas ni firma transacciones. La API es una instantánea indexada, no garantía de que una tarea siga disponible.

## Fase C — Primer servicio vendible
- El primer trabajador implementado es Data QA local para CSV/JSON; genera un informe verificable y tiene pruebas automatizadas.
- Los resultados de prueba se ejecutan con fixtures sintéticos; todavía no hay contrato de cliente ni aceptación externa.
- Antes de ofertarlo en AgenC hay que revisar el formato de entrega, los criterios de aceptación, el precio, la identidad/registro del agente proveedor y cualquier coste o requisito de stake. No se debe publicar un listing hasta revisar esos requisitos.

## Fase D — Escalado sin gastos fijos
- El escaneo se ejecuta manualmente bajo demanda; no se configuró cron, servicio permanente ni hosting de pago.
- Se mantienen controles humanos para reclamar tareas, publicar listings, conectar wallets, firmar, desplegar y pagar.
- No añadir más workers hasta probar demanda real y una primera entrega aceptada con economía positiva.

## Comandos de verificación local

```bash
python -m unittest discover -s tests -v
python -m agent_economy.task_discovery --help
python -m agent_economy.cli --help
```

Para consultar tareas desde una máquina donde haya conectividad de red:

```bash
python -m agent_economy.task_discovery --out output/agenc_task_candidates.json
```

Este último comando consulta el API público y crea un archivo local. No envía transacciones ni requiere la dirección de la wallet.

## Estado económico honesto
- Ingresos confirmados: 0 demostrados por este prototipo.
- Contratos aceptados: ninguno demostrado.
- Transferencias o comisiones recibidas y conciliadas: ninguna demostrada.
- Próximo hito: ejecutar el escaneo real, inspeccionar manualmente un candidato, probar Data QA de extremo a extremo con datos no sensibles y conseguir evidencia de aceptación antes de conectar cualquier comisión real.
