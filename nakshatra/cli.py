#!/usr/bin/env python3
"""
Nakshatra CLI - Calculate Vedic birth charts, Vimshottari Dashas, Vargas, Ashtakavarga, and Shadbala from the command line.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from nakshatra.core import (
    BirthData,
    Ayanamsa,
    HouseSystem,
    calculate_chart,
)


def main():
    parser = argparse.ArgumentParser(
        prog="nakshatra",
        description="Nakshatra - Vedic Astrology AI Engine CLI (Swiss Ephemeris)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nakshatra --dob 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060 --tz America/New_York
  nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --ayanamsa jhora_lahiri
  nakshatra --dob 1990-05-15 --time 14:30:00 --lat 12.9716 --lon 77.5946 --tz Asia/Kolkata --ayanamsa raman -p
        """
    )
    
    parser.add_argument(
        "--dob", "--date",
        required=True,
        help="Date of birth (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--time",
        required=True,
        help="Time of birth (HH:MM or HH:MM:SS, 24-hour format)"
    )
    parser.add_argument(
        "--lat", "--latitude",
        type=float,
        help="Latitude of birth place"
    )
    parser.add_argument(
        "--lon", "--longitude",
        type=float,
        help="Longitude of birth place"
    )
    parser.add_argument(
        "--tz", "--timezone",
        help="IANA timezone (e.g., America/New_York, Asia/Kolkata)"
    )
    parser.add_argument(
        "--place",
        help="Place name (for reference only)"
    )
    parser.add_argument(
        "--ayanamsa",
        choices=[a.value for a in Ayanamsa],
        default=Ayanamsa.LAHIRI.value,
        help=f"Ayanamsa system (default: {Ayanamsa.LAHIRI.value})"
    )
    parser.add_argument(
        "--house-system",
        choices=[h.value for h in HouseSystem],
        default=HouseSystem.WHOLE_SIGN.value,
        help=f"House system (default: {HouseSystem.WHOLE_SIGN.value})"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "markdown", "csv", "diagram"],
        default="table",
        help="Output format: table (default), json, markdown, csv, diagram"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print JSON output (forces --format json)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Auto-save to timestamped file (e.g., chart_19970522_045300.json)"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Nakshatra 0.1.0"
    )
    
    args = parser.parse_args()
    
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
    
    # Format output
    fmt = "json" if args.pretty else args.format
    if fmt == "table":
        output = chart.to_table()
    elif fmt == "markdown":
        output = chart.to_markdown()
    elif fmt == "csv":
        output = chart.to_csv()
    elif fmt == "diagram":
        output = chart.to_diagram()
    elif fmt == "json":
        output = chart.to_json() if args.pretty else chart.model_dump_json()
    else:
        output = chart.to_table()

    # Determine destination file path
    target_file = args.output
    if not target_file and args.save:
        ext = "json" if fmt == "json" else "md" if fmt == "markdown" else "csv" if fmt == "csv" else "txt"
        target_file = f"chart_{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}.{ext}"

    if target_file:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Chart saved to {target_file}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()