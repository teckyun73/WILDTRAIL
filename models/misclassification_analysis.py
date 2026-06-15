"""
WildTrail 오분류 분석 모듈

evaluate.py 실행 시 호출되어 misclassified_samples 복사 및 ML_EVAL_REPORT.md 생성.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader


@dataclass
class PredictionRecord:
    true_id: str
    pred_id: str
    confidence: float
    file_path: Path


@dataclass
class ConfusionPair:
    true_id: str
    pred_id: str
    count: int
    rate_of_true: float


def load_species_meta(species_file: Path) -> dict[str, dict]:
    if not species_file.exists():
        return {}
    with species_file.open(encoding="utf-8") as f:
        return {item["id"]: item for item in json.load(f)}


def species_label(species_id: str, meta: dict[str, dict]) -> str:
    item = meta.get(species_id, {})
    common = item.get("common_name", species_id)
    return f"{common} (`{species_id}`)"


def remap_labels(labels: torch.Tensor, folder_classes: list[str], class_to_idx: dict[str, int]) -> torch.Tensor:
    mapping = [class_to_idx[name] for name in folder_classes]
    return torch.tensor([mapping[idx] for idx in labels.tolist()], dtype=torch.long)


@torch.no_grad()
def collect_detailed_predictions(
    model: torch.nn.Module,
    loader: DataLoader,
    folder_classes: list[str],
    class_to_idx: dict[str, int],
    class_ids: list[str],
    device: torch.device,
) -> list[PredictionRecord]:
    dataset = loader.dataset
    records: list[PredictionRecord] = []
    sample_offset = 0

    for images, labels in loader:
        images = images.to(device)
        labels = remap_labels(labels, folder_classes, class_to_idx).to(device)
        outputs = model(images)
        probs = torch.softmax(outputs, dim=1)
        preds = outputs.argmax(dim=1)

        for i in range(images.size(0)):
            path, _ = dataset.samples[sample_offset + i]
            true_id = class_ids[labels[i].item()]
            pred_id = class_ids[preds[i].item()]
            records.append(
                PredictionRecord(
                    true_id=true_id,
                    pred_id=pred_id,
                    confidence=float(probs[i, preds[i]].item()),
                    file_path=Path(path),
                )
            )
        sample_offset += images.size(0)

    return records


def extract_top_confusion_pairs(
    matrix: np.ndarray,
    class_ids: list[str],
    top_k: int = 10,
) -> list[ConfusionPair]:
    pairs: list[ConfusionPair] = []
    for true_idx, true_id in enumerate(class_ids):
        row_total = int(matrix[true_idx].sum())
        if row_total == 0:
            continue
        for pred_idx, pred_id in enumerate(class_ids):
            if true_idx == pred_idx:
                continue
            count = int(matrix[true_idx, pred_idx])
            if count <= 0:
                continue
            pairs.append(
                ConfusionPair(
                    true_id=true_id,
                    pred_id=pred_id,
                    count=count,
                    rate_of_true=count / row_total,
                )
            )
    pairs.sort(key=lambda item: item.count, reverse=True)
    return pairs[:top_k]


def pair_confusion_stats(
    matrix: np.ndarray,
    class_ids: list[str],
    species_a: str,
    species_b: str,
) -> dict:
    if species_a not in class_ids or species_b not in class_ids:
        return {
            "species_a": species_a,
            "species_b": species_b,
            "available": False,
        }

    idx_a = class_ids.index(species_a)
    idx_b = class_ids.index(species_b)
    a_total = int(matrix[idx_a].sum())
    b_total = int(matrix[idx_b].sum())
    a_as_b = int(matrix[idx_a, idx_b])
    b_as_a = int(matrix[idx_b, idx_a])
    bidirectional = a_as_b + b_as_a

    return {
        "species_a": species_a,
        "species_b": species_b,
        "available": True,
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


def copy_misclassified_samples(
    records: list[PredictionRecord],
    pairs: list[ConfusionPair],
    output_dir: Path,
    max_per_pair: int = 3,
) -> list[dict]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied: list[dict] = []
    for pair in pairs:
        matches = [
            record
            for record in records
            if record.true_id == pair.true_id and record.pred_id == pair.pred_id
        ]
        matches.sort(key=lambda item: item.confidence, reverse=True)
        pair_dir = output_dir / f"{pair.true_id}__as__{pair.pred_id}"
        pair_dir.mkdir(parents=True, exist_ok=True)

        for record in matches[:max_per_pair]:
            dest_name = f"{record.file_path.stem}_conf{record.confidence:.3f}{record.file_path.suffix}"
            dest_path = pair_dir / dest_name
            shutil.copy2(record.file_path, dest_path)
            copied.append(
                {
                    "true_id": pair.true_id,
                    "pred_id": pair.pred_id,
                    "confidence": round(record.confidence, 4),
                    "source": str(record.file_path),
                    "dest": str(dest_path),
                }
            )
    return copied


def build_data_recommendations(
    report: dict,
    pairs: list[ConfusionPair],
    species_meta: dict[str, dict],
) -> list[str]:
    recommendations: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()

    for pair in pairs[:5]:
        key = tuple(sorted((pair.true_id, pair.pred_id)))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        recommendations.append(
            f"- **{species_label(pair.true_id, species_meta)} → "
            f"{species_label(pair.pred_id, species_meta)}** ({pair.count}건): "
            f"유사 각도·배경의 추가 이미지와 hard negative 샘플을 양쪽 종 모두 30~50장 수집"
        )

    weak_classes = []
    for class_id, metrics in report.items():
        if class_id in {"accuracy", "macro avg", "weighted avg"}:
            continue
        f1 = metrics.get("f1-score", 0)
        support = metrics.get("support", 0)
        if f1 < 0.75 and support >= 5:
            weak_classes.append((f1, class_id, support))

    weak_classes.sort()
    for f1, class_id, support in weak_classes[:5]:
        recommendations.append(
            f"- **{species_label(class_id, species_meta)}** "
            f"(F1={f1:.2f}, val={int(support)}장): "
            f"조명·각도 다양화, 오분류 상대종과 구분되는 클로즈업 추가"
        )

    return recommendations


def write_ml_eval_report(
    report_path: Path,
    metrics: dict,
    matrix: np.ndarray,
    class_ids: list[str],
    report: dict,
    pairs: list[ConfusionPair],
    species_meta: dict[str, dict],
    copied_samples: list[dict],
    focus_pairs: list[tuple[str, str]],
) -> None:
    evaluated_at = metrics.get("evaluated_at", datetime.now(timezone.utc).isoformat())
    lines = [
        "# WildTrail ML Evaluation Report",
        "",
        f"> 자동 생성: `{evaluated_at}`",
        "",
        "## 1. 요약",
        "",
        "| 지표 | 값 |",
        "|------|-----|",
        f"| Accuracy | {metrics['accuracy']:.2%} |",
        f"| Macro F1 | {metrics['macro_f1']:.2%} |",
        f"| Weighted F1 | {metrics['weighted_f1']:.2%} |",
        f"| 클래스 수 | {metrics['num_classes']} |",
        f"| 검증 샘플 | {metrics['num_samples']} |",
        f"| Checkpoint val_acc | {metrics.get('checkpoint_val_acc', 'N/A')} |",
        "",
        "관련 산출물:",
        "- `reports/metrics.json`",
        "- `reports/confusion_matrix.csv` / `.png`",
        "- `reports/per_class_report.csv`",
        "- `reports/misclassification_pairs.json`",
        "- `reports/misclassified_samples/`",
        "",
        "## 2. Top 10 오분류 쌍",
        "",
        "| 순위 | 실제 종 | 예측 종 | 건수 | 실제 종 기준 비율 |",
        "|------|---------|---------|------|-------------------|",
    ]

    for rank, pair in enumerate(pairs, start=1):
        lines.append(
            f"| {rank} | {species_label(pair.true_id, species_meta)} | "
            f"{species_label(pair.pred_id, species_meta)} | {pair.count} | "
            f"{pair.rate_of_true:.1%} |"
        )

    lines.extend(["", "## 3. 유사 종 혼동 분석", ""])
    for species_a, species_b in focus_pairs:
        stats = pair_confusion_stats(matrix, class_ids, species_a, species_b)
        if not stats["available"]:
            lines.append(
                f"### {species_a} vs {species_b}\n\n"
                f"- 평가 세트 또는 모델 클래스에 포함되지 않음\n"
            )
            continue
        lines.extend(
            [
                f"### {species_label(species_a, species_meta)} vs "
                f"{species_label(species_b, species_meta)}",
                "",
                "| 항목 | 값 |",
                "|------|-----|",
                f"| {species_a} 검증 샘플 | {stats['a_total']} |",
                f"| {species_b} 검증 샘플 | {stats['b_total']} |",
                f"| {species_a} → {species_b} | {stats['a_misclassified_as_b']} "
                f"({stats['a_confusion_rate']:.1%}) |",
                f"| {species_b} → {species_a} | {stats['b_misclassified_as_a']} "
                f"({stats['b_confusion_rate']:.1%}) |",
                f"| 양방향 합계 | {stats['bidirectional_count']} |",
                f"| 전체 대비 혼동률 | {stats['combined_confusion_rate']:.1%} |",
                "",
            ]
        )

    lines.extend(["## 4. 종별 취약 지표 (F1 < 0.80)", ""])
    lines.append("| 종 | Precision | Recall | F1 | Support |")
    lines.append("|----|-----------|--------|----|---------|")
    weak_rows = []
    for class_id, metrics_row in report.items():
        if class_id in {"accuracy", "macro avg", "weighted avg"}:
            continue
        f1 = metrics_row["f1-score"]
        if f1 < 0.80:
            weak_rows.append((f1, class_id, metrics_row))
    weak_rows.sort()
    for _, class_id, metrics_row in weak_rows:
        lines.append(
            f"| {species_label(class_id, species_meta)} | "
            f"{metrics_row['precision']:.2f} | {metrics_row['recall']:.2f} | "
            f"{metrics_row['f1-score']:.2f} | {int(metrics_row['support'])} |"
        )

    lines.extend(["", "## 5. 데이터 보강 권장", ""])
    recommendations = build_data_recommendations(report, pairs, species_meta)
    lines.extend(recommendations or ["- 현재 기준 긴급 보강 대상 없음"])

    lines.extend(
        [
            "",
            "## 6. 오분류 샘플 복사",
            "",
            f"대표 오분류 이미지 **{len(copied_samples)}장**을 "
            f"`reports/misclassified_samples/`에 저장했습니다.",
            "",
            "| 실제 → 예측 | confidence | 파일 |",
            "|-------------|------------|------|",
        ]
    )
    for item in copied_samples[:20]:
        rel = Path(item["dest"]).name
        pair = f"{item['true_id']} → {item['pred_id']}"
        lines.append(f"| {pair} | {item['confidence']:.3f} | `{rel}` |")
    if len(copied_samples) > 20:
        lines.append(f"| ... | | 외 {len(copied_samples) - 20}장 |")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_misclassification_analysis(
    *,
    model: torch.nn.Module,
    loader: DataLoader,
    folder_classes: list[str],
    class_to_idx: dict[str, int],
    class_ids: list[str],
    device: torch.device,
    matrix: np.ndarray,
    report: dict,
    metrics: dict,
    output_dir: Path,
    species_file: Path,
    docs_dir: Path,
    top_k: int = 10,
    max_samples_per_pair: int = 3,
) -> None:
    species_meta = load_species_meta(species_file)
    records = collect_detailed_predictions(
        model, loader, folder_classes, class_to_idx, class_ids, device
    )

    pairs = extract_top_confusion_pairs(matrix, class_ids, top_k=top_k)
    pairs_json_path = output_dir / "misclassification_pairs.json"
    with pairs_json_path.open("w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "true_id": pair.true_id,
                    "pred_id": pair.pred_id,
                    "count": pair.count,
                    "rate_of_true": round(pair.rate_of_true, 4),
                }
                for pair in pairs
            ],
            f,
            ensure_ascii=False,
            indent=2,
        )

    samples_dir = output_dir / "misclassified_samples"
    copied = copy_misclassified_samples(
        records, pairs, samples_dir, max_per_pair=max_samples_per_pair
    )

    focus_pairs = [
        ("pica_pica", "pica_serica"),
        ("pica_pica", "corvus_corone"),
        ("pica_serica", "corvus_corone"),
        ("capreolus_capreolus", "hydropotes_inermis"),
        ("passer_montanus", "parus_minor"),
    ]
    report_path = docs_dir / "ML_EVAL_REPORT.md"
    write_ml_eval_report(
        report_path,
        metrics,
        matrix,
        class_ids,
        report,
        pairs,
        species_meta,
        copied,
        focus_pairs,
    )

    print(f"Saved: {pairs_json_path}")
    print(f"Saved: {samples_dir} ({len(copied)} images)")
    print(f"Saved: {report_path}")
