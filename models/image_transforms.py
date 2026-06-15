"""
WildTrail 이미지 전처리 — 학습·평가·API 추론 공통 정의

train / evaluate / backend identify 가 동일한 파이프라인을 사용하도록 단일 소스로 관리합니다.
"""

from __future__ import annotations

from torchvision import transforms

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
EVAL_RESIZE = 256
EVAL_CROP = 224

PREPROCESS_VERSION = "resize256_centercrop224"


def build_train_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((EVAL_RESIZE, EVAL_RESIZE)),
            transforms.RandomResizedCrop(EVAL_CROP),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def build_eval_transform() -> transforms.Compose:
    """학습 val / evaluate.py / API 추론 공통 파이프라인."""
    return transforms.Compose(
        [
            transforms.Resize((EVAL_RESIZE, EVAL_RESIZE)),
            transforms.CenterCrop(EVAL_CROP),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )
