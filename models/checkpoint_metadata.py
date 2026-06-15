"""
WildTrail checkpoint 메타데이터 유틸리티

학습 시 checkpoint에 버전·데이터 지문·전처리 정보를 함께 저장합니다.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def count_split_images(split_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not split_dir.exists():
        return counts
    for class_dir in sorted(split_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        counts[class_dir.name] = len(
            [
                p
                for p in class_dir.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
            ]
        )
    return counts


def compute_dataset_fingerprint(data_dir: Path) -> str:
    """train/val 종별 이미지 수 기반 지문 (dataset_report_hash 용도)."""
    payload: dict[str, dict[str, int]] = {}
    for split in ("train", "val"):
        payload[split] = count_split_images(data_dir / split)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return digest[:16]


def build_model_version(
    *,
    backbone: str,
    num_classes: int,
    dataset_fingerprint: str,
    trained_at: str,
) -> str:
    date_part = trained_at[:10].replace("-", "")
    return f"wildtrail-{backbone}-{num_classes}c-{date_part}-{dataset_fingerprint[:8]}"


def build_training_metadata(
    *,
    data_dir: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    preprocess_version: str,
    backbone: str = "efficientnet_b0",
    trained_at: str | None = None,
) -> dict:
    trained_at = trained_at or datetime.now(timezone.utc).isoformat()
    fingerprint = compute_dataset_fingerprint(data_dir)
    train_counts = count_split_images(data_dir / "train")
    val_counts = count_split_images(data_dir / "val")
    num_classes = len(train_counts)

    return {
        "model_version": build_model_version(
            backbone=backbone,
            num_classes=num_classes,
            dataset_fingerprint=fingerprint,
            trained_at=trained_at,
        ),
        "trained_at": trained_at,
        "backbone": backbone,
        "preprocess_version": preprocess_version,
        "dataset_fingerprint": fingerprint,
        "dataset_report_hash": fingerprint,
        "dataset_summary": {
            "train_images": sum(train_counts.values()),
            "val_images": sum(val_counts.values()),
            "train_classes": len(train_counts),
            "val_classes": len(val_counts),
        },
        "training": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "data_dir": str(data_dir.resolve()),
        },
    }


def merge_checkpoint_payload(
    *,
    model_state_dict,
    num_classes: int,
    classes: list[str],
    idx_to_species: dict,
    val_acc: float,
    data_dir: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    preprocess_version: str,
) -> dict:
    meta = build_training_metadata(
        data_dir=data_dir,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        preprocess_version=preprocess_version,
    )
    return {
        "model_state_dict": model_state_dict,
        "num_classes": num_classes,
        "classes": classes,
        "idx_to_species": idx_to_species,
        "val_acc": val_acc,
        **meta,
    }
