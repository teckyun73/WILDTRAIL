# Hard Negative 데이터 보강 가이드 (#2-5)

오분류가 잦은 **유사 종 쌍**에 대해 추가 이미지를 수집하고, 재학습 후 혼동률 개선을 측정하는 절차입니다.

## 1. 대상 쌍 (dataset_manifest.json)

`data/dataset_manifest.json`의 `confusion_pairs`에 정의되어 있습니다.

| 우선순위 | 쌍 | baseline 혼동률 | 종당 추가 목표 |
|----------|-----|-----------------|----------------|
| high | 까치 ↔ 어치 | **5.7%** (2건) | +50장 |
| high | 어치 ↔ 까마귀 | 5.9% | +50장 |
| high | 노루 ↔ 고라니 | **16.7%** | +50장 |
| high | 황조롱이 ↔ 참매 | 8.6% | +50장 |
| high | 새사촌 ↔ 쇠박새 | 11.1% | +40장 |
| medium | 까치 ↔ 까마귀 | 2.9% | +40장 |
| medium | 참새 ↔ 검은머리쑥새 | 8.8% | +40장 |
| medium | 말똥가리 ↔ 참매 | 5.7% | +30장 |

> `target_extra`는 **raw/** 폴더 기준 추가 수집 목표입니다.

## 2. 수집 원칙

1. **양쪽 종 모두** 같은 수준으로 보강 (한쪽만 추가하면 편향 발생)
2. **구분이 어려운 각도** 우선: 측면, 원거리, 유사 배경
3. **클로즈업**으로 부리·깃 패턴·체급 차이가 드러나는 샷 포함
4. `reports/misclassified_samples/`의 오분류 예시를 참고해 비슷한 상황 재촬영

### 쌍별 팁 (manifest `collection_tips` 요약)

- **까치/어치:** 날개 청색 패턴(어치), 흑백 대비(까치), 같은 배경 연속 촬영
- **어치/까마귀:** 체급·꼬리 길이·부리 크기 차이가 보이는 구도
- **노루/고라니:** 전신 실루엣, 서식지(숲 가장자리 vs 갈대밭) 차이
- **맹금류:** 비행 자세(선회 vs 급강하), 서식지 배경

## 3. 진행 확인

```bash
cd models
python hard_negative_report.py
# 또는
python prepare_dataset.py hard-negative
```

출력 예시:
- `raw=90/50 gap=0` → 해당 종은 추가 목표 달성
- `gap=25` → raw에 25장 더 필요

산출물: `reports/hard_negative_progress.json`

## 4. baseline 저장 (재학습 전)

```bash
python hard_negative_report.py --save-baseline
```

→ `reports/hard_negative_baseline.json` (현재 혼동률·accuracy 스냅샷)

## 5. 재학습 워크플로

```bash
# 1) raw에 이미지 추가 후
python prepare_dataset.py validate --dir ../data/images/raw
python prepare_dataset.py hard-negative
python prepare_dataset.py split --raw-dir ../data/images/raw --out-dir ../data/images --copy --clear
python validate_coverage.py --strict
python train.py --data-dir ../data/images --epochs 15
python evaluate.py --output ../reports

# 2) 개선율 비교
python hard_negative_report.py --compare-baseline ../reports/hard_negative_baseline.json
```

## 6. 완료 기준

- 각 쌍 **combined_confusion_rate 20% 이상 감소** (baseline 대비)
- 예: 노루↔고라니 16.7% → **13.4% 이하** 목표
- `ML_EVAL_REPORT.md`에 before/after 표 추가 (compare 명령 출력 참고)

## 7. 관련 파일

| 파일 | 용도 |
|------|------|
| `data/dataset_manifest.json` | 쌍 정의·목표·baseline |
| `models/hard_negative_report.py` | 진행·비교 리포트 |
| `reports/hard_negative_baseline.json` | 재학습 전 스냅샷 |
| `reports/hard_negative_progress.json` | 최신 수집 현황 |
| `reports/misclassified_samples/` | 오분류 예시 이미지 |
