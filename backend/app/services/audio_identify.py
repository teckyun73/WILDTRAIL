import json
import logging
import random
import tempfile
from io import BytesIO
from pathlib import Path

from app.config import get_settings
from app.schemas import IdentificationCandidate, IdentificationResult

settings = get_settings()
logger = logging.getLogger(__name__)


class AudioIdentifyService:
    def __init__(self) -> None:
        self.species_ids = self._load_species_ids()
        self.known_species_ids = {item["id"] for item in self.species_ids}
        self.model = None
        self.model_classes = 0
        self.model_val_acc: float | None = None
        self.model_version: str | None = None
        self.trained_at: str | None = None
        self.backbone: str | None = None
        self.preprocess_version: str | None = None
        self.dataset_fingerprint: str | None = None
        self.audio_model_path = Path(settings.model_path).parent / "best_audio_model.pth"
        self._try_load_model()

    def get_status(self) -> dict:
        return {
            "model_loaded": self.model is not None,
            "model_classes": self.model_classes,
            "model_val_acc": self.model_val_acc,
            "model_path": str(self.audio_model_path),
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
        if not self.audio_model_path.exists():
            logger.info(
                "Audio model file not found: %s (stub mode)",
                self.audio_model_path,
            )
            return
        try:
            import numpy as np
            import librosa
            import torch
            from torchvision import models
            import torch.nn as nn

            checkpoint = torch.load(self.audio_model_path, map_location="cpu")
            num_classes = checkpoint.get("num_classes", len(self.species_ids))
            self.model_classes = int(num_classes)
            self.model_val_acc = checkpoint.get("val_acc")
            self.model_version = checkpoint.get("model_version")
            self.trained_at = checkpoint.get("trained_at")
            self.backbone = checkpoint.get("backbone", "resnet18")
            self.preprocess_version = checkpoint.get("preprocess_version")
            self.dataset_fingerprint = checkpoint.get("dataset_fingerprint") or checkpoint.get(
                "dataset_report_hash"
            )
            model = models.resnet18(weights=None)
            model.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()
            self.model = model
            self.idx_to_species = checkpoint.get("idx_to_species", {})
            self._librosa = librosa
            self._np = np
            self._torch = torch
            logger.info(
                "Audio model loaded: %s classes (val_acc=%s) from %s",
                self.model_classes,
                self.model_val_acc,
                self.audio_model_path,
            )
        except Exception:
            logger.warning(
                "Failed to load audio model from %s; falling back to stub mode",
                self.audio_model_path,
                exc_info=True,
            )
            self.model = None

    def _audio_to_tensor(self, content: bytes):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        audio, _ = self._librosa.load(tmp_path, sr=22050, mono=True, duration=3.0)
        Path(tmp_path).unlink(missing_ok=True)
        target_len = 22050 * 3
        if len(audio) < target_len:
            audio = self._np.pad(audio, (0, target_len - len(audio)))
        else:
            audio = audio[:target_len]
        mel = self._librosa.feature.melspectrogram(y=audio, sr=22050, n_mels=128)
        mel_db = self._librosa.power_to_db(mel, ref=self._np.max)
        mel_db = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-6)
        arr = self._np.stack([mel_db, mel_db, mel_db], axis=0).astype("float32")
        return self._torch.from_numpy(arr).unsqueeze(0)

    def _predict_with_model(self, content: bytes) -> list[IdentificationCandidate]:
        tensor = self._audio_to_tensor(content)
        with self._torch.no_grad():
            logits = self.model(tensor)
            probs = self._torch.softmax(logits, dim=1)[0]
        topk = min(max(3, len(self.idx_to_species)), probs.shape[0])
        values, indices = self._torch.topk(probs, topk)
        candidates: list[IdentificationCandidate] = []
        for value, idx in zip(values.tolist(), indices.tolist()):
            species = self.idx_to_species.get(str(idx)) or self.idx_to_species.get(idx)
            if not species:
                continue
            if species["id"] not in self.known_species_ids:
                continue
            candidates.append(
                IdentificationCandidate(
                    species_id=species["id"],
                    common_name=species["common_name"],
                    scientific_name=species["scientific_name"],
                    confidence=round(float(value), 4),
                )
            )
            if len(candidates) == 3:
                break
        return candidates

    def _analyze_audio_features(self, content: bytes) -> dict:
        try:
            import librosa
            import numpy as np

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            audio, sr = librosa.load(tmp_path, sr=22050, mono=True, duration=5.0)
            Path(tmp_path).unlink(missing_ok=True)
            duration = float(librosa.get_duration(y=audio, sr=sr))
            rms = float(np.mean(librosa.feature.rms(y=audio)))
            zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio)))
            return {"duration": duration, "rms": rms, "zcr": zcr, "valid": duration >= 0.5}
        except Exception:
            logger.warning(
                "Audio feature analysis failed; using empty feature set",
                exc_info=True,
            )
            return {"duration": 0, "rms": 0, "zcr": 0, "valid": False}

    def _predict_stub(self, features: dict) -> list[IdentificationCandidate]:
        if not self.species_ids:
            return []
        if not features.get("valid"):
            return [
                IdentificationCandidate(
                    species_id="cettia_diphone",
                    common_name="새사촌",
                    scientific_name="Cettia diphone",
                    confidence=0.35,
                )
            ]
        ranked = random.sample(self.species_ids, min(3, len(self.species_ids)))
        confidences = [0.68, 0.18, 0.09]
        return [
            IdentificationCandidate(
                species_id=item["id"],
                common_name=item["common_name"],
                scientific_name=item["scientific_name"],
                confidence=confidences[i] if i < len(confidences) else 0.05,
            )
            for i, item in enumerate(ranked)
        ]

    def identify(self, content: bytes, filename: str = "") -> IdentificationResult:
        features = self._analyze_audio_features(content)
        if self.model is not None:
            try:
                candidates = self._predict_with_model(content)
                source = "model"
                message = f"오디오 모델로 식별했습니다. 길이 {features['duration']:.1f}초."
            except Exception:
                logger.warning(
                    "Audio model inference failed; falling back to stub mode",
                    exc_info=True,
                )
                candidates = self._predict_stub(features)
                source = "stub"
                message = (
                    f"오디오 스펙트로그램 분석 완료 (길이 {features['duration']:.1f}초). "
                    "추론 실패 — 스텁 결과를 반환합니다."
                )
        else:
            candidates = self._predict_stub(features)
            source = "stub"
            message = (
                f"오디오 스펙트로그램 분석 완료 (길이 {features['duration']:.1f}초). "
                "학습 모델 없음 — models/train_audio.py로 best_audio_model.pth를 생성하세요."
            )
        if not features.get("valid"):
            message += " 녹음이 너무 짧습니다. 1초 이상 권장합니다."
        if filename:
            message += f" 파일: {filename}"
        return IdentificationResult(
            media_type="audio",
            candidates=candidates,
            message=message,
            source=source,
        )


audio_identify_service = AudioIdentifyService()
