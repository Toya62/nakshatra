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

export function getBirthKey(b?: BirthDataInput | null): string {
  if (!b) return "no-chart";
  return `${b.year}-${b.month}-${b.day}_${b.hour}:${b.minute}:${b.second ?? 0}_${Number(b.latitude).toFixed(4)},${Number(b.longitude).toFixed(4)}_${b.timezone || ""}_${b.ayanamsa || "jhora_lahiri"}_${b.house_system || "WholeSign"}`;
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

export interface VedicAspect {
  planet: string;
  source_house: number;
  target_house: number;
  aspect_type: string;
  target_sign?: string;
  aspected_planets?: string[];
  strength?: number;
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
  vedic_aspects?: VedicAspect[];
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

export interface KutaScore {
  name: string;
  max_score: number;
  obtained_score: number;
  bride_val: string;
  groom_val: string;
  is_favorable: boolean;
  dosha_present: boolean;
  cancelled: boolean;
  notes: string;
}

export interface AshtakootaReport {
  varna: KutaScore;
  vashya: KutaScore;
  tara: KutaScore;
  yoni: KutaScore;
  graha_maitri: KutaScore;
  gana: KutaScore;
  bhakoot: KutaScore;
  nadi: KutaScore;
  total_score: number;
  percentage: number;
  verdict: "Uttama" | "Madhyama" | "Adhama";
  summary: string;
}

export interface ExtendedKutasReport {
  mahendra: KutaScore;
  stree_deergha: KutaScore;
  rajju: KutaScore;
  vedha: KutaScore;
}

export interface KujaDoshaDetails {
  is_manglik: boolean;
  severity: "None" | "Low" | "Moderate" | "High";
  score: number;
  afflicted_houses_lagna: number[];
  afflicted_houses_moon: number[];
  afflicted_houses_venus: number[];
  cancellations: string[];
  is_cancelled: boolean;
}

export interface KujaDoshaReport {
  bride: KujaDoshaDetails;
  groom: KujaDoshaDetails;
  is_compatible: boolean;
  verdict: string;
  notes: string;
}

export interface CompatibilityReport {
  bride_name?: string;
  groom_name?: string;
  bride_moon_sign: string;
  bride_nakshatra: string;
  bride_pada: number;
  groom_moon_sign: string;
  groom_nakshatra: string;
  groom_pada: number;
  ashtakoota: AshtakootaReport;
  extended_kutas: ExtendedKutasReport;
  kuja_dosha: KujaDoshaReport;
  overall_score: number;
  recommendation: string;
}

export interface TimeInterval {
  name: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
  nature: "Auspicious" | "Inauspicious" | "Neutral";
  score: number;
  notes: string;
}

export interface HoraItem {
  hora_index: number;
  period_type: "Day" | "Night";
  ruling_planet: string;
  start_time: string;
  end_time: string;
  is_current: boolean;
  nature: string;
  recommended_activities: string;
}

export interface ChoghadiyaItem {
  index: number;
  name: string;
  period_type: "Day" | "Night";
  ruler: string;
  nature: string;
  score: number;
  start_time: string;
  end_time: string;
  is_current: boolean;
}

export interface SpecialYogaStatus {
  sarvartha_siddhi: boolean;
  amrita_siddhi: boolean;
  guru_pushya: boolean;
  ravi_pushya: boolean;
  tripushkar: boolean;
  vishti_bhadra_active: boolean;
  active_yogas: string[];
}

export interface MuhurthaSuitability {
  business_contract: boolean;
  financial_investment: boolean;
  travel: boolean;
  marriage: boolean;
  property_purchase: boolean;
  medical_treatment: boolean;
}

export interface MuhurthaReport {
  timestamp: string;
  timezone: string;
  latitude: number;
  longitude: number;
  sunrise_time: string;
  sunset_time: string;
  next_sunrise_time: string;
  panchanga: PanchangaData;
  current_hora: HoraItem;
  current_choghadiya: ChoghadiyaItem;
  special_yogas: SpecialYogaStatus;
  abhijit_muhurtha: TimeInterval;
  brahma_muhurtha: TimeInterval;
  rahu_kalam: TimeInterval;
  yamaganda: TimeInterval;
  gulika_kalam: TimeInterval;
  durmuhurtha: TimeInterval[];
  day_horas: HoraItem[];
  night_horas: HoraItem[];
  day_choghadiyas: ChoghadiyaItem[];
  night_choghadiyas: ChoghadiyaItem[];
  muhurtha_score: number;
  verdict: string;
  suitability: MuhurthaSuitability;
  recommendation: string;
}

export interface PlaceResult {
  name: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  timezone: string;
  elevation_m?: number;
}

export interface TimezoneOffsetInfo {
  timezone: string;
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  utc_offset_seconds: number;
  utc_offset_str: string;
  is_dst: boolean;
  tz_abbreviation: string;
}

export interface BikramSambatDate {
  year: number;
  month: number;
  month_name_en: string;
  month_name_ne: string;
  day: number;
  formatted: string;
  formatted_ne: string;
}

export interface GregorianDate {
  year: number;
  month: number;
  day: number;
  formatted: string;
}

export interface DevanagariNomenclature {
  planets: Record<string, string>;
  signs: Record<string, string>;
  nakshatras: string[];
}

export interface DomainPrediction {
  domain: "career" | "relationship" | "wealth" | "spiritual_dharma" | "health";
  promise_tier: "Exceptional" | "Favorable" | "Mixed" | "Challenging" | "Obstructed";
  primary_houses: number[];
  primary_lords: string[];
  karakas: string[];
  promise_summary: string;
  varga_confirmation: string;
  dasha_timing: string;
  active_transits: string[];
  active_yogas: string[];
  classical_citations: string[];
  remedies: string[];
  key_verdict: string;
  score: number;
}

export interface ParashariRemedy {
  deity: string;
  beej_mantra: string;
  mantra_count: string;
  gemstone: string;
  substitute_gem: string;
  metal: string;
  gem_finger: string;
  gem_caution: string;
  charity_items: string[];
  charity_day: string;
  fasting_day: string;
  spiritual_practice: string;
}

export interface LalKitabUpaya {
  household_remedy: string;
  symbolic_action: string;
  forbidden_actions: string[];
  creature_service: string;
  duration_days: number;
}

export interface PlanetRemedy {
  planet: string;
  house: number;
  sign: string;
  dignity: string;
  affliction_reasons: string[];
  severity: "High" | "Moderate" | "Mild";
  parashari: ParashariRemedy;
  lal_kitab: LalKitabUpaya;
}

export interface RemediesReport {
  natal_lagna: string;
  natal_moon: string;
  active_dasha: string;
  sade_sati_status: string;
  total_afflictions: number;
  afflicted_planets: PlanetRemedy[];
  general_guidelines: string[];
  lal_kitab_precautions: string[];
}

export interface SahamInfo {
  name: string;
  meaning: string;
  longitude: number;
  sign: string;
  degree_in_sign: number;
  house: number;
  formula: string;
}

export interface MonthPrediction {
  month: number;
  month_name: string;
  lord: string;
  theme: string;
  weekday: string;
}

export interface MunthaInfo {
  completed_years: number;
  sign: string;
  degree_in_sign: number;
  longitude: number;
  house: number;
  lord: string;
}

export interface VarsheshwaraInfo {
  planet: string;
  rationale: string;
  score: number;
  dignity: string;
  house: number;
  sign: string;
}

export interface VarshaphalChartSnapshot {
  ascendant: string;
  asc_degree: number;
  planets: {
    name: string;
    sign: string;
    degree: number;
    house: number;
    retrograde: boolean;
    dignity: string | null;
  }[];
  houses: {
    house: number;
    sign: string;
    degree: number;
  }[];
}

export interface VarshaphalReport {
  success: boolean;
  birth_year: number;
  target_year: number;
  completed_years: number;
  solar_return_local: string;
  solar_return_utc: string;
  muntha: MunthaInfo;
  varsheshwara: VarsheshwaraInfo;
  sahams: SahamInfo[];
  month_lords: MonthPrediction[];
  varshaphal_chart: VarshaphalChartSnapshot;
  summary: string;
}

export interface VarshaphalInput {
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
  target_year?: number;
  ayanamsa?: string;
  house_system?: string;
}

export interface KalsarpPlanetStatus {
  name: string;
  sign: string;
  house: number;
  degree_in_sign: number;
  longitude: number;
  within_axis: boolean;
}

export interface KalsarpReport {
  success: boolean;
  has_kalsarp: boolean;
  classification: string;
  rahu_house: number;
  ketu_house: number;
  kalsarp_type: string | null;
  kalsarp_type_description: string | null;
  rahu_sign: string | null;
  ketu_sign: string | null;
  axis_arc_degrees: number | null;
  planets_within_axis: number;
  total_classical_planets: number;
  planet_status: KalsarpPlanetStatus[];
  summary: string;
}

export interface SpecialLagna {
  name: string;
  sign: string;
  house: number;
  degree_in_sign: number;
  longitude: number;
  lord: string;
  rationale: string;
}

export interface SpecialLagnasReport {
  success: boolean;
  lagnas: SpecialLagna[];
  notes: string[];
}

export interface KalsarpInput {
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

export interface SpecialLagnasInput {
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

export interface NavataraEntry {
  planet: string;
  nakshatra: string;
  nakshatra_index: number;
  count_from_janma: number;
  tara: string;
  nature: string;
}

export interface CompoundPair {
  planet_a: string;
  planet_b: string;
  natural: string;
  temporary: string;
  compound: string;
}

export interface GhatiHouse {
  house: number;
  ruler: string;
  sign: string;
}

export interface ChakraReport {
  success: boolean;
  navatara: NavataraEntry[];
  compound_relationships: CompoundPair[];
  ghatchakra: GhatiHouse[];
  janma_nakshatra: string;
  janma_tara_lord_planet: string | null;
  summary: string;
}

export interface ChakraInput {
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

export interface GrahaResult {
  planet: string;
  sign: string;
  house_from_moon: number;
  degree_in_sign: number;
  retrograde: boolean;
  favourable: boolean;
  verdict: string;
}

export interface RashiFalReport {
  success: boolean;
  period: string;
  period_label: string;
  reference_date: string;
  moon_sign: string;
  moon_nakshatra: string | null;
  moon_house_from_self: number;
  overall_verdict: string;
  overall_score: number;
  graha_results: GrahaResult[];
  double_transit_houses: number[];
  sade_sati_active: boolean;
  sade_sati_phase: string | null;
  master_synthesis: string;
}

export interface RashiFalInput {
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
  period?: string;
  reference_date?: string;
  ayanamsa?: string;
  house_system?: string;
}

