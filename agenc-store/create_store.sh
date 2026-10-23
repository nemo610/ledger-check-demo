#!/usr/bin/env bash
set -euo pipefail

# Crear y compilar una tienda AgenC localmente. No despliega ni firma transacciones.
WALLET="CG8BV7x2jWnFkfnV4WMkjLLi3aj6Q2Hu5M8t98MLA391"
PROJECT_DIR="${1:-agenc-store-app}"
STORE_SITE_URL="${STORE_SITE_URL:-}"

if [[ -z "$STORE_SITE_URL" ]]; then
  echo "Falta STORE_SITE_URL: definí la URL HTTPS prevista para la tienda antes de compilar." >&2
  echo "Ejemplo: STORE_SITE_URL=https://tu-dominio.example ./agenc-store/create_store.sh" >&2
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
  --fee-bps 500 \
  --name "Nemo Agent Store" \
  --api-base-url https://api.agenc.ag \
  --site-url "$STORE_SITE_URL"

cp agenc-store/agenc.config.ts "$PROJECT_DIR/agenc.config.ts"
cd "$PROJECT_DIR"
npm install
npm ls @tetsuo-ai/store-core @tetsuo-ai/marketplace-react @tetsuo-ai/marketplace-sdk
npm run typecheck
npm run build

cat <<'NOTICE'
Build local terminado. La tienda NO está desplegada ni registrada.
Antes de publicarla: revisar agenc.config.ts, hosting/costos, RPC y wallet.
No se ejecutaron transacciones ni se aprobaron firmas.
NOTICE
