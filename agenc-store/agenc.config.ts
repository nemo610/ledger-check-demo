import { defineStore } from "@tetsuo-ai/store-core/config";

/**
 * Configuración inicial de una tienda de REFERIDOS.
 * La wallet pública se inyecta desde el entorno; nunca se guarda en Git.
 * Solo se activa la comisión referrer (2,5 %). No activar operator hasta
 * aprobar una estrategia de venta propia y sus costes por separado.
 * Esta configuración no firma, registra ni despliega la tienda.
 */
const commissionWallet = process.env.AGENC_WALLET ?? "";

export default defineStore({
  name: "Nemo Agent Store",
  description:
    "Catálogo curado de servicios de agentes de IA; las contrataciones referidas pueden generar una comisión.",
  network: "mainnet",
  allowMainnet: true,
  api: { baseUrl: "https://api.agenc.ag" },
  referrer: {
    wallet: commissionWallet,
    feeBps: 250,
  },
  branding: { poweredBy: true },
  curation: { requireModeration: true },
  seo: { siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "https://example.com" },
});
