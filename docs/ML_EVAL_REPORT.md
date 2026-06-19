# WildTrail ML Evaluation Report

> 자동 생성: `2026-06-18T17:23:48.667592+00:00`

## 1. 요약

| 지표 | 값 |
|------|-----|
| Accuracy | 83.56% |
| Macro F1 | 82.87% |
| Weighted F1 | 83.55% |
| 클래스 수 | 30 |
| 검증 샘플 | 827 |
| Checkpoint val_acc | 0.8355501813784765 |

관련 산출물:
- `reports/metrics.json`
- `reports/confusion_matrix.csv` / `.png`
- `reports/per_class_report.csv`
- `reports/misclassification_pairs.json`
- `reports/misclassified_samples/`

## 2. Top 10 오분류 쌍

| 순위 | 실제 종 | 예측 종 | 건수 | 실제 종 기준 비율 |
|------|---------|---------|------|-------------------|
| 1 | 황조롱이 (`falco_tinnunculus`) | 참매 (`accipiter_gentilis`) | 7 | 25.0% |
| 2 | 고라니 (`hydropotes_inermis`) | 노루 (`capreolus_capreolus`) | 7 | 25.0% |
| 3 | 쇠박새 (`parus_minor`) | 어치 (`pica_serica`) | 4 | 14.3% |
| 4 | 말똥가리 (`buteo_japonicus`) | 참매 (`accipiter_gentilis`) | 3 | 10.7% |
| 5 | 새사촌 (`cettia_diphone`) | 동박새 (`zosterops_japonicus`) | 3 | 10.7% |
| 6 | 까마귀 (`corvus_corone`) | 해오라기 (`nycticorax_nycticorax`) | 3 | 10.7% |
| 7 | 검은머리쑥새 (`emberiza_schoeniclus`) | 새사촌 (`cettia_diphone`) | 3 | 10.7% |
| 8 | 뿔제비 (`phalacrocorax_carbo`) | 황새 (`ciconia_boyciana`) | 3 | 10.7% |
| 9 | 청둥오리 (`anas_platyrhynchos`) | 꼬리물대 (`tachybaptus_ruficollis`) | 2 | 7.1% |
| 10 | 소쩍새 (`athene_noctua`) | 어치 (`pica_serica`) | 2 | 7.1% |

## 3. 유사 종 혼동 분석

### 까치 (`pica_pica`) vs 어치 (`pica_serica`)

| 항목 | 값 |
|------|-----|
| pica_pica 검증 샘플 | 28 |
| pica_serica 검증 샘플 | 17 |
| pica_pica → pica_serica | 2 (7.1%) |
| pica_serica → pica_pica | 2 (11.8%) |
| 양방향 합계 | 4 |
| 전체 대비 혼동률 | 8.9% |

### 까치 (`pica_pica`) vs 까마귀 (`corvus_corone`)

| 항목 | 값 |
|------|-----|
| pica_pica 검증 샘플 | 28 |
| corvus_corone 검증 샘플 | 28 |
| pica_pica → corvus_corone | 0 (0.0%) |
| corvus_corone → pica_pica | 0 (0.0%) |
| 양방향 합계 | 0 |
| 전체 대비 혼동률 | 0.0% |

### 어치 (`pica_serica`) vs 까마귀 (`corvus_corone`)

| 항목 | 값 |
|------|-----|
| pica_serica 검증 샘플 | 17 |
| corvus_corone 검증 샘플 | 28 |
| pica_serica → corvus_corone | 0 (0.0%) |
| corvus_corone → pica_serica | 2 (7.1%) |
| 양방향 합계 | 2 |
| 전체 대비 혼동률 | 4.4% |

### 노루 (`capreolus_capreolus`) vs 고라니 (`hydropotes_inermis`)

| 항목 | 값 |
|------|-----|
| capreolus_capreolus 검증 샘플 | 28 |
| hydropotes_inermis 검증 샘플 | 28 |
| capreolus_capreolus → hydropotes_inermis | 0 (0.0%) |
| hydropotes_inermis → capreolus_capreolus | 7 (25.0%) |
| 양방향 합계 | 7 |
| 전체 대비 혼동률 | 12.5% |

### 참새 (`passer_montanus`) vs 쇠박새 (`parus_minor`)

| 항목 | 값 |
|------|-----|
| passer_montanus 검증 샘플 | 28 |
| parus_minor 검증 샘플 | 28 |
| passer_montanus → parus_minor | 0 (0.0%) |
| parus_minor → passer_montanus | 0 (0.0%) |
| 양방향 합계 | 0 |
| 전체 대비 혼동률 | 0.0% |

## 4. 종별 취약 지표 (F1 < 0.80)

