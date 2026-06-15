# 학습/추론 전처리 정합성 (#2-3)

## 문제

- **학습(train):** `Resize(256)` → `RandomResizedCrop(224)` → 증강
- **기존 val/추론:** `Resize(224)` 직접 축소 — 학습 시 보는 영역(crop)과 불일치
- `train.py`, `evaluate.py`, `identify.py`에 동일 로직이 **중복 정의**되어 drift 위험

## 해결

`models/image_transforms.py`를 단일 소스로 두고 아래 모듈이 **동일한 eval 파이프라인**을 사용합니다.

```
Resize(256) → CenterCrop(224) → ToTensor → ImageNet Normalize
```

| 모듈 | 용도 |
|------|------|
| `models/image_transforms.py` | 전처리 정의 (SSOT) |
| `models/train.py` | train 증강 / **val 평가** |
| `models/evaluate.py` | 오프라인 평가 |
| `backend/app/services/identify.py` | API 실시간 추론 |

Backend는 `backend/app/services/image_transforms.py` 래퍼로 `models/` 정의를 import합니다.

## 검증 결과 (val 510장, 기존 checkpoint)

| 파이프라인 | Accuracy | Macro F1 |
|------------|----------|----------|
| **이전** `Resize(224)` | 71.37% | 71.49% |
| **통일** `Resize(256)+CenterCrop(224)` | **74.71%** | **74.78%** |
| **개선** | **+3.33%p** | **+3.29%p** |

상세 수치: `reports/preprocess_comparison.json`

## 운영 참고

- 현재 `best_model.pth`의 `val_acc`(71.37%)는 **구 val 전처리** 기준으로 학습·저장된 값입니다.
- API 추론은 **새 파이프라인**을 사용하므로, 실사용 정확도는 evaluate 재측정치(~74.7%)에 더 가깝습니다.
- **재학습** 시 `train.py` val도 동일 파이프라인을 쓰므로 checkpoint `val_acc`와 evaluate/API 결과가 일치합니다.

## 재검증 명령

```powershell
cd models
..\backend\.venv\Scripts\python evaluate.py --data-dir ../data/images/val --checkpoint checkpoints/best_model.pth --output ../reports --skip-misclassification-analysis
```

`metrics.json`의 `preprocess_version` 필드가 `resize256_centercrop224`인지 확인하세요.
