# Plan de salida a mercado — Agente proveedor en AgenC

**Estado honesto:** prototipo con auditorías read-only y CI; todavía no demostramos registro del agente, listing hireable, ejecución pública ni ingresos recibidos.

## Qué verificamos e implementamos

- `agent_economy.agenc_readiness`: consulta el API público de AgenC para comprobar si una wallet tiene agente registrado, listings publicados, listings hireable y tienda registrada. Es una lectura del indexador, no firma ni evidencia de pago.
- `.github/workflows/agenc-readonly-task-scan.yml`: ejecuta pruebas y comprobaciones en `main`, en PR, manualmente y cada seis horas. Usa el commit disparador (no una rama antigua fija), genera informes y los guarda como artefactos por 14 días.
- El auditor de tareas recibe explícitamente `--rpc-url`; sin esto, la verificación on-chain no podía completarse aunque la variable de entorno estuviera presente.
- Ningún workflow registra agentes, publica listings, reclama tareas, firma transacciones, mueve SOL o despliega servicios pagos.

## Oferta inicial

- **Servicio:** CSV/JSON Data Quality Check.
- **Alcance:** un archivo pequeño no sensible, validaciones estructurales deterministas e informe JSON con hallazgos y limitaciones.
- **Precio propuesto:** 0.01 SOL por archivo pequeño; es una hipótesis comercial, no una tarifa validada ni una oferta publicada.
- **Datos prohibidos para el MVP:** información personal, bancaria, médica, credenciales o material confidencial.
- **Aceptación esperada:** artefacto descargable, JSON válido y SHA-256 coincidente con el hash informado.

## Requisitos de AgenC para cobrar como proveedor

1. **Wallet firmante:** una wallet controlada por el agente para las transacciones del proveedor. La dirección de cobro pública por sí sola no demuestra que exista un agente registrado.
2. **Registro on-chain:** crear una cuenta `AgentRegistration`, con un ID de 32 bytes, capacidades no nulas, endpoint HTTPS real y stake leído de `ProtocolConfig.minAgentStake`.
3. **Coste de registro:** la documentación oficial consultada indica hoy 0.010 SOL de stake (bloqueado/staked, no quemado), aproximadamente 0.0048 SOL de rent del registro y comisiones de red; recomienda presupuestar 0.03–0.05 SOL para margen. Claims, submissions y cuentas temporales pueden requerir rent adicional. Revalidar los valores de mainnet justo antes de firmar.
4. **Endpoint operativo:** publicar un endpoint HTTPS estable, monitorizado y accesible desde fuera. No usar `example.com`, localhost ni una URL de desarrollo como endpoint de producción.
5. **ServiceListing:** publicar el listing on-chain desde la wallet de la autoridad; el listing debe apuntar al PDA del agente y fijar precio SOL, hash/URI de especificación, capacidades y condiciones.
6. **Moderación:** autorizar la solicitud de moderación y comprobar que se haya registrado una atestación CLEAN en cadena. Un listing sin esa atestación no es hireable.
7. **Demanda y activación:** una contratación desde un listing crea una tarea; el comprador todavía debe activar su job spec y su moderación antes de que el trabajo sea claimable.
8. **Worker:** filtrar por el PDA del proveedor, verificar el job spec y su SHA-256 on-chain, deadline, reward, capacidades, límites de archivo y alcance. Tratar el job spec como entrada no confiable.
9. **Entrega:** disponer de backend HTTPS con autenticación, límites, expiración/borrado y almacenamiento de artefactos. Calcular SHA-256 en el servidor y entregar un puntero descargable de hasta 64 bytes en `result_data`.
10. **Pago:** el comprador acepta el resultado; sólo contar ingreso tras verificar un recibo/liquidación on-chain. El endpoint de earnings del proveedor por sí solo no demuestra que los fondos llegaron a la wallet.

## Estado de salida

| Control | Estado actual |
|---|---|
| Consultar API pública de AgenC | Implementado en auditoría read-only |
| Comprobar si la wallet tiene AgentRegistration | Implementado; resultado de ejecución pendiente |
| Comprobar listings propios e hireable | Implementado; resultado de ejecución pendiente |
| Verificar tareas con RPC y hash del job spec | Implementado en modo read-only; no ejecuta tareas |
| Pruebas automáticas de readiness | Añadidas en esta rama; CI debe confirmarlas |
| Registro real del agente | Pendiente de wallet firmante y autorización de coste |
| Endpoint HTTPS público real | Pendiente de elegir/configurar hosting |
| Publicación del listing | Pendiente de firma del titular |
| Moderación CLEAN | Pendiente de publicación y atestación |
| Worker de producción + artefactos HTTPS | Pendiente; no se habilita con este cambio |
| Primer pago real | No demostrado |

## Qué requiere intervención humana

No se puede completar de forma segura sólo desde GitHub: una persona debe conectar la wallet en AgenC, revisar el coste real que presenta la transacción y firmar el registro y la publicación. No compartir seed phrase ni clave privada. No firmar si el coste difiere del presupuesto aprobado.

Antes de habilitar claims o entregas reales, debe existir un endpoint HTTPS propio y verificable, el worker debe pasar una prueba end-to-end aislada y el titular debe aprobar explícitamente el primer ciclo real. El código actual no tiene autorización para ejecutar esas operaciones.

## Documentación oficial consultada

- [Trabajar como agente y costes de mainnet](https://agenc.ag/docs/quickstart-workers)
- [Vender servicios como proveedor](https://agenc.ag/docs/quickstart-providers)
- [API REST y campos de listings/agentes](https://agenc.ag/docs/api)
- [SDK TypeScript y revisión de protocolo](https://agenc.ag/docs/sdk)
- [Hosted write surfaces y requisitos de publicación](https://agenc.ag/docs/hosted-writes)
- [Trust, escrow y liquidación](https://agenc.ag/trust)

**Regla:** no anunciar “agente habilitado” hasta que el API confirme el registro y la oferta hireable, el endpoint funcione y la moderación esté CLEAN. No anunciar ingresos hasta verificar la liquidación on-chain.
