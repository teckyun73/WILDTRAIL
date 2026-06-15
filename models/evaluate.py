"""
WildTrail 이미지 분류 모델 평가 스크립트

검증 세트 전체에 대해 inference 후 confusion matrix 및 종별 지표를 생성합니다.

사용법:
  cd models
  python evaluate.py --data-dir ../data/images/val --checkpoint checkpoints/best_model.pth --output ../reports
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from torch.utils.data import DataLoader
from torchvision import datasets, models

from image_transforms import PREPROCESS_VERSION, build_eval_transform


def load_species_names(species_file: Path) -> dict[str, str]:
    if not species_file.exists():
        return {}
    with species_file.open(encoding="utf-8") as f:
        return {item["id"]: item["common_name"] for item in json.load(f)}


def build_model(num_classes: int, checkpoint: dict, device: torch.device) -> torch.nn.Module:
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()
    return model


def build_val_loader(data_dir: Path, batch_size: int) -> tuple[DataLoader, list[str]]:
    dataset = datasets.ImageFolder(data_dir, transform=build_eval_transform())
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    return loader, dataset.classes


def remap_labels(labels: torch.Tensor, folder_classes: list[str], class_to_idx: dict[str, int]) -> torch.Tensor:
    mapping = [class_to_idx[name] for name in folder_classes]
    return torch.tensor([mapping[idx] for idx in labels.tolist()], dtype=torch.long)


@torch.no_grad()
def collect_predictions(
    model: torch.nn.Module,
    loader: DataLoader,
    folder_classes: list[str],
    class_to_idx: dict[str, int],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    y_true: list[int] = []
    y_pred: list[int] = []

    for images, labels in loader:
        images = images.to(device)
        labels = remap_labels(labels, folder_classes, class_to_idx).to(device)
        outputs = model(images)
        preds = outputs.argmax(dim=1)
        y_true.extend(labels.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())

    return np.array(y_true), np.array(y_pred)


def save_confusion_matrix_csv(path: Path, matrix: np.ndarray, class_names: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true\\pred", *class_names])
        for name, row in zip(class_names, matrix):
            writer.writerow([name, *row.tolist()])


def save_per_class_report_csv(path: Path, report: dict) -> None:
    fieldnames = ["class_id", "precision", "recall", "f1-score", "support"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for class_id, metrics in report.items():
            if class_id in {"accuracy", "macro avg", "weighted avg"}:
                continue
            writer.writerow(
                {
                    "class_id": class_id,
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1-score": metrics["f1-score"],
                    "support": metrics["support"],
                }
            )
        for summary_key in ("macro avg", "weighted avg"):
            metrics = report[summary_key]
            writer.writerow(
                {
                    "class_id": summary_key,
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1-score": metrics["f1-score"],
                    "support": metrics["support"],
                }
            )


def configure_matplotlib_font() -> bool:
    """한글 라벨용 폰트 설정. 실패 시 False 반환."""
    from matplotlib import font_manager

    for name in ("Malgun Gothic", "NanumGothic", "AppleGothic"):
        try:
            font_manager.findfont(name, fallback_to_default=False)
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return True
        except ValueError:
            continue
    return False


def label_for_plot(class_id: str, species_names: dict[str, str], korean_font: bool) -> str:
    if korean_font and class_id in species_names:
        return f"{species_names[class_id]}\n({class_id})"
    return class_id


def save_confusion_matrix_png(
    path: Path,
    matrix: np.ndarray,
    class_ids: list[str],
    display_names: list[str],
) -> None:
    size = max(8, len(class_ids) * 0.35)
    fig, ax = plt.subplots(figsize=(size, size))
    im = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=np.arange(len(class_ids)),
        yticks=np.arange(len(class_ids)),
        xticklabels=display_names,
        yticklabels=display_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor", fontsize=7)
    plt.setp(ax.get_yticklabels(), fontsize=7)

    threshold = matrix.max() / 2 if matrix.max() > 0 else 0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            if value == 0:
                continue
            color = "white" if value > threshold else "black"
            ax.text(j, i, str(value), ha="center", va="center", color=color, fontsize=6)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate WildTrail image classifier")
    parser.add_argument("--data-dir", type=Path, default=Path("../data/images/val"))
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/best_model.pth"))
    parser.add_argument("--output", type=Path, default=Path("../reports"))
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--species-file",
        type=Path,
        default=Path("../data/species.json"),
        help="종 한글명 표시용 species.json 경로",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("../docs"),
        help="ML_EVAL_REPORT.md 저장 경로",
    )
    parser.add_argument(
        "--skip-misclassification-analysis",
        action="store_true",
        help="오분류 샘플 복사 및 ML_EVAL_REPORT 생성 생략",
    )
    args = parser.parse_args()

    if not args.data_dir.exists():
        raise FileNotFoundError(f"검증 데이터 디렉터리가 없습니다: {args.data_dir}")
    if not args.checkpoint.exists():
        raise FileNotFoundError(f"체크포인트가 없습니다: {args.checkpoint}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    class_ids: list[str] = checkpoint.get("classes", [])
    if not class_ids:
        raise ValueError("체크포인트에 classes 정보가 없습니다.")
    class_to_idx = {name: idx for idx, name in enumerate(class_ids)}

    loader, folder_classes = build_val_loader(args.data_dir, args.batch_size)
    unknown = [name for name in folder_classes if name not in class_to_idx]
    if unknown:
        raise ValueError(f"체크포인트에 없는 클래스 폴더: {unknown}")

    model = build_model(len(class_ids), checkpoint, device)
    y_true, y_pred = collect_predictions(model, loader, folder_classes, class_to_idx, device)

    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(class_ids))))
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_ids))),
        target_names=class_ids,
        output_dict=True,
        zero_division=0,
    )

    species_names = load_species_names(args.species_file)
    korean_font = configure_matplotlib_font()
    display_names = [
        label_for_plot(class_id, species_names, korean_font) for class_id in class_ids
    ]

    args.output.mkdir(parents=True, exist_ok=True)
    metrics = {
        "accuracy": round(float(accuracy), 6),
        "macro_f1": round(float(macro_f1), 6),
        "weighted_f1": round(float(weighted_f1), 6),
        "num_classes": len(class_ids),
        "num_samples": int(len(y_true)),
        "checkpoint_val_acc": checkpoint.get("val_acc"),
        "checkpoint_path": str(args.checkpoint.resolve()),
        "data_dir": str(args.data_dir.resolve()),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "preprocess_version": PREPROCESS_VERSION,
        "model_version": checkpoint.get("model_version"),
        "trained_at": checkpoint.get("trained_at"),
        "dataset_fingerprint": checkpoint.get("dataset_fingerprint")
        or checkpoint.get("dataset_report_hash"),
    }

    metrics_path = args.output / "metrics.json"
    cm_csv_path = args.output / "confusion_matrix.csv"
    report_csv_path = args.output / "per_class_report.csv"
    cm_png_path = args.output / "confusion_matrix.png"

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    save_confusion_matrix_csv(cm_csv_path, matrix, class_ids)
    save_per_class_report_csv(report_csv_path, report)
    save_confusion_matrix_png(cm_png_path, matrix, class_ids, display_names)

    print(f"Evaluated {metrics['num_samples']} samples across {metrics['num_classes']} classes")
    print(f"accuracy={accuracy:.4f} macro_f1={macro_f1:.4f} weighted_f1={weighted_f1:.4f}")
    if checkpoint.get("val_acc") is not None:
        diff = abs(accuracy - float(checkpoint["val_acc"]))
        print(f"checkpoint val_acc={checkpoint['val_acc']:.4f} (diff={diff:.4f})")
    print(f"Saved: {metrics_path}")
    print(f"Saved: {cm_csv_path}")
    print(f"Saved: {report_csv_path}")
    print(f"Saved: {cm_png_path}")

    if not args.skip_misclassification_analysis:
        from misclassification_analysis import run_misclassification_analysis

        print("Running misclassification analysis...")
        run_misclassification_analysis(
            model=model,
            loader=loader,
            folder_classes=folder_classes,
            class_to_idx=class_to_idx,
            class_ids=class_ids,
            device=device,
            matrix=matrix,
            report=report,
            metrics=metrics,
            output_dir=args.output,
            species_file=args.species_file,
            docs_dir=args.docs_dir,
        )


if __name__ == "__main__":
    main()
