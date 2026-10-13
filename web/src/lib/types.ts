export interface BirthDataInput {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  second?: number;
  latitude: number;
  longitude: number;
  timezone: string;
  place_name?: string;
  ayanamsa?: string;
  house_system?: string;
}

export interface PlanetPosition {
  name: string;
  longitude: number;
  latitude: number;
  speed: number;
  sign: string;
  degree_in_sign: number;
  nakshatra: string;
  pada: number;
  nakshatra_lord: string;
  house: number;
  retrograde: boolean;
  dignity?: string;
}

export interface AscendantData {
  longitude: number;
  sign: string;
  degree_in_sign: number;
  nakshatra: string;
  pada: number;
  nakshatra_lord: string;
}

export interface DashaPeriod {
  lord: string;
  start: string;
  end: string;
  duration_years?: number;
  subs?: DashaPeriod[];
}

export interface VimshottariData {
  birth_nakshatra: string;
  birth_nakshatra_lord: string;
  balance_lord: string;
  balance_years: number;
  current_md?: DashaPeriod;
  current_ad?: DashaPeriod;
  current_pd?: DashaPeriod;
  mahadashas: DashaPeriod[];
}

export interface AshtakavargaData {
  grand_total: number;
  bav: Record<string, Record<string, number>>;
  sav: Record<string, number>;
}

export interface ChartData {
  ascendant: AscendantData;
  planets: PlanetPosition[];
  rahu: PlanetPosition;
  ketu: PlanetPosition;
  houses: { index: number; sign: string; degree: number }[];
  vargas?: Record<string, Record<string, string>>;
  dashas?: VimshottariData;
  ashtakavarga?: AshtakavargaData;
  ayanamsa: { name: string; value: string };
  birth: BirthDataInput;
}

export interface SadeSatiInfo {
  is_active: boolean;
  phase: string;
  saturn_sign: string;
  natal_moon_sign: string;
  house_from_moon: number;
  is_ashtama_shani: boolean;
  is_kantaka_shani: boolean;
}

export interface TransitPlanet {
  name: string;
  sign: string;
  degree_in_sign: number;
  house_from_asc: number;
  house_from_moon: number;
  retrograde: boolean;
}

export interface TransitReport {
  transit_date: string;
  sade_sati: SadeSatiInfo;
  planets: TransitPlanet[];
  double_transit_houses: number[];
  jupiter_gochar_summary: string;
}

export interface PanchangaLimb {
  name: string;
  lord?: string;
  percentage_left?: number;
  pada?: number;
  paksha?: string;
  is_vishti_bhadra?: boolean;
  is_pre_sunrise?: boolean;
}

export interface PanchangaData {
  date: string;
  vara: PanchangaLimb;
  tithi: PanchangaLimb;
  nakshatra: PanchangaLimb;
  yoga: PanchangaLimb;
  karana: PanchangaLimb;
  sunrise_time?: string;
  sunset_time?: string;
  sun_longitude: number;
  moon_longitude: number;
}

export interface YogaResult {
  name: string;
  category: string;
  description: string;
  planets_involved: string[];
  houses_involved: number[];
  is_active: boolean;
}

export interface Citation {
  work: string;
  chapter: string;
  verse: string;
  text: string;
}

export interface RAGAnswer {
  question: string;
  answer: string;
  citations: Citation[];
  model: string;
}

export interface SearchReference {
  chunk_id: string;
  work: string;
  chapter: string;
  verse: string;
  score: number;
  text: string;
}
