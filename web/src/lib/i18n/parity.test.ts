import test from "node:test";
import assert from "node:assert";
import { dictionaries } from "./index.ts";

test("en and ne dictionaries have identical top-level namespaces", () => {
  const enNamespaces = Object.keys(dictionaries.en).sort();
  const neNamespaces = Object.keys(dictionaries.ne).sort();
  assert.deepStrictEqual(neNamespaces, enNamespaces);
});

test("en and ne have identical keys in all nested namespaces", () => {
  const en = dictionaries.en as unknown as Record<string, Record<string, unknown>>;
  const ne = dictionaries.ne as unknown as Record<string, Record<string, unknown>>;

  for (const ns of Object.keys(en)) {
    const enKeys = Object.keys(en[ns]).sort();
    const neKeys = Object.keys(ne[ns]).sort();
    assert.deepStrictEqual(
      neKeys,
      enKeys,
      `Mismatch in keys for namespace: "${ns}". Missing in NE: ${enKeys.filter((k) => !neKeys.includes(k))}, Extra in NE: ${neKeys.filter((k) => !enKeys.includes(k))}`
    );
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
