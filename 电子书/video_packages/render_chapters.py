#!/usr/bin/env python3
"""
数据治理实战 · 视频批量渲染脚本
依赖: pip install playwright && playwright install chromium
     ffmpeg (brew install ffmpeg 或 https://ffmpeg.org/download.html)
用法: python3 render_chapters.py [章节号]
     不带参数 = 渲染全部10章
     python3 render_chapters.py 1    # 只渲染第1章
"""
import subprocess, json, os, time, sys

# ── 配置 ──────────────────────────────────────────────────────
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_CSS = """@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0a0e1a;font-family:'Noto Sans CJK SC','PingFang SC','Microsoft YaHei',sans-serif;}
"""

CSS = """
#bg-grid{position:fixed;inset:0;opacity:0.05;pointer-events:none;
  background-image:linear-gradient(rgba(59,130,246,.5) 1px,transparent 1px),
  linear-gradient(90deg, rgba(59,130,246,.5) 1px,transparent 1px);
  background-size:60px 60px;}
.accent{position:fixed;top:0;left:0;right:0;height:4px;
  background:linear-gradient(90deg,#1e3a6e,#3b82f6,#1e3a6e);z-index:10;}
.badge{position:fixed;bottom:40px;right:60px;font-size:22px;color:rgba(255,255,255,.2);
  letter-spacing:.2em;z-index:10;}
.scene{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
  flex-direction:column;opacity:0;pointer-events:none;}
.scene.active{opacity:1;pointer-events:auto;}
.title-bg{background:linear-gradient(135deg,#0a1628,#1a3a5c,#0a1628);}
.title-main{font-size:78px;font-weight:900;color:#fff;letter-spacing:.08em;
  text-align:center;text-shadow:0 0 80px rgba(59,130,246,.4);}
.title-sub{font-size:26px;color:#93c5fd;margin-top:20px;letter-spacing:.3em;}
.title-ch{font-size:20px;color:#60a5fa;margin-top:40px;letter-spacing:.5em;}
.content-bg{background:linear-gradient(180deg,#0f172a,#1e293b);}
.content-inner{max-width:1400px;width:100%;padding:0 80px;}
.content-title{font-size:50px;font-weight:700;color:#fff;margin-bottom:48px;
  letter-spacing:.05em;position:relative;padding-left:24px;}
.content-title::before{content:'';position:absolute;left:0;top:10%;height:80%;width:6px;
  background:linear-gradient(180deg,#3b82f6,#60a5fa);border-radius:3px;}
.points-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(580px,1fr));gap:18px;}
.point-card{background:rgba(255,255,255,.04);border:1px solid rgba(59,130,246,.2);
  border-radius:14px;padding:22px 30px;font-size:28px;color:#e2e8f0;
  line-height:1.6;display:flex;align-items:flex-start;gap:14px;}
.point-card::before{content:'▶';color:#3b82f6;font-size:18px;margin-top:4px;flex-shrink:0;}
.closing-bg{background:linear-gradient(135deg,#0a1628,#1a2a4a);}
.closing-text{font-size:54px;font-weight:700;color:#fff;text-align:center;
  letter-spacing:.1em;text-shadow:0 0 40px rgba(59,130,246,.3);}
.closing-brand{font-size:26px;color:#60a5fa;margin-top:28px;letter-spacing:.4em;}
"""

