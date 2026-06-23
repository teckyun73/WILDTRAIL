"""
공공 API 연동 스텁

실제 키 발급 후 .env에 설정하면 외부 API를 호출합니다.
현재는 샘플 응답을 반환해 프론트 연동 구조를 검증합니다.

숙박 연동 예정:
- 한국관광공사 Tour API (숙박·관광)
- 공공데이터포털 지역 숙박·민박 정보
- 포털 사이트(야놀자·여기어때 등) API 또는 제휴 링크
"""

from __future__ import annotations

import json
import logging
import re

from app.config import get_settings
from app.schemas import AccommodationOption
from app.services.llm import chat, is_llm_configured

settings = get_settings()
logger = logging.getLogger(__name__)

_ACCOMMODATION_TYPE_LABELS: dict[str, str] = {
    "guesthouse": "게스트하우스",
    "hotel": "호텔",
    "pension": "펜션",
}

_PORTAL_BOOKING_BASE = "https://www.visitkorea.or.kr/search/search_list.jsp"


class PublicApiService:
    def get_weather_stub(self, region: str) -> dict:
        return {
            "region": region,
            "summary": "맑음, 관찰에 적합",
            "temp_c": 18,
            "wind": "약함",
            "source": "stub",
            "note": "기상청 API 키 연동 시 실데이터로 대체",
        }

    def get_nearby_transport_stub(self, region: str) -> dict:
        return {
            "region": region,
            "options": [
                {"type": "KTX", "desc": "가장 가까운 KTX역 환승 후 시내버스"},
                {"type": "시외버스", "desc": "터미널 직행 또는 환승"},
            ],
            "source": "stub",
            "note": "TAGO 대중교통 API 연동 예정",
        }

    def get_tourism_stub(self, region: str) -> dict:
        return {
            "region": region,
            "spots": [
                {"name": f"{region} 생태탐방로", "type": "ecotour"},
                {"name": f"{region} 국립공원 안내소", "type": "visitor_center"},
            ],
            "source": "stub",
            "note": "한국관광공사 Tour API 연동 예정",
        }

    def get_accommodations_stub(
        self,
        region: str,
        accommodation_type: str = "guesthouse",
    ) -> list[dict]:
        """지역·숙박 유형별 샘플 후보 (Tour API / 공공데이터 대체용)."""
        type_label = _ACCOMMODATION_TYPE_LABELS.get(accommodation_type, "숙박")
        region_short = region.split()[-1] if region else "관찰지"

        templates: list[dict] = [
            {
                "name": f"{region_short} {type_label} 에코스테이",
                "type": accommodation_type,
                "region": region,
                "address": f"{region} 관찰지 인근",
                "price_per_night_krw": 45000 if accommodation_type == "guesthouse" else 75000,
                "distance_km": 1.2,
                "rating": 4.3,
                "booking_url": f"{_PORTAL_BOOKING_BASE}?query={region_short}+{type_label}",
                "source": "stub",
                "note": "관찰지 도보·셔틀 15분, 조용한 숙소",
            },
            {
                "name": f"{region_short} 생태관광 {type_label}",
                "type": accommodation_type,
                "region": region,
                "address": f"{region} 시내·터미널 근처",
                "price_per_night_krw": 55000 if accommodation_type == "guesthouse" else 95000,
                "distance_km": 3.5,
                "rating": 4.1,
                "booking_url": f"{_PORTAL_BOOKING_BASE}?query={region_short}+생태",
                "source": "stub",
                "note": "대중교통 접근 용이, 조식 제공(일부)",
            },
            {
                "name": f"{region_short} {type_label} & 카페",
                "type": accommodation_type,
                "region": region,
                "address": f"{region} 주변 농촌·해안 마을",
                "price_per_night_krw": 38000 if accommodation_type == "guesthouse" else 68000,
                "distance_km": 5.8,
                "rating": 4.0,
                "booking_url": f"{_PORTAL_BOOKING_BASE}?query={region_short}+민박",
                "source": "stub",
                "note": "야간 소음 최소, 새벽 출발 관찰에 적합",
            },
        ]

        if accommodation_type == "pension":
            templates.append(
                {
                    "name": f"{region_short} 가족형 펜션",
                    "type": "pension",
                    "region": region,
                    "address": f"{region} 인근 단독주택형",
                    "price_per_night_krw": 120000,
                    "distance_km": 4.2,
                    "rating": 4.5,
                    "booking_url": f"{_PORTAL_BOOKING_BASE}?query={region_short}+펜션",
                    "source": "stub",
                    "note": "2박 이상·가족·소그룹 관찰 여행에 적합",
                }
            )
        elif accommodation_type == "hotel":
            templates.append(
                {
                    "name": f"{region_short} 비즈니스 호텔",
                    "type": "hotel",
                    "region": region,
                    "address": f"{region} 역·터미널 인근",
                    "price_per_night_krw": 89000,
                    "distance_km": 8.0,
                    "rating": 4.2,
                    "booking_url": f"{_PORTAL_BOOKING_BASE}?query={region_short}+호텔",
                    "source": "stub",
                    "note": "역세권·셔틀·택시 이용 편리",
                }
            )

        return templates

    def search_accommodations(
        self,
        *,
        region: str,
        latitude: float,
        longitude: float,
        accommodation_type: str = "guesthouse",
        budget_krw: int = 150000,
        nights: int = 1,
        travelers: int = 1,
    ) -> list[AccommodationOption]:
        """
        숙박 후보 검색.

        실 연동 시 Tour API·공공데이터·포털 API를 latitude/longitude 기준으로 호출합니다.
        현재는 get_accommodations_stub() 결과를 예산·거리 기준으로 필터링합니다.
        """
        # TODO: settings.tour_api_key 등으로 한국관광공사 Tour API 호출
        # TODO: 공공데이터포털 숙박 CSV/API 연동
        raw = self.get_accommodations_stub(region, accommodation_type)

        per_night_budget = budget_krw // max(nights, 1) // max(travelers, 1)
        max_nightly = int(per_night_budget * 0.45)

        options: list[AccommodationOption] = []
        for item in raw:
            price = int(item["price_per_night_krw"])
            if max_nightly > 0 and price > max_nightly:
                continue
            options.append(AccommodationOption(**item))

        if not options:
            options = [AccommodationOption(**item) for item in raw[:2]]

        options.sort(
            key=lambda o: (
                o.distance_km if o.distance_km is not None else 99.0,
                o.price_per_night_krw,
            )
        )
        return options[:5]

    def enrich_accommodation_notes_with_llm(
        self,
        options: list[AccommodationOption],
        *,
        hotspot_name: str,
        hotspot_region: str,
        transport_note: str,
        facilities: str,
        safety_note: str,
        species_name: str,
        origin: str,
        days: int,
        accommodation_type: str,
    ) -> list[AccommodationOption]:
        """패턴 2: stub 숙박 후보의 note만 LLM으로 생태관광 맥락에 맞게 보강."""
        if not options or not is_llm_configured():
            return options

        payload = {
            "hotspot_name": hotspot_name,
            "hotspot_region": hotspot_region,
            "transport_note": transport_note,
            "facilities": facilities,
            "safety_note": safety_note,
            "species_name": species_name,
            "origin": origin,
            "days": days,
            "accommodation_type": accommodation_type,
            "options": [
                {
                    "name": o.name,
                    "type": o.type,
                    "price_per_night_krw": o.price_per_night_krw,
                    "distance_km": o.distance_km,
                    "note": o.note,
                }
                for o in options
            ],
        }

        raw = chat(
            system=(
                "당신은 한국 생태관광 숙박 조언 도우미입니다. "
                "입력 options의 name·가격·거리·유형은 변경하지 마세요. "
                "각 숙소의 note만 1~2문장으로 다시 작성하세요. "
                "새벽·황혼 관찰, 대중교통, 조용한 숙소, 관찰지까지 이동 등에 초점을 맞추세요. "
                "출현 보장·허위 상호·새로운 숙소 추가는 금지합니다. "
                'JSON 배열만 출력: [{"name":"...", "note":"..."}, ...]'
            ),
            user=json.dumps(payload, ensure_ascii=False),
            temperature=0.3,
        )
        if not raw:
            return options

        notes_by_name = self._parse_accommodation_notes_json(raw)
        if not notes_by_name:
            return options

        enriched: list[AccommodationOption] = []
        for opt in options:
            new_note = notes_by_name.get(opt.name)
            if new_note:
                enriched.append(
                    opt.model_copy(update={"note": new_note, "source": "stub+llm"})
                )
            else:
                enriched.append(opt)
        return enriched

    @staticmethod
    def _parse_accommodation_notes_json(raw: str) -> dict[str, str]:
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM accommodation notes JSON")
            return {}

        if not isinstance(data, list):
            return {}

        result: dict[str, str] = {}
        for item in data:
            if isinstance(item, dict) and item.get("name") and item.get("note"):
                result[str(item["name"])] = str(item["note"]).strip()
        return result


public_api_service = PublicApiService()
