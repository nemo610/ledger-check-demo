# Plan de implementación de cobros — Argentina

## Objetivo

Implementar ingresos por comisiones entre agentes de software, con registro verificable y retiro utilizable en Argentina. No se habilitan transferencias ni pagos reales desde este repositorio hasta completar pruebas y una autorización explícita.

## Hallazgo principal

El alias bancario `donatonuevaesperanza` es un destino para transferencias iniciadas por una persona o sistema bancario compatible; no es una dirección de blockchain ni una credencial de API. Por sí solo no permite a un marketplace enviar liquidaciones automáticamente.

## Ruta recomendada para el modelo agente-a-agente

1. **Marketplace/operador:** validar elegibilidad y condiciones del marketplace AgenC, registrar una dirección pública Solana como operador o referente según su documentación y confirmar cómo se atribuyen las comisiones.
2. **Lectura de ingresos:** consultar únicamente los endpoints públicos documentados de hires del operador/referente. Registrar respuesta original, fecha, wallet y estado; los resultados del endpoint no prueban por sí solos una transferencia recibida.
3. **Verificación de liquidación:** para cada operación, comprobar la firma/transacción on-chain, estado confirmado, destinatario, token, importe neto y posibles reembolsos antes de marcarla como cobrada.
4. **Conciliación:** mantener un ledger idempotente que enlace `event_id`, hire/operación, firma de transacción y registro contable. No duplicar ingresos por reintentos de API.
5. **Conversión a pesos argentinos:** estudiar por separado un proveedor regulado y disponible en Argentina que acepte el activo/red exactos, permita retiro a cuenta bancaria propia y tenga KYC/fees conocidos. No prometer conversión automática a Mercado Pago o Santander sin validar ese proveedor y sus términos.

## Papel de Mercado Pago

Mercado Pago Argentina dispone de APIs para recibir pagos y de Split de Pagos 1:1 para marketplaces. El split requiere una aplicación de marketplace, OAuth de vendedores, cuenta de vendedor con el nivel de identificación requerido y una integración de checkout. La documentación indica que el modelo 1:N está restringido a vendedores de cartera asesorada en contacto con el equipo comercial. Esto sirve como alternativa para cobros comerciales convencionales, pero no demuestra que un agente externo pueda liquidar una comisión a través de Mercado Pago sin una operación de checkout y autorización compatibles.

Documentación oficial:
- https://www.mercadopago.com.ar/developers/es
- https://www.mercadopago.com.ar/developers/es/docs/split-payments/split-1-1/overview
- https://www.mercadopago.com.ar/developers/es/docs/split-payments/split-1-1/prerequisites
- https://www.mercadopago.com.ar/developers/es/docs/security/oauth/introduction

## Santander y alias bancario

La cuenta Santander puede ser el destino final de fondos en pesos, pero no debe asumirse que el banco ofrece una API personal de recepción automatizada adecuada para este caso. Verificar con Santander los productos de cobro/API habilitados para el tipo de cuenta. El alias informado no debe tratarse como una API ni como una billetera cripto.

## Seguridad y controles obligatorios

- Nunca pedir, guardar o subir frases semilla, claves privadas, códigos de autenticación ni tokens de Mercado Pago al repositorio.
- Solo dirección pública de Solana para consultas de lectura; nunca firmar o enviar transacciones sin elección explícita de billetera, revisión de importe/red/destinatario y autorización expresa.
- No usar endpoints de consulta que cobren por solicitud sin aprobación previa.
- No registrar ingresos hasta verificar la transacción y conciliar el destinatario real.
- Mantener secretos en variables de entorno/secret manager y fuera de Git.
- Comenzar en modo lectura y pruebas; no activar pagos automáticos ni mover fondos como parte de esta fase.

## Estado de implementación

- Existe un adaptador AgenC de solo lectura en `agent_economy/agenc_adapter.py`.
- El adaptador valida el formato de la dirección y la forma básica de la respuesta del proveedor; informa `settlement_verified: false` y no firma ni envía transacciones.
- El adaptador aún no está conectado al CLI y no cuenta con una suite de pruebas propia; el CI existente no debe interpretarse como prueba de este adaptador.
- No se ha conectado una wallet, una cuenta de Mercado Pago ni Santander; no se han comprobado ingresos reales.

## Próximas tareas técnicas

1. Añadir pruebas unitarias del adaptador: dirección inválida, timeout/HTTP error, JSON inválido, `live != true`, `hires` malformado y respuesta vacía.
2. Integrar un comando explícito de consulta en el CLI, guardando un snapshot fechado sin credenciales y dejando claro que son datos declarados por el proveedor.
3. Añadir un verificador de transacción on-chain independiente antes de cualquier estado `settled/verified`.
4. Documentar un procedimiento de conciliación y retiro sin automatizar movimientos de fondos.
5. Recién después de verificar una liquidación real, evaluar una rampa fiat compatible con Argentina y documentar costes, límites, KYC e impuestos aplicables.