def build_html(ch_num, scenes):
    blocks = []
    for si, scene in enumerate(scenes):
        if scene['type']=='title':
            blocks.append(f'<div class="scene title-bg" id="s{si}"><div class="title-main">{scene["text"]}</div><div class="title-sub">数据治理实战</div><div class="title-ch">第{ch_num}章</div></div>')
        elif scene['type']=='content':
            pts = ''.join(f'<div class="point-card">{p}</div>' for p in scene.get('points',[]))
            blocks.append(f'<div class="scene content-bg" id="s{si}"><div class="content-inner"><div class="content-title" id="t{si}">{scene.get("title","")}</div><div class="points-grid" id="g{si}">{pts}</div></div></div>')
        elif scene['type']=='closing':
            blocks.append(f'<div class="scene closing-bg" id="s{si}"><div class="closing-text">{scene["text"]}</div><div class="closing-brand">米悦说说</div></div>')
    scenes_js = json.dumps(scenes, ensure_ascii=False)
    anim = f"""
<script>
var scenes={scenes_js};
var DUR={json.dumps([s.get('duration',5) for s in scenes])};
var t=0;
for(var i=0;i<scenes.length;i++){{
  (function(ii){{
    setTimeout(function(){{
      document.querySelectorAll('.scene').forEach(function(s,i){{s.classList.toggle('active',i===ii);}});
      var tl=gsap.timeline();
      if(ii===0){{
        tl.from('.title-main',{{opacity:0,y:50,duration:1.5,ease:'power3.out'}})
          .from('.title-sub',{{opacity:0,y:30,duration:.8}},'-=.6')
          .from('.title-ch',{{opacity:0,y:30,duration:.8}},'-=.4');
      }}else if(ii===scenes.length-1){{
        tl.from('.closing-text',{{opacity:0,scale:.85,duration:1.2,ease:'back.out(1.7)'}})
          .from('.closing-brand',{{opacity:0,y:20,duration:.8}},'-=.4');
      }}else{{
        var tEl=document.getElementById('t'+ii);
        var gEl=document.getElementById('g'+ii);
        if(tEl) tl.from(tEl,{{opacity:0,x:-40,duration:.8,ease:'power2.out'}});
        if(gEl) tl.from(gEl.querySelectorAll('.point-card'),{{opacity:0,y:40,stagger:.2,duration:.7,ease:'power2.out'}},'-=.3');
      }}
    }},t*1000);
  }})(i);
  t+=scenes[i].duration||5;
}}
</script>"""
    return f"""<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1920,height=1080"/>
<title>数据治理实战·第{ch_num}章</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<style>{FONTS_CSS}{CSS}</style>
</head><body>
<div id="bg-grid"></div><div class="accent"></div>
<div class="badge">第{ch_num}/10章</div>
{''.join(blocks)}
{anim}
</body></html>"""

