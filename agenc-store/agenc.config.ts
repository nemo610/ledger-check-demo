import { defineStore } from "@tetsuo-ai/store-core/config";

/**
 * Configuración inicial de la tienda AgenC.
 *
 * Objetivo de comisión máxima documentada:
 * - Operador: 20% (máximo individual documentado).
 * - Referidor: 15%.
 * - Protocolo: 5% aplicado por AgenC.
 * - Total máximo: 40%; el agente trabajador conserva 60%.
 *
 * Ambas patas solo aplican cuando se cumplen sus condiciones de atribución.
 * Esta configuración NO registra ni despliega la tienda y no firma operaciones.
 */
export default defineStore({
  name: "Nemo Agent Store",
  description:
    "Tienda independiente de agentes de IA para servicios digitales verificables.",
  network: "mainnet",
  allowMainnet: true,
  api: { baseUrl: "https://api.agenc.ag" },
  referrer: {
    wallet: "CG8BV7x2jWnFkfnV4WMkjLLi3aj6Q2Hu5M8t98MLA391",
    feeBps: 1500,
  },
  operator: {
    wallet: "CG8BV7x2jWnFkfnV4WMkjLLi3aj6Q2Hu5M8t98MLA391",
    feeBps: 2000,
  },
  branding: { poweredBy: true },
  curation: { requireModeration: true },
  seo: { siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "https://example.com" },
});
