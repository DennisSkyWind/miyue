#!/usr/bin/env python3
"""
数据治理实战 · 10章视频批量渲染流水线
流程: scenes.json → animated HTML → Playwright截帧 → FFmpeg合成 → MP4
"""
import subprocess, json, re, os, sys, time

# ── Config ────────────────────────────────────────────────────────────────
BASE = "/home/ubuntu/miyue/电子书/video_chapters"
TEMPLATE_HTML = "/home/ubuntu/miyue/电子书/scene_template.html"
FONTS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0a0e1a;font-family:'Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif;}
"""

SCENE_CSS = """
/* ── Background grid ── */
#bg-grid{position:fixed;inset:0;opacity:0.05;pointer-events:none;
  background-image:linear-gradient(rgba(59,130,246,0.5) 1px,transparent 1px),
  linear-gradient(90deg, rgba(59,130,246,0.5) 1px,transparent 1px);
  background-size:60px 60px;}
/* ── Top accent line ── */
.accent{position:fixed;top:0;left:0;right:0;height:4px;
  background:linear-gradient(90deg,#1e3a6e,#3b82f6,#1e3a6e);z-index:10;}
/* ── Chapter badge ── */
.badge{position:fixed;bottom:40px;right:60px;font-size:22px;color:rgba(255,255,255,0.25);
  letter-spacing:0.2em;z-index:10;}
/* ── Scenes ── */
.scene{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
  flex-direction:column;opacity:0;pointer-events:none;}
.scene.active{opacity:1;pointer-events:auto;}
/* Title scene */
.title-bg{background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 50%,#0a1628 100%);}
.title-main{font-size:80px;font-weight:900;color:#fff;letter-spacing:0.08em;
  text-align:center;text-shadow:0 0 80px rgba(59,130,246,0.4);}
.title-sub{font-size:28px;color:#93c5fd;margin-top:20px;letter-spacing:0.3em;}
.title-ch{font-size:20px;color:#60a5fa;margin-top:40px;letter-spacing:0.5em;}
/* Content scene */
.content-bg{background:linear-gradient(180deg,#0f172a 0%,#1e293b 100%);}
.content-inner{max-width:1400px;width:100%;padding:0 80px;}
.content-title{font-size:52px;font-weight:700;color:#fff;margin-bottom:50px;
  letter-spacing:0.05em;position:relative;padding-left:24px;}
.content-title::before{content:'';position:absolute;left:0;top:10%;height:80%;width:6px;
  background:linear-gradient(180deg,#3b82f6,#60a5fa);border-radius:3px;}
.points-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(580px,1fr));gap:20px;}
.point-card{background:rgba(255,255,255,0.04);border:1px solid rgba(59,130,246,0.2);
  border-radius:16px;padding:24px 32px;font-size:30px;color:#e2e8f0;
  line-height:1.6;display:flex;align-items:flex-start;gap:16px;transition:all 0.3s;}
.point-card::before{content:'▶';color:#3b82f6;font-size:20px;margin-top:4px;flex-shrink:0;}
.point-card b,.point-card strong{color:#93c5fd;}
.point-card em{color:#fcd34d;font-style:normal;}
/* Closing scene */
.closing-bg{background:linear-gradient(135deg,#0a1628 0%,#1a2a4a 100%);}
.closing-text{font-size:56px;font-weight:700;color:#fff;text-align:center;
  letter-spacing:0.1em;text-shadow:0 0 40px rgba(59,130,246,0.3);}
.closing-brand{font-size:28px;color:#60a5fa;margin-top:30px;letter-spacing:0.4em;}
/* Formula/code scene */
.formula-bg{background:linear-gradient(135deg,#0f1a0a 0%,#1a2a15 50%,#0f1a0a 100%);}
.formula-text{font-size:52px;font-weight:700;color:#86efac;text-align:center;
  max-width:1400px;line-height:1.5;font-family:'Courier New',monospace;}
.formula-note{font-size:28px;color:#4ade80;margin-top:40px;text-align:center;}
/* Highlight insight */
.insight-bg{background:linear-gradient(135deg,#1a0a0a 0%,#2a1515 50%,#1a0a0a 100%);}
.insight-text{font-size:64px;font-weight:700;color:#fff;text-align:center;
  max-width:1400px;line-height:1.4;}
.insight-hl{display:inline-block;background:linear-gradient(90deg,#fbbf24,#f59e0b);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
"""

SCENE_HTML = {
    "title": '''<div class="scene title-bg" id="s{i}">
  <div class="title-main">{text}</div>
  <div class="title-sub">数据治理实战</div>
  <div class="title-ch">{chapter}</div>
</div>''',
    "content": '''<div class="scene content-bg" id="s{i}">
  <div class="content-inner">
    <div class="content-title" id="t{i}">{title}</div>
    <div class="points-grid" id="g{i}">
      {points}
    </div>
  </div>
</div>''',
    "closing": '''<div class="scene closing-bg" id="s{i}">
  <div class="closing-text">{text}</div>
  <div class="closing-brand">米悦说说</div>
</div>''',
}

def build_html(chapter_num, scenes):
    """Build animated HTML from scenes list"""
    html_parts = [f"""<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1920,height=1080"/>
<title>数据治理实战·第{chapter_num}章</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<style>{FONTS_CSS}{SCENE_CSS}</style>
</head><body>
<div id="bg-grid"></div><div class="accent"></div>
<div class="badge">第{chapter_num}/10章</div>
"""]
    for si, scene in enumerate(scenes):
        t = scene['type']
        if t == 'title':
            html_parts.append(SCENE_HTML['title'].format(i=si, text=scene['text'], chapter=f"第{chapter_num}章"))
        elif t == 'content':
            pts_html = ''
            for p in scene.get('points', []):
                pts_html += f'<div class="point-card">{p}</div>'
            html_parts.append(SCENE_HTML['content'].format(i=si, title=scene.get('title',''), points=pts_html))
        elif t == 'closing':
            html_parts.append(SCENE_HTML['closing'].format(i=si, text=scene['text']))

    # Animation JS
    anim_js = f"""
<script>
const scenes = {json.dumps(scenes, ensure_ascii=False)};
let current = -1;
const DURATION = scenes.reduce((a,s)=>a+(s.duration||5),0);
let elapsed = 0;

function showScene(idx) {{
  if(idx < 0 || idx >= scenes.length) return;
  document.querySelectorAll('.scene').forEach((s,i)=>{{
    s.classList.toggle('active', i===idx);
  }});
  current = idx;
  const scene = scenes[idx];
  const tl = gsap.timeline();
  if(idx === 0) {{
    tl.from('.title-main', {{opacity:0, y:40, duration:1.2, ease:'power2.out'}})
      .from('.title-sub', {{opacity:0, y:20, duration:0.8, ease:'power2.out'}}, '-=0.6')
      .from('.title-ch', {{opacity:0, y:20, duration:0.8, ease:'power2.out'}}, '-=0.4');
  }} else if(idx === scenes.length-1) {{
    tl.from('.closing-text', {{opacity:0, scale:0.9, duration:1, ease:'back.out(1.7)'}})
      .from('.closing-brand', {{opacity:0, y:20, duration:0.8}}, '-=0.4');
  }} else {{
    tl.from(`#t{{idx}}`, {{opacity:0, x:-30, duration:0.7, ease:'power2.out'}})
      .from(`#g{{idx}} .point-card`, {{opacity:0, y:30, stagger:0.15, duration:0.6, ease:'power2.out'}}, '-=0.3');
  }}
}}

// Auto-advance based on scene durations
function runTimeline() {{
  let t = 0;
  for(let i=0;i<scenes.length;i++) {{
    const delay = t;
    setTimeout(()=>showScene(i), delay*1000);
    t += scenes[i].duration||5;
  }}
  // Loop
  setTimeout(runTimeline, DURATION*1000);
}}
setTimeout(runTimeline, 500);
</script>
</body></html>"""
    html_parts.append(anim_js)
    return '\n'.join(html_parts)

def generate_srt(scenes, total_duration):
    """Generate SRT subtitle file from scenes"""
    srt_lines = []
    cue_idx = 1
    elapsed = 0.5  # start 0.5s in
    
    # Build flat list of subtitle cues
    cues = []
    for scene in scenes:
        if scene['type'] == 'title':
            cues.append((elapsed, elapsed + scene.get('duration', 4), scene['text']))
            elapsed += scene.get('duration', 4)
        elif scene['type'] == 'content':
            if scene.get('title'):
                cues.append((elapsed, elapsed + 1.5, scene['title']))
                elapsed += 1.5
            for pt in scene.get('points', []):
                cues.append((elapsed, elapsed + 2, pt))
                elapsed += 2
            elapsed += scene.get('duration', 5) - 1.5 - len(scene.get('points',[]))*2
        elif scene['type'] == 'closing':
            cues.append((elapsed, elapsed + scene.get('duration', 3), scene['text']))
    
    # Trim to total_duration
    all_cues = []
    for start, end, text in cues:
        if start < total_duration:
            all_cues.append((start, min(end, total_duration), text))
    
    for si, (start, end, text) in enumerate(all_cues):
        srt_lines.append(f"{si+1}")
        srt_lines.append(f"{ms(start)} --> {ms(end)}")
        srt_lines.append(text)
        srt_lines.append("")
    
    return '\n'.join(srt_lines)

def ms(t):
    h = int(t//3600); m = int((t%3600)//60); s = int(t%60); ms = int((t%1)*1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def render_chapter(ch_num, scenes, audio_mp3):
    """Render one chapter: HTML + frames + video"""
    work = f"{BASE}/chapter{ch_num}"
    html_path = f"{work}/html/chapter{ch_num}.html"
    frames_dir = f"{work}/frames"
    video_path = f"{work}/video/chapter{ch_num}.mp4"
    os.makedirs(f"{work}/frames", exist_ok=True)
    os.makedirs(f"{work}/video", exist_ok=True)

    # 1. Write HTML
    html = build_html(ch_num, scenes)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  HTML: {html_path}")

    # 2. Estimate total duration from audio
    try:
        probe = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', audio_mp3
        ], capture_output=True, text=True, timeout=10)
        total_dur = float(probe.stdout.strip())
    except:
        total_dur = sum(s.get('duration', 5) for s in scenes)

    # 3. Generate SRT
    srt = generate_srt(scenes, total_dur)
    srt_path = f"{work}/subtitles/chapter{ch_num}.srt"
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt)
    print(f"  SRT:  {srt_path}")

    # 4. Capture frames with Playwright
    print(f"  Capturing frames (~{total_dur:.0f}s)...")
    capture_js = f"""
const {{ chromium }} = require('playwright');
const path = require('path');

const URL = 'file://{html_path}';
const FPS = 30;
const TOTAL = {total_dur};
const TOTAL_FRAMES = Math.ceil(TOTAL * FPS);
const OUT_DIR = '{frames_dir}';

(async () => {{
  const browser = await chromium.launch({{
    args: ['--no-sandbox','--disable-setuid-sandbox','--use-gl=angle','--enable-webgl']
  }});
  const ctx = await browser.newContext({{viewport:{{width:1920,height:1080}},deviceScaleFactor:1}});
  const page = await ctx.newPage();
  await page.goto(URL, {{waitUntil:'networkidle'}});
  await page.waitForTimeout(2000); // let GSAP init

  console.log(`Capturing ${{TOTAL_FRAMES}} frames...`);
  for(let i=0;i<TOTAL_FRAMES;i++) {{
    const t = i/FPS;
    // seek audio element if exists
    await page.evaluate((time) => {{
      const audio = document.querySelector('audio');
      if(audio) audio.currentTime = time;
    }}, t);
    await page.waitForTimeout(30);
    await page.screenshot({{
      path: `${{OUT_DIR}}/frame_${{String(i).padStart(5,'0')}}.png`,
      type:'png'
    }});
    if(i%60===0) process.stdout.write(`  ${{(i/TOTAL_FRAMES*100).toFixed(1)}}%\\n`);
  }}
  await browser.close();
  console.log('Done');
}})();
"""
    capture_script = f"/tmp/capture_c{ch_num}.js"
    with open(capture_script, 'w') as f:
        f.write(capture_js)

    try:
        result = subprocess.run(['node', capture_script],
            capture_output=True, text=True, timeout=int(total_dur*2+60))
        print(result.stdout[-200:] if result.stdout else '')
        if result.returncode != 0:
            print("STDERR:", result.stderr[-200:] if result.stderr else '')
    except Exception as e:
        print(f"  Playwright capture error: {e}")

    # 5. Compile video
    frame_count = len([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    print(f"  Frames captured: {frame_count}")

    if frame_count < 50:
        print(f"  [WARN] Low frame count, using fallback background")
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'color=c=0a0e1a:s=1920x1080:d={total_dur}:r=30',
            '-frames:v', str(frame_count or 10),
            f'{frames_dir}/frame_%05d.png'
        ], capture_output=True)
        frame_count = len([f for f in os.listdir(frames_dir) if f.endswith('.png')])

    # Mix narration + gentle BGM
    mixed_audio = f"/tmp/c{ch_num}_mixed.mp3"
    has_bgm = os.path.exists('/home/ubuntu/hf-demo/chapter1-video/assets/bgm.mp3')
    if has_bgm:
        subprocess.run([
            'ffmpeg', '-y',
            '-i', audio_mp3,
            '-i', '/home/ubuntu/hf-demo/chapter1-video/assets/bgm.mp3',
            '-filter_complex', '[0:a]volume=1.2[nar];[1:a]volume=0.2,bass,g=3[bg];[nar][bg]amix=inputs=2:duration=first',
            '-t', str(total_dur), '-q:a', '2', mixed_audio
        ], capture_output=True)
    else:
        mixed_audio = audio_mp3

    # Video from frames
    video_raw = f"/tmp/c{ch_num}_raw.mp4"
    subprocess.run([
        'ffmpeg', '-y',
        '-framerate', '30',
        '-i', f'{frames_dir}/frame_%05d.png',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-pix_fmt', 'yuv420p', '-t', str(total_dur),
        '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-an', video_raw
    ], capture_output=True)
    print(f"  Raw video compiled")

    # Burn subtitles + mux audio
    sub_args = [
        'ffmpeg', '-y',
        '-i', video_raw,
        '-i', mixed_audio,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'aac', '-b:a', '192k',
        '-vf', f"subtitles='{srt_path}':force_style='FontName=Noto Sans SC,FontSize=28,PrimaryColour=&H00FFFFFF,Outline=2,OutlineColour=&H00000000,Bold=1'",
        '-t', str(total_dur),
        video_path
    ]
    result = subprocess.run(sub_args, capture_output=True)
    if result.returncode != 0:
        # Try without subtitles
        subprocess.run([
            'ffmpeg', '-y', '-i', video_raw, '-i', mixed_audio,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '192k',
            '-t', str(total_dur), video_path
        ], capture_output=True)

    if os.path.exists(video_path):
        sz = os.path.getsize(video_path) // (1024*1024)
        print(f"  ✓ Video: {video_path} ({sz}MB)")
    else:
        print(f"  ✗ Video generation failed")

    # Cleanup frames
    subprocess.run(['rm', '-rf', frames_dir], capture_output=True)
    for tmp in [video_raw, mixed_audio, capture_script]:
        subprocess.run(['rm', '-f', tmp], capture_output=True)

    return video_path if os.path.exists(video_path) else None

# ── Main ─────────────────────────────────────────────────────────────────────
print("=" * 60)
print("数据治理实战 · 批量视频渲染")
print("=" * 60)

results = {}
for ch_num in range(1, 11):
    scenes_path = f"{BASE}/chapter{ch_num}/scenes.json"
    audio_mp3 = f"{BASE}/chapter{ch_num}/audio/narration.mp3"
    
    if not os.path.exists(scenes_path):
        print(f"\n[SKIP] Chapter {ch_num}: no scenes.json")
        continue
    if not os.path.exists(audio_mp3):
        print(f"\n[SKIP] Chapter {ch_num}: no audio")
        continue

    with open(scenes_path, encoding='utf-8') as f:
        data = json.load(f)
    scenes = data['scenes']
    title = data['title']
    
    print(f"\n{'='*50}")
    print(f"Rendering Chapter {ch_num}: {title[:40]}")
    print(f"{'='*50}")
    
    result = render_chapter(ch_num, scenes, audio_mp3)
    results[ch_num] = result

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for ch_num, path in results.items():
    status = "✓" if path else "✗"
    print(f"  Chapter {ch_num:2d}: {status} {path or 'FAILED'}")
