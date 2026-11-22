#!/usr/bin/env python3
"""
Nakshatra CLI - Calculate Vedic birth charts, Vimshottari Dashas,
Vargas, Ashtakavarga, and Shadbala from the command line.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from nakshatra.core import (
    Ayanamsa,
    BirthData,
    HouseSystem,
    calculate_chart,
)


def _build_chart_parser() -> argparse.ArgumentParser:
    """Parent parser holding all chart-mode arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--dob", "--date", help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--time", help="Time of birth (HH:MM or HH:MM:SS, 24-hour format)")
    parser.add_argument("--lat", "--latitude", type=float, help="Latitude of birth place")
    parser.add_argument("--lon", "--longitude", type=float, help="Longitude of birth place")
    parser.add_argument(
        "--tz", "--timezone", help="IANA timezone (e.g., America/New_York, Asia/Kolkata)"
    )
    parser.add_argument("--place", help="Place name (for reference only)")
    parser.add_argument(
        "--ayanamsa",
        choices=[a.value for a in Ayanamsa],
        default=Ayanamsa.JHORA_LAHIRI.value,
        help=f"Ayanamsa system (default: {Ayanamsa.JHORA_LAHIRI.value})",
    )
    parser.add_argument(
        "--house-system",
        choices=[h.value for h in HouseSystem],
        default=HouseSystem.WHOLE_SIGN.value,
        help=f"House system (default: {HouseSystem.WHOLE_SIGN.value})",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "markdown", "csv", "diagram"],
        default="table",
        help="Output format: table (default), json, markdown, csv, diagram",
    )
    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Pretty print JSON output (forces --format json)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--save",
        "-s",
        action="store_true",
        help="Auto-save to timestamped file (e.g., chart_19970522_045300.json)",
    )
    parser.add_argument(
        "--varga",
        default="D1",
        help="Divisional chart to display for diagram/varga view (e.g., D1, D9, D10; default: D1)",
    )
    parser.add_argument(
        "--transit",
        nargs="?",
        const="now",
        default=None,
        help=(
            "Calculate planetary transits against natal chart "
            "(e.g., --transit or --transit 2026-10-10)"
        ),
    )
    parser.add_argument(
        "--panchanga",
        action="store_true",
        help="Calculate and display Vedic Panchanga (Tithi, Vara, Nakshatra, Yoga, Karana)",
    )
    parser.add_argument(
        "--yogas",
        action="store_true",
        help="Detect and display classical Vedic Yogas (Mahapurusha, Gaja Kesari, Kemadruma, Neechabhanga, etc.)",
    )
    return parser


def _run_ingest_corpus(args: argparse.Namespace) -> None:
    """Run corpus ingestion (nakshatra ingest-corpus subcommand)."""
    from nakshatra.ai.corpus import ingest_corpus

    try:
        result = ingest_corpus(args.dir, args.out)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingested {result.total_chunks} chunks from {result.total_files} files")
    for report in result.reports:
        translator = report.translator or "unknown translator"
        print(
            f"  {report.work} ({translator}, {report.license}): "
            f"{report.chunks} chunks "
            f"({report.verse_chunks} verse, {report.paragraph_chunks} paragraph) "
            f"from {report.files} file(s)"
        )
    print(f"Index written to {args.out}/corpus.jsonl")


