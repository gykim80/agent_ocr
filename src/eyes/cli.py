"""CLI 엔트리포인트 — /eyes 스킬이 호출하는 백엔드"""
import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        prog="eyes",
        description="로컬 이미지 분석 도구 — 구조화된 Markdown 출력",
    )
    parser.add_argument("image", help="분석할 이미지 파일 경로")
    parser.add_argument("prompt", nargs="?", default=None, help="커스텀 분석 프롬프트")
    parser.add_argument("--layer", type=int, choices=[1, 2, 3], default=None,
                        help="강제 레이어 지정 (1=OS, 2=YOLO, 3=VLM)")
    parser.add_argument("--max-layer", type=int, choices=[1, 2, 3], default=3,
                        help="최대 레이어 제한 (기본: 3)")
    parser.add_argument("--yolo-model", default=None, help="YOLO 모델 경로")
    parser.add_argument("--florence-weights", default=None, help="Florence2 weights 경로")

    args = parser.parse_args()

    # 이미지 파일 존재 확인
    if not os.path.isfile(args.image):
        print(f"Error: 파일을 찾을 수 없습니다: {args.image}", file=sys.stderr)
        sys.exit(1)

    from eyes.pipeline import analyze

    result = analyze(
        image_path=args.image,
        user_prompt=args.prompt,
        max_layer=args.max_layer,
        force_layer=args.layer,
        yolo_model_path=args.yolo_model,
        florence_weights=args.florence_weights,
    )

    # stdout에 Markdown 출력 (Claude Code가 읽을 수 있도록)
    print(result)


if __name__ == "__main__":
    main()
