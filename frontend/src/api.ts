import type {
  EncyclopediaAskResponse,
  Hotspot,
  IdentificationResult,
  MapLocation,
  RegionInfoResponse,
  Sighting,
  SpeciesDetail,
  SpeciesSummary,
  TripPlanRequest,
  TripPlanResponse,
} from "./types";

const API_BASE = "/api/v1";

const BACKEND_START_HINT =
  "백엔드 API(127.0.0.1:8000)에 연결할 수 없습니다. " +
  "새 터미널에서 backend 폴더로 이동한 뒤 " +
  "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 을 먼저 실행하세요.";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch {
    throw new Error(BACKEND_START_HINT);
  }
  if (!response.ok) {
    const detail = await response.text();
    if (response.status === 500 && !detail.trim()) {
      throw new Error(BACKEND_START_HINT);
    }
    throw new Error(detail || `요청 실패: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listSpecies: (q?: string) =>
    request<SpeciesSummary[]>(`/species${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  getSpecies: (id: string) => request<SpeciesDetail>(`/species/${id}`),
  identifyImage: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<IdentificationResult>("/identify/image", {
      method: "POST",
      body: form,
    });
  },
  identifyAudio: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<IdentificationResult>("/identify/audio", {
      method: "POST",
      body: form,
    });
  },
  askEncyclopedia: (question: string, speciesId?: string) =>
    request<EncyclopediaAskResponse>("/encyclopedia/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, species_id: speciesId ?? null }),
    }),
  mapLocations: (speciesId?: string) =>
    request<MapLocation[]>(
      `/locations/map${speciesId ? `?species_id=${encodeURIComponent(speciesId)}` : ""}`
    ),
  regionInfo: (region: string) =>
    request<RegionInfoResponse>(`/locations/region-info?region=${encodeURIComponent(region)}`),
  listLocations: (speciesId?: string) =>
    request<Hotspot[]>(
      `/locations${speciesId ? `?species_id=${encodeURIComponent(speciesId)}` : ""}`
    ),
  planTrip: (payload: TripPlanRequest) =>
    request<TripPlanResponse>("/trips/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  listSightings: () => request<Sighting[]>("/sightings"),
  createSighting: (payload: {
    species_id: string;
    location_name?: string;
    confidence?: number;
    media_type?: string;
    note?: string;
  }) =>
    request<Sighting>("/sightings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
