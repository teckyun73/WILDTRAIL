# WildTrail 데이터 마이그레이션 가이드

## species / hotspot 동기화 (v0.1+)

`species.json` 또는 `hotspots.json`을 수정한 뒤에는 **백엔드를 재시작**하면 자동으로 DB에 반영됩니다.

- `species`: `id` 기준 **upsert** (insert or update)
- `hotspots`: `name + species_id + latitude + longitude` 기준 **upsert**

서버 시작 로그 예시:

```text
INFO Seed sync: species inserted=1 updated=30 (json=31 db=31), hotspots inserted=0 updated=10 ...
INFO Species metadata is in sync with species.json
```

---

## 기존 DB에 신규 종이 없을 때 (예: pica_serica)

### 방법 A — 재시작만 (권장)

```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --reload
```

기존 `wildtrail.db`를 유지한 채 누락 종만 추가·기존 종 메타데이터가 갱신됩니다.

### 방법 B — DB 초기화 (관찰 기록도 삭제됨)

```powershell
cd backend
Remove-Item .\wildtrail.db -ErrorAction SilentlyContinue
.\.venv\Scripts\uvicorn app.main:app --reload
```

`sightings` 등 사용자 기록이 모두 사라집니다. 데모·개발 환경에서만 사용하세요.

---

## 수동 동기화 확인

```powershell
cd backend
.\.venv\Scripts\python -c "
from app.database import SessionLocal
from app.seed import load_seed_data
with SessionLocal() as db:
    r = load_seed_data(db)
    print('in_sync', r.in_sync)
    print('missing', r.missing_species_ids)
"
```

API 확인:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/species/pica_serica
Invoke-RestMethod http://127.0.0.1:8000/health
```

`/health` 응답에서 `species_db_count`, `image_model.model_loaded`, `warnings`를 확인하세요.

---

## JSON에 없는 DB 종

upsert는 **삭제하지 않습니다**. JSON에서 제거한 종이 DB에 남으면 시작 로그에 warning이 출력됩니다.

의도적으로 제거하려면 SQLite에서 직접 삭제하거나 방법 B로 DB를 재생성하세요.

---

## 모델 클래스 수와 species.json

- `species.json`: 도감·API 기준 전체 종 목록
- 학습 모델: `data/images/train/`에 데이터가 있는 종만 포함

두 수가 다를 수 있습니다. `/health` 확장(예정)으로 차이를 확인할 예정입니다.