def main() -> None:
    chart_parser = _build_chart_parser()
    parser = argparse.ArgumentParser(
        prog="nakshatra",
        description="Nakshatra — The Science of Light CLI (Swiss Ephemeris)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[chart_parser],
        epilog="""
Examples:
  nakshatra --dob 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060 --tz America/New_York
  nakshatra --dob 1985-10-24 --time 09:15 --lat 27.7172 --lon 85.3240 --tz Asia/Kathmandu
  nakshatra --dob 1990-05-15 --time 14:30:00 --lat 12.9716 --lon 77.5946 --tz Asia/Kolkata
  nakshatra ingest-corpus --dir corpus --out index
        """,
    )
    parser.add_argument("--version", "-v", action="version", version="Nakshatra 0.1.0")

    subparsers = parser.add_subparsers(dest="command")
    corpus_parser = subparsers.add_parser(
        "ingest-corpus",
        help="Ingest classical text corpus into a chunked JSONL index",
        description=(
            "Ingest classical Vedic astrology texts into a chunked JSONL "
            "index with citation metadata. Each work directory must contain "
            "meta.json with work, translator, and license fields."
        ),
    )
    corpus_parser.add_argument(
        "--dir", default="corpus", help="Corpus root directory (default: corpus)"
    )
    corpus_parser.add_argument(
        "--out",
        default="index",
        help="Output directory for corpus.jsonl + manifest.json (default: index)",
    )

    args = parser.parse_args()

    if args.command == "ingest-corpus":
        _run_ingest_corpus(args)
        return

    # Chart mode: validate required birth data
    if args.dob is None or args.time is None:
        parser.error(
            "--dob and --time are required for chart calculation "
            "(see 'nakshatra ingest-corpus --help' for corpus ingestion)"
        )

    # Parse date
    try:
        date_parts = args.dob.split("-")
        year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
    except (ValueError, IndexError):
        print("Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    # Parse time
    try:
        time_parts = args.time.split(":")
        hour, minute = int(time_parts[0]), int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
    except (ValueError, IndexError):
        print("Error: Invalid time format. Use HH:MM or HH:MM:SS", file=sys.stderr)
        sys.exit(1)

    # Validate required location data
    if args.lat is None or args.lon is None or args.tz is None:
        print("Error: --lat, --lon, and --tz are required", file=sys.stderr)
        sys.exit(1)

    # Create birth data
    birth = BirthData(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        latitude=args.lat,
        longitude=args.lon,
        timezone=args.tz,
        place_name=args.place,
    )

    # Calculate chart
    try:
        chart = calculate_chart(
            birth=birth,
            ayanamsa=Ayanamsa(args.ayanamsa),
            house_system=HouseSystem(args.house_system),
        )
    except Exception as e:
        print(f"Error calculating chart: {e}", file=sys.stderr)
        sys.exit(1)

    # Check for transit calculation
    if args.transit is not None:
        t_date = None
        if args.transit != "now":
            try:
                if "T" in args.transit:
                    t_date = datetime.fromisoformat(args.transit)
                elif " " in args.transit:
                    t_date = datetime.strptime(args.transit, "%Y-%m-%d %H:%M:%S")
                else:
                    t_date = datetime.strptime(args.transit, "%Y-%m-%d")
            except ValueError:
                print(
                    f"Error: Invalid transit date '{args.transit}'. "
                    "Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS",
                    file=sys.stderr,
                )
                sys.exit(1)

        transit_rep = chart.get_transits(t_date)
        fmt = "json" if args.pretty else args.format
        if fmt == "json":
            output = transit_rep.model_dump_json(indent=2 if args.pretty else None)
        else:
            output = transit_rep.to_table()

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Transit report saved to {args.output}", file=sys.stderr)
        else:
            print(output)
        return

    # Check for panchanga calculation
    if args.panchanga:
        p_data = chart.get_panchanga()
        fmt = "json" if args.pretty else args.format
        if fmt == "json":
            output = p_data.model_dump_json(indent=2 if args.pretty else None)
        else:
            output = p_data.to_table()

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Panchanga report saved to {args.output}", file=sys.stderr)
        else:
            print(output)
        return

    # Check for yogas calculation
    if args.yogas:
        import json

        from nakshatra.yogas import format_yogas_markdown, format_yogas_table

        yogas_list = chart.get_yogas()
        fmt = "json" if args.pretty else args.format
        if fmt == "json":
            output = json.dumps(
                [y.model_dump() for y in yogas_list], indent=2 if args.pretty else None
            )
        elif fmt == "markdown":
            output = format_yogas_markdown(yogas_list)
        else:
            output = format_yogas_table(yogas_list)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Yogas report saved to {args.output}", file=sys.stderr)
        else:
            print(output)
        return

    # Format output
    fmt = "json" if args.pretty else args.format
    if fmt == "table":
        output = chart.to_table()
    elif fmt == "markdown":
        output = chart.to_markdown()
    elif fmt == "csv":
        output = chart.to_csv()
    elif fmt == "diagram":
        output = chart.to_diagram(varga=args.varga)
    elif fmt == "json":
        output = chart.to_json() if args.pretty else chart.model_dump_json()
    else:
        output = chart.to_table()

    # Determine destination file path
    target_file = args.output
    if not target_file and args.save:
        if fmt == "json":
            ext = "json"
        elif fmt == "markdown":
            ext = "md"
        elif fmt == "csv":
            ext = "csv"
        else:
            ext = "txt"
        stamp = f"{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}"
        target_file = f"chart_{stamp}.{ext}"

    if target_file:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Chart saved to {target_file}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
