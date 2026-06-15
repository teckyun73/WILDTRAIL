# WildTrail ML Evaluation Report

> 자동 생성: `2026-06-15T06:20:20.164028+00:00`

## 1. 요약

| 지표 | 값 |
|------|-----|
| Accuracy | 71.37% |
| Macro F1 | 71.49% |
| Weighted F1 | 71.51% |
| 클래스 수 | 29 |
| 검증 샘플 | 510 |
| Checkpoint val_acc | 0.7137254901960784 |

관련 산출물:
- `reports/metrics.json`
- `reports/confusion_matrix.csv` / `.png`
- `reports/per_class_report.csv`
- `reports/misclassification_pairs.json`
- `reports/misclassified_samples/`

## 2. Top 10 오분류 쌍

| 순위 | 실제 종 | 예측 종 | 건수 | 실제 종 기준 비율 |
|------|---------|---------|------|-------------------|
| 1 | 노루 (`capreolus_capreolus`) | 고라니 (`hydropotes_inermis`) | 5 | 27.8% |
| 2 | 새사촌 (`cettia_diphone`) | 쇠박새 (`parus_minor`) | 4 | 22.2% |
| 3 | 황조롱이 (`falco_tinnunculus`) | 참매 (`accipiter_gentilis`) | 4 | 22.2% |
| 4 | 참새 (`passer_montanus`) | 검은머리쑥새 (`emberiza_schoeniclus`) | 3 | 17.6% |
| 5 | 참매 (`accipiter_gentilis`) | 새사촌 (`cettia_diphone`) | 2 | 11.8% |
| 6 | 물총새 (`alcedo_atthis`) | 노루 (`capreolus_capreolus`) | 2 | 11.8% |
| 7 | 청둥오리 (`anas_platyrhynchos`) | 검은머리오리 (`melanitta_fusca`) | 2 | 11.8% |
| 8 | 말똥가리 (`buteo_japonicus`) | 참매 (`accipiter_gentilis`) | 2 | 11.1% |
| 9 | 솔부엉이 (`caprimulgus_jotaka`) | 소쩍새 (`athene_noctua`) | 2 | 11.1% |
| 10 | 황새 (`ciconia_boyciana`) | 해오라기 (`nycticorax_nycticorax`) | 2 | 11.1% |

## 3. 유사 종 혼동 분석

### 까치 (`pica_pica`) vs 어치 (`pica_serica`)

| 항목 | 값 |
|------|-----|
| pica_pica 검증 샘플 | 18 |
| pica_serica 검증 샘플 | 17 |
| pica_pica → pica_serica | 0 (0.0%) |
| pica_serica → pica_pica | 0 (0.0%) |
| 양방향 합계 | 0 |
| 전체 대비 혼동률 | 0.0% |

### 까치 (`pica_pica`) vs 까마귀 (`corvus_corone`)

| 항목 | 값 |
|------|-----|
| pica_pica 검증 샘플 | 18 |
| corvus_corone 검증 샘플 | 17 |
| pica_pica → corvus_corone | 0 (0.0%) |
| corvus_corone → pica_pica | 1 (5.9%) |
| 양방향 합계 | 1 |
| 전체 대비 혼동률 | 2.9% |

### 어치 (`pica_serica`) vs 까마귀 (`corvus_corone`)

| 항목 | 값 |
|------|-----|
| pica_serica 검증 샘플 | 17 |
| corvus_corone 검증 샘플 | 17 |
| pica_serica → corvus_corone | 2 (11.8%) |
| corvus_corone → pica_serica | 0 (0.0%) |
| 양방향 합계 | 2 |
| 전체 대비 혼동률 | 5.9% |

### 노루 (`capreolus_capreolus`) vs 고라니 (`hydropotes_inermis`)

