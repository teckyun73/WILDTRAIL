"""
WildTrail 이미지 데이터셋 준비 도구

명령:
  python prepare_dataset.py init
  python prepare_dataset.py validate --dir ../data/images/raw
  python prepare_dataset.py split --raw-dir ../data/images/raw --out-dir ../data/images
  python prepare_dataset.py report --dir ../data/images
  python prepare_dataset.py dedupe --dir ../data/images/raw
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MIN_SIZE = 224


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_species_ids(root: Path) -> list[str]:
    species_file = root / "data" / "species.json"
    with species_file.open(encoding="utf-8") as f:
        return [item["id"] for item in json.load(f)]


def load_manifest(root: Path) -> dict:
    manifest_file = root / "data" / "dataset_manifest.json"
    if not manifest_file.exists():
        return {}
    with manifest_file.open(encoding="utf-8") as f:
        return json.load(f)


def iter_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        p
        for p in directory.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def cmd_init(args: argparse.Namespace) -> None:
    root = project_root()
    species_ids = load_species_ids(root)
    base = Path(args.out_dir)
    for sub in ("raw", "train", "val", "rejected"):
        for species_id in species_ids:
            (base / sub / species_id).mkdir(parents=True, exist_ok=True)
    print(f"Created folders for {len(species_ids)} species under {base.resolve()}")


def validate_image(path: Path) -> tuple[bool, str]:
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if w < MIN_SIZE or h < MIN_SIZE:
                return False, f"too_small:{w}x{h}"
    except Exception as exc:
        return False, f"corrupt:{exc}"
    return True, "ok"


def cmd_validate(args: argparse.Namespace) -> None:
    target = Path(args.dir)
    images = iter_images(target)
    ok_count = 0
    bad: list[tuple[str, str]] = []
    for path in images:
        valid, reason = validate_image(path)
        if valid:
            ok_count += 1
        else:
            bad.append((str(path), reason))
    print(f"Validated {len(images)} images: ok={ok_count}, bad={len(bad)}")
    for path, reason in bad[:30]:
        print(f"  [FAIL] {path} ({reason})")
    if len(bad) > 30:
        print(f"  ... and {len(bad) - 30} more")


def cmd_split(args: argparse.Namespace) -> None:
    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    random.seed(args.seed)

    for species_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        images = iter_images(species_dir)
        if not images:
            continue
        random.shuffle(images)
        val_count = max(1, int(len(images) * args.val_ratio))
        val_set = set(images[:val_count])
        train_set = images[val_count:]

        for subset_name, subset_files in (("train", train_set), ("val", list(val_set))):
            dest_root = out_dir / subset_name / species_dir.name
            if args.clear:
                if dest_root.exists():
                    shutil.rmtree(dest_root)
            dest_root.mkdir(parents=True, exist_ok=True)
            for src in subset_files:
                dest = dest_root / src.name
                if args.copy:
                    shutil.copy2(src, dest)
                else:
                    shutil.move(str(src), dest)

        print(
            f"{species_dir.name}: total={len(images)} "
            f"train={len(train_set)} val={len(val_set)}"
        )


def cmd_report(args: argparse.Namespace) -> None:
    root = project_root()
    base = Path(args.dir)
    manifest = load_manifest(root)
    targets = {
        item["id"]: item.get("target_count", 80)
        for item in manifest.get("species", [])
    }
    min_required = manifest.get("min_images_per_species", 80)

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for subset in ("raw", "train", "val"):
        subset_dir = base / subset
        if not subset_dir.exists():
            continue
        for species_dir in subset_dir.iterdir():
            if species_dir.is_dir():
                counts[species_dir.name][subset] = len(iter_images(species_dir))

    species_ids = load_species_ids(root)
    print(f"{'species_id':<28} {'raw':>5} {'train':>6} {'val':>5} {'total':>6} {'target':>7} status")
    print("-" * 72)
    insufficient = 0
    for species_id in species_ids:
        raw = counts[species_id].get("raw", 0)
        train = counts[species_id].get("train", 0)
        val = counts[species_id].get("val", 0)
        total = raw + train + val if raw else train + val
        target = targets.get(species_id, min_required)
        status = "OK" if total >= min_required else "LOW"
        if status == "LOW":
            insufficient += 1
        print(
            f"{species_id:<28} {raw:>5} {train:>6} {val:>5} {total:>6} {target:>7} {status}"
        )
    print("-" * 72)
    print(f"Insufficient species (<{min_required}): {insufficient}/{len(species_ids)}")


def file_hash(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_dedupe(args: argparse.Namespace) -> None:
    target = Path(args.dir)
    seen: dict[str, Path] = {}
    duplicates: list[tuple[Path, Path]] = []
    for path in iter_images(target):
        digest = file_hash(path)
        if digest in seen:
            duplicates.append((path, seen[digest]))
        else:
            seen[digest] = path

    print(f"Found {len(duplicates)} duplicate files")
    if not duplicates:
        return

    reject_dir = target.parent / "rejected" / "_duplicates"
    reject_dir.mkdir(parents=True, exist_ok=True)
    for dup, original in duplicates:
        if args.move:
            dest = reject_dir / dup.name
            shutil.move(str(dup), dest)
            print(f"MOVED {dup} (dup of {original})")
        else:
            print(f"DUP {dup} == {original}")


def cmd_hard_negative(args: argparse.Namespace) -> None:
    from hard_negative_report import build_report, print_report, save_baseline

    root = project_root()
    manifest_file = Path(args.manifest)
    data_dir = Path(args.data_dir)
    species_file = root / "data" / "species.json"
    confusion_csv = Path(args.confusion_csv)
    output = Path(args.output)

    report = build_report(
        manifest_file,
        data_dir,
        species_file,
        confusion_csv,
        baseline_file=(
            root / "reports" / "hard_negative_baseline.json"
            if (root / "reports" / "hard_negative_baseline.json").exists()
            else None
        ),
    )
    species_names = {
        item["id"]: item.get("common_name", item["id"])
        for item in json.load(species_file.open(encoding="utf-8"))
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": report.generated_at,
                "manifest_version": report.manifest_version,
                "hard_negative_extra_per_pair": report.hard_negative_extra_per_pair,
                "pairs": [pair.__dict__ for pair in report.pairs],
                "summary": report.summary,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print_report(report, species_names)
    print(f"Saved: {output.resolve()}")
    if args.save_baseline:
        metrics_file = root / "reports" / "metrics.json"
        save_baseline(
            report,
            Path(args.save_baseline),
            metrics_file,
            data_dir,
            manifest_file,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WildTrail dataset utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create raw/train/val/rejected folders")
    p_init.add_argument("--out-dir", type=Path, default=project_root() / "data" / "images")
    p_init.set_defaults(func=cmd_init)

    p_val = sub.add_parser("validate", help="Validate image files")
    p_val.add_argument("--dir", type=Path, required=True)
    p_val.set_defaults(func=cmd_validate)

    p_split = sub.add_parser("split", help="Split raw into train/val")
    p_split.add_argument("--raw-dir", type=Path, required=True)
    p_split.add_argument("--out-dir", type=Path, required=True)
    p_split.add_argument("--val-ratio", type=float, default=0.2)
    p_split.add_argument("--seed", type=int, default=42)
    p_split.add_argument("--copy", action="store_true", help="Copy instead of move")
    p_split.add_argument("--clear", action="store_true", help="Clear train/val before split")
    p_split.set_defaults(func=cmd_split)

    p_report = sub.add_parser("report", help="Report per-species counts")
    p_report.add_argument("--dir", type=Path, default=project_root() / "data" / "images")
    p_report.set_defaults(func=cmd_report)

    p_dedupe = sub.add_parser("dedupe", help="Find duplicate images by MD5")
    p_dedupe.add_argument("--dir", type=Path, required=True)
    p_dedupe.add_argument("--move", action="store_true", help="Move duplicates to rejected/")
    p_dedupe.set_defaults(func=cmd_dedupe)

    p_hn = sub.add_parser("hard-negative", help="Hard negative 수집 진행 리포트")
    p_hn.add_argument(
        "--manifest",
        type=Path,
        default=project_root() / "data" / "dataset_manifest.json",
    )
    p_hn.add_argument("--data-dir", type=Path, default=project_root() / "data" / "images")
    p_hn.add_argument(
        "--confusion-csv",
        type=Path,
        default=project_root() / "reports" / "confusion_matrix.csv",
    )
    p_hn.add_argument(
        "--output",
        type=Path,
        default=project_root() / "reports" / "hard_negative_progress.json",
    )
    p_hn.add_argument(
        "--save-baseline",
        type=Path,
        nargs="?",
        const=project_root() / "reports" / "hard_negative_baseline.json",
    )
    p_hn.set_defaults(func=cmd_hard_negative)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
