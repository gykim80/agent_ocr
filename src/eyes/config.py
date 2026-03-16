"""설정 관리"""
import os
from pathlib import Path

# 모델 weights 저장 경로
MODELS_DIR = Path(os.environ.get(
    "EYES_MODELS_DIR",
    Path.home() / ".cache" / "eyes" / "models"
))

# OmniParser YOLO weights
YOLO_MODEL_PATH = MODELS_DIR / "icon_detect" / "model.pt"

# Florence2 weights (선택적)
FLORENCE2_DIR = MODELS_DIR / "icon_caption_florence"

# 에스컬레이션 임계값
L1_OCR_MIN_COUNT = 5          # OCR 결과가 이 수 미만이면 L2로 에스컬레이션
L1_CLASSIFY_ESCALATE = {"diagram", "photo", "illustration"}

# YOLO 설정
YOLO_CONF_THRESHOLD = 0.05
YOLO_IOU_THRESHOLD = 0.7

# Florence2 설정
FLORENCE2_MAX_ICONS = 20
FLORENCE2_CROP_SIZE = 64

# Ollama 설정 (L3)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("EYES_VLM_MODEL", "qwen3-vl:2b")
