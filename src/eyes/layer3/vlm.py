"""Layer 3: Ollama VLM 호출 (선택적)"""
import base64
import json
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VLMResult:
    description: str = ""
    elapsed_sec: float = 0.0
    available: bool = False
    model: str = ""


def query_vlm(
    image_path: str,
    prompt: str = "Describe this image in detail. Include all visible UI elements, text, layout structure, and colors.",
    model: str | None = None,
    base_url: str | None = None,
) -> VLMResult:
    """Ollama VLM으로 이미지 분석"""
    from eyes.config import OLLAMA_BASE_URL, OLLAMA_MODEL
    url = base_url or OLLAMA_BASE_URL
    mdl = model or OLLAMA_MODEL

    # Ollama 실행 확인
    try:
        urllib.request.urlopen(f"{url}/api/tags", timeout=2)
    except (urllib.error.URLError, ConnectionRefusedError):
        return VLMResult(available=False)

    # 이미지를 base64로 인코딩
    image_data = Path(image_path).read_bytes()
    b64 = base64.b64encode(image_data).decode("utf-8")

    payload = json.dumps({
        "model": mdl,
        "prompt": prompt,
        "images": [b64],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
        elapsed = time.time() - t0
        return VLMResult(
            description=result.get("response", ""),
            elapsed_sec=round(elapsed, 3),
            available=True,
            model=mdl,
        )
    except Exception as e:
        print(f"VLM 호출 실패: {e}", file=sys.stderr)
        return VLMResult(available=False)
