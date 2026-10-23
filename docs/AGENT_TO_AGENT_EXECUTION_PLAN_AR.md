# Plan operativo: agentes que venden servicios a otros agentes

**Objetivo:** generar ingresos prestando servicios digitales verificables a agentes de IA, cobrando por trabajo realizado o una comisión de intermediación cuando el mercado soporte ese mecanismo. La afiliación tradicional queda como canal secundario, no como estrategia central.

## Modelo comercial prioritario

### 1. Operador / intermediario en AgenC
- Preparar una tienda de agentes con listings concretos, alcance, precio/recompensa, formato de entrega y criterios de aceptación.
- Revisar las condiciones actuales de AgenC para comisiones de operador y referente antes de publicar.
- La comisión solo existe si la plataforma atribuye una contratación y la liquidación es confirmada. Una configuración local no crea ingresos por sí misma.

### 2. Agentes trabajadores
Construir primero servicios acotados que puedan ejecutarse con software gratuito/local y producir un artefacto comprobable:
- **Code QA:** ejecutar pruebas, detectar fallos reproducibles y generar informe.
- **Data QA:** validar CSV/JSON, encontrar duplicados, valores faltantes y anomalías; producir un reporte.
- **Research brief:** investigación con fuentes, fecha, resumen y enlaces, sin inventar resultados.
- **Document transformer:** convertir documentos estructurados a formatos acordados, sin procesar datos sensibles sin autorización.

Cada listing debe especificar entradas, salida, límites, tiempo estimado, precio, criterios de aceptación y política de revisión. No prometer capacidades que todavía no estén probadas.

### 3. Motor de derivación y comisiones
- Registrar cada oportunidad con ID único, mercado, agente cliente, agente ejecutor, valor, estado, fuente y prueba de aceptación.
- Calcular comisiones solo a partir de eventos válidos del proveedor y políticas expresamente habilitadas.
- Rechazar duplicados, auto-referidos, estados no confirmados, importes inválidos y eventos sin evidencia.
- Separar **propuesta de comisión**, **ingreso reportado por la plataforma** y **dinero recibido verificado**. No son equivalentes.

## Fases de ejecución

### Fase A — Seguridad y preparación
1. Mantener el trabajo en la rama agent-to-agent-monetization-v1 y revisar la PR antes de fusionar.
2. Eliminar direcciones de wallet codificadas de forma fija; usar una dirección pública configurada por el titular solo cuando esté lista. Nunca pedir ni almacenar seed phrase o clave privada.
3. Mantener mainnet, firma de transacciones, despliegues pagos y reclamación automática de tareas desactivados hasta que haya revisión explícita.
4. Ejecutar tests y CI; conservar resultados reproducibles.

### Fase B — Descubrimiento de demanda
1. Usar únicamente endpoints/comandos documentados y de solo lectura para descubrir tareas disponibles.
2. Guardar una instantánea con fecha, requisitos, recompensa, fecha límite, criterios de aceptación y comisiones/costes conocidos.
3. Puntuar cada tarea por beneficio neto estimado, dificultad, riesgo y capacidad real del agente.
4. No reclamar tareas ni comprometer entregas hasta validar la recompensa neta y el flujo de aceptación.

### Fase C — Primer servicio vendible
1. Elegir una tarea pequeña que el agente pueda completar de extremo a extremo.
2. Ejecutar una prueba con datos sintéticos o no sensibles.
3. Entregar un archivo verificable y registrar evidencia de aceptación.
4. Conectar los eventos reales del proveedor al ledger solo después de confirmar su esquema y condiciones.
5. Conciliar la comisión contra el registro del proveedor y, cuando corresponda, la transacción en cadena.

### Fase D — Escalar sin gastos fijos
- Priorizar ejecuciones locales o cuotas gratuitas reales.
- No desplegar servicios programados con cargo ni activar hosting pago sin autorización.
- Automatizar primero la lectura, clasificación y preparación de propuestas; mantener aprobación humana para claims, publicaciones, firmas y pagos.
- Añadir más agentes solo cuando el primero demuestre demanda, aceptación y economía positiva.

## Métricas de decisión
- tareas disponibles y elegibles;
- propuestas enviadas / aceptadas;
- entregas aceptadas;
- ingreso bruto reportado;
- comisión neta después de costes;
- horas de intervención humana;
- fallos, reversiones y disputas;
- ingreso efectivamente recibido y conciliado.

## Estado y límites actuales
El repositorio contiene un prototipo de ledger y utilidades de descubrimiento/consulta de AgenC de solo lectura. Las pruebas de CI no equivalen a un agente operativo en producción. Aún hay que verificar wallet pública elegida por el titular, publicación del storefront/listings, runtime de ejecución, flujo real de tareas, aceptación y primera liquidación. No se afirma que exista ingreso ni una integración de cobro activa.

## Regla de seguridad
No guardar frases semilla, claves privadas, contraseñas ni tokens en el repositorio, logs o chat. No firmar transacciones, pagar servicios, activar despliegues con cargo ni reclamar tareas que impliquen obligaciones sin autorización explícita.
