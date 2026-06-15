from sqlalchemy.orm import Session

from app.models import Species
from app.schemas import HealthResponse, ModelStatus
from app.services.audio_identify import audio_identify_service
from app.services.identify import identify_service
from app.services.llm import get_llm_status


def build_health_response(db: Session) -> HealthResponse:
    species_json_count = len(identify_service.species_ids)
    species_db_count = db.query(Species).count()

    image_status = identify_service.get_status()
    audio_status = audio_identify_service.get_status()

    warnings: list[str] = []

    if species_json_count != species_db_count:
        warnings.append(
            f"species 수 불일치: species.json={species_json_count}, db={species_db_count}"
        )

    if image_status["model_loaded"]:
        if image_status["model_classes"] != species_json_count:
            warnings.append(
                "이미지 모델 클래스 수("
                f"{image_status['model_classes']})와 species.json({species_json_count})가 다릅니다."
            )
        if not image_status.get("model_version"):
            warnings.append(
                "이미지 모델 checkpoint에 model_version 메타데이터가 없습니다. "
                "models/stamp_checkpoint.py 실행을 권장합니다."
            )
    else:
        warnings.append(
            "이미지 분류 모델이 로드되지 않았습니다. 식별 API는 stub 모드로 동작합니다."
        )

    if not audio_status["model_loaded"]:
        warnings.append(
            "오디오 분류 모델이 로드되지 않았습니다. 오디오 식별은 분석+stub 모드입니다."
        )

    llm_status = get_llm_status()
    if not llm_status.configured:
        key_name = "OPENAI_API_KEY" if llm_status.provider == "openai" else "GEMINI_API_KEY"
        warnings.append(
            f"LLM API 키가 설정되지 않았습니다 ({llm_status.provider}). "
            f"backend/.env에 {key_name}를 추가하세요."
        )

    status = "ok" if not warnings else "degraded"

    return HealthResponse(
        status=status,
        service="wildtrail-api",
        image_model=ModelStatus(**image_status),
        audio_model=ModelStatus(**audio_status),
        species_json_count=species_json_count,
        species_db_count=species_db_count,
        llm_configured=llm_status.configured,
        llm_provider=llm_status.provider,
        llm_model=llm_status.model,
        warnings=warnings,
    )
