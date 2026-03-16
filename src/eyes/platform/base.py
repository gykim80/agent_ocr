"""크로스플랫폼 추상화 베이스 클래스"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OCRResult:
    """OCR 결과 단일 항목"""
    text: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]


@dataclass
class OCROutput:
    """OCR 전체 결과"""
    texts: list[OCRResult] = field(default_factory=list)
    elapsed_sec: float = 0.0
    provider: str = "unknown"

    @property
    def count(self) -> int:
        return len(self.texts)


@dataclass
class ClassifyOutput:
    """이미지 분류 결과"""
    category: str = "unknown"  # screenshot, photo, diagram, illustration, error_log
    confidence: float = 0.0
    provider: str = "unknown"
    details: dict = field(default_factory=dict)


class OCRProvider(ABC):
    """OCR 프로바이더 인터페이스"""
    name: str = "base"

    @abstractmethod
    def extract(self, image_path: str, languages: Optional[list[str]] = None) -> OCROutput:
        ...


class ClassifyProvider(ABC):
    """이미지 분류 프로바이더 인터페이스"""
    name: str = "base"

    @abstractmethod
    def classify(self, image_path: str) -> ClassifyOutput:
        ...
