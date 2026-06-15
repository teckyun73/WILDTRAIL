# Contributing to WildTrail

WildTrail에 관심 가져 주셔서 감사합니다. 교육·포트폴리오 MVP이지만 이슈와 PR을 환영합니다.

## 개발 환경

1. [README.md](README.md) Quick Start 따라 backend + frontend 실행
2. ML 작업 시 `models/README.md` 참고
3. DB 시드 변경 후 [docs/MIGRATION.md](docs/MIGRATION.md) 확인

## 브랜치·커밋

- 기능: `feat/short-description`
- 수정: `fix/short-description`
- 문서: `docs/short-description`
- 커밋 메시지는 **왜** 변경했는지 한 문장으로 (영문/한글 모두 가능)

## PR 전 체크

- [ ] `/health` 응답 확인
- [ ] 식별 API `source` 필드 유지 (model/stub)
- [ ] `.env`, `data/images/`, `models/checkpoints/` 등 **비밀·대용량 파일 미포함**
- [ ] ML 변경 시 `evaluate.py` 또는 `validate_coverage.py` 실행

## 이슈 등록

버그는 [GitHub Issue 템플릿](.github/ISSUE_TEMPLATE/bug_report.md)을 사용해 주세요.

## 데이터 기여

- 이미지: [DATA_COLLECTION_GUIDE.md](docs/DATA_COLLECTION_GUIDE.md)
- 유사 종 보강: [HARD_NEGATIVE_GUIDE.md](docs/HARD_NEGATIVE_GUIDE.md)
- 출처·라이선스는 `data/images/sources.csv`에 기록

## 코드 스타일

- Python: surrounding code와 동일한 패턴 유지, 불필요한 추상화 지양
- TypeScript/React: 기존 `App.tsx` 탭 구조·Tailwind 패턴 따르기
