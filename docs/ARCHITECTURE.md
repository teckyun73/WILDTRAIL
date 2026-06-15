# WildTrail 아키텍처

## 개요

WildTrail은 **식별 → 도감 → 관찰지 → 여행** 사용자 여정을 한 UI에서 제공하는 생태 관광 MVP입니다.

## 구성 요소

```text
Frontend (React + Vite + Tailwind + Leaflet)
    ↓ REST /api/v1
Backend (FastAPI)
    ├── IdentifyService      # EfficientNet-B0 / stub
    ├── AudioIdentifyService # librosa + stub
    ├── EncyclopediaRAG      # TF-IDF + optional OpenAI
    ├── TripPlannerService   # rules + optional LLM
    ├── Species / Hotspot / Sighting (SQLAlchemy)
    └── seed upsert (species.json, hotspots.json)
Data
    ├── species.json (31종 메타)
    ├── hotspots.json
    └── images/ (Git 제외, ImageFolder)
Models
    ├── train.py / evaluate.py / validate_coverage.py
    ├── image_transforms.py (학습·추론 전처리 SSOT)
    └── checkpoints/ (Git 제외)
```

## API (주요)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 모델·DB·OpenAI 상태 |
| POST | `/api/v1/identify/image` | 이미지 식별 (`source`: model/stub) |
| POST | `/api/v1/identify/audio` | 오디오 식별 |
| POST | `/api/v1/encyclopedia/ask` | RAG Q&A |
| GET | `/api/v1/species` | 도감 목록 |
| GET | `/api/v1/species/{id}` | 도감 상세 |
| GET | `/api/v1/locations` | 관찰 핫스팟 |
| POST | `/api/v1/trips/plan` | 여행 일정 |
| GET/POST | `/api/v1/sightings` | 관찰 기록 |

## ML 파이프라인

```text
raw/ → split → train/val → train.py → best_model.pth
                              ↓
                    evaluate.py → reports/
                    misclassification_analysis → ML_EVAL_REPORT.md
```

- 전처리: `Resize(256) + CenterCrop(224)` ([PREPROCESS_ALIGNMENT.md](./PREPROCESS_ALIGNMENT.md))
- 커버리지: `validate_coverage.py --strict` (학습 전)
- checkpoint 메타: `model_version`, `dataset_fingerprint` ([models/README.md](../models/README.md))

## Phase 2+

- 오디오 CNN (`train_audio.py`)
- 영상 YOLO 파이프라인
- PostGIS 거리 기반 핫스팟
- 비동기 추론 큐 (Celery/Redis)

## 관련 문서

- [README.md](../README.md)
- [DEMO_SCRIPT.md](./DEMO_SCRIPT.md)
- [MIGRATION.md](./MIGRATION.md)
