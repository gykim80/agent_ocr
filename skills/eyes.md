# /eyes — 로컬 이미지 분석

이미지를 로컬에서 분석하여 구조화된 Markdown 텍스트를 생성합니다.
LLM에 이미지를 직접 전송하지 않으므로 비용 $0.

## Usage
```
/eyes <이미지경로> [커스텀 프롬프트]
```

## Examples
```
/eyes screenshot.png
/eyes error.png "에러 내용 분석"
/eyes diagram.png "아키텍처 관계 설명"
/eyes ui.png --layer 2
```

## Instructions

사용자가 `/eyes`를 호출하면, 아래 단계를 수행하라:

1. 인자에서 이미지 경로와 선택적 프롬프트를 파싱한다.
2. Bash 도구로 다음 명령을 실행한다:
   ```bash
   cd /Users/andrew.kim/Desktop/eyes && python -m eyes "<이미지경로>" "<프롬프트>"
   ```
   - 프롬프트가 없으면 두 번째 인자를 생략한다.
   - `--layer 1|2|3` 옵션이 있으면 해당 레이어를 강제 사용한다.
   - `--max-layer 1|2` 옵션이 있으면 최대 레이어를 제한한다.

3. 명령의 stdout 출력(Markdown)을 그대로 사용자에게 보여준다.
4. stderr 출력은 진행 상황 로그이므로, 오류가 있으면 사용자에게 알린다.

## OmniParser YOLO 모델 경로
YOLO 모델이 기본 캐시 위치에 없으면 프로젝트 내 경로를 사용한다:
```bash
python -m eyes "<이미지>" --yolo-model "OmniParser/weights/icon_detect/model.pt"
```

## Florence2 weights 경로
```bash
python -m eyes "<이미지>" --florence-weights "OmniParser/weights/icon_caption_florence"
```

## 출력
분석 결과는 Markdown 형식으로 stdout에 출력된다:
- Image metadata (크기, 포맷, 모드)
- Scene description (Florence2 캡션, 있을 경우)
- UI Elements (YOLO 감지 결과 + OCR 텍스트 매칭)
- Text Content (OCR 전체 텍스트)
- Color Palette (지배색, 다크/라이트 모드)
- VLM Analysis (Ollama 분석, 있을 경우)

## 설치 상태 확인
```bash
cd /Users/andrew.kim/Desktop/eyes && python -c "
import eyes; print('eyes OK')
try:
    from ultralytics import YOLO; print('YOLO OK')
except: print('YOLO: pip install ultralytics')
try:
    from transformers import AutoProcessor; print('Florence2 OK')
except: print('Florence2: pip install transformers==4.46.3')
"
```
