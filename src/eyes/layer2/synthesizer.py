"""L1+L2 결과 합성기 — OCR 텍스트와 YOLO 영역을 공간 매칭"""
from dataclasses import dataclass, field
from eyes.platform.base import OCRResult
from eyes.layer2.yolo_detect import UIElement


@dataclass
class SynthesizedElement:
    """YOLO 영역 + 매칭된 OCR 텍스트"""
    bbox: list[int]
    width: int
    height: int
    confidence: float
    category: str
    texts: list[str] = field(default_factory=list)
    caption: str = ""  # Florence2 캡션 (있을 경우)


def _bbox_contains(outer: list[int], inner: list[int], margin: int = 10) -> bool:
    """outer bbox가 inner bbox를 포함하는지 확인 (margin 여유)"""
    return (
        inner[0] >= outer[0] - margin
        and inner[1] >= outer[1] - margin
        and inner[2] <= outer[2] + margin
        and inner[3] <= outer[3] + margin
    )


def synthesize(
    elements: list[UIElement],
    ocr_texts: list[OCRResult],
    icon_captions: list[dict] | None = None,
) -> list[SynthesizedElement]:
    """YOLO 요소에 OCR 텍스트와 캡션을 매칭"""
    caption_map: dict[str, str] = {}
    if icon_captions:
        for ic in icon_captions:
            key = ",".join(str(x) for x in ic.get("bbox", []))
            caption_map[key] = ic.get("caption", "")

    results: list[SynthesizedElement] = []
    for elem in elements:
        # 카테고리별 매칭 마진 조정
        margin = {"large_region": 20, "medium_element": 10, "small_icon": 5}.get(
            elem.category, 10
        )
        matched_texts = [
            t.text for t in ocr_texts
            if _bbox_contains(elem.bbox, t.bbox, margin)
        ]

        key = ",".join(str(x) for x in elem.bbox)
        caption = caption_map.get(key, "")

        results.append(SynthesizedElement(
            bbox=elem.bbox,
            width=elem.width,
            height=elem.height,
            confidence=elem.confidence,
            category=elem.category,
            texts=matched_texts,
            caption=caption,
        ))

    return results
