"""Windows winocr 기반 프로바이더"""
import time
from typing import Optional
from eyes.platform.base import OCRProvider, OCRResult, OCROutput


class WindowsOCR(OCRProvider):
    """Windows winocr OCR"""
    name = "winocr"

    def extract(self, image_path: str, languages: Optional[list[str]] = None) -> OCROutput:
        import asyncio
        import winocr
        from PIL import Image

        image = Image.open(image_path)
        w, h = image.size

        # winocr는 async → sync 래핑
        lang = "ko" if languages and "ko" in languages else "en"

        t0 = time.time()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            winocr.recognize_pil(image, lang=lang)
        )
        loop.close()
        elapsed = time.time() - t0

        results: list[OCRResult] = []
        for line in result.lines:
            text = line.text.strip()
            if not text:
                continue
            # winocr bbox: x, y, w, h
            bx, by, bw, bh = line.x, line.y, line.width, line.height
            results.append(OCRResult(
                text=text,
                confidence=0.9,  # winocr는 confidence 미제공, 기본값
                bbox=[bx, by, bx + bw, by + bh],
            ))

        results.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
        return OCROutput(texts=results, elapsed_sec=round(elapsed, 3), provider=self.name)
