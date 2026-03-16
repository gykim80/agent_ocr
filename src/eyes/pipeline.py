"""3계층 파이프라인 오케스트레이터"""
import sys
import time
from typing import Optional

from eyes.platform.factory import get_ocr_provider, get_classifier
from eyes.layer1.color import analyze_color
from eyes.layer1.meta import extract_meta
from eyes.formatter.markdown import format_analysis


def _should_escalate_to_l2(ocr_count: int, classification: str, user_prompt: Optional[str]) -> bool:
    """L1 → L2 에스컬레이션 판단"""
    if ocr_count < 5:
        return True
    if classification in ("diagram", "photo", "illustration"):
        return True
    if user_prompt and any(w in user_prompt for w in ["상세", "detail", "UI", "요소", "element"]):
        return True
    return False


def _should_escalate_to_l3(
    ocr_count: int, yolo_count: int, classification: str, user_prompt: Optional[str]
) -> bool:
    """L2 → L3 에스컬레이션 판단"""
    if yolo_count < 3 and ocr_count < 5:
        return True
    if classification == "diagram":
        return True
    if user_prompt and any(w in user_prompt for w in ["의미", "관계", "설명", "why", "explain"]):
        return True
    return False


def analyze(
    image_path: str,
    user_prompt: Optional[str] = None,
    max_layer: int = 3,
    force_layer: Optional[int] = None,
    yolo_model_path: Optional[str] = None,
    florence_weights: Optional[str] = None,
) -> str:
    """이미지 분석 파이프라인 실행 → Markdown 반환"""
    t_total = time.time()

    # ─── L1: Zero-Cost ───
    print("[L1] OS 네이티브 분석...", file=sys.stderr)
    meta = extract_meta(image_path)
    color = analyze_color(image_path)
    ocr_provider = get_ocr_provider()
    ocr = ocr_provider.extract(image_path)
    classifier = get_classifier()
    classification = classifier.classify(image_path)

    print(f"  OCR: {ocr.count} texts ({ocr.elapsed_sec}s, {ocr.provider})", file=sys.stderr)
    print(f"  Color: {'Dark' if color.is_dark_mode else 'Light'} mode", file=sys.stderr)
    print(f"  Type: {classification.category} ({classification.provider})", file=sys.stderr)

    yolo = None
    caption = None
    vlm = None
    synthesized = None

    # L2 에스컬레이션 판단
    need_l2 = (
        force_layer in (2, 3)
        or (force_layer is None and max_layer >= 2
            and _should_escalate_to_l2(ocr.count, classification.category, user_prompt))
    )

    if need_l2:
        print("\n[L2] Semantic 분석...", file=sys.stderr)
        try:
            from eyes.layer2.yolo_detect import detect_ui_elements
            yolo = detect_ui_elements(image_path, model_path=yolo_model_path)
            print(f"  YOLO: {yolo.count} elements ({yolo.elapsed_sec}s, {yolo.device})", file=sys.stderr)

            # Florence2 캡셔닝 (선택적)
            try:
                from eyes.layer2.florence_caption import caption_image
                # small_icon만 캡셔닝 대상
                icon_boxes = [
                    {"bbox": e.bbox}
                    for e in yolo.elements
                    if e.category == "small_icon" and e.confidence > 0.1
                ][:20]

                if icon_boxes:
                    caption = caption_image(
                        image_path, yolo_boxes=icon_boxes, weights_dir=florence_weights
                    )
                    if caption.available:
                        print(
                            f"  Florence2: scene + {len(caption.icon_captions)} icons ({caption.elapsed_sec}s)",
                            file=sys.stderr,
                        )
            except ImportError:
                pass

            # L1+L2 합성
            from eyes.layer2.synthesizer import synthesize
            icon_caps = (
                [{"bbox": ic.bbox, "caption": ic.caption} for ic in caption.icon_captions]
                if caption and caption.available else None
            )
            synthesized = synthesize(yolo.elements, ocr.texts, icon_caps)

        except ImportError:
            print("  L2 모듈 미설치 (ultralytics). pip install eyes-cli[semantic]", file=sys.stderr)
        except Exception as e:
            print(f"  L2 오류: {e}", file=sys.stderr)

    # L3 에스컬레이션 판단
    yolo_count = yolo.count if yolo else 0
    need_l3 = (
        force_layer == 3
        or (force_layer is None and max_layer >= 3
            and _should_escalate_to_l3(ocr.count, yolo_count, classification.category, user_prompt))
    )

    if need_l3:
        print("\n[L3] VLM 분석...", file=sys.stderr)
        try:
            from eyes.layer3.vlm import query_vlm
            vlm_prompt = user_prompt or (
                "Describe this image in detail. Include all visible UI elements, "
                "text, layout structure, and colors."
            )
            vlm = query_vlm(image_path, prompt=vlm_prompt)
            if vlm.available:
                print(f"  VLM: {vlm.model} ({vlm.elapsed_sec}s)", file=sys.stderr)
            else:
                print("  VLM 미사용 (Ollama 미실행)", file=sys.stderr)
        except Exception as e:
            print(f"  L3 오류: {e}", file=sys.stderr)

    elapsed_total = time.time() - t_total
    print(f"\n총 소요: {elapsed_total:.1f}s", file=sys.stderr)

    # Markdown 출력 생성
    return format_analysis(
        image_path=image_path,
        meta=meta,
        color=color,
        classification=classification,
        ocr=ocr,
        yolo=yolo,
        caption=caption,
        vlm=vlm,
        synthesized=synthesized,
        user_prompt=user_prompt,
    )
