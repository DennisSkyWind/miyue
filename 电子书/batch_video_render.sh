#!/bin/bash
set -e

SOURCE="/home/ubuntu/miyue/电子书/数据治理实战：从二级分类到落地执行.md"
OUTPUT_BASE="/home/ubuntu/miyue/电子书/video_chapters"
TEMPLATE_HTML="/home/ubuntu/chapter1-video/scene_template.js"
FONT="/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
mkdir -p "$OUTPUT_BASE"

# ── Chapter metadata ──────────────────────────────────────────────
declare -a CH
CH[1]="第一章 数据治理的本质：不是治数据，是治责任"
CH[2]="第二章 主数据二级分类模型：谁该管、谁不该管"
CH[3]="第三章 治理模式选择：集中制、联邦制还是混合制"
CH[4]="第四章 源端治理四步法"
CH[5]="第五章 主数据平台定位：核查+分发"
CH[6]="第六章 数据治理的正确顺序：为什么HR主数据要优先"
CH[7]="第七章 撬动HR主数据治理：从确权到建组织的路径"
CH[8]="第九章 实战案例：某药企数据治理项目复盘"
CH[9]="第十章 数据治理的10条实战军规"
CH[10]="附录"

# ── Extract chapter N body from markdown ─────────────────────────
extract_chapter() {
  local n=$1
  python3 << PYEOF
with open('$SOURCE', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
chapters = []
current = None
buf = []
for line in lines:
    if line.startswith('## ') and not line.startswith('### '):
        if current is not None:
            chapters.append((current, '\n'.join(buf).strip()))
        current = line[3:].strip()
        buf = []
    elif current is not None:
        buf.append(line)
if current is not None:
    chapters.append((current, '\n'.join(buf).strip()))
# chapters[0]=TOC, [1..10]=ch1..ch10
if $n >= 1 and $n <= 10:
    title, body = chapters[$n]
    print(f"__TITLE__={title}")
    print("__BODY__START")
    print(body)
    print("__BODY__END")
PYEOF
}

# ── Build scenes JSON for a chapter ──────────────────────────────
build_scenes() {
  local n=$1
  local title=$(extract_chapter $n | grep '^__TITLE__=' | cut -d= -f2-)
  local body=$(extract_chapter $n | awk '/^__BODY__START/,/^__BODY__END/' | sed '1d;$d')

  python3 << PYEOF
import json, sys

title = """$title"""
body = """$body"""

# ── Parse bullets from markdown body ──────────────────────────────
import re
lines = body.split('\n')
scenes = []

# Scene 1: Title card
scenes.append({"type":"title","text":title,"duration":4})

# Scene 2: Opening / problem statement
open_buf = []
for line in lines:
    if line.startswith('### ') or line.startswith('## '): break
    if line.strip(): open_buf.append(line.strip())
if open_buf:
    scenes.append({"type":"content","title":"问题","points":open_buf[:6],"duration":8})

# Remaining sections as content scenes
current_title = ""
current_points = []
for line in lines:
    line = line.strip()
    if not line: continue
    if line.startswith('### ') and not line.startswith('#### '):
        if current_title and current_points:
            scenes.append({"type":"content","title":current_title,"points":current_points,"duration":7})
        current_title = line.lstrip('#').strip()
        current_points = []
    elif line.startswith('- ') or line.startswith('* '):
        txt = re.sub(r'^[*-]\s+','',line)
        if txt and len(txt) > 2:
            current_points.append(txt)
    elif line.startswith('```') or line.startswith('>'): continue
    elif re.match(r'^Table', line): continue
    elif current_title:
        # plain text → add as point if short enough
        clean = re.sub(r'[#`*|]','',line).strip()
        if clean and len(clean) > 5:
            current_points.append(clean)
        if len(current_points) >= 5:
            scenes.append({"type":"content","title":current_title,"points":current_points,"duration":7})
            current_points = []

if current_title and current_points:
    scenes.append({"type":"content","title":current_title,"points":current_points,"duration":7})

# Closing scene
scenes.append({"type":"closing","text":"米悦说说 · 数据治理实战","duration":3})

print(json.dumps({"title":title,"scenes":scenes}, ensure_ascii=False, indent=2))
PYEOF
}

# ── Main loop ────────────────────────────────────────────────────
for n in {1..10}; do
  echo "=== Processing Chapter $n: ${CH[$n]} ==="
  WORK_DIR="$OUTPUT_BASE/chapter${n}"
  mkdir -p "$WORK_DIR"/{audio,html,subtitles,video}

  # Build scenes
  SCENES_JSON=$(build_scenes $n)
  echo "$SCENES_JSON" > "$WORK_DIR/scenes.json"

  # TTS narration (Edge-TTS YunxiNeural, 0.8x speed for readability)
  echo "  [TTS] Generating audio..."
  TITLE=$(echo "$SCENES_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['title'])")
  AUDIO_WAV="$WORK_DIR/audio/narration.wav"
  AUDIO_MP3="$WORK_DIR/audio/narration.mp3"

  # Generate full narration from all scene texts
  python3 << PYEOF
import subprocess, json, re

with open('$WORK_DIR/scenes.json', encoding='utf-8') as f:
    data = json.load(f)

narration_lines = []
for scene in data['scenes']:
    if scene['type'] == 'title':
        narration_lines.append(scene['text'])
    elif scene['type'] == 'content':
        if scene.get('title'):
            narration_lines.append(scene['title'])
        narration_lines.extend(scene.get('points', []))
    elif scene['type'] == 'closing':
        narration_lines.append(scene['text'])

full_text = '\n'.join(narration_lines)
print(full_text, file=open('$WORK_DIR/narration_raw.txt','w',encoding='utf-8'))
PYEOF

  edge-tts --voice "zh-CN-YunxiNeural" --rate "+0%" --text-file "$WORK_DIR/narration_raw.txt" --write-media "$AUDIO_WAV" 2>/dev/null ||   edge-tts --voice "zh-CN-YunxiNeural" --rate "+0%" --write-media "$AUDIO_WAV" <<< "$(cat $WORK_DIR/narration_raw.txt)" 2>/dev/null || true

  if [ -f "$AUDIO_WAV" ]; then
    ffmpeg -y -i "$AUDIO_WAV" -ar 44100 -ac 2 -q:a 2 "$AUDIO_MP3" 2>/dev/null && echo "  [OK] Audio: $(du -sh $AUDIO_MP3 | cut -f1)" || true
  fi

  echo "  [Done] Chapter $n → $WORK_DIR"
done

echo "=== ALL 10 CHAPTERS PROCESSED ==="
