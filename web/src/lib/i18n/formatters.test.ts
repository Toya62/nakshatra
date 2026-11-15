import test from "node:test";
import assert from "node:assert";
import { toDevanagariDigits, formatNumber, formatDegree } from "./formatters.ts";

test("converts arabic digits to devanagari", () => {
  assert.strictEqual(toDevanagariDigits("2026"), "२०२६");
  assert.strictEqual(toDevanagariDigits(1997), "१९९७");
  assert.strictEqual(toDevanagariDigits("0123456789"), "०१२३४५६७८९");
});

test("formats numbers by language", () => {
  assert.strictEqual(formatNumber(12.5, "ne"), "१२.५");
  assert.strictEqual(formatNumber(12.5, "en"), "12.5");
  assert.strictEqual(formatNumber(0, "ne"), "०");
  assert.strictEqual(formatNumber(100, "ne"), "१००");
});

test("formats degrees by language", () => {
  assert.strictEqual(formatDegree(24.385, "ne", 2), "२४.३९°");
  assert.strictEqual(formatDegree(24.385, "en", 2), "24.39°");
  assert.strictEqual(formatDegree(0, "ne", 1), "०.०°");
});
