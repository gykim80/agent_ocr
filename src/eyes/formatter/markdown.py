"""구조화된 Markdown 출력 생성"""
import os
from typing import Optional


def format_analysis(
    image_path: str,
    meta: "ImageMeta",
    color: "ColorResult",
    classification: "ClassifyOutput",
    ocr: "OCROutput",
    yolo: Optional["YOLOResult"] = None,
    caption: Optional["CaptionResult"] = None,
    vlm: Optional["VLMResult"] = None,
    synthesized: Optional[list] = None,
    user_prompt: Optional[str] = None,
) -> str:
    """분석 결과를 Markdown 텍스트로 변환"""
    lines: list[str] = []
    fname = os.path.basename(image_path)
    mode = "Dark" if color.is_dark_mode else "Light"
    img_type = classification.category.replace("_", " ").title()

    # 헤더
    lines.append(f"## Image Analysis: {fname}")
    lines.append(f"**Size**: {meta.width}x{meta.height}px | **Mode**: {mode} | **Type**: {img_type}")
    if user_prompt:
        lines.append(f"**Query**: {user_prompt}")
    lines.append("")

    # VLM 분석 (L3, 있으면 최상단)
    if vlm and vlm.available and vlm.description:
        lines.append("### VLM Analysis")
        lines.append(vlm.description.strip())
        lines.append("")

    # Scene 캡션 (Florence2, 있으면)
    if caption and caption.available and caption.scene_caption:
        lines.append("### Scene")
        lines.append(caption.scene_caption)
        if caption.detailed_caption:
            lines.append(f"\n**Detailed**: {caption.detailed_caption}")
        lines.append("")

    # 합성 결과 (L2, 있으면)
    if synthesized:
        large = [s for s in synthesized if s.category == "large_region"]
        medium = [s for s in synthesized if s.category == "medium_element"]
        small = [s for s in synthesized if s.category == "small_icon"]

        total = len(synthesized)
        lines.append(f"### UI Elements ({total} detected)")

        if large:
            lines.append(f"\n**Large regions** ({len(large)}):")
            for e in large[:10]:
                b = e.bbox
                text_preview = f' → "{e.texts[0]}"' if e.texts else ""
                cap = f" ({e.caption})" if e.caption else ""
                lines.append(
                    f"- [{b[0]},{b[1]}→{b[2]},{b[3]}] {e.width}x{e.height}px{text_preview}{cap}"
                )

        if medium:
            lines.append(f"\n**Medium elements** ({len(medium)}):")
            for e in medium[:15]:
                b = e.bbox
                text_preview = f' → "{e.texts[0]}"' if e.texts else ""
                cap = f" ({e.caption})" if e.caption else ""
                lines.append(
                    f"- [{b[0]},{b[1]}→{b[2]},{b[3]}] {e.width}x{e.height}px{text_preview}{cap}"
                )

        if small:
            lines.append(f"\n**Small icons/buttons** ({len(small)}):")
            for e in small[:20]:
                b = e.bbox
                text_preview = f' "{e.texts[0]}"' if e.texts else ""
                cap = f" ({e.caption})" if e.caption else ""
                lines.append(f"- [{b[0]},{b[1]}] {e.width}x{e.height}px{text_preview}{cap}")

        lines.append("")

    # YOLO만 있고 합성 없으면 (fallback)
    elif yolo and yolo.count > 0:
        lines.append(f"### UI Elements (YOLO: {yolo.count} detected)")
        for e in yolo.elements[:30]:
            b = e.bbox
            lines.append(f"- [{b[0]},{b[1]}→{b[2]},{b[3]}] {e.width}x{e.height}px (conf: {e.confidence})")
        lines.append("")

    # OCR 텍스트
    if ocr.count > 0:
        lines.append(f"### Text Content (OCR: {ocr.count} items)")
        for t in ocr.texts[:30]:
            b = t.bbox
            lines.append(f'- [{b[0]},{b[1]}] "{t.text}"')
        if ocr.count > 30:
            lines.append(f"- ... and {ocr.count - 30} more")
        lines.append("")

    # 색상 팔레트
    lines.append("### Color Palette")
    for c in color.palette:
        lines.append(f"- {c['hex']} ({c['pct']}%)")
    lines.append("")

    return "\n".join(lines)
