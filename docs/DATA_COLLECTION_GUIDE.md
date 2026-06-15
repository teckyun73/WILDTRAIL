# WildTrail 이미지 학습 데이터 수집 가이드

이 문서는 WildTrail CNN 이미지 분류 모델(30종 MVP)을 위한 **데이터 수집·정리·검증** 절차를 설명합니다.

---

## 1. 목표

| 항목 | 권장 기준 |
|------|-----------|
| 종 수 | 30종 (`data/species.json` 기준) |
| 종당 최소 이미지 | **80장** (train+val 합산) |
| 권장 이미지 | **150~300장** |
| train / val 비율 | **80% / 20%** |
| 이미지 최소 해상도 | 224×224 이상 |
| 파일 형식 | JPG, PNG, WEBP |

> 종당 80장 미만이면 과적합·오분류 위험이 큽니다. 유사 종(까치/어치, 쇠백로/중대백로)은 **더 많은 데이터**가 필요합니다.

---

## 2. 폴더 구조

```text
data/images/
├── raw/                    # 수집 직후 원본 (종별 하위 폴더)
│   ├── pica_pica/
│   └── corvus_corone/
├── train/                  # 학습용 (ImageFolder)
│   └── pica_pica/
├── val/                    # 검증용
│   └── pica_pica/
├── rejected/               # 품질 미달·오라벨 이미지
└── sources.csv             # 출처·라이선스 기록 (권장)
```

폴더 자동 생성:

```bash
cd models
python prepare_dataset.py init
```

---

## 3. 데이터 수집 소스 (우선순위)

### 3-1. 직접 촬영 (최우선 · 권장 비율 40% 이상)

- **장점**: 실제 서비스 사용 환경과 유사, 저작권 문제 없음
- **촬영 팁**
  - 같은 종이라도 **각도·거리·배경·조명**을 다양하게
  - 너무 작게 찍힌 개체, 심한 흔들림, 가림 50% 이상은 제외
  - 멸종위기종은 **원거리·텔레포토**만, 보호구역 규정 준수
- **파일명 규칙**: `YYYYMMDD_HHMM_<species_id>_001.jpg`

### 3-2. AI Hub (한국 정부 공개 데이터)

- [AI Hub](https://aihub.or.kr) — 조류·곤충·야생동물 이미지 데이터셋 검색
- 다운로드 후 `species_id` 폴더로 **라벨 매핑**하여 복사
- 이용약관·출처 표기 필수

### 3-3. iNaturalist (Research Grade 관찰)

- [iNaturalist](https://www.inaturalist.org) — 한국 관찰 기록
- **Research Grade** + CC 라이선스(CC BY, CC BY-SA, CC0)만 사용
- 학명(`scientific_name`)으로 `species_id`와 매칭

### 3-4. Wikimedia Commons

- CC 라이선스 이미지만 사용
- `sources.csv`에 URL·작가·라이선스 기록

### 3-5. 사용 금지·주의

- 저작권 불명 이미지, 웹 무단 크롤링
- 보호종 근접 촬영으로 인한 서식지 교란
- 동일 이미지의 과도한 augmentation을 **다른 사진처럼 취급**하는 것

---

## 4. 라벨링·품질 기준

### 포함 (O)

- 종의 전체 또는 식별 가능한 부분(머리·부리·날개 패턴)이 보임
- 1장에 1종이 주 피사체
- 자연 환경·도심·습지 등 **다양한 배경**

### 제외 (X) → `rejected/`로 이동

- 종 식별 불가(너무 작음, 흔함, 실루엣만)
- 잘못된 라벨(유사 종 혼동)
- 워터마크·텍스트가 화면의 30% 이상
- 손그림·일러스트·인형·조각상

### 유사 종 주의 리스트

| 그룹 | 종 ID |
|------|--------|
| 까치류 | `pica_pica` |
| 비둘기 | `streptopelia_orientalis`, `columba_livia` |
| 백로류 | `egretta_garzetta`, `nycticorax_nycticorax` |
| 오리류 | `anas_platyrhynchos`, `tadorna_tadorna`, `melanitta_fusca` |
| 사슴류 | `capreolus_capreolus`, `hydropotes_inermis` |

---

## 5. 워크플로우 (권장 순서)

```text
1. init        폴더 생성
2. 수집        raw/<species_id>/ 에 이미지 저장
3. validate    깨진 파일·규격 미달 검사
4. split       train/val 분할
5. report      종별 장수·부족 종 확인
6. train       EfficientNet 학습
7. 연동        backend .env MODEL_PATH 설정
```

### 명령어 예시

```bash
cd models

# 1) 폴더 초기화
python prepare_dataset.py init

# 2) raw 데이터 검증
python prepare_dataset.py validate --dir ../data/images/raw

# 3) train/val 분할 (80/20, 시드 고정)
python prepare_dataset.py split --raw-dir ../data/images/raw --out-dir ../data/images --val-ratio 0.2

# 4) 현황 리포트
python prepare_dataset.py report --dir ../data/images

# 5) 학습
python train.py --data-dir ../data/images --epochs 15 --batch-size 16
```

---

## 6. sources.csv 기록 양식

`data/images/sources.csv`:

```csv
filename,species_id,source_type,source_url,license,collector,collected_at
20260412_pica_001.jpg,pica_pica,self,,CC-BY-4.0-self,홍길동,2026-04-12
magpie_042.jpg,pica_pica,inaturalist,https://...,CC-BY-NC,,
```

---

## 7. 종별 수집 목표 (MVP)

`data/dataset_manifest.json`에 종별 `target_count`, `priority`, `notes`가 정의되어 있습니다.

우선순위 **high** 종부터 150장 이상 채운 뒤, **medium** → **low** 순으로 확장하세요.

**Hard negative 보강:** 유사 종 쌍별 추가 수집 계획은 [HARD_NEGATIVE_GUIDE.md](./HARD_NEGATIVE_GUIDE.md)를 참고하세요.

```bash
cd models
python hard_negative_report.py
```

---

## 8. 학습 후 검증

- val accuracy **75% 이상**을 1차 목표
- 혼동 행렬에서 유사 종 쌍 오분류율 확인
- 실제 스마트폰 촬영 이미지 20장으로 **별도 테스트** 권장

---

## 9. 체크리스트

- [ ] `prepare_dataset.py init` 실행
- [ ] 30종 `raw/` 폴더에 데이터 배치
- [ ] `validate` 통과 (깨진 파일 0건)
- [ ] 종당 80장 이상 (`report` 확인)
- [ ] `sources.csv` 작성
- [ ] `split` 후 train/val 생성
- [ ] `train.py` 실행 → `models/checkpoints/best_model.pth`
- [ ] backend 재시작 후 `/api/v1/identify/image` 실제 모델 응답 확인

---

## 10. 문제 해결

| 증상 | 대응 |
|------|------|
| 특정 종 accuracy 낮음 | 해당 종 raw 데이터 2배 수집, 유사 종 negative 샘플 추가 |
| train acc 높고 val acc 낮음 | augmentation 줄이기, 배경 다양화, 데이터 누수(중복) 제거 |
| 모델 로드 안 됨 | `MODEL_PATH` 경로·`idx_to_species` 키 확인 |
