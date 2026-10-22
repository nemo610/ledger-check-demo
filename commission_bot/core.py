"""Small, local-first affiliate campaign helper. No automatic posting or scraping."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_OFFER_FIELDS = {"id", "name", "description", "audience", "affiliate_url", "commission_model"}


def load_offers(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("El catálogo debe ser una lista JSON.")
    seen = set()
    for i, offer in enumerate(data):
        if not isinstance(offer, dict):
            raise ValueError(f"La oferta #{i + 1} debe ser un objeto.")
        missing = REQUIRED_OFFER_FIELDS - offer.keys()
        if missing:
            raise ValueError(f"Oferta #{i + 1}: faltan campos: {', '.join(sorted(missing))}")
        if not str(offer["id"]).strip() or offer["id"] in seen:
            raise ValueError(f"ID de oferta vacío o duplicado: {offer['id']!r}")
        seen.add(offer["id"])
        parsed = urlparse(str(offer["affiliate_url"]))
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"URL de afiliado inválida para {offer['id']}: se requiere HTTPS.")
        if not offer.get("affiliate_approved", False):
            raise ValueError(f"La oferta {offer['id']} no está marcada como aprobada por el programa.")
    return data


def make_draft(offer: dict, channel: str = "social") -> str:
    """Create a human-reviewable draft; never publishes it."""
    if channel not in {"social", "email", "blog"}:
        raise ValueError("Canal admitido: social, email o blog.")
    name = str(offer["name"]).strip()
    description = re.sub(r"\s+", " ", str(offer["description"])).strip()
    audience = str(offer["audience"]).strip()
    url = str(offer["affiliate_url"]).strip()
    if not name or not description or not audience:
        raise ValueError("Nombre, descripción y audiencia no pueden estar vacíos.")
    disclosure = "Aviso de afiliación: puedo recibir una comisión si contratás mediante este enlace, sin costo adicional para vos."
    if channel == "email":
        return f"Asunto: Una herramienta para {audience}\n\n{description}\n\nMás información: {url}\n\n{disclosure}\n\nRevisá el producto, sus condiciones y su precio antes de decidir."
    if channel == "blog":
        return f"# {name}: ¿para quién puede servir?\n\n{description}\n\nEstá orientado a: {audience}. Revisá las características, limitaciones, precios y condiciones oficiales antes de contratar.\n\nMás información: {url}\n\n> {disclosure}\n"
    return f"{name}: {description}\n\nSi estás en el público de {audience}, compará las condiciones y el precio oficial antes de decidir: {url}\n\n{disclosure}\n#HerramientasDigitales #Recursos"


def generate_campaigns(offers: list[dict], channel: str = "social") -> list[dict]:
    return [{"offer_id": offer["id"], "offer_name": offer["name"], "channel": channel,
             "draft": make_draft(offer, channel), "status": "BORRADOR: requiere revisión humana"} for offer in offers]


def write_campaigns(offers_path: str | Path, output_path: str | Path, channel: str = "social") -> int:
    offers = load_offers(offers_path)
    campaigns = generate_campaigns(offers, channel)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n\n---\n\n".join(
        f"<!-- oferta: {item['offer_id']} | canal: {item['channel']} | {item['status']} -->\n{item['draft']}"
        for item in campaigns
    ) + "\n", encoding="utf-8")
    return len(campaigns)


def summarize_events(events_path: str | Path) -> dict:
    """Summarize a manually exported CSV with event_type, offer_id and amount."""
    totals = defaultdict(lambda: {"clicks": 0, "conversions": 0, "commission": 0.0})
    with Path(events_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"event_type", "offer_id", "amount"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV requiere columnas: event_type, offer_id, amount.")
        for line, row in enumerate(reader, start=2):
            kind = (row.get("event_type") or "").strip().lower()
            offer_id = (row.get("offer_id") or "").strip()
            if not offer_id:
                raise ValueError(f"Fila {line}: offer_id vacío.")
            if kind not in {"click", "conversion", "commission"}:
                raise ValueError(f"Fila {line}: event_type debe ser click, conversion o commission.")
            try:
                amount = float(row.get("amount") or 0)
            except ValueError as exc:
                raise ValueError(f"Fila {line}: amount no es numérico.") from exc
            if amount < 0:
                raise ValueError(f"Fila {line}: amount no puede ser negativo.")
            key = totals[offer_id]
            if kind == "click":
                key["clicks"] += 1
            elif kind == "conversion":
                key["conversions"] += 1
            else:
                key["commission"] += amount
    return {offer: {**values, "commission": round(values["commission"], 2)}
            for offer, values in sorted(totals.items())}


def write_report(events_path: str | Path, output_path: str | Path) -> dict:
    report = summarize_events(events_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
