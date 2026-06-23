import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import HotspotMap from "./components/HotspotMap";
import type {
  EncyclopediaAskResponse,
  Hotspot,
  IdentificationResult,
  MapLocation,
  RegionInfoResponse,
  Sighting,
  SpeciesDetail,
  SpeciesSummary,
  TripPlanResponse,
} from "./types";

type Tab = "identify" | "encyclopedia" | "locations" | "trip" | "records";

const TABS: { id: Tab; label: string }[] = [
  { id: "identify", label: "식별" },
  { id: "encyclopedia", label: "도감" },
  { id: "locations", label: "관찰지" },
  { id: "trip", label: "여행" },
  { id: "records", label: "기록" },
];

function formatKrw(value: number) {
  return `${value.toLocaleString("ko-KR")}원`;
}

const ACCOMMODATION_LABELS: Record<string, string> = {
  guesthouse: "게스트하우스",
  hotel: "호텔",
  pension: "펜션",
};

function accommodationSourceLabel(source: string) {
  if (source === "stub") return "샘플 데이터";
  if (source === "stub+llm") return "샘플+AI 설명 보강";
  return source;
}

function confidenceColor(confidence: number) {
  if (confidence >= 0.8) return "text-green-700";
  if (confidence >= 0.6) return "text-amber-700";
  return "text-red-700";
}

function identifySourceBadge(source: IdentificationResult["source"]) {
  if (source === "model") {
    return {
      label: "AI 모델",
      className: "bg-forest-700 text-white",
    };
  }
  return {
    label: "데모 모드",
    className: "bg-amber-100 text-amber-900",
  };
}

