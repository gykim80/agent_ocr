"""OmniParser YOLO UI 요소 감지"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from PIL import Image


@dataclass
class UIElement:
    bbox: list[int]  # [x1, y1, x2, y2]
    width: int
    height: int
    confidence: float
    category: str = "ui_element"  # large_region, medium_element, small_icon


@dataclass
class YOLOResult:
    elements: list[UIElement] = field(default_factory=list)
    elapsed_sec: float = 0.0
    device: str = "cpu"
    image_size: tuple[int, int] = (0, 0)

    @property
    def count(self) -> int:
        return len(self.elements)


def _get_device() -> str:
    """최적 디바이스 자동 선택"""
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _categorize_element(ew: int, eh: int, iw: int, ih: int) -> str:
    """UI 요소 크기에 따른 카테고리 분류"""
    area_ratio = (ew * eh) / (iw * ih)
    if area_ratio > 0.05:
        return "large_region"
    if area_ratio > 0.01:
        return "medium_element"
    return "small_icon"


def detect_ui_elements(
    image_path: str,
    model_path: Optional[str] = None,
    conf_threshold: float = 0.05,
    iou_threshold: float = 0.7,
) -> YOLOResult:
    """YOLO로 UI 요소 감지"""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics 미설치. pip install ultralytics", file=sys.stderr)
        return YOLOResult()

    from eyes.config import YOLO_MODEL_PATH
    model_file = model_path or str(YOLO_MODEL_PATH)

    if not Path(model_file).exists():
        print(f"YOLO 모델 없음: {model_file}", file=sys.stderr)
        return YOLOResult()

    device = _get_device()
    model = YOLO(model_file)
    model.to(device)

    image = Image.open(image_path).convert("RGB")
    iw, ih = image.size

    t0 = time.time()
    result = model.predict(
        source=image, conf=conf_threshold, iou=iou_threshold, verbose=False
    )
    elapsed = time.time() - t0

    boxes_raw = result[0].boxes.xyxy.cpu().tolist()
    confs_raw = result[0].boxes.conf.cpu().tolist()

    elements: list[UIElement] = []
    for box, conf in zip(boxes_raw, confs_raw):
        x1, y1, x2, y2 = box
        ew, eh = int(x2 - x1), int(y2 - y1)
        elements.append(UIElement(
            bbox=[int(x1), int(y1), int(x2), int(y2)],
            width=ew, height=eh,
            confidence=round(conf, 3),
            category=_categorize_element(ew, eh, iw, ih),
        ))

    # 신뢰도 순 정렬
    elements.sort(key=lambda e: -e.confidence)

    return YOLOResult(
        elements=elements,
        elapsed_sec=round(elapsed, 3),
        device=device,
        image_size=(iw, ih),
    )
