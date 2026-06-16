# WildTrail ML Evaluation Report

> 자동 생성: `2026-06-15T14:37:31.034398+00:00`

## 1. 요약

| 지표 | 값 |
|------|-----|
| Accuracy | 74.77% |
| Macro F1 | 74.65% |
| Weighted F1 | 74.72% |
| 클래스 수 | 29 |
| 검증 샘플 | 543 |
| Checkpoint val_acc | 0.7476979742173112 |

관련 산출물:
- `reports/metrics.json`
- `reports/confusion_matrix.csv` / `.png`
- `reports/per_class_report.csv`
- `reports/misclassification_pairs.json`
- `reports/misclassified_samples/`

## 2. Top 10 오분류 쌍

| 순위 | 실제 종 | 예측 종 | 건수 | 실제 종 기준 비율 |
|------|---------|---------|------|-------------------|
| 1 | 고라니 (`hydropotes_inermis`) | 노루 (`capreolus_capreolus`) | 4 | 17.4% |
| 2 | 황조롱이 (`falco_tinnunculus`) | 참매 (`accipiter_gentilis`) | 3 | 12.5% |
| 3 | 황조롱이 (`falco_tinnunculus`) | 말똥가리 (`buteo_japonicus`) | 3 | 12.5% |
| 4 | 참새 (`passer_montanus`) | 검은머리쑥새 (`emberiza_schoeniclus`) | 3 | 12.5% |
| 5 | 뿔제비 (`phalacrocorax_carbo`) | 황새 (`ciconia_boyciana`) | 3 | 17.6% |
| 6 | 참매 (`accipiter_gentilis`) | 황조롱이 (`falco_tinnunculus`) | 2 | 9.1% |
| 7 | 청둥오리 (`anas_platyrhynchos`) | 까마귀 (`corvus_corone`) | 2 | 11.8% |
| 8 | 청둥오리 (`anas_platyrhynchos`) | 꼬리물대 (`tachybaptus_ruficollis`) | 2 | 11.8% |
| 9 | 새사촌 (`cettia_diphone`) | 참매 (`accipiter_gentilis`) | 2 | 11.1% |
| 10 | 새사촌 (`cettia_diphone`) | 쇠박새 (`parus_minor`) | 2 | 11.1% |

## 3. 유사 종 혼동 분석

### 까치 (`pica_pica`) vs 어치 (`pica_serica`)

| 항목 | 값 |
|------|-----|
| pica_pica 검증 샘플 | 18 |
| pica_serica 검증 샘플 | 17 |
| pica_pica → pica_serica | 1 (5.6%) |
| pica_serica → pica_pica | 0 (0.0%) |
| 양방향 합계 | 1 |
| 전체 대비 혼동률 | 2.9% |

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
| pica_serica → corvus_corone | 0 (0.0%) |
| corvus_corone → pica_serica | 0 (0.0%) |
| 양방향 합계 | 0 |
| 전체 대비 혼동률 | 0.0% |

### 노루 (`capreolus_capreolus`) vs 고라니 (`hydropotes_inermis`)

| 항목 | 값 |
|------|-----|
| capreolus_capreolus 검증 샘플 | 28 |
| hydropotes_inermis 검증 샘플 | 23 |
| capreolus_capreolus → hydropotes_inermis | 1 (3.6%) |
| hydropotes_inermis → capreolus_capreolus | 4 (17.4%) |
| 양방향 합계 | 5 |
| 전체 대비 혼동률 | 9.8% |

### 참새 (`passer_montanus`) vs 쇠박새 (`parus_minor`)

| 항목 | 값 |
|------|-----|
| passer_montanus 검증 샘플 | 24 |
| parus_minor 검증 샘플 | 18 |
| passer_montanus → parus_minor | 0 (0.0%) |
| parus_minor → passer_montanus | 0 (0.0%) |
| 양방향 합계 | 0 |
| 전체 대비 혼동률 | 0.0% |

## 4. 종별 취약 지표 (F1 < 0.80)

