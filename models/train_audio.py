"""
WildTrail 오디오(조류 울음) 분류 학습 스크립트

데이터 구조:
  data/audio/
    train/
      pica_pica/
        clip001.wav
    val/
      pica_pica/

사용법:
  cd models
  .\\ml.ps1 split_audio.py --data-dir ..\\data\\audio
  .\\ml.ps1 train_audio.py --data-dir ..\\data\\audio --epochs 20
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

try:
    import librosa
    import numpy as np
except ImportError as exc:
    raise SystemExit("librosa, numpy 필요: pip install librosa soundfile") from exc


SAMPLE_RATE = 22050
N_MELS = 128
DURATION_SEC = 3.0


class MelSpectrogramDataset(Dataset):
    def __init__(self, root: Path, transform=None, preload: bool = True):
        self.samples: list[tuple[Path, int]] = []
        self.classes = sorted(p.name for p in root.iterdir() if p.is_dir())
        self.class_to_idx = {name: idx for idx, name in enumerate(self.classes)}
        exts = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
        for class_name in self.classes:
            for path in (root / class_name).rglob("*"):
                if path.suffix.lower() in exts:
                    self.samples.append((path, self.class_to_idx[class_name]))
        self.transform = transform
        self._cache: list[torch.Tensor] = []
        if preload and self.samples:
            self._preload()

    def _preload(self) -> None:
        print(f"Preloading {len(self.samples)} clips from {self.samples[0][0].parents[1].name}...", flush=True)
        failed = 0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for index, (path, _) in enumerate(self.samples, start=1):
                try:
                    mel = torch.from_numpy(self._load_mel(path))
                except Exception:
                    failed += 1
                    mel = torch.zeros((3, N_MELS, 1), dtype=torch.float32)
                self._cache.append(mel)
                if index % 100 == 0 or index == len(self.samples):
                    print(f"  cached {index}/{len(self.samples)}", flush=True)
        if failed:
            print(f"  warning: {failed} clips failed to load and were zero-filled", flush=True)

    def __len__(self) -> int:
        return len(self.samples)

    def _load_mel(self, path: Path) -> np.ndarray:
        audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=DURATION_SEC)
        target_len = int(SAMPLE_RATE * DURATION_SEC)
        if len(audio) < target_len:
            audio = np.pad(audio, (0, target_len - len(audio)))
        else:
            audio = audio[:target_len]
        mel = librosa.feature.melspectrogram(y=audio, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        mel_db = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-6)
        img = np.stack([mel_db, mel_db, mel_db], axis=0).astype(np.float32)
        return img

    def __getitem__(self, index: int):
        _, label = self.samples[index]
        tensor = self._cache[index] if self._cache else torch.from_numpy(self._load_mel(self.samples[index][0]))
        if self.transform:
            tensor = self.transform(tensor)
        return tensor, label


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
        correct += (outputs.argmax(1) == labels).sum().item()
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
        correct += (outputs.argmax(1) == labels).sum().item()
        total += images.size(0)
    return total_loss / total, correct / total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("../data/audio"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--output", type=Path, default=Path("checkpoints/best_audio_model.pth"))
    parser.add_argument("--no-preload", action="store_true", help="Mel 스펙트로그램 사전 캐시 비활성화")
    args = parser.parse_args()

    train_root = args.data_dir / "train"
    val_root = args.data_dir / "val"
    if not train_root.exists():
        raise FileNotFoundError(f"{train_root} 없음. data/audio/train/<species_id>/ 구조로 준비하세요.")
    if not val_root.exists():
        raise FileNotFoundError(
            f"{val_root} 없음. 먼저 split_audio.py를 실행하세요: "
            ".\\ml.ps1 split_audio.py --data-dir ..\\data\\audio --clear-val"
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}", flush=True)
    preload = not args.no_preload
    train_ds = MelSpectrogramDataset(train_root, preload=preload)
    val_ds = MelSpectrogramDataset(val_root, preload=preload)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
    model.fc = nn.Linear(model.fc.in_features, len(train_ds.classes))
    model = model.to(device)

    species_file = Path("../data/species.json")
    species_map = {}
    if species_file.exists():
        with species_file.open(encoding="utf-8") as f:
            for item in json.load(f):
                species_map[item["id"]] = item
    idx_to_species = {
        idx: species_map.get(name, {"id": name, "common_name": name, "scientific_name": name})
        for idx, name in enumerate(train_ds.classes)
    }

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    best_acc = 0.0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        print(
            f"Epoch {epoch}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}",
            flush=True,
        )
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "num_classes": len(train_ds.classes),
                    "classes": train_ds.classes,
                    "idx_to_species": idx_to_species,
                    "val_acc": val_acc,
                    "model_type": "audio_resnet18",
                },
                args.output,
            )
            print(f"Saved {args.output} (val_acc={val_acc:.4f})", flush=True)


if __name__ == "__main__":
    main()
