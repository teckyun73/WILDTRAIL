"""
WildTrail 오디오 train/val 분리 스크립트

기존 data/audio/train/<species_id>/ 파일에서 검증 세트를 분리합니다.

사용법:
  cd models
  .\\ml.ps1 split_audio.py --data-dir ..\\data\\audio
  .\\ml.ps1 split_audio.py --data-dir ..\\data\\audio --dry-run
  .\\ml.ps1 split_audio.py --data-dir ..\\data\\audio --clear-val --copy
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


def iter_audio_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def clear_split_dirs(data_dir: Path, *, clear_train: bool, clear_val: bool) -> None:
    for split_name, enabled in (("train", clear_train), ("val", clear_val)):
        if not enabled:
            continue
        split_dir = data_dir / split_name
        if split_dir.exists():
            shutil.rmtree(split_dir)
        split_dir.mkdir(parents=True, exist_ok=True)


def split_from_train(args: argparse.Namespace) -> dict:
    data_dir = Path(args.data_dir)
    train_root = data_dir / "train"
    val_root = data_dir / "val"

    if not train_root.exists():
        raise FileNotFoundError(
            f"{train_root} 없음. data/audio/train/<species_id>/ 구조로 데이터를 준비하세요."
        )

    if args.clear_val or args.clear:
        clear_split_dirs(data_dir, clear_train=False, clear_val=True)
    val_root.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    summary: dict = {
        "split_at": datetime.now(timezone.utc).isoformat(),
        "data_dir": str(data_dir.resolve()),
        "source": "train",
        "val_ratio": args.val_ratio,
        "seed": args.seed,
        "copy": args.copy,
        "species": [],
        "totals": {"train": 0, "val": 0, "skipped_species": 0},
    }

    species_dirs = sorted(path for path in train_root.iterdir() if path.is_dir())
    if not species_dirs:
        raise FileNotFoundError(f"{train_root} 아래 종 폴더가 없습니다.")

    for species_dir in species_dirs:
        files = iter_audio_files(species_dir)
        if not files:
            summary["totals"]["skipped_species"] += 1
            print(f"{species_dir.name}: SKIP (train 파일 없음)")
            continue

        random.shuffle(files)
        val_count = max(1, int(len(files) * args.val_ratio))
        if len(files) - val_count < 1:
            val_count = max(1, len(files) - 1)

        val_files = files[:val_count]
        train_files = files[val_count:]
        val_dest_root = val_root / species_dir.name
        val_dest_root.mkdir(parents=True, exist_ok=True)

        moved = 0
        for src in val_files:
            dest = val_dest_root / src.name
            if dest.exists():
                if args.skip_existing:
                    continue
                raise FileExistsError(f"이미 존재: {dest} (--skip-existing 사용)")
            if args.dry_run:
                moved += 1
                continue
            if args.copy:
                shutil.copy2(src, dest)
            else:
                shutil.move(str(src), str(dest))
            moved += 1

        species_report = {
            "species_id": species_dir.name,
            "before_total": len(files),
            "train_count": len(train_files),
            "val_count": moved if args.dry_run else len(list(iter_audio_files(val_dest_root))),
            "planned_val_count": len(val_files),
        }
        summary["species"].append(species_report)
        summary["totals"]["train"] += species_report["train_count"]
        summary["totals"]["val"] += species_report["planned_val_count"] if args.dry_run else species_report["val_count"]

        action = "would move" if args.dry_run else ("copied" if args.copy else "moved")
        print(
            f"{species_dir.name}: total={len(files)} "
            f"train={species_report['train_count']} val={species_report['planned_val_count']} ({action})"
        )

    return summary


def split_from_raw(args: argparse.Namespace) -> dict:
    data_dir = Path(args.data_dir)
    raw_root = data_dir / "raw"
    train_root = data_dir / "train"
    val_root = data_dir / "val"

    if not raw_root.exists():
        raise FileNotFoundError(
            f"{raw_root} 없음. data/audio/raw/<species_id>/ 구조로 데이터를 준비하세요."
        )

    if args.clear or args.clear_val:
        clear_split_dirs(data_dir, clear_train=args.clear, clear_val=args.clear or args.clear_val)
    train_root.mkdir(parents=True, exist_ok=True)
    val_root.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    summary: dict = {
        "split_at": datetime.now(timezone.utc).isoformat(),
        "data_dir": str(data_dir.resolve()),
        "source": "raw",
        "val_ratio": args.val_ratio,
        "seed": args.seed,
        "copy": args.copy,
        "species": [],
        "totals": {"train": 0, "val": 0, "skipped_species": 0},
    }

    species_dirs = sorted(path for path in raw_root.iterdir() if path.is_dir())
    for species_dir in species_dirs:
        files = iter_audio_files(species_dir)
        if not files:
            summary["totals"]["skipped_species"] += 1
            print(f"{species_dir.name}: SKIP (raw 파일 없음)")
            continue

        random.shuffle(files)
        val_count = max(1, int(len(files) * args.val_ratio))
        if len(files) - val_count < 1:
            val_count = max(1, len(files) - 1)

        val_files = files[:val_count]
        train_files = files[val_count:]

        for split_name, split_files in (("train", train_files), ("val", val_files)):
            dest_root = data_dir / split_name / species_dir.name
            dest_root.mkdir(parents=True, exist_ok=True)
            for src in split_files:
                dest = dest_root / src.name
                if dest.exists() and args.skip_existing:
                    continue
                if args.dry_run:
                    continue
                if args.copy:
                    shutil.copy2(src, dest)
                else:
                    shutil.move(str(src), dest)

        species_report = {
            "species_id": species_dir.name,
            "before_total": len(files),
            "train_count": len(train_files),
            "val_count": len(val_files),
        }
        summary["species"].append(species_report)
        summary["totals"]["train"] += species_report["train_count"]
        summary["totals"]["val"] += species_report["val_count"]

        action = "would split" if args.dry_run else ("copied" if args.copy else "moved")
        print(
            f"{species_dir.name}: total={len(files)} "
            f"train={species_report['train_count']} val={species_report['val_count']} ({action})"
        )

    return summary


def save_report(summary: dict, output: Path | None) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved report: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split WildTrail audio data into train/val")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("../data/audio"),
        help="data/audio 루트 (train/ 또는 raw/ 포함)",
    )
    parser.add_argument(
        "--source",
        choices=("train", "raw"),
        default="train",
        help="train: 기존 train에서 val 분리 | raw: raw에서 train+val 생성",
    )
    parser.add_argument("--val-ratio", type=float, default=0.2, help="검증 비율 (기본 0.2)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--copy",
        action="store_true",
        help="이동 대신 복사 (train 원본 유지)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="source=raw 일 때 train/val 전체 삭제 후 재생성",
    )
    parser.add_argument(
        "--clear-val",
        action="store_true",
        help="source=train 일 때 val/만 삭제 후 재분리",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="대상 파일이 이미 있으면 건너뜀",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="파일 이동 없이 분리 계획만 출력",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="JSON 리포트 저장 경로 (예: ../reports/audio_split_report.json)",
    )
    args = parser.parse_args()

    if not 0 < args.val_ratio < 1:
        raise SystemExit("--val-ratio는 0과 1 사이여야 합니다.")

    if args.source == "raw":
        summary = split_from_raw(args)
    else:
        summary = split_from_train(args)

    print(
        f"\nDone ({args.source}): "
        f"train={summary['totals']['train']} val={summary['totals']['val']} "
        f"species={len(summary['species'])}"
    )
    if args.dry_run:
        print("DRY RUN - no files were changed.")

    default_report = Path(args.data_dir) / "split_report.json"
    save_report(summary, args.report or default_report)


if __name__ == "__main__":
    main()
