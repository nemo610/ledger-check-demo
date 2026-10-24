import { defineStore } from "@tetsuo-ai/store-core/config";

/**
 * Configuración de tienda AgenC con ingresos separados:
 * - referrer: comisión por compras originadas desde la tienda.
 * - operator: comisión por listings propios publicados con estos términos.
 *
 * Seguridad: devnet por defecto. Mainnet requiere AGENC_ALLOW_MAINNET=true.
 * Las wallets son direcciones públicas configuradas por entorno; no se guardan
 * claves privadas aquí. Este archivo no registra, publica ni firma transacciones.
 */
const allowMainnet = process.env.AGENC_ALLOW_MAINNET === "true";
const commissionWallet = process.env.AGENC_WALLET ?? "";
const operatorWallet = process.env.AGENC_OPERATOR_WALLET ?? "";
const operatorFeeRaw = process.env.AGENC_OPERATOR_FEE_BPS ?? "";
const operatorFeeBps = operatorFeeRaw === "" ? 0 : Number(operatorFeeRaw);

if (!Number.isInteger(operatorFeeBps) || operatorFeeBps < 0 || operatorFeeBps > 2000) {
  throw new Error("AGENC_OPERATOR_FEE_BPS must be an integer from 0 to 2000.");
}
if (operatorFeeBps > 0 && !operatorWallet.trim()) {
  throw new Error("AGENC_OPERATOR_WALLET is required when operator fees are enabled.");
}
if (operatorFeeBps === 0 && operatorWallet.trim()) {
  throw new Error("Operator wallet is configured but its fee is disabled; set AGENC_OPERATOR_FEE_BPS explicitly.");
}

const operator =
  operatorFeeBps > 0
    ? { wallet: operatorWallet.trim(), feeBps: operatorFeeBps }
    : undefined;

export default defineStore({
  name: "Nemo Agent Store",
  description:
    "Catálogo curado de servicios de agentes de IA; las contrataciones referidas pueden generar una comisión.",
  network: allowMainnet ? "mainnet" : "devnet",
  allowMainnet,
  api: { baseUrl: "https://api.agenc.ag" },
  referrer: {
    wallet: commissionWallet,
    feeBps: 250,
  },
  ...(operator ? { operator } : {}),
  branding: { poweredBy: true },
  curation: { requireModeration: true },
  seo: { siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "https://example.com" },
});
