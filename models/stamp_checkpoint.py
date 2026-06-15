"""
기존 checkpoint에 메타데이터를 소급 적용합니다.

사용법:
  cd models
  python stamp_checkpoint.py --checkpoint checkpoints/best_model.pth --data-dir ../data/images
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import torch

from checkpoint_metadata import build_model_version, compute_dataset_fingerprint
from image_transforms import PREPROCESS_VERSION


def stamp_checkpoint(
    checkpoint_path: Path,
    data_dir: Path,
    *,
    note: str = "retroactive metadata stamp",
) -> dict:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    fingerprint = compute_dataset_fingerprint(data_dir)
    num_classes = int(checkpoint.get("num_classes", len(checkpoint.get("classes", []))))
    trained_at = checkpoint.get("trained_at")
    if not trained_at:
        mtime = datetime.fromtimestamp(checkpoint_path.stat().st_mtime, tz=timezone.utc)
        trained_at = mtime.isoformat()

    backbone = checkpoint.get("backbone", "efficientnet_b0")
    model_version = checkpoint.get("model_version") or build_model_version(
        backbone=backbone,
        num_classes=num_classes,
        dataset_fingerprint=fingerprint,
        trained_at=trained_at,
    )

    checkpoint.update(
        {
            "model_version": model_version,
            "trained_at": trained_at,
            "backbone": backbone,
            "preprocess_version": checkpoint.get("preprocess_version", PREPROCESS_VERSION),
            "dataset_fingerprint": fingerprint,
            "dataset_report_hash": fingerprint,
            "metadata_note": note,
        }
    )
    torch.save(checkpoint, checkpoint_path)
    return {
        "model_version": model_version,
        "trained_at": trained_at,
        "dataset_fingerprint": fingerprint,
        "preprocess_version": checkpoint["preprocess_version"],
        "val_acc": checkpoint.get("val_acc"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Stamp metadata into an existing checkpoint")
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/best_model.pth"))
    parser.add_argument("--data-dir", type=Path, default=Path("../data/images"))
    parser.add_argument("--note", type=str, default="retroactive metadata stamp")
    args = parser.parse_args()

    if not args.checkpoint.exists():
        raise FileNotFoundError(f"checkpoint not found: {args.checkpoint}")

    result = stamp_checkpoint(args.checkpoint, args.data_dir, note=args.note)
    print(f"Stamped: {args.checkpoint.resolve()}")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
