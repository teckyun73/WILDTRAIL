import json
import logging
import random
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.config import get_settings
from app.schemas import IdentificationCandidate, IdentificationResult
from app.services.audio_identify import audio_identify_service

settings = get_settings()
logger = logging.getLogger(__name__)


class IdentifyService:
    def __init__(self) -> None:
        self.species_ids = self._load_species_ids()
        self.model = None
        self.model_classes = 0
        self.model_val_acc: float | None = None
        self.model_version: str | None = None
        self.trained_at: str | None = None
        self.backbone: str | None = None
        self.preprocess_version: str | None = None
        self.dataset_fingerprint: str | None = None
        self.model_path = Path(settings.model_path)
        self._try_load_model()

    def get_status(self) -> dict:
        return {
            "model_loaded": self.model is not None,
            "model_classes": self.model_classes,
            "model_val_acc": self.model_val_acc,
            "model_path": str(self.model_path),
            "model_version": self.model_version,
            "trained_at": self.trained_at,
            "backbone": self.backbone,
            "preprocess_version": self.preprocess_version,
            "dataset_fingerprint": self.dataset_fingerprint,
        }

    def _load_species_ids(self) -> list[dict[str, str]]:
        species_file = settings.data_dir / "species.json"
        if not species_file.exists():
            return []
        with species_file.open(encoding="utf-8") as f:
            data = json.load(f)
        return [
            {
                "id": item["id"],
                "common_name": item["common_name"],
                "scientific_name": item["scientific_name"],
            }
            for item in data
        ]

    def _try_load_model(self) -> None:
        model_path = self.model_path
        if not model_path.exists():
            logger.info("Image model file not found: %s (stub mode)", model_path)
            return
        try:
            import torch
            from torchvision import models

            from app.services.image_transforms import PREPROCESS_VERSION, build_eval_transform

            checkpoint = torch.load(model_path, map_location="cpu")
            num_classes = checkpoint.get("num_classes", len(self.species_ids))
            self.model_classes = int(num_classes)
            self.model_val_acc = checkpoint.get("val_acc")
            self.model_version = checkpoint.get("model_version")
            self.trained_at = checkpoint.get("trained_at")
            self.backbone = checkpoint.get("backbone")
            self.dataset_fingerprint = checkpoint.get("dataset_fingerprint") or checkpoint.get(
                "dataset_report_hash"
            )
            model = models.efficientnet_b0(weights=None)
            model.classifier[1] = torch.nn.Linear(
                model.classifier[1].in_features, num_classes
            )
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()
            self.model = model
            self.transform = build_eval_transform()
            self.preprocess_version = checkpoint.get("preprocess_version", PREPROCESS_VERSION)
            self.idx_to_species = checkpoint.get("idx_to_species", {})
            logger.info(
                "Image model loaded: %s classes (val_acc=%s, version=%s, preprocess=%s) from %s",
                self.model_classes,
                self.model_val_acc,
                self.model_version or "unknown",
                self.preprocess_version,
                model_path,
            )
        except Exception:
            logger.warning(
                "Failed to load image model from %s; falling back to stub mode",
                model_path,
                exc_info=True,
            )
            self.model = None

    def _predict_with_model(self, image: Image.Image) -> list[IdentificationCandidate]:
        import torch

        tensor = self.transform(image).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

        topk = min(3, probs.shape[0])
        values, indices = torch.topk(probs, topk)
        candidates: list[IdentificationCandidate] = []
        for value, idx in zip(values.tolist(), indices.tolist()):
            species = self.idx_to_species.get(str(idx)) or self.idx_to_species.get(idx)
            if not species:
                continue
            candidates.append(
                IdentificationCandidate(
                    species_id=species["id"],
                    common_name=species["common_name"],
                    scientific_name=species["scientific_name"],
                    confidence=round(float(value), 4),
                )
            )
        return candidates

    def _predict_stub(self) -> list[IdentificationCandidate]:
        if not self.species_ids:
            return [
                IdentificationCandidate(
                    species_id="pica_pica",
                    common_name="까치",
                    scientific_name="Pica pica",
                    confidence=0.72,
                )
            ]
        ranked = random.sample(self.species_ids, min(3, len(self.species_ids)))
        confidences = [0.82, 0.11, 0.07]
        return [
            IdentificationCandidate(
                species_id=item["id"],
                common_name=item["common_name"],
                scientific_name=item["scientific_name"],
                confidence=confidences[i] if i < len(confidences) else 0.05,
            )
            for i, item in enumerate(ranked)
        ]

    def identify_image(self, content: bytes) -> IdentificationResult:
        image = Image.open(BytesIO(content)).convert("RGB")
        if self.model is not None:
            try:
                candidates = self._predict_with_model(image)
                source = "model"
            except Exception:
                logger.warning(
                    "Image model inference failed; falling back to stub mode",
                    exc_info=True,
                )
                candidates = self._predict_stub()
                source = "stub"
        else:
            candidates = self._predict_stub()
            source = "stub"

        message = (
            "학습된 모델로 식별했습니다."
            if source == "model"
            else "MVP 스텁 모드입니다. models/train.py로 학습 후 best_model.pth를 연결하세요."
        )
        if candidates and candidates[0].confidence < 0.7:
            message += " 신뢰도가 낮습니다. 유사 종을 함께 확인하세요."

        return IdentificationResult(
            media_type="image",
            candidates=candidates,
            message=message,
            source=source,
        )

    def identify_audio(self, content: bytes, filename: str = "") -> IdentificationResult:
        return audio_identify_service.identify(content, filename=filename)

    def identify_video(self) -> IdentificationResult:
        candidates = self._predict_stub()
        return IdentificationResult(
            media_type="video",
            candidates=candidates,
            message="영상 식별은 Phase 2 예정입니다. 현재는 데모 결과를 반환합니다.",
            source="stub",
        )


identify_service = IdentifyService()
