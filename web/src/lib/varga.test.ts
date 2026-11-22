import test from "node:test";
import assert from "node:assert";
import {
  getNakshatra,
  vargaDegree,
  getVargaPositions,
  getVargaAscendant,
  getVargaMoon,
} from "./varga.ts";
import type { ChartData } from "./types.ts";

test("getNakshatra mirrors nakshatra/core.py get_nakshatra", () => {
  // Values cross-checked against the Python backend.
  assert.deepStrictEqual(getNakshatra(0), { nakshatra: "Ashwini", lord: "Ketu", pada: 1 });
  assert.deepStrictEqual(getNakshatra(13.5), { nakshatra: "Bharani", lord: "Venus", pada: 1 });
  assert.deepStrictEqual(getNakshatra(18), { nakshatra: "Bharani", lord: "Venus", pada: 2 });
  assert.deepStrictEqual(getNakshatra(102), { nakshatra: "Pushya", lord: "Saturn", pada: 3 });
  assert.deepStrictEqual(getNakshatra(258), { nakshatra: "Purva Ashadha", lord: "Venus", pada: 2 });
  assert.deepStrictEqual(getNakshatra(350), { nakshatra: "Revati", lord: "Mercury", pada: 1 });
});

test("vargaDegree is the position inside the divisional segment", () => {
  // D9: 12 deg in sign -> 3rd segment starts at 10 deg, 2 deg in -> 18 deg.
  assert.strictEqual(vargaDegree(12, "D9"), 18);
  // Segment boundary stays at 0, never 30.
  assert.strictEqual(vargaDegree(10, "D9"), 0);
  // D1 is unchanged.
  assert.strictEqual(vargaDegree(12.5, "D1"), 12.5);
  // Unknown varga falls back to D1.
  assert.strictEqual(vargaDegree(12.5, "DX"), 12.5);
});

const CHART: ChartData = {
  ascendant: {
    sign: "Aries",
    degree_in_sign: 6.5,
    nakshatra: "Ashwini",
    nakshatra_lord: "Ketu",
    pada: 2,
    longitude: 6.5,
  },
  planets: [
    {
      name: "Sun",
      sign: "Aries",
      degree_in_sign: 12,
      nakshatra: "Ashwini",
      nakshatra_lord: "Ketu",
      pada: 4,
      house: 1,
      retrograde: false,
      longitude: 12,
      latitude: 0,
      speed: 1,
    },
    {
      name: "Moon",
      sign: "Leo",
      degree_in_sign: 6.1,
      nakshatra: "Magha",
      nakshatra_lord: "Ketu",
      pada: 2,
      house: 5,
      retrograde: false,
      longitude: 126.1,
      latitude: 0,
      speed: 1,
    },
  ],
  rahu: {
    name: "Rahu",
    sign: "Libra",
    degree_in_sign: 20,
    nakshatra: "Swati",
    nakshatra_lord: "Rahu",
    pada: 4,
    house: 7,
    retrograde: true,
    longitude: 200,
    latitude: 0,
    speed: -0.05,
  },
  ketu: {
    name: "Ketu",
    sign: "Aries",
    degree_in_sign: 20,
    nakshatra: "Ashwini",
    nakshatra_lord: "Ketu",
    pada: 4,
    house: 1,
    retrograde: true,
    longitude: 20,
    latitude: 0,
    speed: -0.05,
  },
  houses: [],
  vargas: {
    D9: {
      Ascendant: "Sagittarius",
      Sun: "Sagittarius",
      Moon: "Aries",
      "North Node": "Aquarius",
      "South Node": "Leo",
    },
  },
  ayanamsa: { name: "JHora Lahiri", value: "jhora_lahiri" },
  birth: {
    year: 1984,
    month: 2,
    day: 17,
    hour: 9,
    minute: 31,
    second: 0,
    latitude: 27.7,
    longitude: 85.3,
    timezone: "Asia/Kathmandu",
    place_name: "Kathmandu",
  },
};

test("getVargaPositions follows the selected divisional (D9)", () => {
  const rows = getVargaPositions(CHART, "D9");
  const sun = rows.find((r) => r.name === "Sun");
  assert.ok(sun);
  // Sign/house come from the backend varga map, not D1.
  assert.strictEqual(sun.sign, "Sagittarius");
  assert.strictEqual(sun.house, 1);
  assert.strictEqual(sun.signLord, "Jupiter");
  // Degree is the segment position: (12 * 9) % 30 = 18.
  assert.strictEqual(sun.degreeInSign, 18);
  // 258 deg absolute -> Purva Ashadha, pada 2 (matches backend).
  assert.strictEqual(sun.nakshatra, "Purva Ashadha");
  assert.strictEqual(sun.pada, 2);
  // Retrograde is carried over unchanged.
  const rahu = rows.find((r) => r.name === "Rahu");
  assert.ok(rahu);
  assert.strictEqual(rahu.sign, "Aquarius");
  assert.strictEqual(rahu.retrograde, true);
});

test("getVargaPositions falls back to D1 without varga data", () => {
  const rows = getVargaPositions(CHART, "D1");
  const sun = rows.find((r) => r.name === "Sun");
  assert.ok(sun);
  assert.strictEqual(sun.sign, "Aries");
  assert.strictEqual(sun.degreeInSign, 12);
  assert.strictEqual(sun.house, 1);
  assert.strictEqual(sun.nakshatra, "Ashwini");

  const noVargas = getVargaPositions({ ...CHART, vargas: undefined }, "D9");
  assert.strictEqual(noVargas.find((r) => r.name === "Sun")?.sign, "Aries");
});

test("getVargaAscendant/getVargaMoon follow the selected divisional", () => {
  const asc = getVargaAscendant(CHART, "D9");
  assert.strictEqual(asc.sign, "Sagittarius");
  // Ascendant D1 6.5 deg -> (6.5 * 9) % 30 = 28.5.
  assert.strictEqual(asc.degreeInSign, 28.5);
  const moon = getVargaMoon(CHART, "D9");
  assert.ok(moon);
  assert.strictEqual(moon.sign, "Aries");
  assert.strictEqual(moon.degreeInSign, 24.9);
});
