#!/usr/bin/env python3
"""批量生成10章视频的音频+场景JSON"""
import subprocess, json, re, os, sys

SOURCE = "/home/ubuntu/miyue/电子书/数据治理实战：从二级分类到落地执行.md"
OUTPUT_BASE = "/home/ubuntu/miyue/电子书/video_chapters"
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

os.makedirs(OUTPUT_BASE, exist_ok=True)

# ── Load & parse all chapters from markdown ────────────────────────────────
with open(SOURCE, encoding='utf-8') as f:
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

print(f"Total sections parsed: {len(chapters)}")

# chapters[0]=TOC, [1..10]=ch1..ch10
MAIN_CHAPTERS = [(chapters[i][0], chapters[i][1]) for i in range(1, 11)]
CHAPTER_TITLES = [t for t, _ in MAIN_CHAPTERS]

# ── Parse scenes from chapter body ────────────────────────────────────────
def parse_scenes(title, body):
    scenes = []
    all_lines = body.split('\n')

    # Scene 1: Title card
    scenes.append({"type": "title", "text": title, "duration": 4})

    # Scene 2: Opening (lines before first ### heading)
    open_buf = []
    for line in all_lines:
        stripped = line.strip()
        if stripped.startswith('### ') or stripped.startswith('## '):
            break
        if stripped:
            clean = re.sub(r'[#`*>\[\]]', '', stripped).strip()
            if clean:
                open_buf.append(clean)
    if open_buf:
        scenes.append({"type": "content", "title": "问题", "points": open_buf[:6], "duration": 8})

    # Content scenes
    current_title = ""
    current_points = []
    for line in all_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('### ') and not stripped.startswith('#### '):
            if current_title and current_points:
                scenes.append({"type": "content", "title": current_title, "points": current_points[:6], "duration": 7})
            current_title = stripped.lstrip('#').strip()
            current_points = []
        elif stripped.startswith('- ') or stripped.startswith('* '):
            txt = re.sub(r'^[-*]\s+', '', stripped).strip()
            txt = re.sub(r'[#*`]', '', txt).strip()
            if txt and len(txt) > 2:
                current_points.append(txt)
        elif stripped.startswith('```') or stripped.startswith('>'):
            continue
        elif '|' in stripped and stripped.count('|') >= 3:
            continue  # skip table rows
        elif current_title:
            clean = re.sub(r'[#*|`\[\]]', '', stripped).strip()
            if clean and len(clean) > 5 and len(current_points) < 5:
                current_points.append(clean)

    if current_title and current_points:
        scenes.append({"type": "content", "title": current_title, "points": current_points[:6], "duration": 7})

    # Closing
    scenes.append({"type": "closing", "text": "米悦说说 · 数据治理实战", "duration": 3})
    return scenes

# ── Generate TTS audio for text ────────────────────────────────────────────
def generate_tts(text, output_wav):
    """Use Edge-TTS YunxiNeural"""
    import tempfile
    txt_file = output_wav.replace('.wav', '_raw.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(text)
    try:
        subprocess.run([
            'edge-tts',
            '--voice', 'zh-CN-YunxiNeural',
            '--rate', '+0%',
            '--text-file', txt_file,
            '--write-media', output_wav
        ], check=True, capture_output=True, timeout=120)
        return True
    except Exception as e:
        print(f"    TTS failed: {e}")
        return False

def wav_to_mp3(wav_path):
    mp3_path = wav_path.replace('.wav', '.mp3')
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', wav_path,
            '-ar', '44100', '-ac', '2', '-q:a', '2', mp3_path
        ], check=True, capture_output=True, timeout=60)
        return mp3_path
    except:
        return None

# ── Main loop ─────────────────────────────────────────────────────────────────
for idx, (title, body) in enumerate(MAIN_CHAPTERS):
    ch_num = idx + 1
    print(f"\n=== Chapter {ch_num}: {title} ===")
    work_dir = f"{OUTPUT_BASE}/chapter{ch_num}"
    for sub in ('audio', 'html', 'subtitles', 'video'):
        os.makedirs(f"{work_dir}/{sub}", exist_ok=True)

    # Build scenes
    scenes = parse_scenes(title, body)
    scenes_path = f"{work_dir}/scenes.json"
    with open(scenes_path, 'w', encoding='utf-8') as f:
        json.dump({"title": title, "scenes": scenes}, f, ensure_ascii=False, indent=2)
    print(f"  Scenes: {len(scenes)}")

    # Build narration text (concatenate all scene texts)
    narration_parts = []
    for scene in scenes:
        if scene['type'] == 'title':
            narration_parts.append(scene['text'])
        elif scene['type'] == 'content':
            if scene.get('title'):
                narration_parts.append(scene['title'])
            narration_parts.extend(scene.get('points', []))
        elif scene['type'] == 'closing':
            narration_parts.append(scene['text'])

    full_narration = '\n'.join(narration_parts)
    narration_txt_path = f"{work_dir}/narration.txt"
    with open(narration_txt_path, 'w', encoding='utf-8') as f:
        f.write(full_narration)

    # TTS
    wav_path = f"{work_dir}/audio/narration.wav"
    mp3_path = f"{work_dir}/audio/narration.mp3"
    if generate_tts(full_narration, wav_path):
        result = wav_to_mp3(wav_path)
        if result:
            size = os.path.getsize(result)
            print(f"  Audio: {size//1024}KB")
        else:
            print(f"  Audio: generated (mp3 conversion skipped)")
    else:
        print(f"  Audio: FAILED")

    print(f"  Done → {work_dir}")

print("\n=== ALL 10 CHAPTERS PROCESSED ===")
