"""이미지 메타데이터 추출"""
from dataclasses import dataclass
from PIL import Image


@dataclass
class ImageMeta:
    width: int = 0
    height: int = 0
    format: str = "unknown"
    dpi: tuple[int, int] = (72, 72)
    file_size_kb: int = 0


def extract_meta(image_path: str) -> ImageMeta:
    """이미지 기본 메타데이터 추출"""
    import os
    img = Image.open(image_path)
    w, h = img.size
    fmt = img.format or "unknown"
    dpi = img.info.get("dpi", (72, 72))
    file_size = os.path.getsize(image_path) // 1024

    return ImageMeta(
        width=w, height=h,
        format=fmt,
        dpi=(int(dpi[0]), int(dpi[1])),
        file_size_kb=file_size,
    )
