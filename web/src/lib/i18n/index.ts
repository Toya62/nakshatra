import { en } from "./dictionaries/en.ts";
import { ne } from "./dictionaries/ne.ts";
import type { Language, TranslationSchema } from "./types.ts";

export * from "./types.ts";
export * from "./formatters.ts";

export const dictionaries: Record<Language, TranslationSchema> = {
  en,
  ne,
};

export function getTranslation(lang: Language): TranslationSchema {
  return dictionaries[lang] || dictionaries.en;
}