export default function App() {
  const [tab, setTab] = useState<Tab>("identify");
  const [speciesList, setSpeciesList] = useState<SpeciesSummary[]>([]);
  const [selectedSpeciesId, setSelectedSpeciesId] = useState<string>("pica_pica");
  const [speciesDetail, setSpeciesDetail] = useState<SpeciesDetail | null>(null);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [identifyResult, setIdentifyResult] = useState<IdentificationResult | null>(null);
  const [tripPlan, setTripPlan] = useState<TripPlanResponse | null>(null);
  const [sightings, setSightings] = useState<Sighting[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [identifyMode, setIdentifyMode] = useState<"image" | "audio">("image");
  const [mapLocations, setMapLocations] = useState<MapLocation[]>([]);
  const [regionInfo, setRegionInfo] = useState<RegionInfoResponse | null>(null);
  const [ragQuestion, setRagQuestion] = useState("");
  const [ragAnswer, setRagAnswer] = useState<EncyclopediaAskResponse | null>(null);

  const [tripForm, setTripForm] = useState({
    origin: "서울역",
    days: 1,
    budget_krw: 150000,
    travelers: 1,
    accommodation: "guesthouse",
  });

  const filteredSpecies = useMemo(() => {
    if (!search.trim()) return speciesList;
    const q = search.toLowerCase();
    return speciesList.filter(
      (s) =>
        s.common_name.toLowerCase().includes(q) ||
        s.scientific_name.toLowerCase().includes(q)
    );
  }, [speciesList, search]);

  useEffect(() => {
    api.listSpecies().then(setSpeciesList).catch((e) => setError(String(e)));
    api.listSightings().then(setSightings).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!selectedSpeciesId) return;
    api.getSpecies(selectedSpeciesId).then(setSpeciesDetail).catch((e) => setError(String(e)));
    api.listLocations(selectedSpeciesId).then(setHotspots).catch((e) => setError(String(e)));
    api.mapLocations(selectedSpeciesId).then(setMapLocations).catch((e) => setError(String(e)));
  }, [selectedSpeciesId]);

  async function handleImageUpload(file: File) {
    setLoading(true);
    setError("");
    setPreviewUrl(URL.createObjectURL(file));
    try {
      const result = await api.identifyImage(file);
      setIdentifyResult(result);
      if (result.candidates[0]) {
        setSelectedSpeciesId(result.candidates[0].species_id);
        await api.createSighting({
          species_id: result.candidates[0].species_id,
          confidence: result.candidates[0].confidence,
          media_type: "image",
          note: "이미지 식별 기록",
        });
        const records = await api.listSightings();
        setSightings(records);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleAudioUpload(file: File) {
    setLoading(true);
    setError("");
    setPreviewUrl(null);
    try {
      const result = await api.identifyAudio(file);
      setIdentifyResult(result);
      if (result.candidates[0]) {
        setSelectedSpeciesId(result.candidates[0].species_id);
        await api.createSighting({
          species_id: result.candidates[0].species_id,
          confidence: result.candidates[0].confidence,
          media_type: "audio",
          note: `소리 식별: ${file.name}`,
        });
        const records = await api.listSightings();
        setSightings(records);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleAskEncyclopedia() {
    if (!ragQuestion.trim()) return;
    setLoading(true);
    setError("");
    try {
      const answer = await api.askEncyclopedia(ragQuestion, selectedSpeciesId);
      setRagAnswer(answer);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function loadRegionInfo(region: string) {
    try {
      const info = await api.regionInfo(region);
      setRegionInfo(info);
    } catch (e) {
      setError(String(e));
    }
  }

  async function handlePlanTrip() {
    setLoading(true);
    setError("");
    try {
      const plan = await api.planTrip({
        species_id: selectedSpeciesId,
        origin: tripForm.origin,
        days: tripForm.days,
        budget_krw: tripForm.budget_krw,
        travelers: tripForm.travelers,
        preferences: {
          transport: "public",
          accommodation: tripForm.accommodation,
          difficulty: "easy",
        },
      });
      setTripPlan(plan);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="bg-forest-700 text-white">
        <div className="mx-auto max-w-6xl px-4 py-8">
          <p className="text-sm uppercase tracking-[0.2em] text-forest-100">WildTrail</p>
          <h1 className="mt-2 font-display text-4xl">야생동물 관찰 도감 & 여행 플래너</h1>
          <p className="mt-3 max-w-2xl text-forest-100">
            사진으로 동물을 식별하고, 도감 정보와 관찰 핫스팟, 맞춤 여행 일정까지 한 번에
            확인하세요.
          </p>
        </div>
      </header>

      <nav className="sticky top-0 z-10 border-b border-forest-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl gap-2 overflow-x-auto px-4 py-3">
          {TABS.map((item) => (
            <button
              key={item.id}
              onClick={() => setTab(item.id)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                tab === item.id
                  ? "bg-forest-700 text-white"
                  : "bg-forest-50 text-forest-700 hover:bg-forest-100"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}

        {tab === "identify" && (
          <section className="grid gap-8 lg:grid-cols-2">
            <div className="rounded-3xl border border-forest-100 bg-white p-6 shadow-sm">
              <div className="flex gap-2">
                {(["image", "audio"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setIdentifyMode(mode)}
                    className={`rounded-full px-4 py-2 text-sm ${
                      identifyMode === mode
                        ? "bg-forest-700 text-white"
                        : "bg-forest-50 text-forest-700"
                    }`}
                  >
                    {mode === "image" ? "사진" : "소리"}
                  </button>
                ))}
              </div>
              <h2 className="mt-4 text-2xl font-semibold">
                {identifyMode === "image" ? "사진으로 식별" : "소리로 식별"}
              </h2>
              <p className="mt-2 text-sm text-forest-700/80">
                {identifyMode === "image"
                  ? "카메라로 촬영하거나 갤러리에서 이미지를 선택하세요."
                  : "1초 이상 녹음 파일(WAV, MP3)을 업로드하세요."}
              </p>
              <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-forest-500/30 bg-forest-50 px-6 py-16 text-center hover:bg-forest-100/60">
                <span className="text-lg font-medium">
                  {identifyMode === "image" ? "이미지 업로드" : "오디오 업로드"}
                </span>
                <span className="mt-2 text-sm text-forest-700/70">
                  {identifyMode === "image" ? "JPG, PNG 지원" : "WAV, MP3 지원"}
                </span>
                <input
                  type="file"
                  accept={identifyMode === "image" ? "image/*" : "audio/*"}
                  capture={identifyMode === "image" ? "environment" : undefined}
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    if (identifyMode === "image") handleImageUpload(file);
                    else handleAudioUpload(file);
                  }}
                />
              </label>
              {previewUrl && identifyMode === "image" && (
                <img
                  src={previewUrl}
                  alt="업로드 미리보기"
                  className="mt-4 max-h-64 w-full rounded-2xl object-cover"
                />
              )}
            </div>

            <div className="rounded-3xl border border-forest-100 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-semibold">식별 결과</h2>
              {loading && <p className="mt-4 text-forest-700">분석 중...</p>}
              {!loading && !identifyResult && (
                <p className="mt-4 text-forest-700/70">아직 식별 결과가 없습니다.</p>
              )}
              {identifyResult && (
                <div className="mt-4 space-y-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${
                        identifySourceBadge(identifyResult.source).className
                      }`}
                    >
                      {identifySourceBadge(identifyResult.source).label}
                    </span>
                    <span className="text-xs text-forest-700/60">
                      {identifyResult.media_type === "image" ? "이미지" : "오디오"} 식별
                    </span>
                  </div>
                  <p className="text-sm text-forest-700/80">{identifyResult.message}</p>
                  {identifyResult.candidates.map((item) => (
                    <button
                      key={item.species_id}
                      onClick={() => {
                        setSelectedSpeciesId(item.species_id);
                        setTab("encyclopedia");
                      }}
                      className="flex w-full items-center justify-between rounded-2xl border border-forest-100 px-4 py-3 text-left hover:bg-forest-50"
                    >
                      <div>
                        <p className="font-semibold">{item.common_name}</p>
                        <p className="text-sm italic text-forest-700/70">{item.scientific_name}</p>
                      </div>
                      <span className={`font-semibold ${confidenceColor(item.confidence)}`}>
                        {(item.confidence * 100).toFixed(1)}%
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {tab === "encyclopedia" && (
          <section className="grid gap-8 lg:grid-cols-[280px_1fr]">
            <aside className="rounded-3xl border border-forest-100 bg-white p-4 shadow-sm">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="종 이름 검색"
                className="w-full rounded-xl border border-forest-100 px-3 py-2"
              />
              <div className="mt-4 max-h-[520px] space-y-2 overflow-y-auto">
                {filteredSpecies.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSelectedSpeciesId(item.id)}
                    className={`w-full rounded-xl px-3 py-2 text-left ${
                      selectedSpeciesId === item.id
                        ? "bg-forest-700 text-white"
                        : "hover:bg-forest-50"
                    }`}
                  >
                    <p className="font-medium">{item.common_name}</p>
                    <p className="text-xs italic opacity-80">{item.scientific_name}</p>
                  </button>
                ))}
              </div>
            </aside>

            <article className="rounded-3xl border border-forest-100 bg-white p-6 shadow-sm">
              {speciesDetail ? (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h2 className="font-display text-4xl">{speciesDetail.common_name}</h2>
                      <p className="mt-1 italic text-forest-700/80">{speciesDetail.scientific_name}</p>
                    </div>
                    {speciesDetail.protection_grade && (
                      <span className="rounded-full bg-amber-100 px-3 py-1 text-sm text-amber-800">
                        {speciesDetail.protection_grade}
                      </span>
                    )}
                  </div>
                  <p className="mt-4 text-lg">{speciesDetail.description}</p>
                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {[
                      ["서식지", speciesDetail.habitat],
                      ["먹이", speciesDetail.diet],
                      ["번식기", speciesDetail.breeding_season],
                      ["활동 시간", speciesDetail.active_time],
                      ["관찰 적기", speciesDetail.best_months],
                      ["유사 종", speciesDetail.similar_species],
                    ].map(([label, value]) => (
                      <div key={label} className="rounded-2xl bg-forest-50 p-4">
                        <p className="text-sm font-semibold text-forest-700">{label}</p>
                        <p className="mt-1">{value}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 rounded-2xl border border-forest-100 bg-sand p-4">
                    <p className="text-sm font-semibold text-forest-700">관찰 팁</p>
                    <p className="mt-1">{speciesDetail.observation_tips}</p>
                  </div>

                  <div className="mt-6 rounded-2xl border border-forest-100 bg-white p-4">
                    <h3 className="font-semibold">도감 AI 질문 (RAG)</h3>
                    <p className="mt-1 text-sm text-forest-700/70">
                      선택한 종에 대해 자연어로 질문하세요.
                    </p>
                    <div className="mt-3 flex gap-2">
                      <input
                        value={ragQuestion}
                        onChange={(e) => setRagQuestion(e.target.value)}
                        placeholder="예: 어디서 보면 좋나요? 울음소리 특징은?"
                        className="flex-1 rounded-xl border border-forest-100 px-3 py-2"
                      />
                      <button
                        onClick={handleAskEncyclopedia}
                        disabled={loading}
                        className="rounded-xl bg-forest-700 px-4 py-2 text-white disabled:opacity-60"
                      >
                        질문
                      </button>
                    </div>
                    {ragAnswer && (
                      <div className="mt-4 rounded-xl bg-forest-50 p-4 text-sm">
                        <p className="whitespace-pre-wrap">{ragAnswer.answer}</p>
                        <p className="mt-2 text-xs text-forest-700/60">
                          출처: {ragAnswer.source} · 인용 {ragAnswer.citations.length}건
                        </p>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <p>도감 정보를 불러오는 중...</p>
              )}
            </article>
          </section>
        )}

        {tab === "locations" && (
          <section>
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold">관찰 가능 위치</h2>
                <p className="text-sm text-forest-700/80">
                  선택 종: {speciesDetail?.common_name ?? selectedSpeciesId}
                </p>
              </div>
              <select
                value={selectedSpeciesId}
                onChange={(e) => setSelectedSpeciesId(e.target.value)}
                className="rounded-xl border border-forest-100 px-3 py-2"
              >
                {speciesList.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.common_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="mb-8">
              <HotspotMap locations={mapLocations} />
            </div>

            {hotspots[0] && (
              <div className="mb-6">
                <button
                  onClick={() => loadRegionInfo(hotspots[0].region)}
                  className="rounded-full bg-forest-100 px-4 py-2 text-sm text-forest-700"
                >
                  {hotspots[0].region} 지역 정보 (날씨·교통·관광 스텁)
                </button>
                {regionInfo && (
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <div className="rounded-2xl bg-white p-4 text-sm shadow-sm">
                      <p className="font-semibold">날씨</p>
                      <p>{String(regionInfo.weather.summary ?? "")}</p>
                    </div>
                    <div className="rounded-2xl bg-white p-4 text-sm shadow-sm">
                      <p className="font-semibold">교통</p>
                      <p>{String(regionInfo.transport.note ?? "")}</p>
                    </div>
                    <div className="rounded-2xl bg-white p-4 text-sm shadow-sm">
                      <p className="font-semibold">관광</p>
                      <p>{String(regionInfo.tourism.note ?? "")}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-2">
              {hotspots.map((spot) => (
                <div key={spot.id} className="rounded-3xl border border-forest-100 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-semibold">{spot.name}</h3>
                      <p className="text-sm text-forest-700/70">{spot.region}</p>
                    </div>
                    <span className="rounded-full bg-forest-100 px-3 py-1 text-sm">
                      점수 {(spot.observation_score * 100).toFixed(0)}
                    </span>
                  </div>
                  <div className="mt-4 space-y-2 text-sm">
                    <p>좌표: {spot.latitude.toFixed(3)}, {spot.longitude.toFixed(3)}</p>
                    <p>교통: {spot.transport_note}</p>
                    <p>입장료: {spot.entry_fee ? formatKrw(spot.entry_fee) : "무료"}</p>
                    <p>시설: {spot.facilities}</p>
                    <p className="text-amber-800">주의: {spot.safety_note}</p>
                  </div>
                  <a
                    href={`https://map.kakao.com/link/map/${spot.name},${spot.latitude},${spot.longitude}`}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-4 inline-block rounded-full bg-forest-700 px-4 py-2 text-sm text-white"
                  >
                    카카오맵에서 보기
                  </a>
                </div>
              ))}
              {hotspots.length === 0 && (
                <p className="text-forest-700/70">해당 종에 연결된 핫스팟이 없습니다.</p>
              )}
            </div>
          </section>
        )}

        {tab === "trip" && (
          <section className="grid gap-8 lg:grid-cols-[320px_1fr]">
            <form
              className="rounded-3xl border border-forest-100 bg-white p-6 shadow-sm"
              onSubmit={(e) => {
                e.preventDefault();
                handlePlanTrip();
              }}
            >
              <h2 className="text-2xl font-semibold">여행 일정 만들기</h2>
              <label className="mt-4 block text-sm">
                관찰 종
                <select
                  value={selectedSpeciesId}
                  onChange={(e) => setSelectedSpeciesId(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-forest-100 px-3 py-2"
                >
                  {speciesList.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.common_name}
                    </option>
                  ))}
                </select>
              </label>
              {[
                ["출발지", "origin"],
                ["여행 일수", "days"],
                ["예산(원)", "budget_krw"],
                ["인원", "travelers"],
              ].map(([label, key]) => (
                <label key={key} className="mt-4 block text-sm">
                  {label}
                  <input
                    value={tripForm[key as keyof typeof tripForm]}
                    onChange={(e) =>
                      setTripForm((prev) => ({
                        ...prev,
                        [key]: key === "origin" ? e.target.value : Number(e.target.value),
                      }))
                    }
                    className="mt-1 w-full rounded-xl border border-forest-100 px-3 py-2"
                  />
                </label>
              ))}
              <label className="mt-4 block text-sm">
                숙박 유형
                <select
                  value={tripForm.accommodation}
                  onChange={(e) =>
                    setTripForm((prev) => ({ ...prev, accommodation: e.target.value }))
                  }
                  className="mt-1 w-full rounded-xl border border-forest-100 px-3 py-2"
                >
                  {Object.entries(ACCOMMODATION_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                disabled={loading}
                className="mt-6 w-full rounded-full bg-forest-700 px-4 py-3 font-medium text-white disabled:opacity-60"
              >
                {loading ? "생성 중..." : "일정 생성"}
              </button>
            </form>

            <div className="rounded-3xl border border-forest-100 bg-white p-6 shadow-sm">
              {tripPlan ? (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-semibold">
                      {tripPlan.species_name} 관찰 여행 ({tripPlan.days}일)
                    </h2>
                    <p className="mt-2 text-sm text-forest-700/70">
                      추천지: {tripPlan.hotspot_name} · {tripPlan.region} · 생성 방식: {tripPlan.source}
                    </p>
                    <p className="mt-3">{tripPlan.summary}</p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    {Object.entries(tripPlan.costs)
                      .filter(([key]) => key !== "total" && key !== "per_person")
                      .map(([key, value]) => (
                        <div key={key} className="rounded-2xl bg-forest-50 p-3 text-sm">
                          <p className="font-semibold capitalize">{key}</p>
                          <p>{formatKrw(value as number)}</p>
                        </div>
                      ))}
                  </div>
                  <div className="rounded-2xl bg-forest-700 p-4 text-white">
                    <p>총 예상 비용: {formatKrw(tripPlan.costs.total)}</p>
                    <p className="text-sm text-forest-100">
                      1인당 {formatKrw(tripPlan.costs.per_person)}
                    </p>
                  </div>

                  {tripPlan.days > 1 && (
                    <div>
                      <h3 className="font-semibold">추천 숙박</h3>
                      {(tripPlan.accommodation_options ?? []).length > 0 ? (
                        <div className="mt-3 space-y-3">
                          {(tripPlan.accommodation_options ?? []).map((stay) => (
                            <article
                              key={stay.name}
                              className="rounded-2xl border border-forest-100 p-4 text-sm"
                            >
                              <div className="flex flex-wrap items-start justify-between gap-2">
                                <div>
                                  <p className="font-semibold">{stay.name}</p>
                                  <p className="mt-1 text-forest-700/70">
                                    {accommodationTypeLabel(stay.type)} · {stay.region}
                                  </p>
                                </div>
                                <p className="font-semibold text-forest-800">
                                  {formatKrw(stay.price_per_night_krw)}
                                  <span className="text-xs font-normal text-forest-700/60"> /박</span>
                                </p>
                              </div>
                              {stay.address && (
                                <p className="mt-2 text-forest-700/70">{stay.address}</p>
                              )}
                              <div className="mt-2 flex flex-wrap gap-3 text-xs text-forest-700/60">
                                {stay.distance_km != null && (
                                  <span>관찰지 약 {stay.distance_km}km</span>
                                )}
                                {stay.rating != null && <span>평점 {stay.rating.toFixed(1)}</span>}
                                <span>출처: {accommodationSourceLabel(stay.source)}</span>
                              </div>
                              {stay.note && (
                                <p className="mt-2 text-forest-700/80">{stay.note}</p>
                              )}
                              {stay.booking_url && (
                                <a
                                  href={stay.booking_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-3 inline-block text-sm font-medium text-forest-700 underline"
                                >
                                  예약·정보 포털 보기
                                </a>
                              )}
                            </article>
                          ))}
                        </div>
                      ) : (
                        <p className="mt-2 text-sm text-forest-700/70">
                          예산 범위 내 숙박 후보가 없습니다. 예산을 늘리거나 숙박 유형을 변경해 보세요.
                        </p>
                      )}
                    </div>
                  )}

                  <div>
                    <h3 className="font-semibold">준비물</h3>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                      {tripPlan.checklist.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  {tripPlan.days_plan.map((day) => (
                    <div key={day.day} className="rounded-2xl border border-forest-100 p-4">
                      <h3 className="font-semibold">
                        Day {day.day} · {day.title}
                      </h3>
                      <div className="mt-3 space-y-3">
                        {day.items.map((item, idx) => (
                          <div key={idx} className="grid grid-cols-[72px_1fr] gap-3 text-sm">
                            <span className="font-semibold text-forest-700">{item.time}</span>
                            <div>
                              <p className="font-medium">{item.activity}</p>
                              <p className="text-forest-700/70">{item.location}</p>
                              {item.note && <p className="mt-1 text-forest-700/60">{item.note}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  <p className="rounded-2xl bg-amber-50 p-4 text-sm text-amber-900">
                    {tripPlan.disclaimer}
                  </p>
                </div>
              ) : (
                <p className="text-forest-700/70">여행 조건을 입력하고 일정을 생성해 보세요.</p>
              )}
            </div>
          </section>
        )}

        {tab === "records" && (
          <section className="rounded-3xl border border-forest-100 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-semibold">내 관찰 기록</h2>
            <div className="mt-6 space-y-4">
              {sightings.map((item) => (
                <div key={item.id} className="rounded-2xl border border-forest-100 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-lg font-semibold">{item.common_name}</p>
                    <p className="text-sm text-forest-700/70">
                      {new Date(item.created_at).toLocaleString("ko-KR")}
                    </p>
                  </div>
                  <p className="mt-2 text-sm">
                    신뢰도 {(item.confidence * 100).toFixed(1)}% · {item.media_type}
                  </p>
                  {item.note && <p className="mt-1 text-sm text-forest-700/80">{item.note}</p>}
                </div>
              ))}
              {sightings.length === 0 && (
                <p className="text-forest-700/70">아직 기록이 없습니다. 식별 탭에서 시작해 보세요.</p>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
