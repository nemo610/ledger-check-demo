# Integración AgenC — tienda y comisiones optimizadas

## Estrategia de comisiones

La configuración de esta rama propone, dentro del límite documentado por AgenC:

- **Operator: 20% (2000 bps)** para listings creados con estos términos.
- **Referrer: 15% (1500 bps)** para contrataciones atribuidas a la tienda.
- **Protocolo AgenC: 5%**, aplicado por el protocolo.
- **Máximo combinado: 40%**; el agente trabajador conserva el 60% cuando se aplican ambas patas y la tarifa de protocolo.

No es una comisión universal del 35% para cualquier tarea. La pata de referidor requiere atribución a nuestra superficie; la pata de operador requiere listings creados con esos términos y depende de la ruta de liquidación. Las tareas de terceros no pueden recibir nuestra comisión de operador de forma retroactiva. Una comisión alta puede reducir la conversión o hacer que los proveedores elijan otras tiendas.

La configuración se debe volver a comprobar contra los límites de la versión de protocolo activa antes de registrar la tienda. No cambiar las comisiones en producción sin revisar el impacto en los proveedores.

## Estado del repositorio

Este repositorio es un prototipo Python, no una tienda Next.js ya desplegada. El script agenc-store/create_store.sh usa la plantilla oficial create-agenc-store@^0.6.1, copia la configuración de comisiones y ejecuta las comprobaciones de dependencias, tipos y build. El script no publica, registra la tienda ni firma transacciones.

## Opciones de publicación

**Primera opción: tienda alojada en AgenC.** La documentación oficial describe un camino hospedado en agenc.ag/store: reclamar un identificador de tienda, publicar servicios y listings, y consultar las ganancias de referidor en /store/earnings. Las páginas públicas aparecen bajo /@handle. Es el camino más directo para evitar operar infraestructura propia, pero requiere completar la conexión y firma de wallet que pida el sitio y verificar las condiciones vigentes.

**Segunda opción: tienda propia.** El scaffold oficial crea una aplicación Next.js. Requiere elegir una URL HTTPS real, compilar, desplegar en un proveedor compatible, configurar RPC de Solana mainnet y verificar el sitio público. No se debe usar https://example.com como URL real. El script rechaza marcadores de posición y no hace deploy.

## Pasos de prepublicación

1. Confirmar con el titular la wallet pública receptora y la URL/handle deseados; no introducir ni compartir frase semilla o clave privada.
2. Revisar el saldo y el requisito vigente de rent-exemption para cada wallet receptora antes de esperar liquidaciones. Si la cuenta no cumple el mínimo, una liquidación puede revertir.
3. Elegir el camino alojado de AgenC o un hosting compatible sin activar servicios pagos ni aceptar cargos sin autorización explícita.
4. Ejecutar el scaffold y validar npm ls @tetsuo-ai/store-core @tetsuo-ai/marketplace-react @tetsuo-ai/marketplace-sdk, npm run typecheck y npm run build.
5. Revisar el preflight de fees: operador 20%, referidor 15%, protocolo 5%, máximo 40% combinado cuando todas las patas correspondan.
6. Completar registro/publicación solamente con revisión explícita de las transacciones y firmas requeridas.
7. Verificar una contratación de prueba y conciliar el recibo on-chain antes de afirmar que hay ingresos.

## Seguridad y costos

- No se guarda ninguna clave privada ni frase semilla en el repositorio.
- Los cambios de código y la configuración de fees no activan por sí mismos una tienda ni prueban ingresos.
- allowMainnet: true indica opt-in de configuración a mainnet; no autoriza por sí mismo una transacción.
- No ejecutar firmas, registros, transferencias ni activar infraestructura paga sin aprobación explícita.
- La comisión solo es ingreso confirmado cuando una contratación válida se liquida y la transacción reparte la comisión a la wallet correspondiente.

## Documentación oficial

- Lanzar una tienda: https://agenc.ag/docs/launch-a-marketplace
- Economía y límites: https://agenc.ag/trust
- Protocolo y reparto: https://agenc.ag/protocol
