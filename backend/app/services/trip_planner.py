import json

from sqlalchemy.orm import Session

from app.models import Hotspot, Species
from app.services.llm import chat, is_llm_configured
from app.schemas import (
    CostBreakdown,
    TripDayItem,
    TripDayPlan,
    TripPlanRequest,
    TripPlanResponse,
    TripRouteStop,
)

DISCLAIMER = (
    "야생동물 출현은 보장되지 않습니다. 보호구역 규정을 준수하고 안전에 유의하세요. "
    "경비는 참고용 추정치이며 실제 비용과 차이가 있을 수 있습니다."
)


class TripPlannerService:
    def plan(self, db: Session, request: TripPlanRequest) -> TripPlanResponse:
        species = db.get(Species, request.species_id)
        if not species:
            raise ValueError(f"종을 찾을 수 없습니다: {request.species_id}")

        hotspot = self._select_hotspot(db, request)
        costs = self._estimate_costs(request, hotspot)
        days_plan = self._build_schedule(request, species, hotspot)
        summary = self._build_summary(request, species, hotspot, costs)

        if is_llm_configured():
            llm_summary = self._enhance_with_llm(request, species, hotspot, costs, days_plan)
            if llm_summary:
                summary = llm_summary
                source = "llm+rules"
            else:
                source = "rules"
        else:
            source = "rules"

        return TripPlanResponse(
            species_id=species.id,
            species_name=species.common_name,
            origin=request.origin,
            days=request.days,
            travelers=request.travelers,
            hotspot_name=hotspot.name,
            hotspot_latitude=hotspot.latitude,
            hotspot_longitude=hotspot.longitude,
            region=hotspot.region,
            summary=summary,
            checklist=self._build_checklist(species),
            route_stops=self._build_route_stops(request, hotspot, days_plan),
            days_plan=days_plan,
            costs=costs,
            disclaimer=DISCLAIMER,
            source=source,
        )

    def _select_hotspot(self, db: Session, request: TripPlanRequest) -> Hotspot:
        query = db.query(Hotspot).filter(Hotspot.species_id == request.species_id)
        hotspots = query.order_by(Hotspot.observation_score.desc()).all()
        if not hotspots:
            fallback = db.query(Hotspot).order_by(Hotspot.observation_score.desc()).first()
            if not fallback:
                raise ValueError("관찰 핫스팟 데이터가 없습니다.")
            return fallback
        return hotspots[0]

    def _estimate_costs(self, request: TripPlanRequest, hotspot: Hotspot) -> CostBreakdown:
        base_transport = 28000 if request.preferences.transport == "public" else 45000
        transport = base_transport * (1 + (request.days - 1) * 0.35)
        accommodation = 0
        if request.days > 1:
            nightly = 55000 if request.preferences.accommodation == "guesthouse" else 85000
            accommodation = nightly * (request.days - 1)
        food = 18000 * request.days
        entry_fee = hotspot.entry_fee * request.travelers
        misc = 8000 * request.days
        total = int(transport + accommodation + food + entry_fee + misc)
        per_person = int(total / request.travelers)
        return CostBreakdown(
            transport=int(transport),
            accommodation=int(accommodation),
            food=int(food),
            entry_fee=int(entry_fee),
            misc=int(misc),
            total=total,
            per_person=per_person,
        )

    def _build_schedule(
        self, request: TripPlanRequest, species: Species, hotspot: Hotspot
    ) -> list[TripDayPlan]:
        plans: list[TripDayPlan] = []
        for day in range(1, request.days + 1):
            if day == 1:
                items = [
                    TripDayItem(
                        time="06:30",
                        activity="출발",
                        location=request.origin,
                        note="간단한 아침 식사 후 이동",
                    ),
                    TripDayItem(
                        time="09:00",
                        activity=f"{species.common_name} 관찰",
                        location=hotspot.name,
                        note=hotspot.transport_note or "조용히 접근하세요",
                    ),
                    TripDayItem(
                        time="12:00",
                        activity="주변 탐방·식사",
                        location=hotspot.region,
                        note=hotspot.facilities,
                    ),
                    TripDayItem(
                        time="15:00",
                        activity="재관찰 또는 근처 생태 탐방로",
                        location=hotspot.name,
                        note=species.observation_tips[:120],
                    ),
                ]
                if request.days == 1:
                    items.append(
                        TripDayItem(
                            time="18:00",
                            activity="귀가",
                            location=request.origin,
                            note="일몰 전 이동 권장",
                        )
                    )
                title = f"{hotspot.region} 당일 관찰" if request.days == 1 else "이동 및 1차 관찰"
            else:
                items = [
                    TripDayItem(
                        time="05:30",
                        activity="새벽 관찰",
                        location=hotspot.name,
                        note="활발한 시간대에 집중 관찰",
                    ),
                    TripDayItem(
                        time="10:00",
                        activity="휴식 및 기록 정리",
                        location=hotspot.region,
                        note="관찰 노트·사진 백업",
                    ),
                    TripDayItem(
                        time="14:00",
                        activity="주변 습지·숲길 탐방",
                        location=hotspot.region,
                        note="유사 서식지 확장 관찰",
                    ),
                ]
                if day == request.days:
                    items.append(
                        TripDayItem(
                            time="16:00",
                            activity="귀가",
                            location=request.origin,
                            note="대중교통 시간표 확인",
                        )
                    )
                title = f"Day {day} 심화 관찰"
            plans.append(TripDayPlan(day=day, title=title, items=items))
        return plans

    def _build_route_stops(
        self, request: TripPlanRequest, hotspot: Hotspot, days_plan: list[TripDayPlan]
    ) -> list[TripRouteStop]:
        origin = request.origin.strip()
        destination = hotspot.name.strip()
        stops: list[TripRouteStop] = []
        if origin:
            stops.append(TripRouteStop(name=origin, role="출발"))

        seen = {origin, destination}
        for day in days_plan:
            for item in day.items:
                location = item.location.strip()
                if location and location not in seen:
                    stops.append(TripRouteStop(name=location, role="경유"))
                    seen.add(location)
                    if len(stops) >= 5:
                        break
            if len(stops) >= 5:
                break

        if destination:
            stops.append(
                TripRouteStop(
                    name=destination,
                    role="주요 관찰지",
                    latitude=hotspot.latitude,
                    longitude=hotspot.longitude,
                )
            )
        return stops

    def _build_checklist(self, species: Species) -> list[str]:
        base = ["쌍안경(8x42 권장)", "카메라/스마트폰", "방수 신발", "모자·선크림", "간식·물"]
        if species.category == "bird":
            base.append("조류 도감 앱 또는 노트")
        if species.protection_grade:
            base.append("보호종 관찰 거리 준수(텔레포토 렌즈 권장)")
        return base

    def _build_summary(
        self,
        request: TripPlanRequest,
        species: Species,
        hotspot: Hotspot,
        costs: CostBreakdown,
    ) -> str:
        return (
            f"{request.origin}에서 출발해 {request.days}일 동안 {hotspot.name} 일대에서 "
            f"{species.common_name} 관찰을 추천합니다. 예상 총비용은 약 {costs.total:,}원이며 "
            f"1인당 {costs.per_person:,}원 수준입니다. {hotspot.safety_note}"
        )

    def _enhance_with_llm(
        self,
        request: TripPlanRequest,
        species: Species,
        hotspot: Hotspot,
        costs: CostBreakdown,
        days_plan: list[TripDayPlan],
    ) -> str | None:
        payload = {
            "species": species.common_name,
            "hotspot": hotspot.name,
            "region": hotspot.region,
            "days": request.days,
            "travelers": request.travelers,
            "budget": request.budget_krw,
            "costs": costs.model_dump(),
            "schedule": [day.model_dump() for day in days_plan],
        }
        return chat(
            system=(
                "당신은 한국 생태관광 플래너입니다. 제공된 사실만 사용하고 "
                "2~3문장으로 일정 요약을 작성하세요. 출현 보장 표현은 금지합니다."
            ),
            user=json.dumps(payload, ensure_ascii=False),
            temperature=0.4,
        )


trip_planner_service = TripPlannerService()
