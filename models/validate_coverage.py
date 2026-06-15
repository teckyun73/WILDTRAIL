"""
WildTrail 클래스 커버리지 검증 스크립트

species.json ↔ train/val 데이터 ↔ checkpoint classes 일치 여부를 점검합니다.

사용법:
  cd models
  python validate_coverage.py --data-dir ../data/images --checkpoint checkpoints/best_model.pth
  python validate_coverage.py --strict   # 불일치 시 exit code 1 (CI용)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import torch

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def iter_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_species_meta(species_file: Path) -> list[dict]:
    with species_file.open(encoding="utf-8") as f:
        return json.load(f)


def load_manifest_targets(manifest_file: Path) -> dict[str, int]:
    if not manifest_file.exists():
        return {}
    with manifest_file.open(encoding="utf-8") as f:
        manifest = json.load(f)
    return {item["id"]: int(item.get("target_count", 80)) for item in manifest.get("species", [])}


def list_class_dirs(split_dir: Path) -> dict[str, Path]:
    if not split_dir.exists():
        return {}
    return {
        child.name: child
        for child in sorted(split_dir.iterdir())
        if child.is_dir()
    }


def load_checkpoint_classes(checkpoint_path: Path | None) -> list[str]:
    if checkpoint_path is None or not checkpoint_path.exists():
        return []
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    return list(checkpoint.get("classes", []))


@dataclass
class SpeciesCoverage:
    species_id: str
    common_name: str
    raw_count: int = 0
    train_count: int = 0
    val_count: int = 0
    total_labeled: int = 0
    target_count: int = 80
    in_species_json: bool = True
    in_train: bool = False
    in_val: bool = False
    in_checkpoint: bool = False
    train_empty: bool = False
    val_empty: bool = False
    status: str = "OK"
    issues: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    checked_at: str
    species_json_count: int
    train_class_count: int
    val_class_count: int
    checkpoint_class_count: int
    min_images_per_species: int
    in_sync: bool
    warnings: list[str] = field(default_factory=list)
    missing_from_train: list[str] = field(default_factory=list)
    missing_from_val: list[str] = field(default_factory=list)
    missing_from_checkpoint: list[str] = field(default_factory=list)
    extra_in_train: list[str] = field(default_factory=list)
    extra_in_val: list[str] = field(default_factory=list)
    extra_in_checkpoint: list[str] = field(default_factory=list)
    empty_train_folders: list[str] = field(default_factory=list)
    empty_val_folders: list[str] = field(default_factory=list)
    low_image_species: list[str] = field(default_factory=list)
    species: list[SpeciesCoverage] = field(default_factory=list)


def build_coverage_report(
    *,
    data_dir: Path,
    species_file: Path,
    manifest_file: Path,
    checkpoint_path: Path | None,
    min_images: int,
) -> CoverageReport:
    species_meta = load_species_meta(species_file)
    species_ids = [item["id"] for item in species_meta]
    common_names = {item["id"]: item.get("common_name", item["id"]) for item in species_meta}
    targets = load_manifest_targets(manifest_file)

    raw_dirs = list_class_dirs(data_dir / "raw")
    train_dirs = list_class_dirs(data_dir / "train")
    val_dirs = list_class_dirs(data_dir / "val")
    checkpoint_classes = load_checkpoint_classes(checkpoint_path)
    checkpoint_set = set(checkpoint_classes)

    all_observed = (
        set(species_ids)
        | set(train_dirs)
        | set(val_dirs)
        | set(raw_dirs)
        | checkpoint_set
    )

    species_rows: list[SpeciesCoverage] = []
    warnings: list[str] = []
    missing_from_train: list[str] = []
    missing_from_val: list[str] = []
    missing_from_checkpoint: list[str] = []
    empty_train_folders: list[str] = []
    empty_val_folders: list[str] = []
    low_image_species: list[str] = []

    for species_id in sorted(all_observed):
        in_json = species_id in species_ids
        train_path = train_dirs.get(species_id)
        val_path = val_dirs.get(species_id)
        raw_count = len(iter_images(raw_dirs[species_id])) if species_id in raw_dirs else 0
        train_count = len(iter_images(train_path)) if train_path else 0
        val_count = len(iter_images(val_path)) if val_path else 0
        total_labeled = train_count + val_count
        target = targets.get(species_id, min_images)

        row = SpeciesCoverage(
            species_id=species_id,
            common_name=common_names.get(species_id, species_id),
            raw_count=raw_count,
            train_count=train_count,
            val_count=val_count,
            total_labeled=total_labeled,
            target_count=target,
            in_species_json=in_json,
            in_train=species_id in train_dirs,
            in_val=species_id in val_dirs,
            in_checkpoint=species_id in checkpoint_set,
            train_empty=bool(train_path) and train_count == 0,
            val_empty=bool(val_path) and val_count == 0,
        )

        if not in_json:
            row.status = "EXTRA"
            row.issues.append("species.json에 없는 폴더/클래스")
        elif species_id not in train_dirs:
            row.status = "MISSING_TRAIN"
            row.issues.append("train 폴더 없음")
            missing_from_train.append(species_id)
        elif train_count == 0:
            row.status = "EMPTY_TRAIN"
            row.issues.append("train 폴더가 비어 있음")
            empty_train_folders.append(species_id)
            missing_from_train.append(species_id)
        elif species_id not in val_dirs:
            row.status = "MISSING_VAL"
            row.issues.append("val 폴더 없음")
            missing_from_val.append(species_id)
        elif val_count == 0:
            row.status = "EMPTY_VAL"
            row.issues.append("val 폴더가 비어 있음")
            empty_val_folders.append(species_id)
            missing_from_val.append(species_id)
        elif total_labeled < min_images:
            row.status = "LOW"
            row.issues.append(f"학습 가능 이미지 {total_labeled}장 < 최소 {min_images}장")
            low_image_species.append(species_id)
        elif checkpoint_set and species_id not in checkpoint_set:
            row.status = "MISSING_CHECKPOINT"
            row.issues.append("checkpoint classes에 없음")
            missing_from_checkpoint.append(species_id)
        else:
            row.status = "OK"

        if checkpoint_set and in_json and species_id not in checkpoint_set:
            if species_id not in missing_from_checkpoint:
                missing_from_checkpoint.append(species_id)

        species_rows.append(row)

    extra_in_train = sorted(set(train_dirs) - set(species_ids))
    extra_in_val = sorted(set(val_dirs) - set(species_ids))
    extra_in_checkpoint = sorted(checkpoint_set - set(species_ids))

    if missing_from_train:
        warnings.append(
            f"species.json 대비 train 누락 {len(missing_from_train)}종: {', '.join(missing_from_train)}"
        )
    if missing_from_val:
        warnings.append(
            f"species.json 대비 val 누락 {len(missing_from_val)}종: {', '.join(missing_from_val)}"
        )
    if checkpoint_set and missing_from_checkpoint:
        warnings.append(
            f"checkpoint 대비 누락 {len(missing_from_checkpoint)}종: "
            f"{', '.join(missing_from_checkpoint)}"
        )
    if extra_in_train:
        warnings.append(f"train에만 있는 미등록 폴더: {', '.join(extra_in_train)}")
    if extra_in_val:
        warnings.append(f"val에만 있는 미등록 폴더: {', '.join(extra_in_val)}")
    if extra_in_checkpoint:
        warnings.append(f"checkpoint에만 있는 클래스: {', '.join(extra_in_checkpoint)}")
    if low_image_species:
        warnings.append(
            f"80장 미만 종 {len(low_image_species)}개: {', '.join(low_image_species)}"
        )

    json_species = set(species_ids)
    train_species_with_data = {
        sid for sid, path in train_dirs.items() if len(iter_images(path)) > 0
    }
    val_species_with_data = {sid for sid, path in val_dirs.items() if len(iter_images(path)) > 0}

    in_sync = (
        not missing_from_train
        and not missing_from_val
        and not empty_train_folders
        and not empty_val_folders
        and not extra_in_train
        and not extra_in_val
        and not low_image_species
        and (not checkpoint_set or not missing_from_checkpoint)
        and (not checkpoint_set or checkpoint_set == train_species_with_data)
    )

    return CoverageReport(
        checked_at=datetime.now(timezone.utc).isoformat(),
        species_json_count=len(species_ids),
        train_class_count=len(train_dirs),
        val_class_count=len(val_dirs),
        checkpoint_class_count=len(checkpoint_classes),
        min_images_per_species=min_images,
        in_sync=in_sync,
        warnings=warnings,
        missing_from_train=sorted(set(missing_from_train)),
        missing_from_val=sorted(set(missing_from_val)),
        missing_from_checkpoint=sorted(set(missing_from_checkpoint)),
        extra_in_train=extra_in_train,
        extra_in_val=extra_in_val,
        extra_in_checkpoint=extra_in_checkpoint,
        empty_train_folders=sorted(empty_train_folders),
        empty_val_folders=sorted(empty_val_folders),
        low_image_species=sorted(low_image_species),
        species=species_rows,
    )


def print_report(report: CoverageReport) -> None:
    print("WildTrail Class Coverage Report")
    print("=" * 72)
    print(f"species.json     : {report.species_json_count}")
    print(f"train folders    : {report.train_class_count}")
    print(f"val folders      : {report.val_class_count}")
    print(f"checkpoint classes: {report.checkpoint_class_count}")
    print(f"min images/species: {report.min_images_per_species}")
    print(f"in_sync          : {report.in_sync}")
    print("-" * 72)
    print(
        f"{'species_id':<28} {'train':>6} {'val':>5} {'total':>6} "
        f"{'ckpt':>5} {'status':<16} common_name"
    )
    print("-" * 72)
    for row in report.species:
        if not row.in_species_json:
            continue
        ckpt = "Y" if row.in_checkpoint else "-"
        print(
            f"{row.species_id:<28} {row.train_count:>6} {row.val_count:>5} "
            f"{row.total_labeled:>6} {ckpt:>5} {row.status:<16} {row.common_name}"
        )

    extras = [row for row in report.species if not row.in_species_json]
    if extras:
        print("-" * 72)
        print("Extra folders/classes (not in species.json):")
        for row in extras:
            print(
                f"  {row.species_id}: train={row.train_count}, val={row.val_count}, "
                f"status={row.status}"
            )

    if report.warnings:
        print("-" * 72)
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")


def main() -> None:
    root = project_root()
    parser = argparse.ArgumentParser(description="Validate species/class coverage")
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "images")
    parser.add_argument("--species-file", type=Path, default=root / "data" / "species.json")
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=root / "data" / "dataset_manifest.json",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("checkpoints/best_model.pth"),
        help="checkpoint 경로 (없으면 데이터만 검증)",
    )
    parser.add_argument("--output", type=Path, default=root / "reports" / "coverage_report.json")
    parser.add_argument("--min-images", type=int, default=80)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="불일치/누락 시 exit code 1 반환 (CI·학습 전 게이트)",
    )
    args = parser.parse_args()

    checkpoint = args.checkpoint if args.checkpoint.exists() else None
    if args.checkpoint and not checkpoint:
        print(f"Note: checkpoint not found ({args.checkpoint}), skipping model class check.")

    report = build_coverage_report(
        data_dir=args.data_dir,
        species_file=args.species_file,
        manifest_file=args.manifest_file,
        checkpoint_path=checkpoint,
        min_images=args.min_images,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    print_report(report)
    print("-" * 72)
    print(f"Saved: {args.output.resolve()}")

    if args.strict and not report.in_sync:
        print("STRICT: coverage check failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