| 항목 | 값 |
|------|-----|
| capreolus_capreolus 검증 샘플 | 18 |
| hydropotes_inermis 검증 샘플 | 18 |
| capreolus_capreolus → hydropotes_inermis | 5 (27.8%) |
| hydropotes_inermis → capreolus_capreolus | 1 (5.6%) |
| 양방향 합계 | 6 |
| 전체 대비 혼동률 | 16.7% |

### 참새 (`passer_montanus`) vs 쇠박새 (`parus_minor`)

| 항목 | 값 |
|------|-----|
| passer_montanus 검증 샘플 | 17 |
| parus_minor 검증 샘플 | 18 |
| passer_montanus → parus_minor | 0 (0.0%) |
| parus_minor → passer_montanus | 0 (0.0%) |
| 양방향 합계 | 0 |
| 전체 대비 혼동률 | 0.0% |

## 4. 종별 취약 지표 (F1 < 0.80)

| 종 | Precision | Recall | F1 | Support |
|----|-----------|--------|----|---------|
| 참매 (`accipiter_gentilis`) | 0.39 | 0.65 | 0.49 | 17 |
| 황조롱이 (`falco_tinnunculus`) | 0.62 | 0.44 | 0.52 | 18 |
| 참새 (`passer_montanus`) | 0.73 | 0.47 | 0.57 | 17 |
| 딱새 (`turdus_naumanni`) | 0.67 | 0.56 | 0.61 | 18 |
| 할미새 (`motacilla_alba`) | 0.57 | 0.67 | 0.62 | 18 |
| 청둥오리 (`anas_platyrhynchos`) | 0.67 | 0.59 | 0.62 | 17 |
| 해오라기 (`nycticorax_nycticorax`) | 0.63 | 0.67 | 0.65 | 18 |
| 쇠박새 (`parus_minor`) | 0.56 | 0.78 | 0.65 | 18 |
| 멧비둘기 (`streptopelia_orientalis`) | 1.00 | 0.50 | 0.67 | 18 |
| 소쩍새 (`athene_noctua`) | 0.65 | 0.72 | 0.68 | 18 |
| 새사촌 (`cettia_diphone`) | 0.65 | 0.72 | 0.68 | 18 |
| 황새 (`ciconia_boyciana`) | 0.71 | 0.67 | 0.69 | 18 |
| 까마귀 (`corvus_corone`) | 0.65 | 0.76 | 0.70 | 17 |
| 노루 (`capreolus_capreolus`) | 0.75 | 0.67 | 0.71 | 18 |
| 황제갈매기 (`hydroprogne_caspia`) | 0.71 | 0.71 | 0.71 | 17 |
| 고라니 (`hydropotes_inermis`) | 0.62 | 0.83 | 0.71 | 18 |
| 검은머리쑥새 (`emberiza_schoeniclus`) | 0.75 | 0.71 | 0.73 | 17 |
| 뿔제비 (`phalacrocorax_carbo`) | 0.75 | 0.71 | 0.73 | 17 |
| 집비둘기 (`columba_livia`) | 0.76 | 0.76 | 0.76 | 17 |
| 쇠백로 (`egretta_garzetta`) | 0.76 | 0.76 | 0.76 | 17 |
| 어치 (`pica_serica`) | 0.76 | 0.76 | 0.76 | 17 |

## 5. 데이터 보강 권장

