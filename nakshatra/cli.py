#!/usr/bin/env python3
"""
Nakshatra CLI - Calculate Vedic birth charts from command line.
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
        description="Nakshatra - Vedic Astrology AI Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nakshatra --dob 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060 --tz America/New_York
  nakshatra --dob 1990-05-15 --time 14:30 --place "New York, NY"
  nakshatra --dob 1990-05-15 --time 14:30:00 --lat 12.9716 --lon 77.5946 --tz Asia/Kolkata --ayanamsa raman
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
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print JSON output"
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
    
    # Output JSON
    output = chart.to_json() if args.pretty else chart.model_dump_json()
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Chart saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()