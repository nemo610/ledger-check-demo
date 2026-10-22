"""Command line interface for Commission Bot."""
import argparse
import json
from .core import write_campaigns, write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera borradores de afiliación y resume reportes CSV locales.")
    sub = parser.add_subparsers(dest="command", required=True)
    drafts = sub.add_parser("drafts", help="Generar borradores para revisión humana")
    drafts.add_argument("--offers", default="data/offers.example.json")
    drafts.add_argument("--out", default="output/campaign_drafts.md")
    drafts.add_argument("--channel", choices=["social", "email", "blog"], default="social")
    report = sub.add_parser("report", help="Resumir exportación CSV del programa de afiliados")
    report.add_argument("--events", required=True)
    report.add_argument("--out", default="output/commission_report.json")
    args = parser.parse_args()
    if args.command == "drafts":
        count = write_campaigns(args.offers, args.out, args.channel)
        print(f"Generados {count} borradores revisables en {args.out}; no se publicó nada.")
    else:
        result = write_report(args.events, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Reporte guardado en {args.out}; los importes dependen del CSV importado.")


if __name__ == "__main__":
    main()
