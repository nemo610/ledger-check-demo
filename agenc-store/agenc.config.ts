import { defineStore } from "@tetsuo-ai/store-core/config";

/**
 * Configuración inicial de la tienda AgenC.
 *
 * Comisión de referidor: 5% para contrataciones originadas desde esta superficie.
 * Comisión de operador: 5% para listings publicados con estos términos.
 * AgenC cobra su 5% de protocolo por separado; en un reparto con ambas tarifas
 * el agente trabajador conservaría aproximadamente el 85%.
 *
 * Este archivo NO registra la tienda ni despliega el sitio por sí solo.
 * La activación requiere scaffold/build, revisión de los fees y conexión de
 * una wallet que firme las operaciones on-chain necesarias.
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
    feeBps: 500,
  },
  operator: {
    wallet: "CG8BV7x2jWnFkfnV4WMkjLLi3aj6Q2Hu5M8t98MLA391",
    feeBps: 500,
  },
  branding: { poweredBy: true },
  curation: { requireModeration: true },
  seo: { siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "https://example.com" },
});
