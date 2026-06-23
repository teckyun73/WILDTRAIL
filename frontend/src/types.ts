export interface SpeciesSummary {
  id: string;
  common_name: string;
  scientific_name: string;
  category: string;
  protection_grade: string | null;
  best_months: string;
  image_url: string | null;
}

export interface SpeciesDetail extends SpeciesSummary {
  habitat: string;
  diet: string;
  breeding_season: string;
  active_time: string;
  observation_tips: string;
  similar_species: string;
  description: string;
}

export interface IdentificationCandidate {
  species_id: string;
  common_name: string;
  scientific_name: string;
  confidence: number;
}

export interface IdentificationResult {
  media_type: string;
  candidates: IdentificationCandidate[];
  message: string;
  source: "model" | "stub";
}

export interface Hotspot {
  id: number;
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  species_id: string;
  species_name: string;
  best_months: string;
  observation_score: number;
  access_level: string;
  transport_note: string;
  entry_fee: number;
  facilities: string;
  safety_note: string;
}

export interface TripPlanRequest {
  species_id: string;
  origin: string;
  days: number;
  budget_krw: number;
  travelers: number;
  month?: number;
  preferences: {
    transport: string;
    accommodation: string;
    difficulty: string;
  };
}

export interface CostBreakdown {
  transport: number;
  accommodation: number;
  food: number;
  entry_fee: number;
  misc: number;
  total: number;
  per_person: number;
}

export interface TripDayItem {
  time: string;
  activity: string;
  location: string;
  note: string;
}

export interface TripDayPlan {
  day: number;
  title: string;
  items: TripDayItem[];
}

export interface AccommodationOption {
  name: string;
  type: string;
  region: string;
  address: string;
  price_per_night_krw: number;
  distance_km: number | null;
  rating: number | null;
  booking_url: string;
  source: string;
  note: string;
}

export interface TripPlanResponse {
  species_id: string;
  species_name: string;
  origin: string;
  days: number;
  travelers: number;
  hotspot_name: string;
  region: string;
  summary: string;
  checklist: string[];
  accommodation_options: AccommodationOption[];
  days_plan: TripDayPlan[];
  costs: CostBreakdown;
  disclaimer: string;
  source: string;
}

export interface EncyclopediaAskResponse {
  question: string;
  species_id: string | null;
  answer: string;
  citations: {
    chunk_id: string;
    title: string;
    source: string;
    species_id: string | null;
  }[];
  source: string;
}

export interface MapLocation {
  id: number;
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  species_id: string;
  species_name: string;
  observation_score: number;
  entry_fee: number;
  transport_note: string;
}

export interface RegionInfoResponse {
  region: string;
  weather: Record<string, unknown>;
  transport: Record<string, unknown>;
  tourism: Record<string, unknown>;
}

export interface Sighting {
  id: number;
  species_id: string;
  common_name: string;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
  confidence: number;
  media_type: string;
  note: string;
  created_at: string;
}
