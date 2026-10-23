#!/usr/bin/env bash
set -euo pipefail

# Crear y compilar una tienda AgenC localmente. No despliega ni firma transacciones.
WALLET="${AGENC_WALLET:-}"
PROJECT_DIR="${1:-agenc-store-app}"
STORE_SITE_URL="${STORE_SITE_URL:-}"

if [[ -z "$WALLET" || ! "$WALLET" =~ ^[1-9A-HJ-NP-Za-km-z]{32,44}$ ]]; then
  echo "Falta AGENC_WALLET o no parece una dirección pública Solana válida." >&2
  echo "Configurá solo la dirección pública; nunca uses la seed phrase ni la clave privada." >&2
  exit 2
fi

if [[ -z "$STORE_SITE_URL" ]]; then
  echo "Falta STORE_SITE_URL: definí la URL HTTPS prevista para la tienda antes de compilar." >&2
  echo "Ejemplo: STORE_SITE_URL=https://tu-proyecto.vercel.app ./agenc-store/create_store.sh" >&2
  exit 2
fi

if [[ ! "$STORE_SITE_URL" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?(/.*)?$ ]]; then
  echo "STORE_SITE_URL debe ser una URL HTTPS válida." >&2
  exit 2
fi

if [[ "$STORE_SITE_URL" == *example.com* || "$STORE_SITE_URL" == *tu-proyecto* || "$STORE_SITE_URL" == *example.test* ]]; then
  echo "STORE_SITE_URL todavía parece un marcador de posición; usá la URL real del hosting." >&2
  exit 2
fi

if [[ "$PROJECT_DIR" == "." || "$PROJECT_DIR" == "/" || -e "$PROJECT_DIR" ]]; then
  echo "El directorio destino ya existe o no es seguro: $PROJECT_DIR" >&2
  echo "Elegí un directorio nuevo para no sobrescribir archivos." >&2
  exit 2
fi

npx --yes create-agenc-store@^0.6.1 "$PROJECT_DIR" \
  --yes \
  --template marketplace-store \
  --network mainnet \
  --allow-mainnet \
  --referrer "$WALLET" \
  --fee-bps 1500 \
  --name "Nemo Agent Store" \
  --api-base-url https://api.agenc.ag \
  --site-url "$STORE_SITE_URL"

cp agenc-store/agenc.config.ts "$PROJECT_DIR/agenc.config.ts"
cd "$PROJECT_DIR"
npm install
export NEXT_PUBLIC_SITE_URL="$STORE_SITE_URL"
export AGENC_WALLET="$WALLET"
npm ls @tetsuo-ai/store-core @tetsuo-ai/marketplace-react @tetsuo-ai/marketplace-sdk
npm run typecheck
npm run build

cat <<'NOTICE'
Build local terminado. La tienda NO está desplegada ni registrada.
Comisiones configuradas: operador 20%, referidor 15%, protocolo 5% cuando corresponda.
Antes de publicar: revisar hosting/costos, la URL, los fees y las operaciones on-chain.
No se ejecutaron transacciones ni se aprobaron firmas.
NOTICE
