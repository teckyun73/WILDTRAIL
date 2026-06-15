"""
공공 API 연동 스텁

실제 키 발급 후 .env에 설정하면 외부 API를 호출합니다.
현재는 샘플 응답을 반환해 프론트 연동 구조를 검증합니다.
"""

from __future__ import annotations

from app.config import get_settings

settings = get_settings()


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


public_api_service = PublicApiService()
