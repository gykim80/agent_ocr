"""Linux Tesseract 기반 프로바이더"""
import time
from typing import Optional
from eyes.platform.base import OCRProvider, OCRResult, OCROutput


class TesseractOCR(OCRProvider):
    """Linux pytesseract OCR"""
    name = "tesseract"

    def extract(self, image_path: str, languages: Optional[list[str]] = None) -> OCROutput:
        import pytesseract
        from PIL import Image

        lang_str = "+".join(languages) if languages else "eng+kor"
        image = Image.open(image_path)
        w, h = image.size

        t0 = time.time()
        # tsv 형태로 단어별 위치 포함 결과 추출
        data = pytesseract.image_to_data(image, lang=lang_str, output_type=pytesseract.Output.DICT)
        elapsed = time.time() - t0

        results: list[OCRResult] = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue
            conf = int(data["conf"][i])
            if conf < 0:
                continue
            x = data["left"][i]
            y = data["top"][i]
            bw = data["width"][i]
            bh = data["height"][i]
            results.append(OCRResult(
                text=text,
                confidence=round(conf / 100.0, 3),
                bbox=[x, y, x + bw, y + bh],
            ))

        # 위치 기준 정렬
        results.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
        return OCROutput(texts=results, elapsed_sec=round(elapsed, 3), provider=self.name)
