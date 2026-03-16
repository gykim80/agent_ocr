"""PIL-only 범용 fallback (어떤 OS든 동작)"""
import time
from collections import Counter
from typing import Optional
from PIL import Image
from eyes.platform.base import (
    OCRProvider, OCROutput, ClassifyProvider, ClassifyOutput,
)


class FallbackOCR(OCRProvider):
    """PIL-only OCR — 텍스트 추출 불가, 빈 결과 반환 + L2 에스컬레이션 유도"""
    name = "fallback-none"

    def extract(self, image_path: str, languages: Optional[list[str]] = None) -> OCROutput:
        return OCROutput(texts=[], elapsed_sec=0.0, provider=self.name)


class HeuristicClassifier(ClassifyProvider):
    """PIL 기반 휴리스틱 이미지 분류 (크로스플랫폼)"""
    name = "heuristic"

    def classify(self, image_path: str) -> ClassifyOutput:
        t0 = time.time()
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        aspect = w / h

        # 축소 이미지에서 분석
        small = img.resize((200, 200))
        pixels = list(small.getdata())

        # 색상 다양성 분석
        quantized = [tuple(c // 32 * 32 for c in p) for p in pixels]
        unique_colors = len(set(quantized))
        top_colors = Counter(quantized).most_common(5)
        top_color_pct = top_colors[0][1] / len(pixels) if top_colors else 0

        # 밝기 분석
        avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)

        elapsed = time.time() - t0

        # 분류 휴리스틱
        category = self._classify(aspect, unique_colors, top_color_pct, avg_brightness, w, h)

        return ClassifyOutput(
            category=category,
            confidence=0.6,  # 휴리스틱이므로 중간 신뢰도
            provider=self.name,
            details={
                "unique_colors": unique_colors,
                "top_color_pct": round(top_color_pct, 2),
                "avg_brightness": round(avg_brightness, 1),
                "aspect_ratio": round(aspect, 2),
            },
        )

    def _classify(
        self, aspect: float, unique_colors: int, top_pct: float,
        brightness: float, w: int, h: int,
    ) -> str:
        # 스크린샷: 16:9~16:10 비율, 고해상도, 낮은 색상 다양성
        if 1.4 < aspect < 2.0 and w >= 1280:
            return "screenshot"
        # 다이어그램: 밝은 배경 + 낮은 색상 수
        if brightness > 200 and unique_colors < 50:
            return "diagram"
        # 사진: 높은 색상 다양성
        if unique_colors > 300:
            return "photo"
        # 에러 로그: 어두운 배경 + 중간 비율
        if brightness < 80 and 1.0 < aspect < 2.5:
            return "error_log"
        return "screenshot"
