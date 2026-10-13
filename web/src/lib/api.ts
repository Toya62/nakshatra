import {
  BirthDataInput,
  ChartData,
  PanchangaData,
  RAGAnswer,
  SearchReference,
  TransitReport,
  YogaResult,
} from "./types";

const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    if ((window as unknown as { __NAKSHATRA_API_URL__?: string }).__NAKSHATRA_API_URL__) {
      return (window as unknown as { __NAKSHATRA_API_URL__: string }).__NAKSHATRA_API_URL__!;
    }
    return "/api/py";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8004";
};

export async function checkApiHealth(customUrl?: string): Promise<{ status: string; url: string }> {
  const urlsToTry = customUrl ? [customUrl] : [
    "/api/py",
    "http://127.0.0.1:8004",
    "http://localhost:8004",
    "http://127.0.0.1:8000",
  ];

  for (const url of urlsToTry) {
    try {
      const res = await fetch(`${url}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        if (typeof window !== "undefined") {
          (window as unknown as { __NAKSHATRA_API_URL__: string }).__NAKSHATRA_API_URL__ = url;
        }
        return { status: "connected", url };
      }
    } catch {
      // try next
    }
  }
  return { status: "offline", url: getApiBaseUrl() };
}

export async function fetchChart(input: BirthDataInput): Promise<ChartData> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/chart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      year: input.year,
      month: input.month,
      day: input.day,
      hour: input.hour,
      minute: input.minute,
      second: input.second ?? 0,
      latitude: input.latitude,
      longitude: input.longitude,
      timezone: input.timezone,
      place_name: input.place_name,
      ayanamsa: input.ayanamsa || "jhora_lahiri",
      house_system: input.house_system || "WholeSign",
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to calculate birth chart");
  }

  const json = await res.json();
  return json.data;
}

export async function fetchTransits(
  natal: BirthDataInput,
  transitDate?: string
): Promise<TransitReport> {
  const baseUrl = getApiBaseUrl();
  const body: Record<string, unknown> = {
    year: natal.year,
    month: natal.month,
    day: natal.day,
    hour: natal.hour,
    minute: natal.minute,
    second: natal.second ?? 0,
    latitude: natal.latitude,
    longitude: natal.longitude,
    timezone: natal.timezone,
  };

  if (transitDate) {
    body.transit_date = transitDate;
  }

  const res = await fetch(`${baseUrl}/transits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to calculate transits");
  }

  const json = await res.json();
  return json.data;
}

export async function fetchPanchanga(
  dateStr: string,
  timeStr: string,
  latitude: number,
  longitude: number,
  timezone: string
): Promise<PanchangaData> {
  const baseUrl = getApiBaseUrl();
  const [year, month, day] = dateStr.split("-").map(Number);
  const [hour, minute] = timeStr.split(":").map(Number);

  const res = await fetch(`${baseUrl}/panchanga`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      year,
      month,
      day,
      hour,
      minute,
      second: 0,
      latitude,
      longitude,
      timezone,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to calculate panchanga");
  }

  const json = await res.json();
  return json.data;
}

export async function fetchYogas(input: BirthDataInput): Promise<YogaResult[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/yogas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to detect yogas");
  }

  const json = await res.json();
  return json.data;
}

export async function askConsultation(
  question: string,
  birth?: BirthDataInput,
  topK: number = 4
): Promise<{ answer: RAGAnswer; references: SearchReference[] }> {
  const baseUrl = getApiBaseUrl();
  const body: Record<string, unknown> = {
    question,
    top_k: topK,
    index_dir: "index",
  };

  if (birth) {
    body.birth = {
      year: birth.year,
      month: birth.month,
      day: birth.day,
      hour: birth.hour,
      minute: birth.minute,
      second: birth.second ?? 0,
      latitude: birth.latitude,
      longitude: birth.longitude,
      timezone: birth.timezone,
    };
  }

  const res = await fetch(`${baseUrl}/rag/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Consultation query failed");
  }

  const json = await res.json();
  return {
    answer: json.data,
    references: json.references || [],
  };
}

export interface StreamHandlers {
  onInit?: (data: { model: string; references: SearchReference[] }) => void;
  onToken?: (token: string) => void;
  onDone?: (data: { citations: RAGAnswer["citations"]; model: string }) => void;
  onError?: (err: string) => void;
}

export async function askConsultationStream(
  question: string,
  handlers: StreamHandlers,
  birth?: BirthDataInput,
  topK: number = 4
): Promise<void> {
  const baseUrl = getApiBaseUrl();
  const body: Record<string, unknown> = {
    question,
    top_k: topK,
    index_dir: "index",
  };

  if (birth) {
    body.birth = {
      year: birth.year,
      month: birth.month,
      day: birth.day,
      hour: birth.hour,
      minute: birth.minute,
      second: birth.second ?? 0,
      latitude: birth.latitude,
      longitude: birth.longitude,
      timezone: birth.timezone,
    };
  }

  const res = await fetch(`${baseUrl}/rag/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Streaming consultation failed");
  }

  if (!res.body) {
    throw new Error("No response body returned for stream");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const block of lines) {
      const trimmed = block.trim();
      if (!trimmed.startsWith("data: ")) continue;
      const jsonStr = trimmed.slice(6);
      try {
        const parsed = JSON.parse(jsonStr);
        if (parsed.type === "init") {
          handlers.onInit?.(parsed);
        } else if (parsed.type === "token") {
          handlers.onToken?.(parsed.token);
        } else if (parsed.type === "done") {
          handlers.onDone?.(parsed);
        } else if (parsed.type === "error") {
          handlers.onError?.(parsed.error);
        }
      } catch {
        // ignore parse errors on partial frames
      }
    }
  }
}
