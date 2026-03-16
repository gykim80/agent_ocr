"""Florence2 아이콘 캡셔닝 (선택적)"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image


@dataclass
class IconCaption:
    bbox: list[int]
    size: str
    caption: str


@dataclass
class CaptionResult:
    scene_caption: str = ""
    detailed_caption: str = ""
    icon_captions: list[IconCaption] = field(default_factory=list)
    elapsed_sec: float = 0.0
    available: bool = False


_model_cache: dict = {}


def _load_florence2(weights_dir: str, device: str):
    """Florence2 모델 로드 (캐시)"""
    cache_key = f"{weights_dir}:{device}"
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    import torch
    from transformers import AutoProcessor, AutoModelForCausalLM

    hf_model_id = "microsoft/Florence-2-base"
    processor = AutoProcessor.from_pretrained(hf_model_id, trust_remote_code=True)

    dtype = torch.float16 if device != "cpu" else torch.float32
    try:
        model = AutoModelForCausalLM.from_pretrained(
            weights_dir, torch_dtype=dtype, trust_remote_code=True
        )
        if device != "cpu":
            model = model.to(device)
    except Exception:
        model = AutoModelForCausalLM.from_pretrained(
            hf_model_id, torch_dtype=dtype, trust_remote_code=True
        )
        if device != "cpu":
            model = model.to(device)

    _model_cache[cache_key] = (model, processor)
    return model, processor


def _run_task(model, processor, image: Image.Image, task: str, device: str) -> dict:
    """Florence2 단일 태스크 실행"""
    import torch
    dtype = torch.float16 if device != "cpu" else torch.float32
    inputs = processor(text=task, images=image, return_tensors="pt")
    inputs = {k: v.to(device) if torch.is_tensor(v) else v for k, v in inputs.items()}
    if device != "cpu":
        inputs["pixel_values"] = inputs["pixel_values"].to(dtype)

    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        do_sample=False,
        num_beams=3,
    )
    text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    return processor.post_process_generation(
        text, task=task, image_size=(image.width, image.height)
    )


def caption_image(
    image_path: str,
    yolo_boxes: list[dict] | None = None,
    weights_dir: str | None = None,
    max_icons: int = 20,
) -> CaptionResult:
    """Florence2로 이미지 캡셔닝"""
    try:
        from transformers import AutoProcessor  # noqa: F401
    except ImportError:
        return CaptionResult(available=False)

    from eyes.config import FLORENCE2_DIR
    wdir = weights_dir or str(FLORENCE2_DIR)

    if not Path(wdir).exists():
        return CaptionResult(available=False)

    # 디바이스 선택
    from eyes.layer2.yolo_detect import _get_device
    device = _get_device()

    t0 = time.time()
    try:
        model, processor = _load_florence2(wdir, device)
    except Exception as e:
        print(f"Florence2 로드 실패: {e}", file=sys.stderr)
        return CaptionResult(available=False)

    image = Image.open(image_path).convert("RGB")

    # 전체 이미지 캡션
    caption = _run_task(model, processor, image, "<CAPTION>", device)
    scene = caption.get("<CAPTION>", "")

    detailed = _run_task(model, processor, image, "<DETAILED_CAPTION>", device)
    detail = detailed.get("<DETAILED_CAPTION>", "")

    # 아이콘별 캡셔닝
    icon_captions: list[IconCaption] = []
    if yolo_boxes:
        for box_info in yolo_boxes[:max_icons]:
            bbox = box_info["bbox"]
            x1, y1, x2, y2 = bbox
            cropped = image.crop((x1, y1, x2, y2))
            if cropped.width < 5 or cropped.height < 5:
                continue
            cropped_resized = cropped.resize((64, 64))
            result = _run_task(model, processor, cropped_resized, "<CAPTION>", device)
            cap = result.get("<CAPTION>", "unknown")
            icon_captions.append(IconCaption(
                bbox=bbox,
                size=f"{x2 - x1}x{y2 - y1}",
                caption=cap,
            ))

    elapsed = time.time() - t0
    return CaptionResult(
        scene_caption=scene,
        detailed_caption=detail,
        icon_captions=icon_captions,
        elapsed_sec=round(elapsed, 3),
        available=True,
    )