| 종 | Precision | Recall | F1 | Support |
|----|-----------|--------|----|---------|
| 참매 (`accipiter_gentilis`) | 0.54 | 0.59 | 0.57 | 22 |
| 뿔제비 (`phalacrocorax_carbo`) | 0.67 | 0.59 | 0.62 | 17 |
| 새사촌 (`cettia_diphone`) | 0.69 | 0.61 | 0.65 | 18 |
| 황새 (`ciconia_boyciana`) | 0.62 | 0.72 | 0.67 | 18 |
| 할미새 (`motacilla_alba`) | 0.67 | 0.67 | 0.67 | 18 |
| 멧비둘기 (`streptopelia_orientalis`) | 0.73 | 0.61 | 0.67 | 18 |
| 말똥가리 (`buteo_japonicus`) | 0.61 | 0.78 | 0.68 | 18 |
| 청둥오리 (`anas_platyrhynchos`) | 0.73 | 0.65 | 0.69 | 17 |
| 해오라기 (`nycticorax_nycticorax`) | 0.91 | 0.56 | 0.69 | 18 |
| 쇠박새 (`parus_minor`) | 0.60 | 0.83 | 0.70 | 18 |
| 어치 (`pica_serica`) | 0.65 | 0.76 | 0.70 | 17 |
| 황조롱이 (`falco_tinnunculus`) | 0.83 | 0.62 | 0.71 | 24 |
| 소쩍새 (`athene_noctua`) | 0.80 | 0.67 | 0.73 | 18 |
| 검은머리쑥새 (`emberiza_schoeniclus`) | 0.75 | 0.71 | 0.73 | 17 |
| 참새 (`passer_montanus`) | 0.80 | 0.67 | 0.73 | 24 |
| 두루미 (`grus_japonensis`) | 0.92 | 0.61 | 0.73 | 18 |
| 검은머리오리 (`melanitta_fusca`) | 0.72 | 0.76 | 0.74 | 17 |
| 까마귀 (`corvus_corone`) | 0.62 | 0.94 | 0.74 | 17 |
| 고라니 (`hydropotes_inermis`) | 0.73 | 0.83 | 0.78 | 23 |
| 집비둘기 (`columba_livia`) | 0.74 | 0.82 | 0.78 | 17 |
| 동박새 (`zosterops_japonicus`) | 0.87 | 0.72 | 0.79 | 18 |

## 5. 데이터 보강 권장

- **고라니 (`hydropotes_inermis`) → 노루 (`capreolus_capreolus`)** (4건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **황조롱이 (`falco_tinnunculus`) → 참매 (`accipiter_gentilis`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **황조롱이 (`falco_tinnunculus`) → 말똥가리 (`buteo_japonicus`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **참새 (`passer_montanus`) → 검은머리쑥새 (`emberiza_schoeniclus`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **뿔제비 (`phalacrocorax_carbo`) → 황새 (`ciconia_boyciana`)** (3건): 유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집
- **참매 (`accipiter_gentilis`)** (F1=0.57, val=22장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **뿔제비 (`phalacrocorax_carbo`)** (F1=0.62, val=17장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **새사촌 (`cettia_diphone`)** (F1=0.65, val=18장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **황새 (`ciconia_boyciana`)** (F1=0.67, val=18장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가
- **할미새 (`motacilla_alba`)** (F1=0.67, val=18장): 조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가

## 6. 오분류 샘플 복사

대표 오분류 이미지 **25장**을 `reports/misclassified_samples/`에 저장했습니다.

| 실제 → 예측 | confidence | 파일 |
|-------------|------------|------|
| hydropotes_inermis → capreolus_capreolus | 0.916 | `고라니21_conf0.916.jpg` |
| hydropotes_inermis → capreolus_capreolus | 0.908 | `hydropotes inermis_55_conf0.908.jpg` |
| hydropotes_inermis → capreolus_capreolus | 0.707 | `hydropotes inermis_38_conf0.706.jpg` |
| falco_tinnunculus → accipiter_gentilis | 0.798 | `falco tinnunculus_54_conf0.798.jpg` |
| falco_tinnunculus → accipiter_gentilis | 0.502 | `falco tinnunculus_42_conf0.502.jpg` |
| falco_tinnunculus → accipiter_gentilis | 0.459 | `falco tinnunculus_34_conf0.459.jpg` |
| falco_tinnunculus → buteo_japonicus | 0.838 | `falco tinnunculus_44_conf0.838.jpg` |
| falco_tinnunculus → buteo_japonicus | 0.794 | `falco tinnunculus_59_conf0.794.jpg` |
| falco_tinnunculus → buteo_japonicus | 0.616 | `falco tinnunculus_61_conf0.616.jpg` |
| passer_montanus → emberiza_schoeniclus | 0.933 | `passer montanus_44_conf0.933.jpg` |
| passer_montanus → emberiza_schoeniclus | 0.530 | `passer montanus_65_conf0.530.jpg` |
| passer_montanus → emberiza_schoeniclus | 0.227 | `passer montanus_10_conf0.227.jpg` |
| phalacrocorax_carbo → ciconia_boyciana | 0.607 | `phalacrocorax carbo_20_conf0.607.jpg` |
| phalacrocorax_carbo → ciconia_boyciana | 0.259 | `phalacrocorax carbo_32_conf0.259.jpg` |
| phalacrocorax_carbo → ciconia_boyciana | 0.163 | `phalacrocorax carbo_16_conf0.163.jpg` |
| accipiter_gentilis → falco_tinnunculus | 0.628 | `accipiter gentilis_81_conf0.628.jpg` |
| accipiter_gentilis → falco_tinnunculus | 0.594 | `accipiter gentilis_64_conf0.594.jpg` |
| anas_platyrhynchos → corvus_corone | 0.754 | `anas platyrhynchos_40_conf0.754.jpg` |
| anas_platyrhynchos → corvus_corone | 0.701 | `anas platyrhynchos_30_conf0.700.jpg` |
| anas_platyrhynchos → tachybaptus_ruficollis | 0.733 | `anas platyrhynchos_60_conf0.733.jpg` |
| ... | | 외 5장 |
