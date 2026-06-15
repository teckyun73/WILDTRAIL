"""
WildTrail hard negative 데이터 보강 진행 리포트

dataset_manifest.json 의 confusion_pairs 대비 raw/train 수집 현황과
confusion matrix 기반 혼동률을 추적합니다.

사용법:
  cd models
  python hard_negative_report.py
  python hard_negative_report.py --save-baseline ../reports/hard_negative_baseline.json
  python hard_negative_report.py --compare-baseline ../reports/hard_negative_baseline.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_species_names(species_file: Path) -> dict[str, str]:
    if not species_file.exists():
        return {}
    return {item["id"]: item.get("common_name", item["id"]) for item in load_json(species_file)}


def count_images(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(
        [p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    )


def load_confusion_matrix(path: Path) -> tuple[list[str], list[list[int]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        class_ids = header[1:]
        rows: list[list[int]] = []
        for row in reader:
            rows.append([int(v) for v in row[1:]])
    return class_ids, rows


def pair_confusion_stats(
    class_ids: list[str],
    matrix: list[list[int]],
    species_a: str,
    species_b: str,
) -> dict:
    if species_a not in class_ids or species_b not in class_ids:
        return {"available": False, "species_a": species_a, "species_b": species_b}
    idx_a = class_ids.index(species_a)
    idx_b = class_ids.index(species_b)
    a_total = sum(matrix[idx_a])
    b_total = sum(matrix[idx_b])
    a_as_b = matrix[idx_a][idx_b]
    b_as_a = matrix[idx_b][idx_a]
    bidirectional = a_as_b + b_as_a
    return {
        "available": True,
        "species_a": species_a,
        "species_b": species_b,
        "a_total": a_total,
        "b_total": b_total,
        "a_misclassified_as_b": a_as_b,
        "b_misclassified_as_a": b_as_a,
        "bidirectional_count": bidirectional,
        "a_confusion_rate": round(a_as_b / a_total, 4) if a_total else 0.0,
        "b_confusion_rate": round(b_as_a / b_total, 4) if b_total else 0.0,
        "combined_confusion_rate": round(
            bidirectional / (a_total + b_total), 4
        )
        if (a_total + b_total)
        else 0.0,
    }


@dataclass
class PairProgress:
    pair: list[str]
    priority: str
    target_extra: int
    reason: str
    baseline_combined_confusion_rate: float
    current_combined_confusion_rate: float | None = None
    improvement_pp: float | None = None
    target_reduction_rate: float = 0.2
    meets_target: bool | None = None
    species_progress: list[dict] = field(default_factory=list)
    status: str = "PENDING"
    collection_tips: list[str] = field(default_factory=list)


@dataclass
class HardNegativeReport:
    generated_at: str
    manifest_version: int
    hard_negative_extra_per_pair: int
    pairs: list[PairProgress]
    summary: dict


def build_pair_progress(
    pair_def: dict,
    data_dir: Path,
    species_names: dict[str, str],
    current_stats: dict | None,
    baseline_raw_counts: dict[str, int] | None,
) -> PairProgress:
    species_a, species_b = pair_def["pair"]
    target_extra = int(pair_def.get("target_extra", 50))
    baseline_rate = float(pair_def.get("baseline_combined_confusion_rate", 0.0))
    target_reduction = float(pair_def.get("target_reduction_rate", 0.2))

    species_progress = []
    pair_ready = True
    for species_id in pair_def["pair"]:
        raw_count = count_images(data_dir / "raw" / species_id)
        train_count = count_images(data_dir / "train" / species_id)
        val_count = count_images(data_dir / "val" / species_id)
        baseline_raw = (
            baseline_raw_counts.get(species_id, raw_count)
            if baseline_raw_counts
            else raw_count
        )
        additional_collected = max(0, raw_count - baseline_raw)
        gap = max(0, target_extra - additional_collected)
        if gap > 0:
            pair_ready = False
        species_progress.append(
            {
                "species_id": species_id,
                "common_name": species_names.get(species_id, species_id),
                "raw_count": raw_count,
                "baseline_raw_count": baseline_raw,
                "additional_collected": additional_collected,
                "train_count": train_count,
                "val_count": val_count,
                "target_extra": target_extra,
                "gap_to_target_extra": gap,
            }
        )

    current_rate = None
    improvement_pp = None
    meets_target = None
    if current_stats and current_stats.get("available"):
        current_rate = float(current_stats["combined_confusion_rate"])
        improvement_pp = round((baseline_rate - current_rate) * 100, 2)
        if baseline_rate > 0:
            meets_target = (baseline_rate - current_rate) / baseline_rate >= target_reduction
        else:
            meets_target = current_rate == 0.0

    if pair_ready:
        status = "READY_FOR_SPLIT"
    else:
        status = "COLLECTING"

    return PairProgress(
        pair=[species_a, species_b],
        priority=pair_def.get("priority", "medium"),
        target_extra=target_extra,
        reason=pair_def.get("reason", ""),
        baseline_combined_confusion_rate=baseline_rate,
        current_combined_confusion_rate=current_rate,
        improvement_pp=improvement_pp,
        target_reduction_rate=target_reduction,
        meets_target=meets_target,
        species_progress=species_progress,
        status=status,
        collection_tips=pair_def.get("collection_tips", []),
    )


def build_report(
    manifest_file: Path,
    data_dir: Path,
    species_file: Path,
    confusion_csv: Path | None,
    baseline_file: Path | None = None,
) -> HardNegativeReport:
    manifest = load_json(manifest_file)
    species_names = load_species_names(species_file)

    baseline_raw_counts: dict[str, int] | None = None
    if baseline_file and baseline_file.exists():
        baseline_data = load_json(baseline_file)
        baseline_raw_counts = baseline_data.get("species_raw_counts")

    class_ids: list[str] = []
    matrix: list[list[int]] = []
    if confusion_csv and confusion_csv.exists():
        class_ids, matrix = load_confusion_matrix(confusion_csv)

    pairs: list[PairProgress] = []
    for pair_def in manifest.get("confusion_pairs", []):
        a, b = pair_def["pair"]
        stats = (
            pair_confusion_stats(class_ids, matrix, a, b)
            if class_ids
            else None
        )
        pairs.append(
            build_pair_progress(
                pair_def, data_dir, species_names, stats, baseline_raw_counts
            )
        )

    collecting = sum(1 for p in pairs if p.status == "COLLECTING")
    ready = sum(1 for p in pairs if p.status == "READY_FOR_SPLIT")
    summary = {
        "pair_count": len(pairs),
        "collecting_pairs": collecting,
        "ready_for_split_pairs": ready,
        "high_priority_pairs": sum(1 for p in pairs if p.priority == "high"),
    }

    return HardNegativeReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        manifest_version=int(manifest.get("version", 1)),
        hard_negative_extra_per_pair=int(manifest.get("hard_negative_extra_per_pair", 50)),
        pairs=pairs,
        summary=summary,
    )


def print_report(report: HardNegativeReport, species_names: dict[str, str]) -> None:
    print("WildTrail Hard Negative Progress")
    print("=" * 80)
    print(
        f"pairs={report.summary['pair_count']} "
        f"collecting={report.summary['collecting_pairs']} "
        f"ready={report.summary['ready_for_split_pairs']}"
    )
    print("-" * 80)
    for pair in report.pairs:
        a, b = pair.pair
        label_a = species_names.get(a, a)
        label_b = species_names.get(b, b)
        print(f"[{pair.priority}] {label_a} <-> {label_b} ({pair.status})")
        print(f"  reason: {pair.reason}")
        print(
            f"  baseline confusion: {pair.baseline_combined_confusion_rate:.1%}"
            + (
                f" -> current: {pair.current_combined_confusion_rate:.1%}"
                if pair.current_combined_confusion_rate is not None
                else ""
            )
        )
        if pair.improvement_pp is not None:
            target = f"{pair.target_reduction_rate:.0%} reduction"
            met = "OK" if pair.meets_target else "NEED MORE"
            print(f"  improvement: {pair.improvement_pp:+.2f}pp ({target}) [{met}]")
        for sp in pair.species_progress:
            print(
                f"    {sp['common_name']} ({sp['species_id']}): "
                f"raw={sp['raw_count']} (+{sp['additional_collected']}/{sp['target_extra']}) "
                f"train={sp['train_count']} val={sp['val_count']} "
                f"gap={sp['gap_to_target_extra']}"
            )
        print()


def save_baseline(
    report: HardNegativeReport,
    path: Path,
    metrics_file: Path | None,
    data_dir: Path,
    manifest_file: Path,
) -> None:
    metrics = load_json(metrics_file) if metrics_file and metrics_file.exists() else {}
    manifest = load_json(manifest_file)
    species_ids: set[str] = set()
    for pair_def in manifest.get("confusion_pairs", []):
        species_ids.update(pair_def["pair"])

    species_raw_counts = {
        species_id: count_images(data_dir / "raw" / species_id)
        for species_id in sorted(species_ids)
    }

    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "overall_accuracy": metrics.get("accuracy"),
        "macro_f1": metrics.get("macro_f1"),
        "preprocess_version": metrics.get("preprocess_version"),
        "species_raw_counts": species_raw_counts,
        "pairs": [
            {
                "pair": pair.pair,
                "combined_confusion_rate": pair.current_combined_confusion_rate
                if pair.current_combined_confusion_rate is not None
                else pair.baseline_combined_confusion_rate,
            }
            for pair in report.pairs
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved baseline: {path.resolve()}")


def print_comparison(current: HardNegativeReport, baseline_file: Path) -> None:
    baseline = load_json(baseline_file)
    print("Hard Negative Before/After Comparison")
    print("=" * 80)
    print(
        f"baseline saved_at: {baseline.get('saved_at')} "
        f"accuracy={baseline.get('overall_accuracy')}"
    )
    if current.pairs and current.pairs[0].current_combined_confusion_rate is not None:
        print(f"current evaluated_at: {current.generated_at}")
    print("-" * 80)
    print(f"{'pair':<40} {'baseline':>10} {'current':>10} {'delta':>10} {'target':>8}")
    baseline_map = {
        tuple(item["pair"]): item.get("combined_confusion_rate", 0.0)
        for item in baseline.get("pairs", [])
    }
    for pair in current.pairs:
        key = tuple(pair.pair)
        base = float(baseline_map.get(key, pair.baseline_combined_confusion_rate))
        cur = pair.current_combined_confusion_rate
        if cur is None:
            continue
        delta_pp = (base - cur) * 100
        met = "OK" if pair.meets_target else "-"
        name = f"{pair.pair[0]}<->{pair.pair[1]}"
        print(
            f"{name:<40} {base:>9.1%} {cur:>9.1%} {delta_pp:>+9.2f}pp {met:>8}"
        )


def main() -> None:
    root = project_root()
    parser = argparse.ArgumentParser(description="Hard negative collection progress")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "data" / "dataset_manifest.json",
    )
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "images")
    parser.add_argument("--species-file", type=Path, default=root / "data" / "species.json")
    parser.add_argument(
        "--confusion-csv",
        type=Path,
        default=root / "reports" / "confusion_matrix.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "reports" / "hard_negative_progress.json",
    )
    parser.add_argument(
        "--save-baseline",
        type=Path,
        nargs="?",
        const=root / "reports" / "hard_negative_baseline.json",
        help="현재 혼동률을 baseline으로 저장",
    )
    parser.add_argument(
        "--compare-baseline",
        type=Path,
        help="저장된 baseline과 현재 혼동률 비교",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=root / "reports" / "hard_negative_baseline.json",
        help="추가 수집 진행률 계산용 baseline (species_raw_counts)",
    )
    parser.add_argument(
        "--metrics-file",
        type=Path,
        default=root / "reports" / "metrics.json",
    )
    args = parser.parse_args()

    baseline_for_progress = args.baseline_file if args.baseline_file.exists() else None
    report = build_report(
        manifest_file=args.manifest,
        data_dir=args.data_dir,
        species_file=args.species_file,
        confusion_csv=args.confusion_csv,
        baseline_file=baseline_for_progress,
    )
    species_names = load_species_names(args.species_file)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    print_report(report, species_names)
    print("-" * 80)
    print(f"Saved: {args.output.resolve()}")

    if args.save_baseline:
        save_baseline(
            report,
            args.save_baseline,
            args.metrics_file,
            args.data_dir,
            args.manifest,
        )

    if args.compare_baseline and args.compare_baseline.exists():
        print()
        print_comparison(report, args.compare_baseline)


if __name__ == "__main__":
    main()
