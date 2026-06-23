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

from app.config import get_settings
from app.schemas import AccommodationOption

settings = get_settings()

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


public_api_service = PublicApiService()
