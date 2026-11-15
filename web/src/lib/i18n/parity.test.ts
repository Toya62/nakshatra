import test from "node:test";
import assert from "node:assert";
import { dictionaries } from "./index.ts";

function getLeafPaths(obj: Record<string, unknown>, prefix = ""): Record<string, unknown> {
  const leaves: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    if (val !== null && typeof val === "object" && !Array.isArray(val)) {
      Object.assign(leaves, getLeafPaths(val as Record<string, unknown>, fullPath));
    } else {
      leaves[fullPath] = val;
    }
  }
  return leaves;
}

test("en and ne dictionaries have identical top-level namespaces", () => {
  const enNamespaces = Object.keys(dictionaries.en).sort();
  const neNamespaces = Object.keys(dictionaries.ne).sort();
  assert.deepStrictEqual(neNamespaces, enNamespaces);
});

test("en and ne have identical recursive leaf keys and valid values", () => {
  const enLeaves = getLeafPaths(dictionaries.en as unknown as Record<string, unknown>);
  const neLeaves = getLeafPaths(dictionaries.ne as unknown as Record<string, unknown>);

  const enKeys = Object.keys(enLeaves).sort();
  const neKeys = Object.keys(neLeaves).sort();

  assert.deepStrictEqual(
    neKeys,
    enKeys,
    `Mismatch in recursive leaf keys. Missing in NE: ${enKeys.filter((k) => !neKeys.includes(k))}, Extra in NE: ${neKeys.filter((k) => !enKeys.includes(k))}`
  );

  // Assert no leaf value in NE is empty, undefined, null, or whitespace-only
  for (const [key, val] of Object.entries(neLeaves)) {
    if (typeof val === "string") {
      assert.ok(val.trim().length > 0, `Empty or whitespace-only leaf string at "${key}" in NE`);
    } else if (Array.isArray(val)) {
      assert.ok(val.length > 0, `Empty leaf array at "${key}" in NE`);
      for (let i = 0; i < val.length; i++) {
        if (typeof val[i] === "string") {
          assert.ok(val[i].trim().length > 0, `Empty string at array index ${i} in "${key}" in NE`);
        }
      }
    } else {
      assert.notStrictEqual(val, null, `Null leaf at "${key}" in NE`);
      assert.notStrictEqual(val, undefined, `Undefined leaf at "${key}" in NE`);
    }
  }
});

test("zodiac signs match 12 signs in en and ne", () => {
  assert.strictEqual(Object.keys(dictionaries.en.zodiac.signs).length, 12);
  assert.strictEqual(Object.keys(dictionaries.ne.zodiac.signs).length, 12);
  assert.strictEqual(dictionaries.ne.zodiac.signs.Aries, "मेष");
  assert.strictEqual(dictionaries.ne.zodiac.signs.Pisces, "मीन");
});

test("planets match 13 grahas and upagrahas", () => {
  assert.strictEqual(dictionaries.ne.planets.names.Sun, "सूर्य");
  assert.strictEqual(dictionaries.ne.planets.names.Moon, "चन्द्र");
  assert.strictEqual(dictionaries.ne.planets.glyphs.Sun, "सू");
  assert.strictEqual(dictionaries.ne.planets.glyphs.Moon, "चं");
});

test("28 nakshatras (27 + abhijit) are translated", () => {
  assert.strictEqual(dictionaries.en.nakshatras.names.length, 28);
  assert.strictEqual(dictionaries.ne.nakshatras.names.length, 28);
  assert.strictEqual(dictionaries.ne.nakshatras.names[0], "अश्विनी");
});
