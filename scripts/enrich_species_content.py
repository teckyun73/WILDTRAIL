"""
species.json / extra.json 내용 보강 스크립트 (종 추가 없음)

사용법:
  cd backend && ..\\backend\\.venv\\Scripts\\python ..\\scripts\\enrich_species_content.py
  cd backend && ..\\backend\\.venv\\Scripts\\python ..\\scripts\\enrich_species_content.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

SPECIES_PATCHES: dict[str, dict[str, str]] = {
    "pica_pica": {
        "habitat": "도시 공원, 캠퍼스, 농경지, 산림 가장자리, 하천변",
        "observation_tips": "둥지·영역 방어 시 '치치치' 경계음이 큽니다. 도심에서도 연중 관찰 가능하며, 바닥에서 먹이 찾는 모습을 가까이서 보기 쉽습니다. 8x42 쌍안경으로 부리·깃 패턴을 확인하세요.",
        "similar_species": "어치(날개·꼬리 청색 반짝임), 까마귀(체구 훨씬 큼·전체 검은색)",
        "description": "흑백 대비가 뚜렷하고 꼬리가 긴 대표적인 도시 조류입니다. 한국 전역 텃새로 공원·마을에서 흔하며, 번식기에는 둥지 근처에서 경계 행동을 보입니다. 깃털 광택과 긴 꼬리 실루엣으로 멀리서도 식별하기 쉽습니다.",
    },
    "corvus_corone": {
        "habitat": "산지, 농경지, 도심 공원, 강변, 해안부",
        "observation_tips": "크고 날카로운 '까악-' 울음과 넓적한 날개 비행이 특징입니다. 무리로 이동하며 먹이를 찾을 때는 땅에 내려앉기도 합니다. 겨울철 무리 관찰에 적합합니다.",
        "similar_species": "떼까마귀(무리 비행·울음 톤 다름), 어치(체구 작고 꼬리 김)",
        "description": "지능과 적응력이 뛰어난 대형 텃새입니다. 잡식성으로 도시부터 산지까지 넓게 분포하며, 도구 사용과 학습 능력으로 잘 알려져 있습니다. 검은 깃털과 두꺼운 부리가 대표적입니다.",
    },
    "passer_montanus": {
        "habitat": "마을, 논밭, 공원, 숲 가, 도시 녹지",
        "observation_tips": "떼 지어 서식하며 짧은 '짹짹' 지저귐을 반복합니다. 수수한 갈색 깃이 특징이며, 머리 뒤쪽 흰 반점(암컷·청년)으로 참새류 구분에 도움이 됩니다. 논두렁·울타리에서 가까이 관찰 가능합니다.",
        "similar_species": "집나무새(영어권), 검은머리쑥새(갈대밭·부리 형태 다름)",
        "description": "한국 농촌·도시에서 가장 흔한 소형 조류 중 하나입니다. 씨앗과 곤충을 먹으며 마을과 논 주변에서 연중 볼 수 있습니다. 작은 체구지만 무리 생활로 서식지에서 쉽게 발견됩니다.",
    },
    "streptopelia_orientalis": {
        "habitat": "산림, 공원, 농경지, 도시 녹지",
        "observation_tips": "낮은 가지에 앉아 '우-구-구-구' 울음을 반복합니다. 목 뒤 검은 반점과 붉은 눈이 식별 포인트입니다. 새벽·저녁 울음이 잘 들리며, 둥지는 관목·나무 위에 만듭니다.",
        "similar_species": "쇠비둘기(체구 작음), 집비둘기(도심·색 변이 다양)",
        "description": "목 뒤 검은 반점이 있는 대표적인 산비둘기입니다. 한국 전역 텃새로 산·공원·마을에서 흔하며, 차분한 울음으로 봄·여름철 아침을 알립니다. 비둘기과 중에서 자연 환경에 가까운 종입니다.",
    },
    "columba_livia": {
        "habitat": "도심 건물, 교량, 광장, 항구",
        "observation_tips": "건물 지붕· ledge 에서 무리로 쉬거나 곡선 비행합니다. 색형(회색·흰색·반점)이 다양합니다. 사람과 가까운 거리에서도 관찰되나, 번식지는 피하는 것이 좋습니다.",
        "similar_species": "멧비둘기(산림·목 뒤 반점), 원종 회색형과 유색형 혼재",
        "description": "전 세계 도시에서 가장 흔한 비둘기입니다. 원래 암반 서식 습성을 건물에 적용하며, 강한 비행력과 방향 감각으로 알려져 있습니다. 도심 생태계의 대표적인 조류입니다.",
    },
    "turdus_naumanni": {
        "habitat": "산림, 공원, 과수원, 도시 녹지",
        "observation_tips": "겨울철 붉은 배·흰 반점·검은 목이 뚜렷합니다. 땅에서 먹이를 찾으며, 열매가 많은 공원·산책로에서 관찰하기 좋습니다. 11~3월이 peak 시즌입니다.",
        "similar_species": "회색딱새(여름철), 박새·동박새(체구 훨씬 작음)",
        "description": "겨울철 한국을 찾는 대표적인 방랑성 지딜새입니다. 북쪽 번식지에서 내려와 공원·산림에서 열매를 먹으며, 붉은 배색이 겨울 조류 관찰의 하이라이트입니다.",
    },
    "buteo_japonicus": {
        "habitat": "산지, 개활지, 농경지, 도로변",
        "observation_tips": "넓은 날개를 펼친 채 공중 선회(hovering 아님)하며 서식지를 돕니다. 전망 좋은 언덕·갈대밭 가장자리에서 장시간 관찰 가능합니다. 망원렌즈 8x~10x 권장.",
        "similar_species": "새매(숲속 급비행·긴 꼬리), 말똥가리는 선회·넓은 날개",
        "description": "한국에서 가장 흔한 대형 부리(맹금류)입니다. 설치류와 곤충을 잡아먹으며 산지와 농경지를 넓게 이용합니다. 공중 선회 모습이 장관이며, 생태계 균형에 중요한 포식자입니다.",
    },
    "alcedo_atthis": {
        "habitat": "맑은 하천, 저수지, 용수로, 소하천",
        "observation_tips": "전봇대·나룻터·낮은 가지에 앉아 물을 주시하다 급강하합니다. 청록색 깃이 햇빛에 반짝입니다. 소음을 줄이고 강변에서 10m 이상 거리를 유지하세요.",
        "similar_species": "청딱따구리(숲·빨간 머리), 물총새는 물가·청록색",
        "description": "청록색 깃과 큰 부리가 특징인 소형 물가 조류입니다. 맑은 물가에 서식하며 작은 물고기를 잡아먹습니다. 급강하 사냥 장면은 야생 관찰의 대표적인 순간입니다.",
    },
    "nycticorax_nycticorax": {
        "habitat": "습지, 갯벌, 저수지, 도시 공원 연못",
        "observation_tips": "낮에는 숲·관목에 숨어 쉬고, 황혼·새벽에 먹이 활동합니다. 굽은 목·빨간 눈·짧은 다리가 특징입니다. 저녁 습지 방문 시 조용히 접근하세요.",
        "similar_species": "중대백로(낮 활동·체구 큼), 쇠백로(흰색·낮 활동)",
        "description": "황혼형 왜가리목으로 습지·갯벌에서 흔합니다. 낮에는 웅크린 자세로 숨어 있어 저녁·새벽 관찰이 유리합니다. 번식기에는 띠 무늬 깃이 나타납니다.",
    },
    "egretta_garzetta": {
        "habitat": "갯벌, 하천, 논, 연못, 해안 습지",
        "observation_tips": "흰 깃·검은 부리·검은 다리(번식기 발가락 노란색)가 특징입니다. 얕은 물에서 먹이 사냥하며, 느린 걸음과 급격한 목 움직임을 보입니다.",
        "similar_species": "중대백로(체구·부리 큼), 백로(다리·부리 색 다름)",
        "description": "우아한 흰색 물새로 습지·농경지에서 흔합니다. 작은 물고기와 곤충을 잡아먹으며, 갯벌과 논에서 청정 지표종으로도 알려져 있습니다.",
    },
    "grus_japonensis": {
        "habitat": "습지, 철새도래지(철원, 순천만 등)",
        "observation_tips": "망원렌즈(20x 이상) 필수, 지정 관찰로·전망대 이용. 100m 이상 거리 유지, 플래시·드론·먹이 금지. 겨울철 무리 급식·비행 장면이 장관입니다.",
        "similar_species": "흑두루미(깃색·체구), 두루미는 흰 목·검은 목·빨간 정수리",
        "description": "겨울 철새의 상징이며 멸종위기 야생생물 1급입니다. 습지 보전이 종 survival의 핵심이며, 우아한 춤과 울음으로 유명합니다. 관찰 시 보호구역 규정을 반드시 준수하세요.",
    },
    "ciconia_boyciana": {
        "habitat": "하천, 습지, 농경지(복원 지역)",
        "observation_tips": "지정 관찰 구역·전망대에서만 관람하세요. 흰 깃·검은 날개·주황 부리가 특징입니다. 번식기 둥지 근처 접근은 금지될 수 있습니다.",
        "similar_species": "흑색황새(검은색), 황새는 흰 몸·검은 날개",
        "description": "멸종위기 1급 대형 조류로 하천·습지 복원과 함께 재도입·방사가 진행 중입니다. 한국·동아시아 습지 보전의 상징종입니다.",
    },
    "anas_platyrhynchos": {
        "habitat": "호수, 하천, 저수지, 공원 연못, 습지",
        "observation_tips": "수컷은 녹색 머리·갈색 가슴, 암컷은 갈색 줄무늬입니다. 머리 아래로 물속 먹이 탐색(dabbling)하는 모습이 흔합니다. 겨울철 무리 관찰에 좋습니다.",
        "similar_species": "쇠청둥오리(체구 작음), 검은머리오리(해안·겨울)",
        "description": "가장 널리 알려진 오리로 공원 연못부터 자연 습지까지 서식합니다. dabbling 오리의 대표종이며, 한국 전역에서 연중 관찰 가능합니다.",
    },
    "tadorna_tadorna": {
        "habitat": "갯벌, 하구, 연안 습지, 큰 호수",
        "observation_tips": "흰·갈·검 대비가 뚜렷하고 부리 붉은색이 특징입니다. 겨울철 갯벌·하구에서 무리 관찰, 울음은 '끽끽' 소리가 큽니다.",
        "similar_species": "바다오리(해안), 청둥오리(녹색 머리 수컷)",
        "description": "겨울철 갯벌과 하구에서 흔한 오리입니다. 화려한 대비색과 큰 체구로 멀리서도 식별하기 쉽습니다. 조개·식물을 섭식합니다.",
    },
    "motacilla_alba": {
        "habitat": "하천, 도로변, 공원, 농경지, 해안",
        "observation_tips": "꼬리를 위아래로 흔들며 땅에서 곤충을 쫓습니다. 흰색·회색형(지역·계절)이 있으며, 도로·물가에서 가까이 관찰됩니다.",
        "similar_species": "노랑할미새(노란 배), 할미새는 흰·회색 위주",
        "description": "물가와 개활지에서 흔한 소형 텃새입니다. 꼬리 흔들기 행동이 특징적이며, 곤충 포식으로 농경지에도 유익합니다.",
    },
    "parus_minor": {
        "habitat": "활엽수림, 공원, 정원, 도시 녹지",
        "observation_tips": "나뭇가지를 따라 빠르게 이동하며 '치-chi' 울음. 노란 배·흰 뺨·검은 목줄이 특징입니다. 먹이통·수국숲에서 가까이 관찰 가능합니다.",
        "similar_species": "진박새(더 작음), 새사촌(수풀·울음만 큼·보기 어려움)",
        "description": "한국 전역 공원·숲에서 가장 흔한 박새입니다. 곤충과 씨앗을 먹으며 연중 활발히 움직입니다. 노란 배색이 식별에 유리합니다.",
    },
    "zosterops_japonicus": {
        "habitat": "수목, 정원, 공원, 과수원",
        "observation_tips": "눈 주위 흰색 고리가 가장 큰 특징입니다. 무리로 꽃·곤충을 찾으며, 봄·여름 개화기에 수국·벚꽃 주변에서 관찰하기 좋습니다.",
        "similar_species": "쇠박새(노란 배·목줄), 동박새는 눈 고리·작은 체구",
        "description": "작고 활발한 소형 조류로 정원·공원에서 흔합니다. 눈 주위 흰색 띠로 쉽게 구분되며, 꽃가루와 곤충을 먹습니다.",
    },
    "cettia_diphone": {
        "habitat": "관목숲, 공원 숲, 습지 가장자리",
        "observation_tips": "울음 '치-chi-chi'가 크지만 수풀 속에 숨어 보기 어렵습니다. 새벽·아침에 소리로 위치를 잡고, 쌍안경으로 가장자리 관목을 관찰하세요.",
        "similar_species": "울새(울음 다름), 쇠박새(노란 배·나무 위 활동)",
        "description": "울음은 크지만 은신성이 강한 작은 새입니다. 관목·수풀에서 곤충을 먹으며, 소리로만 존재감을 드러내는 경우가 많습니다.",
    },
    "tachybaptus_ruficollis": {
        "habitat": "연못, 저수지, 용수로, 공원 호수",
        "observation_tips": "작은 체구·짧은 꼬리·잠수 후 다시 떠오르는 모습이 특징입니다. 번식기 목 앞쪽 붉은색, 새끼는 줄무늬를 탑니다.",
        "similar_species": "큰뿔제비(체구 큼), 꼬리물대는 작고 꼬리 짧음",
        "description": "작은 연못·저수지에서 흔한 물새입니다. 잠수하여 작은 물고기를 잡아먹으며, 조용한 물가에서 관찰하기 좋습니다.",
    },
    "phalacrocorax_carbo": {
        "habitat": "해안, 큰 호수, 강 하구",
        "observation_tips": "날개를 펼쳐 말리는 모습, 긴 목·갈고리 부리가 특징입니다. 잠수 후 수면 근처에서 머리만 내미는 모습도 흔합니다.",
        "similar_species": "가마우지(체구·서식지), 뿔제비는 대형·검은 광택",
        "description": "물고기를 잡아먹는 대형 수조입니다. 우수한 잠수 능력을 가지며, 해안과 큰 내수에서 흔합니다. 날개 말리기 행동이 대표적입니다.",
    },
    "hydroprogne_caspia": {
        "habitat": "강 하구, 큰 호수, 연안",
        "observation_tips": "부리 크고 붉으며, 강한 비행과 급강하 사냥을 합니다. 한강 하구·낙동강 하구 등에서 여름철 관찰, 망원렌즈 권장.",
        "similar_species": "갈매기(부리·비행 형태), 황제갈매기는 부리 특대",
        "description": "한국에서 가장 큰 갈매기류 중 하나입니다. 강 하구에서 물고기를 사냥하며, 강력한 비행력으로 알려져 있습니다.",
    },
    "accipiter_gentilis": {
        "habitat": "숲, 산림 가장자리, 넓은 숲",
        "observation_tips": "숲 가장자리에서 빠른 비행·긴 꼬리·짧은 날개가 특징입니다. 망원렌즈로 나무 사이를 관찰하세요. 새매·참매 혼동 주의.",
        "similar_species": "새매(더 작음), 황조롱이(공중 정지·개활지)",
        "description": "산림형 대형 맹금류로 빠르고 민첩한 비행이 특징입니다. 숲 생태계의 최상위 포식자 중 하나입니다.",
    },
    "falco_tinnunculus": {
        "habitat": "개활지, 농경지, 도로변, 해안 절벽",
        "observation_tips": "공중에서 날개·꼬리 각도를 유지하며 '정지(hovering)' 비행이 대표적입니다. 전봇대·전선에 앉아 서식지를 돕기도 합니다.",
        "similar_species": "송골매(체구·무늬), 참매(숲·급비행)",
        "description": "갈색·붉은 톤의 소형 맹금류로 공중 정지 사냥으로 유명합니다. 농경지에서 설치류·곤충을 잡아 생태계에 기여합니다.",
    },
    "caprimulgus_jotaka": {
        "habitat": "소나무숲, 산림, 암석지",
        "observation_tips": "낮에는 나뭇가지에 나무껍질처럼 위장해 휴식, 밤·새벽에 울음. '쿠-쿠-쿠' 울음은 멀리서 들립니다. 손전등 남용 자제.",
        "similar_species": "염주종다리(울음·서식), 솔부엉이는 더 큰 체구",
        "description": "나뭇껍질 위장색을 가진 야행성 조류입니다. 나방 등 야간 곤충을 잡아먹으며, 낮에는 거의 움직이지 않습니다.",
    },
    "athene_noctua": {
        "habitat": "마을, 암석지, 공원, 농가",
        "observation_tips": "작은 체구·눈썹 같은 깃털·노란 눈이 특징. 황혼·밤에 '부-부-' 울음, 낮에도 가끔 나무 구멍·지붕에서 보입니다.",
        "similar_species": "올빼미(체구 큼), 소쩍새는 작고 마을 친화적",
        "description": "마을 근처에서도 볼 수 있는 소형 올빼미입니다. 설치류와 곤충을 잡아먹으며, 농경지에 유익한 포식자입니다.",
    },
    "capreolus_capreolus": {
        "habitat": "산림 가장자리, 초원, 농경지 경계, 숲길",
        "observation_tips": "새벽·황혼에 숲 가장자리·초지에서 조용히 관찰. 큰 소리·손전등 피하기. 수컷은 뿔(번식기), 암컷은 더 작은 체구. 8x42 쌍안경·은은한 옷차림.",
        "similar_species": "고라니(습지·작은 체구·뿔 없음), 노루는 숲·뿔(수컷)",
        "description": "한국 산림·농경지 경계에서 흔한 사슴류입니다. 새벽·저녁 활동이 많으며, 조용한 관찰이 필수입니다. 여름 털은 붉고 겨울은 회색빛입니다.",
    },
    "hydropotes_inermis": {
        "habitat": "갈대밭, 습지, 논두렁, 하천변",
        "observation_tips": "습지·논두렁에서 새벽·저녁 목격. 작은 체구·뿔 없음·짧은 꼬리. 고라니는 '깡-' 경고음 후 달아남. 바람 방향 고려해 접근.",
        "similar_species": "노루(숲·수컷 뿔·체구 큼), 고라니는 습지·무늬 털",
        "description": "한국 고유종 사슴류로 갈대밭·습지에 적응했습니다. 뿔이 없고 작은 체구가 특징이며, 농경지와 자연 습지 경계에서 관찰됩니다.",
    },
    "lutrinae_lutra": {
        "habitat": "맑은 하천, 계곡, 저수지(수질 양호)",
        "observation_tips": "멸종위기종 — 조용히·먼 거리에서 관찰. 물고기 사냥·헤엄·바위 위 휴식 모습. 먹이 주기·접근 금지. 새벽·저녁 활동 많음.",
        "similar_species": "담비(육상·작은 체구), 수달은 물·헤엄",
        "description": "맑은 물에서 서식하는 멸종위기 1급 포유류입니다. 수질 지표종으로 하천 보전의 상징입니다. 관찰 시 생태 교란을 최소화하세요.",
    },
    "melanitta_fusca": {
        "habitat": "해안, 큰 호수, 강 하구",
        "observation_tips": "겨울철 바다·큰 강에서 무리 관찰. 수컷 검은색·노란 부리, 암컷 갈색. 파도가 잔잔한 날 해변·방조제에서 망원렌즈 관찰.",
        "similar_species": "바다오리(종류 다양), 검은머리오리는 큰 부리·겨울철",
        "description": "겨울철 해안 관찰 인기 종으로 바닷가·하구에서 흔합니다. 조개·갑각류를 잠수해 먹으며, 무리로 이동합니다.",
    },
    "emberiza_schoeniclus": {
        "habitat": "갈대밭, 습지, 갯벌 가장자리",
        "observation_tips": "갈대 위·가장자리에서 '지-지-지' 울음. 수컷 검은 머리·흰 목, 암컷 줄무늬. 5~9월 갈대밭 습지 방문, 소음 최소화.",
        "similar_species": "멧쑥새(습지·무늬), 참새(마을·체구·색 다름)",
        "description": "습지 갈대밭의 대표적인 울음새입니다. 번식기 수컷의 검은 머리와 흰 목이 아름답습니다. 습지 보전과 밀접한 종입니다.",
    },
}

EXTRA_ENTRIES: list[dict[str, str]] = [
    {
        "species_id": "pica_pica",
        "title": "까치 vs 어치 구분법",
        "content": "까치(Pica pica)는 흑백 대비가 강하고 꼬리·날개에 강한 청색 반짝임이 적은 경우가 많습니다. 어치(Pica serica)는 한국 산림·공원에 흔하며 날개·꼬리 청색·보라 반짝임이 더 뚜렷합니다. 울음과 행동은 유사하므로 사진에서는 부리·날개 색과 꼬리 길이로 구분하세요.",
    },
    {
        "species_id": "corvus_corone",
        "title": "까마귀 vs 어치·까치",
        "content": "까마귀는 체구가 크고 전체 검은색이며 부리가 두껍습니다. 어치·까치는 상대적으로 작고 꼬리가 길며 흑백(또는 청색) 패턴이 있습니다. 멀리서 실루엣만 보일 때는 크기와 꼬리 길이로 먼저 구분하세요.",
    },
    {
        "species_id": "capreolus_capreolus",
        "title": "노루 vs 고라니 구분",
        "content": "노루는 숲 가장자리·초지에서 흔하고 수컷은 뿔이 있습니다. 고라니는 갈대밭·습지·논두렁에 가깝고 체구가 작으며 뿔이 없습니다. 털 무늬는 계절·조명에 따라 달라 보일 수 있어 서식지와 체형을 함께 확인하세요.",
    },
    {
        "species_id": "falco_tinnunculus",
        "title": "황조롱이 vs 참매·새매",
        "content": "황조롱이는 개활지에서 공중 정지(hovering) 비행을 합니다. 참매·새매는 숲 가장자리에서 빠른 급비행과 긴 꼬리가 특징입니다. 서식지(개활지 vs 숲)와 비행 패턴으로 구분하는 것이 가장 확실합니다.",
    },
    {
        "species_id": "cettia_diphone",
        "title": "새사촌 vs 쇠박새",
        "content": "새사촌은 수풀 속에서 큰 소리로 울지만 보기 어렵습니다. 쇠박새는 노란 배·흰 뺨·검은 목줄이 뚜렷하고 나뭇가지를 따라 잘 보입니다. 소리만 들릴 때는 녹음 후 비교하고, 눈으로 볼 때는 배색·목줄을 확인하세요.",
    },
    {
        "species_id": "passer_montanus",
        "title": "참새 vs 검은머리쑥새",
        "content": "참새는 마을·논·공원에서 흔한 갈색 소형새입니다. 검은머리쑥새는 갈대밭·습지에서 번식하며 수컷 머리가 검고 목이 흰색입니다. 서식지(마을 vs 갈대)와 부리·체색으로 구분하세요.",
    },
    {
        "species_id": "anas_platyrhynchos",
        "title": "청둥오리 식별 포인트",
        "content": "수컷은 번식기 녹색 머리·갈색 가슴·노란 부리, 암컷은 갈색 줄무늬입니다. 비번식기 수컷은 암컷과 비슷해질 수 있습니다. 머리 아래로 물속을 탐색하는 dabbling 행동이 특징입니다.",
    },
    {
        "species_id": "alcedo_atthis",
        "title": "물총새 관찰 장소·시간",
        "content": "맑은 소하천·저수지·농용 수로에서 연중 관찰 가능합니다. 전봇대·돌·나 가지에 앉아 물을 주시하다 급강하합니다. 햇빛이 비치는 날 청록색 깃이 가장 선명합니다.",
    },
    {
        "species_id": "buteo_japonicus",
        "title": "말똥가리 선회 관찰 팁",
        "content": "개활지·농경지·산기슭에서 바람을 타고 넓은 날개로 선회합니다. 한 자리에서 10분 이상 같은 구역을 돌며 사냥할 때가 많습니다. 망원렌즈와 삼각대를 사용하면 날개 패턴 관찰에 유리합니다.",
    },
    {
        "species_id": "parus_minor",
        "title": "쇠박새 관찰 팁",
        "content": "공원·정원에서 연중 활발합니다. 먹이통·수국·은행나무에서 무리 지어 나타나기도 합니다. '치-chi' 울음과 노란 배가 식별에 도움이 됩니다.",
    },
    {
        "species_id": "nycticorax_nycticorax",
        "title": "해오라기 야·황혼 관찰",
        "content": "낮에는 숲·관목에 숨어 쉬므로 저녁·새벽 습지 방문이 유리합니다. 빨간 눈·굽은 목·짧은 다리를 확인하세요. 손전등은 다른 동물과 조류에 스트레스를 줄 수 있어 최소 사용하세요.",
    },
    {
        "species_id": "melanitta_fusca",
        "title": "검은머리오리 겨울철 관찰",
        "content": "11~3월 해안·큰 강·하구에서 무리로 볼 수 있습니다. 파도가 잔잔한 날 방조제·해변에서 망원렌즈로 관찰하세요. 잠수 후 다시 떠오르는 간격으로 먹이를 찾습니다.",
    },
    {
        "species_id": "athene_noctua",
        "title": "소쩍새 야간 관찰 예절",
        "content": "마을·공원에서 황혼·밤 울음이 들릴 수 있습니다. 강한 조명·접근은 번식·서식에 방해가 됩니다. 소리로 위치를 파악한 뒤 멀리서 관찰하세요.",
    },
    {
        "species_id": "hydropotes_inermis",
        "title": "고라니 서식지·행동",
        "content": "갈대밭·습지·논두렁·하천변에서 새벽·저녁에 활동합니다. 경고음 후 빠르게 숨습니다. 노루보다 작고 습지에 가깝게 서식하는 점이 다릅니다.",
    },
    {
        "species_id": "tadorna_tadorna",
        "title": "홍오리 겨울철 갯벌",
        "content": "겨울철 갯벌·하구에서 흰·갈·검 대비가 뚜렷합니다. 무리로 이동하며 조개·식물을 섭식합니다. 조수·간조 시간표와 함께 갯벌 관찰을 계획하세요.",
    },
    {
        "species_id": "motacilla_alba",
        "title": "할미새 꼬리 흔들기",
        "content": "물가·도로·공원에서 꼬리를 위아래로 흔들며 곤충을 잡습니다. 흰색·회색형이 있으며 지역에 따라 겨울에 머무는 개체가 있습니다.",
    },
    {
        "species_id": "zosterops_japonicus",
        "title": "동박새 무리 관찰",
        "content": "봄·여름 꽃·곤충이 많은 정원·공원에서 무리로 나타납니다. 눈 주위 흰색 고리가 가장 확실한 식별점입니다.",
    },
    {
        "species_id": "phalacrocorax_carbo",
        "title": "뿔제비 날개 말리기",
        "content": "잠수 후 바위·부두·나무에 앉아 날개를 펼쳐 말립니다. 깊은 잠수로 물고기를 잡으며, 해안과 큰 호수에서 관찰됩니다.",
    },
    {
        "species_id": "accipiter_gentilis",
        "title": "참매 숲 가장자리",
        "content": "숲 가장자리·넓은 숲에서 빠른 비행으로 나타납니다. 맹금류는 민감하므로 먼 거리에서 관찰하고, 둥지·영역 근처 접근은 피하세요.",
    },
    {
        "species_id": "caprimulgus_jotaka",
        "title": "솔부엉이 야행성",
        "content": "밤·새벽 '쿠-쿠-쿠' 울음, 낮에는 나무에 위장해 휴식합니다. 숲길에서 우연히 발견할 수 있으나, 손전등으로 직접 비추지 마세요.",
    },
    {
        "species_id": "tachybaptus_ruficollis",
        "title": "꼬리물대 연못",
        "content": "작은 연못·저수지에서 잠수·부유를 반복합니다. 번식기 목 앞쪽 붉은색, 새끼는 줄무늬입니다. 조용한 물가에서 관찰하세요.",
    },
    {
        "species_id": "hydroprogne_caspia",
        "title": "황제갈매기 하구",
        "content": "한강·낙동강 하구 등에서 여름철 관찰. 부리가 크고 붉으며 급강하 사냥을 합니다. 강바람이 강한 날은 전망대·다리 위가 유리합니다.",
    },
    {
        "species_id": "turdus_naumanni",
        "title": "딱새 겨울 공원",
        "content": "11~3월 공원·산책로·과수원에서 열매를 먹습니다. 붉은 배·흰 반점·검은 목으로 겨울새 중 식별이 쉬운 편입니다.",
    },
    {
        "species_id": "columba_livia",
        "title": "집비둘기 도심",
        "content": "건물·교량·광장에서 무리 생활합니다. 색형이 다양하므로 AI 식별 시 배경·자세가 혼동 요인이 될 수 있습니다.",
    },
    {
        "species_id": "streptopelia_orientalis",
        "title": "멧비둘기 울음",
        "content": "'우-구-구-구' 울음으로 봄·여름 아침 숲을 채웁니다. 목 뒤 검은 반점과 붉은 눈으로 멧비둘기를 확인하세요.",
    },
]


def apply_species_patches(species: list[dict]) -> int:
    updated = 0
    for item in species:
        patch = SPECIES_PATCHES.get(item["id"])
        if not patch:
            continue
        item.update(patch)
        updated += 1
    return updated


def merge_extra_entries(existing: list[dict], new_entries: list[dict]) -> tuple[list[dict], int]:
    index = {(e.get("species_id"), e.get("title")): i for i, e in enumerate(existing)}
    added = 0
    for entry in new_entries:
        key = (entry.get("species_id"), entry.get("title"))
        if key in index:
            existing[index[key]] = entry
        else:
            existing.append(entry)
            added += 1
    return existing, added


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich species.json and extra.json content")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    species_path = ROOT / "data" / "species.json"
    extra_path = ROOT / "data" / "knowledge" / "extra.json"

    species = json.loads(species_path.read_text(encoding="utf-8"))
    extra = json.loads(extra_path.read_text(encoding="utf-8"))

    species_count = apply_species_patches(species)
    extra, extra_added = merge_extra_entries(extra, EXTRA_ENTRIES)

    print(f"species.json: {species_count}/{len(species)} entries enriched")
    print(f"extra.json: {extra_added} added, {len(extra)} total entries")

    if args.dry_run:
        print("DRY RUN - files not written")
        return

    species_path.write_text(
        json.dumps(species, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    extra_path.write_text(
        json.dumps(extra, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {species_path}")
    print(f"Wrote {extra_path}")


if __name__ == "__main__":
    main()
