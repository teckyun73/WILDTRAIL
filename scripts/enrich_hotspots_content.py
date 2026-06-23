"""
hotspots.json 관찰지 내용 보강 스크립트

- 기존 10곳: transport_note / facilities / safety_note 상세화
- 신규 관찰지: 종 커버리지 확대 (species.json에 있는 종만)

사용법:
  cd backend && ..\\.venv\\Scripts\\python ..\\scripts\\enrich_hotspots_content.py
  cd backend && ..\\.venv\\Scripts\\python ..\\scripts\\enrich_hotspots_content.py --dry-run
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# name 기준으로 기존 항목 텍스트 보강
HOTSPOT_PATCHES: dict[str, dict] = {
    "순천만 국가정원 갯벌": {
        "transport_note": (
            "KTX 순천역(약 50분·서울 기준) 하차 → 순천역 1번 출구 시내버스 "
            "'순천만국가정원·순천만습지'행(약 35~40분) 또는 택시 25분. "
            "자가용은 국가정원 주차장(유료) 이용, 성수기·주말 혼잡. "
            "왕복 4~5시간 이상 여유 권장."
        ),
        "facilities": (
            "순천만국가정원 전망대·갯벌탐방로·습지전시관·화장실·매점·휠체어 구간 일부. "
            "쇠백로·중대백로·갯벌 철새는 전망대·S자탐방로·갈대밭 코스에서 관찰. "
            "망원렌즈·삼각대 대여 없음 — 직접 지참."
        ),
        "safety_note": (
            "갯벌 미끄럼·함몰 위험 — 지정 탐방로만 이용. 만조·간조 시간표(조석 앱) 확인 후 "
            "간조 2시간 전후가 갯벌 진입·철새 관찰에 유리. 여름 모기·자외선 대비, "
            "철새에게 먹이 주기·드론·플래시 금지."
        ),
    },
    "한강하구 생태공원": {
        "transport_note": (
            "김포골드라인(9호선 환승) 화곡역 → 김포골드라인 마곡·양촌 방향 → "
            "김포공항역 환승 또는 버스 60·61·88번 등 '한강하구'·'생태공원' 하차. "
            "자가용은 한강하구 생태공원 주차장(무료·협소). 서울 서부에서 당일치기 적합."
        ),
        "facilities": (
            "탐방로·전망대·생태해설·화장실. 황제갈매기·갈매기·물새는 하구 전망대·"
            "강변 산책로에서 관찰. 5~9월 번식·서식 peak, 망원 8x~10x 권장."
        ),
        "safety_note": (
            "강풍·조수 시 강변 난간 밖 접근 금지. 여름 장마·겨울 강풍 시 전망대 이용 주의. "
            "새끼 철·번식기 둥지·서식지 접근 자제, 쓰레기 반출."
        ),
    },
    "철원 평야 두루미 공원": {
        "transport_note": (
            "KTX·ITX 서울·용산 → 철원(또는 근정) → 철원터미널 시외버스·택시(약 20분). "
            "자가용은 '두루미공원'·'철원 평야' 네비, 겨울철(11~2월) 주차 혼잡. "
            "전망대 개장 시간(일출 전·일몰 후 제한) 사전 확인."
        ),
        "facilities": (
            "지정 전망대·해설 프로그램·주차장·화장실·기념품. "
            "두루미 무리는 새벽·해질녘 급식·서식 시간대에 활발. "
            "쌍안경·망원렌즈 필수, 현장 해설(겨울 시즌) 활용 권장."
        ),
        "safety_note": (
            "멸종위기 1급 — 지정 관찰 구역·전망대 밖 접근·촬영 접근 금지. "
            "플래시·드론·큰 소음·먹이 금지, 100m 이상 거리 유지. "
            "겨울 영하·강풍 대비, 새벽 기온 낮음."
        ),
    },
    "무의도 갯벌": {
        "transport_note": (
            "인천 1호선 인천역 1번 출구 → 시내버스 15·27·45번 '무의도'·'갯벌' 하차(약 25분). "
            "인천대공원·차이나타운 인근에서 택시 15분. "
            "간조 시간에 맞춰 도착해야 갯벌 체험·홍오리 관찰 가능."
        ),
        "facilities": (
            "갯벌체험로·편의점·화장실·주민 마을. 홍오리·갈매기·도요새는 "
            "간조 시 갯벌·방조제에서 관찰. 장화·모자 지참, 겨울 방한."
        ),
        "safety_note": (
            "간조 2~3시간 전후만 갯벌 진입 가능 — 조석표 필수. "
            "진흙 함몰·미끄럼 주의, 혼자 깊은 갯벌 진입 금지. "
            "철새에게 먹이 주지 마세요."
        ),
    },
    "지리산 노고단": {
        "transport_note": (
            "KTX·ITX 구례역 하차 → 구례터미널 '노고단'·'구례' 행 시내버스(약 40~50분) "
            "또는 택시 30분. 자가용은 노고단 주차장(소형, 성수기 만차). "
            "새벽·황혼 관찰 시 숙소(구례·산청) 1박 권장."
        ),
        "facilities": (
            "노고단 정상 전망·등산로·쉼터·화장실(계절). "
            "노루·사슴류는 초지·숲 경계, 새벽 5~7시·저녁 18~20시 peak. "
            "헤드랜턴·쌍안경, 등산화 필수."
        ),
        "safety_note": (
            "야간·새벽 단독 탐방 위험 — 동행 권장. 안개·강풍·기온 급변 대비. "
            "야생동물 접근·먹이 금지, 플래시·큰 소음 자제. "
            "국립공원 내 취사·캠핑 규정 준수."
        ),
    },
    "내장산 국립공원": {
        "transport_note": (
            "KTX 정읍역 → 정읍터미널 '내장산'·'내장사' 셔틀·시내버스(약 30분). "
            "자가용은 내장산국립공원 주차장(유료). "
            "케이블카 이용 시 대기 시간 성수기 1시간 이상."
        ),
        "facilities": (
            "케이블카·탐방로·박물관·숙박 인근 민박. "
            "말똥가리·맹금류는 개활지·산기슭·케이블카 상부 전망에서 선회 관찰. "
            "봄·가을 migration 시즌(3~5월, 9~11월) 유리."
        ),
        "safety_note": (
            "산악 기상 변화·낙석 구간 주의, 등산복·우비 지참. "
            "맹금류 둥지·서식지 접근 금지. 케이블카 혼잡 시 일찍 입장."
        ),
    },
    "판암공원 일대": {
        "transport_note": (
            "지하철 5호선 금호역 3번 출구 도보 10분, 또는 2호선 성수역·뚝섬역 버스 환승. "
            "자가용 주차 협소 — 대중교통 권장. "
            "도심 당일·출퇴근 전후 1~2시간 관찰 가능."
        ),
        "facilities": (
            "판암공원·뚝섬한강공원 연결 산책로·벤치·화장실. "
            "까치·참새·비둘기·물총새(한강변) 연중 관찰. "
            "쌍안경 없이도 가까이 관찰 가능, 봄 둥지·경계 행동 주목."
        ),
        "safety_note": (
            "한강변 야간·우천 시 미끄럼 주의. "
            "둥지·새끼 철 무리 접근·촬영 자제. "
            "도심이라 소음·인파 많음 — 이른 아침이 유리."
        ),
    },
    "청평 수달 서식지": {
        "transport_note": (
            "ITX·경춘선 청평역 하차 → 북한강변 산책로 도보 15~20분(수달 포인트는 "
            "역 북쪽 하천). 자가용은 청평역 인근 공영주차 후 도보. "
            "새벽·저녁 2~3시간 집중 관찰 권장."
        ),
        "facilities": (
            "하천 산책로·낚시터(일부) — 조용한 구간에서 관찰. "
            "수달은 물고기 사냥·헤엄·바위 휴식 모습. "
            "멀리서 쌍안경·장망원, 소음 최소화."
        ),
        "safety_note": (
            "멸종위기 1급 — 접근·먹이·플래시·드론 금지, 30m 이상 거리. "
            "수달은 소음·진동에 매우 민감, 속삭이듯 관찰. "
            "겨울 결빙·여름 장마 시 강변 접근 주의."
        ),
    },
    "강화도 갯벌 생태공원": {
        "transport_note": (
            "신분당선·2호선 강남 → 신도림 → 1호선 인천方向 → 신인천역 "
            "또는 서울역·용산 시외버스 '강화'·'강화터미널'(약 1~1.5시간). "
            "터미널에서 갯벌생태공원 택시·마을버스 10~15분."
        ),
        "facilities": (
            "탐방로·전망대·카페·화장실·주차장. "
            "해오라기·백로·도요새는 황혼·새벽 습지·갯벌에서 관찰. "
            "저녁 17~19시, 새벽 5~7시 time slot 추천."
        ),
        "safety_note": (
            "황혼·새벽 방한·보온, 손전등 최소 사용(조류·동물 스트레스). "
            "갯벌·간조 시 진흙 주의. "
            "번식기 둥지·무리 접근 금지."
        ),
    },
    "제주 곶자왈": {
        "transport_note": (
            "제주공항 → 렌터카(30~40분) 또는 시내버스·택시. "
            "대표 곳: 한림공원 인근·1100고지·성산 일대 곶자왈. "
            "1일 코스로 2~3곳 순환 가능."
        ),
        "facilities": (
            "숲길·해설판·주차장(곳마다 상이). "
            "동박새·울새·제주 특유 조류는 4~9월 개화·곤충 시즌 활발. "
            "쌍안경·모기 기피제, 곶자왈 바닥 뿌리·이끼 미끄럼 주의."
        ),
        "safety_note": (
            "곶자왈 진입로·계단 미끄럼, 우천 시 등산로 폐쇄 확인. "
            "제주 기후 변화 빠름 — 겉옷 지참. "
            "야생화·서식지 훼손 금지."
        ),
    },
}

# species.json에 있는 종만 — 신규 관찰지 추가
NEW_HOTSPOTS: list[dict] = [
    {
        "name": "팔당댐 북한강 물총새길",
        "region": "경기 가평",
        "latitude": 37.524,
        "longitude": 127.318,
        "species_id": "alcedo_atthis",
        "best_months": "4,5,6,7,8,9",
        "observation_score": 0.85,
        "access_level": "easy",
        "transport_note": (
            "경춘선 팔당역 하차 → 북한강변 산책로 도보 10분. "
            "자가용은 팔당댐·두물머리 주차장(주말 혼잡). "
            "전봇대·낮은 가지에 앉은 물총새 포인트 다수."
        ),
        "entry_fee": 0,
        "facilities": (
            "강변 산책로·낚시터·편의점·화장실. "
            "청록색 깃·급강하 사냥 장면 연중 관찰 가능, "
            "햇빛 좋은 날 오전 9~11시 유리."
        ),
        "safety_note": (
            "강변 난간 밖·낚시터 침입 주의. "
            "물총새에게 소음·접근 최소화, 플래시 금지."
        ),
    },
    {
        "name": "서울숲 쇠박새·동박새 서식지",
        "region": "서울 성동",
        "latitude": 37.544,
        "longitude": 127.037,
        "species_id": "parus_minor",
        "best_months": "3,4,5,6,7,8,9,10",
        "observation_score": 0.78,
        "access_level": "easy",
        "transport_note": (
            "분당선 서울숲역 3번 출구 바로 앞, "
            "뚝섬역·성수역에서도 도보 10~15분. "
            "대중교통·당일치기 최적."
        ),
        "entry_fee": 0,
        "facilities": (
            "메타세쿼이아길·연못·전망대·화장실·카페. "
            "쇠박새·동박새·참새 무리, 봄~가을 개화기 peak. "
            "쌍안경 없이도 가까이 관찰."
        ),
        "safety_note": (
            "주말·공휴일 인파 많음 — 평일 이른 아침 추천. "
            "둥지·새끼 철 접근·먹이 금지."
        ),
    },
    {
        "name": "올림픽공원 딱새 겨울숲",
        "region": "서울 송파",
        "latitude": 37.521,
        "longitude": 127.121,
        "species_id": "turdus_naumanni",
        "best_months": "11,12,1,2,3",
        "observation_score": 0.81,
        "access_level": "easy",
        "transport_note": (
            "5호선 올림픽공원역·8호선 몽촌토성역 도보 5~10분. "
            "몽촌토성·해랑길 일대 산책로."
        ),
        "entry_fee": 0,
        "facilities": (
            "넓은 산책로·과수·열매나무·화장실. "
            "11~3월 붉은 배·흰 반점 딱새 무리, "
            "땅에서 먹이 찾는 모습 관찰 용이."
        ),
        "safety_note": (
            "겨울 결빙·바람 대비. "
            "새에게 먹이 주지 마세요."
        ),
    },
    {
        "name": "월드컵공원 호수 청둥오리",
        "region": "서울 마포",
        "latitude": 37.569,
        "longitude": 126.897,
        "species_id": "anas_platyrhynchos",
        "best_months": "3,4,5,6,9,10,11",
        "observation_score": 0.74,
        "access_level": "easy",
        "transport_note": (
            "6호선 월드컵경기장역 1번 출구 도보 10분. "
            "하늘공원·노을공원과 연결, 주차 가능."
        ),
        "entry_fee": 0,
        "facilities": (
            "인공호수·잔디광장·화장실. "
            "청둥오리·원앙·물새 연중 관찰, "
            "봄 번식기 수컷 녹색 머리 선명."
        ),
        "safety_note": (
            "호수 난간 밖 접근·어린이 낙수 주의. "
            "오리에게 빵·과자 금지(건강·수질)."
        ),
    },
    {
        "name": "함평천 갈대습지",
        "region": "전남 함평",
        "latitude": 35.065,
        "longitude": 126.521,
        "species_id": "emberiza_schoeniclus",
        "best_months": "5,6,7,8,9",
        "observation_score": 0.83,
        "access_level": "moderate",
        "transport_note": (
            "KTX 나주역 → 함평 시외버스(약 40분). "
            "자가용은 '함평천'·'함평갈대' 네비. "
            "5~9월 갈대 peak."
        ),
        "entry_fee": 0,
        "facilities": (
            "갈대밭 전망·탐방데크(일부)·화장실. "
            "검은머리쑥새 수컷 검은 머리·흰 목, "
            "'지-지-지' 울음으로 위치 파악."
        ),
        "safety_note": (
            "갈대밭 화재·입화 금지, 지정 데크만 이용. "
            "습지 소음 최소화, 번식기 접근 자제."
        ),
    },
    {
        "name": "강화 도라소습지",
        "region": "인천 강화",
        "latitude": 37.689,
        "longitude": 126.452,
        "species_id": "hydropotes_inermis",
        "best_months": "4,5,6,7,8,9",
        "observation_score": 0.77,
        "access_level": "hard",
        "transport_note": (
            "강화터미널 → 도라소·갯벌 방면 마을버스·택시(20분). "
            "새벽·저녁 시간대 이동 계획 필수."
        ),
        "entry_fee": 0,
        "facilities": (
            "갈대·습지·논두렁 — 시설 최소. "
            "고라니는 습지·갈대 가장자리, "
            "바람 상류에서 조용히 접근."
        ),
        "safety_note": (
            "습지·갯벌 함몰 주의, 간조·야간 단독 탐방 금지. "
            "고라니 경계음 후 달아남 — 플래시·소음 자제."
        ),
    },
    {
        "name": "태안몰·만리포 해변",
        "region": "충남 태안",
        "latitude": 36.786,
        "longitude": 126.142,
        "species_id": "melanitta_fusca",
        "best_months": "11,12,1,2,3",
        "observation_score": 0.8,
        "access_level": "easy",
        "transport_note": (
            "서울 → 서해안고속도로 태안·만리포 IC(약 2.5~3시간). "
            "대중교통은 서울→태안 시외버스 후 택시."
        ),
        "entry_fee": 0,
        "facilities": (
            "해변·방조제·펜션·식당. "
            "11~3월 검은머리오리·바다오리 무리, "
            "파도 잔잔한 날 망원렌즈 관찰."
        ),
        "safety_note": (
            "겨울 해안 강풍·파도 주의, 방조제 난간 밖 금지. "
            "조류 떼에 접근·놀래키지 마세요."
        ),
    },
    {
        "name": "임진강 하류 황새·물새",
        "region": "경기 파주",
        "latitude": 37.895,
        "longitude": 126.715,
        "species_id": "ciconia_boyciana",
        "best_months": "3,4,5,10,11",
        "observation_score": 0.75,
        "access_level": "moderate",
        "transport_note": (
            "경의중앙선 파주역·운천역 → 택시·버스(임진강·하사리). "
            "자가용은 임진각·하류 전망 포인트 주차."
        ),
        "entry_fee": 0,
        "facilities": (
            "하천·습지·전망 포인트 — 시설 제한적. "
            "황새·왜가리·물새 원거리 관찰, "
            "망원 20x 이상 권장."
        ),
        "safety_note": (
            "멸종위기종 — 지정 구역·먼 거리 관찰. "
            "군사·민간 접근 제한 구역 확인, "
            "드론·플래시·접근 금지."
        ),
    },
    {
        "name": "안성 농경지 황조롱이",
        "region": "경기 안성",
        "latitude": 37.008,
        "longitude": 127.279,
        "species_id": "falco_tinnunculus",
        "best_months": "3,4,5,6,9,10",
        "observation_score": 0.79,
        "access_level": "easy",
        "transport_note": (
            "KTX·ITX 평택·오송 → 안성 시외버스. "
            "자가용은 안성·죽산 일대 농로·전선(개활지). "
            "전봇대·전선 앉은 새 관찰."
        ),
        "entry_fee": 0,
        "facilities": (
            "개활 농경지·두렁 — 시설 없음. "
            "공중 정지(hovering) 비행, "
            "차량 안에서 망원 관찰 권장."
        ),
        "safety_note": (
            "농로·작업 중인 밭 침입 금지, "
            "농가·차량 통행 주의. "
            "둥지·서식지 접근 자제."
        ),
    },
    {
        "name": "낙동강 하구 황제갈매기",
        "region": "경남 창원",
        "latitude": 35.095,
        "longitude": 128.814,
        "species_id": "hydroprogne_caspia",
        "best_months": "5,6,7,8,9",
        "observation_score": 0.87,
        "access_level": "moderate",
        "transport_note": (
            "KTX·SRT 창원중앙역 → 시내버스·택시(낙동강하구·"
            "명지·대합). 자가용은 하구 전망·방조제 주차."
        ),
        "entry_fee": 0,
        "facilities": (
            "하구 전망·방조제·어항 인근. "
            "5~9월 황제갈매기 급강하 사냥, "
            "강바람 약한 날 다리·제방 관찰."
        ),
        "safety_note": (
            "하구 조수·강풍 주의. "
            "어업·선박 통행 구역 침입 금지."
        ),
    },
    {
        "name": "월아산 호수 뿔제비",
        "region": "경북 영천",
        "latitude": 35.978,
        "longitude": 128.957,
        "species_id": "phalacrocorax_carbo",
        "best_months": "4,5,6,7,8,9,10",
        "observation_score": 0.76,
        "access_level": "moderate",
        "transport_note": (
            "KTX 동대구역 → 영천 시외버스 → 월아산(약 1.5시간). "
            "자가용은 월아산 일원 주차."
        ),
        "entry_fee": 3000,
        "facilities": (
            "호수·등산로·전망·화장실. "
            "뿔제비 날개 말리기·잠수 후 수면, "
            "호수변 바위·나무."
        ),
        "safety_note": (
            "산악 등산로 규정 준수. "
            "호숫가 미끄럼·낙석 주의."
        ),
    },
    {
        "name": "양평 두물머리·용두레",
        "region": "경기 양평",
        "latitude": 37.528,
        "longitude": 127.298,
        "species_id": "motacilla_alba",
        "best_months": "3,4,5,6,7,8,9,10",
        "observation_score": 0.73,
        "access_level": "easy",
        "transport_note": (
            "ITX 양평역 → 택시·버스(두물머리 20분). "
            "주말·단풍 시즌 교통 혼잡."
        ),
        "entry_fee": 0,
        "facilities": (
            "강변 산책로·카페·주차장. "
            "할미새·물총새·오리, "
            "물가·도로변 꼬리 흔들기 행동."
        ),
        "safety_note": (
            "강변·보 조수 시 안전 거리. "
            "인파 많은 구간에서 삼각대 자리 확보 어려움."
        ),
    },
]


def apply_patches(hotspots: list[dict]) -> int:
    updated = 0
    by_name = {h["name"]: h for h in hotspots}
    for name, patch in HOTSPOT_PATCHES.items():
        if name not in by_name:
            continue
        by_name[name].update(patch)
        updated += 1
    return updated


def merge_new_hotspots(hotspots: list[dict], new_items: list[dict]) -> tuple[list[dict], int]:
    existing_names = {h["name"] for h in hotspots}
    added = 0
    for item in new_items:
        if item["name"] in existing_names:
            continue
        hotspots.append(item)
        existing_names.add(item["name"])
        added += 1
    return hotspots, added


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich hotspots.json content")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    path = ROOT / "data" / "hotspots.json"
    hotspots = json.loads(path.read_text(encoding="utf-8"))

    patched = apply_patches(hotspots)
    hotspots, added = merge_new_hotspots(hotspots, NEW_HOTSPOTS)

    print(f"hotspots.json: {patched} patched, {added} added, {len(hotspots)} total")

    if args.dry_run:
        print("DRY RUN - file not written")
        return

    path.write_text(
        json.dumps(hotspots, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
