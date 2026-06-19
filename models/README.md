# WildTrail ML Models

> **Windows:** `python` 대신 `backend/.venv`의 Python을 사용하세요. (`torch` 등 ML 패키지가 여기 설치됩니다.)

```powershell
cd models
# 방법 1 — 래퍼 스크립트 (권장)
.\ml.ps1 evaluate.py --output ..\reports

# 방법 2 — venv Python 직접 호출
..\backend\.venv\Scripts\python evaluate.py --output ..\reports
```

가상환경이 없다면:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 1. 데이터 준비

```bash
python prepare_dataset.py init
python prepare_dataset.py validate --dir ../data/images/raw
python prepare_dataset.py split --raw-dir ../data/images/raw --out-dir ../data/images --copy
python prepare_dataset.py report --dir ../data/images
```

## 2. 이미지 분류 학습

```bash
python prepare_dataset.py report --dir ../data/images
python validate_coverage.py --data-dir ../data/images --checkpoint checkpoints/best_model.pth --strict
python train.py --data-dir ../data/images --epochs 15
```

→ `checkpoints/best_model.pth` → backend `.env` `MODEL_PATH`

## 2-1. 모델 평가 (confusion matrix)

```bash
python evaluate.py --data-dir ../data/images/val --checkpoint checkpoints/best_model.pth --output ../reports
```

산출물:
- `reports/metrics.json` — accuracy, macro/weighted F1
- `reports/confusion_matrix.csv`
- `reports/per_class_report.csv`
- `reports/confusion_matrix.png`

오분류 분석(Top 10 쌍, 샘플 복사, `docs/ML_EVAL_REPORT.md`)도 함께 생성됩니다.

전처리는 `models/image_transforms.py`에서 단일 정의됩니다 (`Resize(256)` + `CenterCrop(224)`).

## 2-4. 클래스 커버리지 검증

학습 전 `species.json` ↔ train/val ↔ checkpoint 일치 여부를 확인합니다.

```bash
python validate_coverage.py --data-dir ../data/images --checkpoint checkpoints/best_model.pth
python validate_coverage.py --strict   # CI/학습 전 게이트 (불일치 시 exit 1)
```

산출물: `reports/coverage_report.json`

## 2-5. Hard negative 데이터 보강

유사 종 쌍별 추가 수집 계획·진행 추적:

```bash
python hard_negative_report.py
python hard_negative_report.py --save-baseline
python prepare_dataset.py hard-negative
```

가이드: [docs/HARD_NEGATIVE_GUIDE.md](../docs/HARD_NEGATIVE_GUIDE.md)

## 2-6. Checkpoint 메타데이터

학습 시 `model_version`, `trained_at`, `dataset_fingerprint` 등이 checkpoint에 저장됩니다.

```bash
# 기존 checkpoint 소급 적용
python stamp_checkpoint.py --checkpoint checkpoints/best_model.pth --data-dir ../data/images
```

`/health` 응답의 `image_model`에 `model_version`, `val_acc`, `preprocess_version` 노출.

## 3. 오디오 분류 학습

```powershell
cd models

# 1) train → val 분리 (최초 1회 또는 재분리 시)
.\ml.ps1 split_audio.py --data-dir ..\data\audio --dry-run   # 계획 확인
.\ml.ps1 split_audio.py --data-dir ..\data\audio --clear-val

# 2) 학습
.\ml.ps1 train_audio.py --data-dir ..\data\audio --epochs 20
```

`split_audio.py` 옵션:
- `--val-ratio 0.2` — 검증 비율 (기본 20%)
- `--copy` — 이동 대신 복사 (train 원본 유지)
- `--source raw` — `data/audio/raw/`에서 train+val 생성
- `--report ../reports/audio_split_report.json` — JSON 리포트 저장

→ `checkpoints/best_audio_model.pth` (백엔드 자동 로드)

## 가이드

- [docs/DATA_COLLECTION_GUIDE.md](../docs/DATA_COLLECTION_GUIDE.md)
- [data/audio/README.md](../data/audio/README.md)
