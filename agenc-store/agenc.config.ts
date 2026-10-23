import { defineStore } from "@tetsuo-ai/store-core/config";

/**
 * Configuración inicial de la tienda AgenC.
 * La dirección pública se inyecta desde el entorno; nunca guardar una wallet
 * personal fija en el repositorio. Esta configuración no firma ni despliega.
 */
const commissionWallet = process.env.AGENC_WALLET ?? "";

export default defineStore({
  name: "Nemo Agent Store",
  description:
    "Tienda independiente de agentes de IA para servicios digitales verificables.",
  network: "mainnet",
  allowMainnet: true,
  api: { baseUrl: "https://api.agenc.ag" },
  referrer: {
    wallet: commissionWallet,
    feeBps: 250,
  },
  operator: {
    wallet: commissionWallet,
    feeBps: 500,
  },
  branding: { poweredBy: true },
  curation: { requireModeration: true },
  seo: { siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "https://example.com" },
});
