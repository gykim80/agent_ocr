# /ocr — Local Image Analysis for AI Agents

> **[한국어 문서 (Korean)](docs/README_KO.md)**

Zero-cost local image analysis tool that converts images into structured Markdown text. Designed as a Claude Code skill (`/ocr`) so LLMs can understand images **without expensive vision API calls**.

## Why?

Attaching images directly to LLMs costs ~$0.01-0.04 per image. This tool analyzes images **locally** and outputs structured text that any LLM can understand — at **$0 cost**.

### Before / After

<p align="center">
  <img src="demo_output/tweakcn_before_after.png" alt="Before/After comparison" width="100%">
</p>

> Left: Original screenshot | Right: `/ocr` L2 detection — 44 UI elements + 38 OCR texts extracted locally

<p align="center">
  <img src="demo_output/tweakcn_detection.png" alt="Detection result with bounding boxes" width="80%">
</p>

### Token & Cost Comparison

Real screenshots are **Retina/4K resolution**. `Cmd+Shift+3` on a MacBook Pro 14" captures 3024×1964px — that's **2,125 tokens per image**, re-sent every turn.

| Device | Resolution | Vision API Tokens | 10-Turn Cost (Opus) | /ocr |
|--------|-----------|-------------------|---------------------|------|
| MacBook Pro 14" (Retina) | 3024×1964 | 2,125 | $0.319 | **$0** |
| MacBook Pro 16" (Retina) | 3456×2234 | 2,635 | $0.395 | **$0** |
| Dell 4K Monitor | 3840×2160 | 2,635 | $0.395 | **$0** |
| iMac 24" (Retina 4.5K) | 4480×2520 | 4,165 | $0.625 | **$0** |
| Windows FHD | 1920×1080 | 1,105 | $0.166 | **$0** |

**Monthly cost** (20 screenshots/day × 30 days):

| Model | Vision API | /ocr | Savings |
|-------|-----------|------|---------|
| Claude Opus | **$19.12** | $0 | 100% |
| Claude Sonnet | **$3.83** | $0 | 100% |
| GPT-4o | **$4.78** | $0 | 100% |

`/ocr` converts any image into **~600 tokens of structured Markdown** regardless of resolution. No image tokens in context, no per-turn re-billing, no context window pollution.

## 3-Layer Hybrid Pipeline

```
/ocr image.png
  │
  ▼
┌─────────────────────────────────────────────┐
│  L1: Zero-Cost (always runs)                │
│  OS OCR + Color Analysis + Classification   │
│  ~3s | 0MB models | $0                      │
└──────────────┬──────────────────────────────┘
               │ auto-escalate if OCR < 5 texts
               ▼
┌─────────────────────────────────────────────┐
│  L2: Semantic (optional install)            │
│  YOLO UI Detection + Florence2 Captioning   │
│  ~8s | 39MB-1GB models                      │
└──────────────┬──────────────────────────────┘
               │ auto-escalate for diagrams
               ▼
┌─────────────────────────────────────────────┐
│  L3: VLM (optional, via Ollama)             │
│  Full natural language image understanding  │
│  ~15s | 2GB+ model                          │
└─────────────────────────────────────────────┘
```

## Install

```bash
git clone https://github.com/gykim80/agent_ocr.git
cd agent_ocr
pip install -e ".[macos]"   # macOS (auto-detects Retina)
# pip install -e ".[linux]" # Linux
# pip install -e ".[full]"  # L2: YOLO + Florence2 included
```

### As Claude Code Skill

```bash
cp skills/eyes.md ~/.claude/commands/ocr.md
```

That's it. Just use it:

```
/ocr screenshot.png
/ocr error.png "what's the error?"
/ocr diagram.png --layer 2
```

The agent handles everything — dependency checks, layer escalation, model downloads. You just pass an image.

> **L2/L3 models are auto-downloaded on first use.** No manual setup needed.
> YOLO weights (39MB) → `~/.cache/eyes/models/`
> Ollama VLM → `ollama pull qwen3-vl:2b`

## Output Example

```markdown
## Image Analysis: dashboard.png
**Size**: 1920x1080px | **Mode**: Light | **Type**: Screenshot

### Scene
A file management application with sidebar navigation.

### UI Elements (264 detected)
**Large regions** (1):
- [0,64→256,1080] 256x1016px → "Sidebar"

**Small icons/buttons** (263):
- [32,100] 24x24px "search" (search icon)
- [32,140] 24x24px "settings" (gear icon)

### Text Content (OCR: 201 items)
- [32,20] "Dashboard"
- [400,100] "Total Revenue"
- [400,140] "$12,450"

### Color Palette
- #FFFFFF (72%) | #F5F5F5 (15%) | #007AFF (8%)
```

## Cross-Platform Support

| Platform | L1 OCR | L1 Classify | L2 YOLO | L3 VLM |
|----------|--------|-------------|---------|--------|
| macOS    | Vision Framework | VNClassify | MPS/CPU | Ollama |
| Linux    | Tesseract | PIL Heuristic | CUDA/CPU | Ollama |
| Windows  | winocr | PIL Heuristic | CUDA/CPU | Ollama |

## Project Structure

```
src/eyes/
├── platform/        # Cross-platform abstraction
│   ├── base.py      # ABC interfaces
│   ├── darwin.py     # macOS Vision
│   ├── linux.py      # Tesseract
│   ├── windows.py    # winocr
│   ├── fallback.py   # PIL-only universal
│   └── factory.py    # Auto-detect OS → provider
├── layer1/          # Zero-cost analysis
│   ├── color.py      # Palette + dark mode
│   └── meta.py       # Image metadata
├── layer2/          # Semantic analysis
│   ├── yolo_detect.py       # OmniParser YOLO
│   ├── florence_caption.py  # Florence2 captioning
│   └── synthesizer.py       # OCR + YOLO spatial merge
├── layer3/          # VLM analysis
│   └── vlm.py       # Ollama API
├── formatter/
│   └── markdown.py  # Adaptive Markdown output
├── pipeline.py      # 3-layer orchestrator
├── cli.py           # CLI entry point
└── config.py        # Settings
```

## License

MIT
