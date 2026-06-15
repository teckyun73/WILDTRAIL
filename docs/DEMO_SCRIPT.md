# WildTrail 3분 발표 데모 시나리오

발표자가 문서만 보고 리허설할 수 있도록 구성했습니다.  
**사전 조건:** Backend(8000) + Frontend(5173) 실행, `best_model.pth` 배치 권장.

---

## 타임라인 (총 ~3분)

| 시간 | 행동 | 기대 결과 | 말할 포인트 |
|------|------|-----------|-------------|
| 0:00 | 앱 접속 `http://127.0.0.1:5173` | WildTrail 메인 | "식별→도감→지도→여행 한 화면 흐름" |
| 0:15 | **식별** 탭 → 두루미/까치 사진 업로드 | Top-1 종, confidence, **AI 모델** 배지 | `source: model` vs stub 구분 |
| 0:50 | **도감** 탭 → 어치 선택 → RAG 질문 | 종 정보 + 답변 | API 키 있으면 LLM, 없으면 템플릿 |
| 1:30 | **관찰지** 탭 | 철원·순천 등 핫스팟 마커 | Leaflet + species 연동 |
| 2:00 | **여행** 탭 → 두루미 2일 일정 생성 | 일정·경비·준비물 | LLM 요약은 선택 기능 |
| 2:35 | `/health` 또는 한계 설명 | 29종, ~75% acc | 솔직한 MVP 한계 강조 |
| 2:50 | Q&A | — | 로드맵·hard negative 보강 |

---

## 1. 식별 데모 (0:15 ~ 0:50)

### 추천 샘플

| 우선 | 종 | 기대 |
|------|-----|------|
| 1 | `grus_japonensis` (두루미) | confidence 높음, 데모 임팩트 |
| 2 | `pica_pica` (까치) | 흔한 종, 인지도 좋음 |
| 3 | `corvus_corone` (까마귀) | 대형 조류 대비 |

### UI 확인 포인트

- 결과 카드에 **AI 모델** (녹색) 또는 **데모 모드** (노란색) 배지
- Top-3 후보와 confidence
- 신뢰도 낮을 때 안내 문구

### API로 미리 검증 (선택)

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | Select-Object status, @{n='model';e={$_.image_model.model_loaded}}
```

`model_loaded: false`이면 stub 모드 — "모델 파일은 Git 제외, 학습 가이드 참고"라고 설명.

---

## 2. 도감 RAG (0:50 ~ 1:30)

1. 도감 탭에서 **어치** (`pica_serica`) 선택
2. 질문 예: *"어치는 까치와 어떻게 구분하나요?"*
3. 인용(citations) 출처 표시 확인

**OPENAI_API_KEY 없을 때:** 템플릿 기반 스니펫 응답 — "LLM 연동은 env 설정 한 줄로 활성화" 언급.

---

## 3. 관찰지 지도 (1:30 ~ 2:00)

1. 관찰지 탭 → 지도 로드
2. 핫스팟 마커 클릭 → 종·지역 정보
3. 두루미·황새 등 멸종위기종은 **원거리 관찰** 주의 문구 언급

---

## 4. 여행 플래너 (2:00 ~ 2:35)

1. 종: **두루미**, 출발: **서울**, 2일, 2명
2. 생성 결과: `days_plan`, `costs`, `checklist`, disclaimer
3. `source: rules` vs `llm+rules` 설명

---

## 5. 한계 & 로드맵 마무리 (2:35 ~ 2:50)

아래를 짧게 언급 (솔직함이 신뢰를 줍니다):

| 항목 | 현재 |
|------|------|
| 식별 종 | 29종 (JSON 31종) |
| val accuracy | ~71% (학습) / ~75% (통일 전처리 evaluate) |
| 오디오 | 분석 + stub |
| 영상 | Phase 2 |
| 유사종 | 까치/어치, 노루/고라니 hard negative 보강 중 |

`/health` 한 줄:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/health).warnings
```

---

## 실패 시 대체 시나리오

| 문제 | 대체 |
|------|------|
| 모델 미로드 (stub) | "데모 모드 배지" 보여주며 파이프라인·학습 스토리 설명 |
| 식별 confidence 낮음 | 까치/까마귀 등 흔한 종으로 재시도 |
| OpenAI 429/미설정 | RAG 템플릿 응답으로 도감 탭만 시연 |
| 포트 8000 충돌 | `netstat`로 프로세스 종료 후 재시작 |
| 지도 타일 느림 | 관찰지 탭 스킵, API `/api/v1/locations` JSON으로 대체 설명 |

---

## 발표 전 체크리스트

- [ ] `uvicorn` + `npm run dev` 실행 중
- [ ] `Invoke-RestMethod http://127.0.0.1:8000/health` → `status` 확인
- [ ] 데모용 사진 2~3장 준비 (`data/images/val/`에서 복사 가능)
- [ ] (선택) `OPENAI_API_KEY` 설정
- [ ] 브라우저 탭: 앱 + `/docs` 또는 `/health`

---

## 관련 링크

- [README Quick Start](../README.md#빠른-시작-15분)
- [ML_EVAL_REPORT.md](./ML_EVAL_REPORT.md)
- [DATA_COLLECTION_GUIDE.md](./DATA_COLLECTION_GUIDE.md)
