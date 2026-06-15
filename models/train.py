"""
WildTrail 이미지 분류 모델 학습 스크립트

데이터 구조:
  data/images/
    pica_pica/
      img001.jpg
    corvus_corone/
      ...

사용법:
  python train.py --data-dir ../data/images --epochs 10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models

from image_transforms import PREPROCESS_VERSION, build_eval_transform, build_train_transform
from checkpoint_metadata import merge_checkpoint_payload


def _remove_empty_class_dirs(split_dir: Path) -> None:
    if not split_dir.exists():
        return
    for class_dir in split_dir.iterdir():
        if class_dir.is_dir() and not any(class_dir.iterdir()):
            class_dir.rmdir()


def build_dataloaders(data_dir: Path, batch_size: int):
    _remove_empty_class_dirs(data_dir / "train")
    _remove_empty_class_dirs(data_dir / "val")

    train_transform = build_train_transform()
    val_transform = build_eval_transform()

    train_dataset = datasets.ImageFolder(data_dir / "train", transform=train_transform)
    val_dataset = datasets.ImageFolder(data_dir / "val", transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    return train_loader, val_loader, train_dataset.classes


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += images.size(0)
    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        total_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += images.size(0)
    return total_loss / total, correct / total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("../data/images"))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--output", type=Path, default=Path("checkpoints/best_model.pth"))
    args = parser.parse_args()

    if not (args.data_dir / "train").exists():
        raise FileNotFoundError(
            f"{args.data_dir / 'train'} 가 없습니다. 종별 폴더로 이미지를 준비하세요."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader, classes = build_dataloaders(args.data_dir, args.batch_size)

    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(classes))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    species_file = Path("../data/species.json")
    species_map = {}
    if species_file.exists():
        with species_file.open(encoding="utf-8") as f:
            for item in json.load(f):
                species_map[item["id"]] = item

    idx_to_species = {}
    for idx, class_name in enumerate(classes):
        meta = species_map.get(class_name, {"id": class_name, "common_name": class_name, "scientific_name": class_name})
        idx_to_species[idx] = meta

    best_acc = 0.0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        print(
            f"Epoch {epoch}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )
        if val_acc > best_acc:
            best_acc = val_acc
            payload = merge_checkpoint_payload(
                model_state_dict=model.state_dict(),
                num_classes=len(classes),
                classes=classes,
                idx_to_species=idx_to_species,
                val_acc=val_acc,
                data_dir=args.data_dir,
                epochs=args.epochs,
                batch_size=args.batch_size,
                lr=args.lr,
                preprocess_version=PREPROCESS_VERSION,
            )
            torch.save(payload, args.output)
            print(
                f"Saved checkpoint to {args.output} "
                f"(val_acc={val_acc:.4f}, version={payload['model_version']})"
            )


if __name__ == "__main__":
    main()
