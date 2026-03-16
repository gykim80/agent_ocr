"""PIL 기반 색상 분석"""
import time
from collections import Counter
from dataclasses import dataclass, field
from PIL import Image


@dataclass
class ColorResult:
    is_dark_mode: bool = False
    avg_brightness: float = 0.0
    palette: list[dict] = field(default_factory=list)
    elapsed_sec: float = 0.0


def analyze_color(image_path: str) -> ColorResult:
    """이미지 색상 분석 — 팔레트 추출 + 다크모드 감지"""
    t0 = time.time()
    img = Image.open(image_path).convert("RGB")
    small = img.resize((200, 200))
    pixels = list(small.getdata())

    # 밝기 분석
    avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)
    is_dark = avg_brightness < 128

    # 지배색 추출 (32단계 양자화)
    quantized = [tuple(c // 32 * 32 for c in p) for p in pixels]
    top_colors = Counter(quantized).most_common(5)
    palette = [
        {
            "rgb": list(c),
            "hex": "#{:02x}{:02x}{:02x}".format(*c),
            "pct": round(n / len(pixels) * 100, 1),
        }
        for c, n in top_colors
    ]

    elapsed = time.time() - t0
    return ColorResult(
        is_dark_mode=is_dark,
        avg_brightness=round(avg_brightness, 1),
        palette=palette,
        elapsed_sec=round(elapsed, 3),
    )
