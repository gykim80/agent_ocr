"""플랫폼 자동 감지 및 프로바이더 팩토리"""
import platform
import sys
from eyes.platform.base import OCRProvider, ClassifyProvider


def get_ocr_provider() -> OCRProvider:
    """현재 OS에 맞는 OCR 프로바이더 반환"""
    system = platform.system()

    if system == "Darwin":
        try:
            from eyes.platform.darwin import DarwinOCR
            return DarwinOCR()
        except ImportError:
            print("pyobjc-framework-Vision 미설치. pip install pyobjc-framework-Vision", file=sys.stderr)

    elif system == "Linux":
        try:
            from eyes.platform.linux import TesseractOCR
            return TesseractOCR()
        except ImportError:
            print("pytesseract 미설치. pip install pytesseract && sudo apt install tesseract-ocr", file=sys.stderr)

    elif system == "Windows":
        try:
            from eyes.platform.windows import WindowsOCR
            return WindowsOCR()
        except ImportError:
            print("winocr 미설치. pip install winocr", file=sys.stderr)

    # fallback: OCR 불가, L2 에스컬레이션 유도
    from eyes.platform.fallback import FallbackOCR
    return FallbackOCR()


def get_classifier() -> ClassifyProvider:
    """현재 OS에 맞는 분류기 반환"""
    system = platform.system()

    if system == "Darwin":
        try:
            from eyes.platform.darwin import DarwinClassifier
            return DarwinClassifier()
        except ImportError:
            pass

    # macOS 이외 또는 import 실패 → 휴리스틱
    from eyes.platform.fallback import HeuristicClassifier
    return HeuristicClassifier()
