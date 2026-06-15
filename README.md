# WildTrail

> 사진·소리로 야생동물을 식별하고, 도감·관찰지·여행 일정까지 한 번에 — 생태 관광 MVP

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](backend/)
[![React](https://img.shields.io/badge/UI-React-61DAFB)](frontend/)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch-EE4C2C)](models/)

---

## 한 줄 소개

**WildTrail**은 촬영한 사진(또는 소리)으로 동물 종을 추정하고, RAG 도감 질의, Leaflet 관찰지 지도, 맞춤 여행 플래너를 제공하는 **교육·포트폴리오용 생태 관광 플랫폼**입니다.

---

## 스크린샷

> Git 저장소에는 UI 스크린샷이 포함되지 않습니다. 로컬 실행 후 `docs/images/`에 캡처를 추가하세요. (가이드: [docs/images/README.md](docs/images/README.md))

| 식별 | 도감 RAG | 관찰지 지도 | 여행 일정 |
|------|----------|-------------|-----------|
| *(로컬 캡처)* | *(로컬 캡처)* | *(로컬 캡처)* | *(로컬 캡처)* |

3분 발표 시나리오: **[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)**

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **이미지 식별** | EfficientNet-B0, 29종 CNN (모델 없으면 stub 데모) |
| **오디오 식별** | librosa 스펙트로그램 분석 + stub (학습 모델 선택) |
| **도감 RAG** | TF-IDF 검색 + OpenAI 요약 (키 없으면 템플릿) |
| **관찰지 지도** | Leaflet + `hotspots.json` 핫스팟 |
| **여행 플래너** | 규칙 기반 일정·경비 + LLM 요약 (선택) |
| **관찰 기록** | SQLite sightings 타임라인 |

---

## 아키텍처

```mermaid
flowchart LR
  subgraph Client
    UI[React + Vite + Tailwind]
    Map[Leaflet Map]
  end
  subgraph API[FastAPI Backend]
    ID[Identify CNN]
    RAG[RAG + LLM]
    Trip[Trip Planner]
    DB[(SQLite)]
  end
  subgraph ML[Models]
    CKPT[best_model.pth]
    Train[train.py / evaluate.py]
  end
  subgraph Data
    JSON[species.json / hotspots.json]
    IMG[data/images]
  end
  UI --> API
  Map --> API
  ID --> CKPT
  RAG --> JSON
  Trip --> DB
  API --> DB
  Train --> IMG
  Train --> CKPT
```

상세: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 빠른 시작 (15분)

Windows PowerShell 기준. **모델 파일·학습 이미지는 Git에 없습니다** — clone 직후에는 이미지 식별이 **stub(데모) 모드**입니다.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend (새 터미널)

```powershell
cd frontend
npm install
npm run dev
```

### 3. 동작 확인

| URL | 기대 결과 |
|-----|-----------|
| http://127.0.0.1:5173 | WildTrail UI |
| http://127.0.0.1:8000/health | `image_model`, `species_json_count` 등 |
| http://127.0.0.1:8000/docs | Swagger API |

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json -Depth 5
```

### 4. (선택) 학습 모델 연결

`models/checkpoints/best_model.pth`를 배치하거나 직접 학습한 뒤 `backend/.env`:

```env
MODEL_PATH=../models/checkpoints/best_model.pth
```

백엔드 재시작 → `/health`의 `image_model.model_loaded: true`, 식별 결과 `source: "model"`.

### 포트 충돌 시

```powershell
# 8000 점유 프로세스 확인
netstat -ano | findstr :8000
# PID 종료 후 uvicorn 재시작
```

---

## Git에 없는 것 (clone 후 별도 준비)

| 항목 | 경로 | 용도 |
|------|------|------|
| 학습 이미지 | `data/images/` | CNN 학습·식별 |
| 모델 가중치 | `models/checkpoints/best_model.pth` | 이미지 식별 |
| OpenAI 키 | `backend/.env` | RAG·여행 LLM |
| UI 스크린샷 | `docs/images/` | README·발표 |

---

## What Works / What Doesn't

| 기능 | clone 직후 | 데이터+모델 후 | `OPENAI_API_KEY` 후 |
|------|------------|----------------|---------------------|
| 이미지 식별 | stub (데모) | **AI 모델** (29종) | AI 모델 |
| 오디오 식별 | 분석 + stub | 분석 + stub | 분석 + stub |
| 도감 조회 | ✅ | ✅ | ✅ |
| RAG Q&A | 템플릿 | 템플릿 | **LLM** |
| 여행 플래너 | 규칙 엔진 | 규칙 엔진 | LLM 요약 |
| 관찰지 지도 | ✅ | ✅ | ✅ |
| 관찰 기록 | ✅ | ✅ | ✅ |

---

## 환경 변수

`backend/.env.example` → `.env` 복사:

| 변수 | 필수 | 설명 |
|------|------|------|
| `DATABASE_URL` | | SQLite 경로 (기본 `sqlite:///./wildtrail.db`) |
| `MODEL_PATH` | | 이미지 모델 checkpoint (기본 `../models/checkpoints/best_model.pth`) |
| `OPENAI_API_KEY` | 선택 | 도감 RAG·여행 LLM |
| `OPENAI_MODEL` | | 기본 `gpt-4o-mini` |
| `CORS_ORIGINS` | | 프론트 URL (기본 `http://localhost:5173`) |
| `MAX_IMAGE_MB` | | 업로드 제한 (기본 10) |
| `MAX_AUDIO_MB` | | 기본 20 |
| `MAX_VIDEO_MB` | | 기본 50 |

---

## API 예시

```powershell
# 도감 목록
Invoke-RestMethod http://127.0.0.1:8000/api/v1/species

# 이미지 식별 (PowerShell 7+)
$form = @{ file = Get-Item ".\sample.jpg" }
Invoke-RestMethod http://127.0.0.1:8000/api/v1/identify/image -Method Post -Form $form

# 여행 일정
$body = @{
  species_id = "grus_japonensis"
  origin = "서울"
  days = 2
  travelers = 2
  budget_krw = 300000
  preferences = @{ transport = "public"; accommodation = "guesthouse" }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/v1/trips/plan -Method Post -Body $body -ContentType "application/json"
```

---

## 학습 데이터 준비 & 모델 학습

```powershell
cd models
python prepare_dataset.py init
python prepare_dataset.py validate --dir ../data/images/raw
python prepare_dataset.py split --raw-dir ../data/images/raw --out-dir ../data/images --copy
python validate_coverage.py --strict
python train.py --data-dir ../data/images --epochs 15
python evaluate.py --data-dir ../data/images/val --checkpoint checkpoints/best_model.pth --output ../reports
```

| 문서 | 내용 |
|------|------|
| [DATA_COLLECTION_GUIDE.md](docs/DATA_COLLECTION_GUIDE.md) | 이미지 수집 |
| [HARD_NEGATIVE_GUIDE.md](docs/HARD_NEGATIVE_GUIDE.md) | 유사 종 보강 |
| [ML_EVAL_REPORT.md](docs/ML_EVAL_REPORT.md) | 평가·오분류 분석 |
| [models/README.md](models/README.md) | ML 스크립트 요약 |

---

## 현재 한계 (Known Limitations)

- **식별 종 수:** 학습 모델 **29종** (`species.json` 31종 — 홍오리·수달 데이터·모델 미포함)
- **이미지 정확도:** checkpoint val **~71%**, 통일 전처리 evaluate **~75%** (데이터·유사종에 따라 변동)
- **오디오/영상:** 오디오 CNN 미학습, 영상 식별은 Phase 2 stub
- **공공 API:** 일부 지역정보·날씨는 스텁 응답
- **동기 추론:** PyTorch 추론이 API 스레드에서 동기 실행 (MVP 수준)

---

## 프로젝트 구조

```
WildTrail/
├── backend/          # FastAPI, SQLite, RAG, 식별 서비스
├── frontend/         # React + Vite + Tailwind + Leaflet
├── data/             # species.json, hotspots.json, images/
├── models/           # train.py, evaluate.py, checkpoints/
├── reports/          # ML 평가 산출물 (로컬 생성)
└── docs/             # 아키텍처, 수집·데모 가이드
```

---

## 로드맵

- [x] P0: DB 시드 upsert, `/health`, 업로드 검증, 로깅
- [x] P1: evaluate.py, 오분류 분석, 전처리 정합성, 커버리지 검증
- [ ] hard negative 수집 후 재학습 (까치/어치·노루/고라니 등)
- [ ] 오디오 CNN 학습 (`train_audio.py`)
- [ ] 영상 YOLO 파이프라인
- [ ] PostGIS 거리 기반 핫스팟 정렬

---

## 문서 목록

| 문서 | 설명 |
|------|------|
| [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 3분 발표 시나리오 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 시스템 설계 |
| [MIGRATION.md](docs/MIGRATION.md) | DB 시드 마이그레이션 |
| [PREPROCESS_ALIGNMENT.md](docs/PREPROCESS_ALIGNMENT.md) | 학습/추론 전처리 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 기여 가이드 |

---

## 라이선스 & 데이터 출처

- **코드:** [MIT License](LICENSE)
- **이미지 데이터:** 직접 촬영·AI Hub·iNaturalist(CC)·Wikimedia(CC) 등 — 출처·라이선스는 `data/images/sources.csv` 권장 ([수집 가이드](docs/DATA_COLLECTION_GUIDE.md))
- **멸종위기·보호종:** 관찰 거리·보호구역 규정 준수. 출현은 보장되지 않습니다.

---

## 기여

이슈·PR 환영합니다. [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.