- **노루 (`capreolus_capreolus`) → 고라니 (`hydropotes_inermis`)** (5건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **새사촌 (`cettia_diphone`) → 쇠박새 (`parus_minor`)** (4건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **황조롱이 (`falco_tinnunculus`) → 참매 (`accipiter_gentilis`)** (4건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **참새 (`passer_montanus`) → 검은머리쑥새 (`emberiza_schoeniclus`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **참매 (`accipiter_gentilis`) → 새사촌 (`cettia_diphone`)** (2건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **참매 (`accipiter_gentilis`)** (F1=0.49, val=17장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **황조롱이 (`falco_tinnunculus`)** (F1=0.52, val=18장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **참새 (`passer_montanus`)** (F1=0.57, val=17장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **딱새 (`turdus_naumanni`)** (F1=0.61, val=18장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **할미새 (`motacilla_alba`)** (F1=0.62, val=18장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가

## 6. 오분류 샘플 복사

대표 오분류 이미지 **24장**을 `reports/misclassified_samples/`에 저장했습니다.

| 실제 종 | 예측 종 | confidence | 파일 |
|---------|---------|------------|------|
| capreolus_capreolus → hydropotes_inermis | | 0.920 | `capreolus capreolus_37_conf0.920.jpg` |
| capreolus_capreolus → hydropotes_inermis | | 0.858 | `capreolus capreolus_33_conf0.858.jpg` |
| capreolus_capreolus → hydropotes_inermis | | 0.637 | `capreolus capreolus_82_conf0.637.jpg` |
| cettia_diphone → parus_minor | | 0.855 | `cettia diphone_26_conf0.855.jpg` |
| cettia_diphone → parus_minor | | 0.806 | `cettia diphone_22_conf0.806.jpg` |
| cettia_diphone → parus_minor | | 0.764 | `cettia diphone_38_conf0.764.jpg` |
| falco_tinnunculus → accipiter_gentilis | | 0.647 | `falco tinnunculus_54_conf0.647.jpg` |
| falco_tinnunculus → accipiter_gentilis | | 0.587 | `falco tinnunculus_42_conf0.587.jpg` |
| falco_tinnunculus → accipiter_gentilis | | 0.405 | `falco tinnunculus_81_conf0.405.jpg` |
| passer_montanus → emberiza_schoeniclus | | 0.712 | `passer montanus_20_conf0.712.jpg` |
| passer_montanus → emberiza_schoeniclus | | 0.656 | `passer montanus_75_conf0.656.jpg` |
| passer_montanus → emberiza_schoeniclus | | 0.488 | `passer montanus_25_conf0.488.jpg` |
| accipiter_gentilis → cettia_diphone | | 0.372 | `accipiter gentilis_27_conf0.372.jpg` |
| accipiter_gentilis → cettia_diphone | | 0.233 | `accipiter gentilis_7_conf0.233.jpg` |
| alcedo_atthis → capreolus_capreolus | | 0.406 | `alcedo atthis_72_conf0.406.jpg` |
| alcedo_atthis → capreolus_capreolus | | 0.249 | `alcedo atthis_31_conf0.249.jpg` |
| anas_platyrhynchos → melanitta_fusca | | 0.815 | `anas platyrhynchos_68_conf0.815.jpg` |
| anas_platyrhynchos → melanitta_fusca | | 0.565 | `anas platyrhynchos_75_conf0.565.jpg` |
| buteo_japonicus → accipiter_gentilis | | 0.644 | `buteo japonicus_89_conf0.644.jpg` |
| buteo_japonicus → accipiter_gentilis | | 0.492 | `buteo japonicus_56_conf0.492.jpg` |
| ... | | | 외 4장 |

## 7. Hard Negative 보강 계획 (#2-5)

재학습 전 baseline 저장: `reports/hard_negative_baseline.json` (accuracy **74.71%**, preprocess `resize256_centercrop224`)

| 쌍 | baseline 혼동률 | 추가 수집(종당) | 우선순위 |
|----|----------------|-----------------|----------|
| 까치 ↔ 어치 | **5.7%** (2건) | +50장 | high |
| 노루 ↔ 고라니 | 16.7% | +50장 | high |
| 어치 ↔ 까마귀 | 5.9% | +50장 | high |
| 황조롱이 ↔ 참매 | 8.6% | +50장 | high |
| 새사촌 ↔ 쇠박새 | 11.1% | +40장 | high |

진행 확인: `python models/hard_negative_report.py`  
상세 가이드: [docs/HARD_NEGATIVE_GUIDE.md](./HARD_NEGATIVE_GUIDE.md)