def gen_srt(scenes, total_dur):
    def ms(t):
        h=int(t//3600); m=int((t%3600)//60); s=int(t%60); ms=int((t%1)*1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    cues=[]; elapsed=0.5
    for scene in scenes:
        if scene['type']=='title':
            d=scene.get('duration',4); cues.append((elapsed,elapsed+d,scene['text'])); elapsed+=d
        elif scene['type']=='content':
            for txt in [scene.get('title','')]+list(scene.get('points',[])):
                if txt: d=max(1.5,len(txt)/6); cues.append((elapsed,elapsed+d,txt)); elapsed+=d
        elif scene['type']=='closing':
            d=scene.get('duration',3); cues.append((elapsed,elapsed+d,scene['text'])); elapsed+=d
    lines=[]
    for i,(s,e,txt) in enumerate(cues):
        lines.extend([f'{i+1}',f'{ms(s)} --> {ms(min(e,total_dur))}',txt,''])
    return '\n'.join(lines)

def capture_frames(html_path, frames_dir, scenes, fps=8):
    from playwright.sync_api import sync_playwright
    os.makedirs(frames_dir, exist_ok=True)
    DUR = [s.get('duration',5) for s in scenes]
    scene_starts = []
    t = 0
    for d in DUR:
        scene_starts.append(t)
        t += d
    total_dur = sum(DUR)
    total_frames = int(total_dur * fps)
    scenes_js = json.dumps(scenes, ensure_ascii=False)

    print(f'  Capturing {total_frames} frames at {fps}fps (~{total_dur:.0f}s)...')
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox','--disable-setuid-sandbox','--use-gl=angle','--enable-webgl'])
        ctx = browser.new_context(viewport={'width':1920,'height':1080}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(f'file://{html_path}', wait_until='load')
        page.wait_for_timeout(800)
        t0 = time.time()

        for i in range(total_frames):
            elapsed = i / fps
            si = 0
            for si in range(len(DUR)):
                if elapsed < scene_starts[si] + DUR[si]:
                    break
            scene_time = max(0, elapsed - scene_starts[si])

            page.evaluate(f'''
                (function(){{
                    var DUR={json.dumps(DUR)};
                    var starts={json.dumps(scene_starts)};
                    var t={elapsed};
                    var si=0;
                    for(var j=0;j<DUR.length;j++){{if(t<starts[j]+DUR[j]){{si=j;break;}}}}
                    var cur=document.querySelector('.scene.active');
                    var next=document.getElementById('s'+si);
                    if(cur!==next){{
                        document.querySelectorAll('.scene').forEach(function(s,i){{s.classList.toggle('active',i===si);}});
                        if(window._tl){{window._tl.kill();window._tl=null;}}
                        var scenes={scenes_js};
                        var tl=gsap.timeline();
                        if(si===0){{
                            tl.from('.title-main',{{opacity:0,y:50,duration:1.5,ease:'power3.out'}})
                              .from('.title-sub',{{opacity:0,y:30,duration:.8}},'-=.6')
                              .from('.title-ch',{{opacity:0,y:30,duration:.8}},'-=.4');
                        }}else if(si===scenes.length-1){{
                            tl.from('.closing-text',{{opacity:0,scale:.85,duration:1.2,ease:'back.out(1.7)'}})
                              .from('.closing-brand',{{opacity:0,y:20,duration:.8}},'-=.4');
                        }}else{{
                            var tEl=document.getElementById('t'+si);
                            var gEl=document.getElementById('g'+si);
                            if(tEl) tl.from(tEl,{{opacity:0,x:-40,duration:.8,ease:'power2.out'}});
                            if(gEl) tl.from(gEl.querySelectorAll('.point-card'),{{opacity:0,y:40,stagger:.2,duration:.7,ease:'power2.out'}},'-=.3');
                        }}
                        window._tl=tl;
                        if({scene_time}>0) tl.seek({scene_time});
                    }}
                }})()
            ''')
            page.wait_for_timeout(0.05)
            page.screenshot(path=f'{frames_dir}/frame_{i:05d}.png', type='png')
            if (i+1)%30==0:
                dt=time.time()-t0; rate=(i+1)/dt; eta=(total_frames-i-1)/rate
                print(f'  {i+1}/{total_frames} ({(i+1)*100//total_frames}%, ETA:{eta:.0f}s)')

        browser.close()
    return total_frames

def render_chapter(ch_num):
    work = os.path.join(THIS_DIR, f'chapter{ch_num}_package')
    html_path = os.path.join(work, 'index.html')
    audio = os.path.join(work, 'narration.mp3')
    scenes_path = os.path.join(work, 'scenes.json')
    frames_dir = os.path.join(work, 'frames')
    output = os.path.join(work, f'chapter{ch_num}.mp4')

    with open(scenes_path, encoding='utf-8') as f:
        data = json.load(f)
    scenes = data['scenes']

    probe = subprocess.run(['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0',audio], capture_output=True, text=True)
    total_dur = float(probe.stdout.strip())

    # Write SRT
    srt_path = os.path.join(work, 'subtitles.srt')
    if not os.path.exists(srt_path):
        with open(srt_path,'w',encoding='utf-8') as f:
            f.write(gen_srt(scenes, total_dur))

    # Capture frames
    nframes = capture_frames(html_path, frames_dir, scenes, fps=8)

    # Compile video
    raw = os.path.join(work, 'raw.mp4')
    actual_fps = nframes / total_dur
    r = subprocess.run(['ffmpeg','-y',
        '-framerate', str(round(actual_fps, 1)),
        '-i', f'{frames_dir}/frame_%05d.png',
        '-c:v','libx264','-preset','fast','-crf','20',
        '-pix_fmt','yuv420p',
        '-vf','scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-t',str(total_dur),'-an',raw], capture_output=True)
    if r.returncode != 0:
        print(f'  FFmpeg error: {r.stderr[-200:]}')
        return False

    # Final: burn subtitles + mux audio
    r = subprocess.run(['ffmpeg','-y','-i',raw,'-i',audio,
        '-c:v','libx264','-preset','fast','-crf','20',
        '-c:a','aac','-b:a','192k',
        '-vf',f"subtitles='{srt_path}':force_style='FontName=Noto Sans CJK SC,FontSize=28,PrimaryColour=&H00FFFFFF,Outline=2,OutlineColour=&H00000000,Bold=1'",
        '-t',str(total_dur),output], capture_output=True)
    if r.returncode != 0:
        subprocess.run(['ffmpeg','-y','-i',raw,'-i',audio,
            '-c:v','libx264','-preset','fast','-crf','20',
            '-c:a','aac','-b:a','192k',
            '-t',str(total_dur),output], capture_output=True)

    # Cleanup frames
    subprocess.run(['rm','-rf',frames_dir], capture_output=True)
    subprocess.run(['rm','-f',raw], capture_output=True)

    sz = os.path.getsize(output)//(1024*1024) if os.path.exists(output) else 0
    print(f'  ✓ Chapter {ch_num}: {output} ({sz}MB)')
    return sz > 0

# ── 主入口 ──────────────────────────────────────────────────────
if __name__ == '__main__':
    chapters = list(range(1, 11))
    if len(sys.argv) > 1:
        chapters = [int(sys.argv[1])]

    print(f"=" * 50)
    print(f"数据治理实战 · 视频渲染")
    print(f"=" * 50)
    print(f"待渲染章节: {chapters}")
    print(f"输出目录: {THIS_DIR}")
    print(f"=" * 50)

    results = {}
    for ch in chapters:
        print(f"\n>>> Chapter {ch}")
        try:
            results[ch] = render_chapter(ch)
        except Exception as e:
            print(f'  Error: {e}')
            results[ch] = False

    print(f"\n{'='*50}")
    print('SUMMARY')
    for ch, ok in results.items():
        print(f'  Chapter {ch}: {"✓" if ok else "✗"}')