| 종 | Precision | Recall | F1 | Support |
|----|-----------|--------|----|---------|
| 어치 (`pica_serica`) | 0.40 | 0.47 | 0.43 | 17 |
| 황조롱이 (`falco_tinnunculus`) | 0.64 | 0.57 | 0.60 | 28 |
| 참매 (`accipiter_gentilis`) | 0.62 | 0.86 | 0.72 | 28 |
| 해오라기 (`nycticorax_nycticorax`) | 0.67 | 0.79 | 0.72 | 28 |
| 고라니 (`hydropotes_inermis`) | 0.89 | 0.61 | 0.72 | 28 |
| 뿔제비 (`phalacrocorax_carbo`) | 0.95 | 0.64 | 0.77 | 28 |
| 소쩍새 (`athene_noctua`) | 0.90 | 0.68 | 0.78 | 28 |
| 청둥오리 (`anas_platyrhynchos`) | 0.79 | 0.79 | 0.79 | 28 |
| 할미새 (`motacilla_alba`) | 0.79 | 0.79 | 0.79 | 28 |
| 홍오리 (`tadorna_tadorna`) | 0.87 | 0.72 | 0.79 | 18 |

## 5. 데이터 보강 권장

- **황조롱이 (`falco_tinnunculus`) → 참매 (`accipiter_gentilis`)** (7건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **고라니 (`hydropotes_inermis`) → 노루 (`capreolus_capreolus`)** (7건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **쇠박새 (`parus_minor`) → 어치 (`pica_serica`)** (4건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **말똥가리 (`buteo_japonicus`) → 참매 (`accipiter_gentilis`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **새사촌 (`cettia_diphone`) → 동박새 (`zosterops_japonicus`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **어치 (`pica_serica`)** (F1=0.43, val=17장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **황조롱이 (`falco_tinnunculus`)** (F1=0.60, val=28장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **참매 (`accipiter_gentilis`)** (F1=0.72, val=28장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **해오라기 (`nycticorax_nycticorax`)** (F1=0.72, val=28장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **고라니 (`hydropotes_inermis`)** (F1=0.72, val=28장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가

## 6. 오분류 샘플 복사

대표 오분류 이미지 **28장**을 `reports/misclassified_samples/`에 저장했습니다.

| 실제 → 예측 | confidence | 파일 |
|-------------|------------|------|
| falco_tinnunculus → accipiter_gentilis | 0.952 | `falco tinnunculus_9_conf0.952.jpg` |
| falco_tinnunculus → accipiter_gentilis | 0.910 | `황조롱이--24x_postolka_dst6039_conf0.910.jpg` |
| falco_tinnunculus → accipiter_gentilis | 0.871 | `falco tinnunculus_44_conf0.871.jpg` |
| hydropotes_inermis → capreolus_capreolus | 0.899 | `고라니21_conf0.899.jpg` |
| hydropotes_inermis → capreolus_capreolus | 0.895 | `hydropotes inermis_25_conf0.895.jpg` |
| hydropotes_inermis → capreolus_capreolus | 0.887 | `hydropotes inermis_52_conf0.887.jpg` |
| parus_minor → pica_serica | 0.820 | `parus minor_69_conf0.819.jpg` |
| parus_minor → pica_serica | 0.808 | `parus minor_30_conf0.808.jpg` |
| parus_minor → pica_serica | 0.791 | `parus minor_27_conf0.791.jpg` |
| buteo_japonicus → accipiter_gentilis | 0.953 | `buteo japonicus_56_conf0.953.jpg` |
| buteo_japonicus → accipiter_gentilis | 0.953 | `buteo japonicus_62 (2)_conf0.953.jpg` |
| buteo_japonicus → accipiter_gentilis | 0.689 | `buteo japonicus_86_conf0.689.jpg` |
| cettia_diphone → zosterops_japonicus | 0.755 | `cettia diphone_48_conf0.755.jpg` |
| cettia_diphone → zosterops_japonicus | 0.734 | `cettia diphone_32_conf0.734.jpg` |
| cettia_diphone → zosterops_japonicus | 0.669 | `cettia diphone_45_conf0.669.jpg` |
| corvus_corone → nycticorax_nycticorax | 0.975 | `corvus corone_89_conf0.975.jpg` |
| corvus_corone → nycticorax_nycticorax | 0.861 | `corvus corone_87_conf0.861.jpg` |
| corvus_corone → nycticorax_nycticorax | 0.489 | `corvus corone_4_conf0.489.jpg` |
| emberiza_schoeniclus → cettia_diphone | 0.833 | `emberiza schoeniclus_40_conf0.832.jpg` |
| emberiza_schoeniclus → cettia_diphone | 0.585 | `emberiza schoeniclus_48_conf0.585.jpg` |
| ... | | 외 8장 |
