"""macOS Vision Framework 기반 프로바이더"""
import time
from typing import Optional
from eyes.platform.base import OCRProvider, OCRResult, OCROutput, ClassifyProvider, ClassifyOutput


class DarwinOCR(OCRProvider):
    """macOS Vision.framework OCR"""
    name = "macos-vision"

    def extract(self, image_path: str, languages: Optional[list[str]] = None) -> OCROutput:
        import Vision
        import Quartz

        langs = languages or ["ko", "en"]

        url = Quartz.CFURLCreateWithFileSystemPath(
            None, image_path, Quartz.kCFURLPOSIXPathStyle, False
        )
        source = Quartz.CGImageSourceCreateWithURL(url, None)
        cg_image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
        w = Quartz.CGImageGetWidth(cg_image)
        h = Quartz.CGImageGetHeight(cg_image)

        results: list[OCRResult] = []

        def handler(request, error):
            observations = request.results()
            if not observations:
                return
            for obs in observations:
                candidates = obs.topCandidates_(1)
                if not candidates:
                    continue
                text = candidates[0].string()
                confidence = candidates[0].confidence()
                box = obs.boundingBox()
                x1 = int(box.origin.x * w)
                y1 = int((1 - box.origin.y - box.size.height) * h)
                bw = int(box.size.width * w)
                bh = int(box.size.height * h)
                results.append(OCRResult(
                    text=text,
                    confidence=round(confidence, 3),
                    bbox=[x1, y1, x1 + bw, y1 + bh],
                ))

        t0 = time.time()
        request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handler)
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setRecognitionLanguages_(langs)
        request.setUsesLanguageCorrection_(True)

        img_handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        img_handler.performRequests_error_([request], None)
        elapsed = time.time() - t0

        # 위치 기준 정렬 (위→아래, 왼→오른)
        results.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
        return OCROutput(texts=results, elapsed_sec=round(elapsed, 3), provider=self.name)


class DarwinClassifier(ClassifyProvider):
    """macOS VNClassifyImageRequest 기반 이미지 분류"""
    name = "macos-vision-classify"

    def classify(self, image_path: str) -> ClassifyOutput:
        import Vision
        import Quartz

        url = Quartz.CFURLCreateWithFileSystemPath(
            None, image_path, Quartz.kCFURLPOSIXPathStyle, False
        )
        source = Quartz.CGImageSourceCreateWithURL(url, None)
        cg_image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)

        classifications = []

        def handler(request, error):
            observations = request.results()
            if not observations:
                return
            for obs in observations[:10]:
                classifications.append({
                    "label": obs.identifier(),
                    "confidence": round(obs.confidence(), 3),
                })

        request = Vision.VNClassifyImageRequest.alloc().initWithCompletionHandler_(handler)
        img_handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        img_handler.performRequests_error_([request], None)

        # 분류 결과를 eyes 카테고리로 매핑
        category = self._map_category(classifications)
        top_conf = classifications[0]["confidence"] if classifications else 0.0

        return ClassifyOutput(
            category=category,
            confidence=top_conf,
            provider=self.name,
            details={"raw_labels": classifications[:5]},
        )

    def _map_category(self, classifications: list[dict]) -> str:
        """Vision 분류 레이블을 eyes 카테고리로 매핑"""
        if not classifications:
            return "unknown"
        labels = {c["label"].lower() for c in classifications[:5]}
        # 스크린샷/UI 관련
        if any(w in labels for w in ["document", "text", "screen"]):
            return "screenshot"
        if any(w in labels for w in ["drawing", "chart", "diagram"]):
            return "diagram"
        if any(w in labels for w in ["outdoor", "indoor", "nature", "people", "animal"]):
            return "photo"
        return "screenshot"  # 기본값: 스크린샷으로 가정
