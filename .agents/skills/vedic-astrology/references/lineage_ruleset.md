# Calculation Lineage & Astronomical Ruleset

Authentic Vedic Astrology requires declaring the computational lineage to ensure precision and avoid conflation with Western Tropical or competing schools.

## Default Mainline Lineage (`mainline-parashara-v1`)

- **Zodiac**: Sidereal (Nirayana) fixed to the galactic constellations.
- **Ayanamsa**: Jhora-Lahiri / Chitra Paksha Lahiri (~23.84° to 24.15° epoch dependent).
- **Ephemeris Engine**: Swiss Ephemeris (`pyswisseph`) based on JPL DE431/DE406 ephemerides.
- **House System (Bhava Chalita vs Rashi)**:
  - Default: Whole Sign (Rashi-as-House), where the entire sign of the Ascendant constitutes the 1st House.
  - Secondary: Sripati / Porphyry for cusp strength evaluation.
- **Node Calculation**: Mean Rahu/Ketu (Rahu Mean, Ketu 180° opposite).
- **Dasha System**: Vimshottari Dasha based on exact Moon Nakshatra longitude at birth (120 solar years cycle).
- **Day Boundary**: Vedic sunrise for Tithi, Vara, Nakshatra, Yoga, and Karana (Panchanga).
