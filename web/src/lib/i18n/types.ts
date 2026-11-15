export type Language = "en" | "ne";

export interface TranslationSchema {
  common: {
    appName: string;
    tagline: string;
    loading: string;
    error: string;
    success: string;
    save: string;
    copy: string;
    copied: string;
    calculate: string;
    calculating: string;
    reset: string;
    close: string;
    details: string;
    degrees: string;
    house: string;
    sign: string;
    lord: string;
    status: string;
    verdict: string;
    recommendation: string;
    connected: string;
    offline: string;
    connecting: string;
  };
  nav: {
    core_engine: string;
    planetary_analysis: string;
    jaimini_special: string;
    temporal_transits: string;
    remedies_ai: string;
    chart: string;
    table: string;
    panchanga: string;
    dasha: string;
    ashtakavarga: string;
    transits: string;
    rashi_fal: string;
    yogas: string;
    timeline: string;
    compatibility: string;
    muhurtha: string;
    remedies: string;
    varshaphal: string;
    kalsarp: string;
    special_lagnas: string;
    chakra: string;
    consult: string;
  };
  birthForm: {
    title: string;
    subtitle: string;
    dob: string;
    tob: string;
    place: string;
    latitude: string;
    longitude: string;
    timezone: string;
    ayanamsa: string;
    houseSystem: string;
    gender: string;
    male: string;
    female: string;
    other: string;
    calculateBtn: string;
    useCurrentTime: string;
    bikramSambatToggle: string;
    bsDateLabel: string;
    adDateLabel: string;
    placeSearchPlaceholder: string;
    recentPlaces: string;
    validationError: string;
  };
  zodiac: {
    signs: Record<
      | "Aries"
      | "Taurus"
      | "Gemini"
      | "Cancer"
      | "Leo"
      | "Virgo"
      | "Libra"
      | "Scorpio"
      | "Sagittarius"
      | "Capricorn"
      | "Aquarius"
      | "Pisces",
      string
    >;
    elements: {
      fire: string;
      earth: string;
      air: string;
      water: string;
    };
    modalities: {
      movable: string;
      fixed: string;
      dual: string;
    };
  };
  planets: {
    names: Record<
      | "Sun"
      | "Moon"
      | "Mars"
      | "Mercury"
      | "Jupiter"
      | "Venus"
      | "Saturn"
      | "Rahu"
      | "Ketu"
      | "Ascendant"
      | "Uranus"
      | "Neptune"
      | "Pluto",
      string
    >;
    glyphs: Record<
      | "Sun"
      | "Moon"
      | "Mars"
      | "Mercury"
      | "Jupiter"
      | "Venus"
      | "Saturn"
      | "Rahu"
      | "Ketu"
      | "Ascendant",
      string
    >;
    dignities: {
      exalted: string;
      debilitated: string;
      own: string;
      moolatrikona: string;
      friendly: string;
      neutral: string;
      enemy: string;
    };
    motion: {
      direct: string;
      retrograde: string;
      combust: string;
    };
  };
  bhavas: {
    houses: Record<number, { name: string; title: string; significations: string }>;
    classifications: {
      kendra: string;
      trikona: string;
      upachaya: string;
      dusthana: string;
      maraka: string;
    };
  };
  nakshatras: {
    names: string[];
    pada: string;
    lord: string;
  };
  panchanga: {
    title: string;
    subtitle: string;
    tithi: string;
    vara: string;
    nakshatra: string;
    yoga: string;
    karana: string;
    sunrise: string;
    sunset: string;
    sunSign: string;
    moonSign: string;
    rahuKaal: string;
    yamaghanta: string;
    gulika: string;
    paksha: {
      shukla: string;
      krishna: string;
    };
  };
  dasha: {
    title: string;
    subtitle: string;
    mahadasha: string;
    antardasha: string;
    pratyantardasha: string;
    startDate: string;
    endDate: string;
    duration: string;
    balanceAtBirth: string;
    currentDasha: string;
  };
  ashtakavarga: {
    title: string;
    subtitle: string;
    sarvashtakavarga: string;
    bhinnashtakavarga: string;
    bindus: string;
    total: string;
    strengthHigh: string;
    strengthMedium: string;
    strengthLow: string;
  };
  varshaphal: {
    title: string;
    subtitle: string;
    varsheshwara: string;
    muntha: string;
    munthaLord: string;
    targetYear: string;
    completedYears: string;
    solarReturn: string;
    sahams: string;
    monthLords: string;
    annualReading: string;
    chartSnapshot: string;
  };
  kalsarp: {
    title: string;
    subtitle: string;
    axisArc: string;
    planetsWithinAxis: string;
    classification: string;
    fullKalsarp: string;
    partialKalsarp: string;
    noKalsarp: string;
    grahaStatus: string;
    types: Record<string, string>;
  };
  specialLagnas: {
    title: string;
    subtitle: string;
    lagnasCount: string;
    calculationNotes: string;
    mastersReading: string;
    names: Record<string, string>;
  };
  chakras: {
    title: string;
    subtitle: string;
    goodTara: string;
    badTara: string;
    navataraTitle: string;
    compoundTitle: string;
    ghatchakraTitle: string;
    janmaNakshatra: string;
    taraNature: {
      good: string;
      bad: string;
    };
  };
  rashiFal: {
    title: string;
    subtitle: string;
    chandraLagna: string;
    period: string;
    referenceDate: string;
    periods: {
      daily: string;
      weekly: string;
      monthly: string;
      yearly: string;
    };
    overallVerdict: string;
    sadeSati: string;
    doubleTransit: string;
    supportiveTransits: string;
    watchfulTransits: string;
    mastersSynthesis: string;
    grahaResults: string;
  };
  muhurtha: {
    title: string;
    subtitle: string;
    selectActivity: string;
    auspiciousTimings: string;
    ratings: {
      auspicious: string;
      moderate: string;
      inauspicious: string;
    };
  };
  compatibility: {
    title: string;
    subtitle: string;
    groom: string;
    bride: string;
    totalScore: string;
    ashtakootaMilan: string;
    manglikCheck: string;
    verdictTitle: string;
    kootas: Record<
      "varna" | "vashya" | "tara" | "yoni" | "graha_maitri" | "gana" | "bhakoot" | "nadi",
      string
    >;
  };
  remedies: {
    title: string;
    subtitle: string;
    gemstone: string;
    mantra: string;
    donation: string;
    yantra: string;
    rudraksha: string;
    fasting: string;
  };
  consultation: {
    title: string;
    subtitle: string;
    inputPlaceholder: string;
    sendBtn: string;
    stopBtn: string;
    thinking: string;
    sampleQueriesTitle: string;
    disclaimer: string;
    clearChat: string;
    exportChat: string;
    samples: string[];
  };
}
