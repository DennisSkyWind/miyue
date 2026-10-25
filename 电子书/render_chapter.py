#!/usr/bin/env python3
"""单章视频渲染 - 固定FPS截帧 + FFmpeg"""
import subprocess, json, os, time, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright

BASE = "/home/ubuntu/miyue/电子书/video_chapters"

def build_html(ch_num, scenes):
    FONTS = """@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
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
var TOTAL=DUR.reduce(function(a,b){{return a+b;}},0);
var t=0;
for(var i=0;i<scenes.length;i++){{
  (function(ii){{
    setTimeout(function(){{
      document.querySelectorAll('.scene').forEach(function(s,i){{s.classList.toggle('active',i===ii);}});
      var tl=gsap.timeline();
      if(ii===0){{
        tl.from('.title-main',{{opacity:0,y:50,duration:1.5,ease:'power3.out'}})
          .from('.title-sub',{{opacity:0,y:30,duration:.8}}, '-=.6')
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
<style>{FONTS}{CSS}</style>
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
            d=scene.get('duration',4)
            cues.append((elapsed,elapsed+d,scene['text'])); elapsed+=d
        elif scene['type']=='content':
            for txt in [scene.get('title','')]+list(scene.get('points',[])):
                if txt:
                    d=max(1.5,len(txt)/6)
                    cues.append((elapsed,elapsed+d,txt)); elapsed+=d
        elif scene['type']=='closing':
            d=scene.get('duration',3)
            cues.append((elapsed,elapsed+d,scene['text'])); elapsed+=d
    lines=[]
    for i,(s,e,txt) in enumerate(cues):
        lines.extend([f'{i+1}',f'{ms(s)} --> {ms(min(e,total_dur))}',txt,''])
    return '\n'.join(lines)

def capture_at_fps(html_path, frames_dir, scenes, fps=8):
    """Capture frames at fixed FPS. Only evaluate JS on scene changes; screenshot directly otherwise."""
    os.makedirs(frames_dir, exist_ok=True)
    total_dur = sum(s.get('duration',5) for s in scenes)
    total_frames = int(total_dur * fps)

    # Start local HTTP server so external CDN resources (fonts, GSAP) load properly
    html_dir = os.path.dirname(os.path.abspath(html_path))
    os.chdir(html_dir)  # ensure working dir matches so the handler can serve files
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=html_dir, **kwargs)
        def log_message(self, format, *args):
            pass  # suppress request logging
    server = HTTPServer(('127.0.0.1', 0), QuietHandler)
    t_server = Thread(target=server.serve_forever, daemon=True)
    t_server.start()
    port = server.server_address[1]

    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            '--no-sandbox','--disable-setuid-sandbox',
            '--use-gl=angle','--enable-webgl','--disable-gpu-sandbox'])
        ctx = browser.new_context(viewport={'width':1920,'height':1080}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(f'http://127.0.0.1:{port}/' + os.path.basename(html_path), wait_until='load')
        page.wait_for_timeout(2000)

        scenes_js = json.dumps(scenes, ensure_ascii=False)
        DUR = [s.get('duration',5) for s in scenes]
        scene_starts = []
        t = 0
        for d in DUR:
            scene_starts.append(t)
            t += d

        print(f'  Capturing {total_frames} frames at {fps}fps (~{total_dur:.0f}s, {len(scenes)} scenes)...')
        t0 = time.time()

        # Precompute which scene each frame belongs to (avoid recomputing every frame)
        frame_scene = []
        for i in range(total_frames):
            elapsed = i / fps
            si = 0
            for si in range(len(DUR)):
                if elapsed < scene_starts[si] + DUR[si]:
                    break
            else:
                si = len(DUR) - 1
            frame_scene.append(si)

        last_si = -1
        for i in range(total_frames):
            si = frame_scene[i]

            # Only call evaluate when scene changes
            if si != last_si:
                elapsed = i / fps
                scene_time = max(0, elapsed - scene_starts[si])

                try:
                    page.evaluate(f'''
                        (function(){{
                            var scenes={scenes_js};
                            var si={si};
                            var sceneT={scene_time};
                            // Switch active scene
                            document.querySelectorAll('.scene').forEach(function(s, idx){{s.classList.toggle('active', idx===si);}});
                            // Rebuild & seek GSAP timeline
                            if(window._tl){{window._tl.kill();window._tl=null;}}
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
                            if(sceneT>0) tl.seek(sceneT);
                        }})()
                    ''')
                except Exception as e:
                    print(f'  [WARN] evaluate error at frame {i} scene {si}: {{e}}')
                last_si = si
                last_si = si

            page.screenshot(path=f'{frames_dir}/frame_{i:05d}.png', type='png')

            if (i+1) % 30 == 0:
                dt = time.time()-t0
                rate = (i+1)/dt
                eta = (total_frames-i-1)/rate
                print(f'  {i+1}/{total_frames} ({(i+1)*100//total_frames}%, ETA:{eta:.0f}s)')

        dt = time.time()-t0
        print(f'  Done: {total_frames} frames in {dt:.0f}s ({total_frames/dt:.1f} fps)')
        browser.close()
    server.shutdown()
    return total_frames

def render_chapter(ch_num, scenes, audio_mp3):
    work = f'{BASE}/chapter{ch_num}'
    html_path = f'{work}/html/chapter{ch_num}.html'
    frames_dir = f'{work}/frames'
    video_path = f'{work}/video/chapter{ch_num}.mp4'
    os.makedirs(f'{work}/frames', exist_ok=True)
    os.makedirs(f'{work}/video', exist_ok=True)

    probe = subprocess.run(['ffprobe','-v','quiet','-show_entries','format=duration',
        '-of','csv=p=0',audio_mp3], capture_output=True, text=True, timeout=15)
    total_dur = float(probe.stdout.strip())

    with open(html_path,'w',encoding='utf-8') as f:
        f.write(build_html(ch_num, scenes))
    print(f'  HTML: {html_path}')

    os.makedirs(f'{work}/subtitles', exist_ok=True)
    srt_path = f'{work}/subtitles/chapter{ch_num}.srt'
    with open(srt_path,'w',encoding='utf-8') as f:
        f.write(gen_srt(scenes, total_dur))
    print(f'  SRT: {srt_path} ({total_dur:.0f}s)')

    nframes = capture_at_fps(html_path, frames_dir, scenes, fps=8)
    print(f'  Captured {nframes} frames')

    # Audio mix (BGM if available, else raw narration)
    bgm = '/home/ubuntu/hf-demo/chapter1-video/assets/bgm.mp3'
    mixed = f'/tmp/c{ch_num}_mixed.mp3'
    if os.path.exists(bgm):
        r = subprocess.run(['ffmpeg','-y','-i',audio_mp3,'-i',bgm,
            '-filter_complex','[0:a]volume=1.2[nar];[1:a]volume=0.2[bg];[nar][bg]amix=inputs=2:duration=first',
            '-t',str(total_dur),'-q:a','2',mixed], capture_output=True)
        if r.returncode == 0:
            print('  Mixed audio (narration + BGM)')
        else:
            print('  Audio mix failed, using raw narration')
            mixed = audio_mp3
    else:
        mixed = audio_mp3

    # Raw video from frames
    raw = f'/tmp/c{ch_num}_raw.mp4'
    r = subprocess.run(['ffmpeg','-y',
        '-framerate','8',
        '-i',f'{frames_dir}/frame_%05d.png',
        '-c:v','libx264','-preset','fast','-crf','20',
        '-pix_fmt','yuv420p',
        '-vf','scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-t',str(total_dur),'-an',raw], capture_output=True)
    if r.returncode != 0:
        print('  FFmpeg raw error:', r.stderr[-300:] if r.stderr else '')
    print('  Raw video compiled')

    # Burn subtitles + mux audio
    r = subprocess.run(['ffmpeg','-y',
        '-i',raw,'-i',mixed,
        '-c:v','libx264','-preset','fast','-crf','20',
        '-c:a','aac','-b:a','192k',
        '-vf',f"subtitles='{srt_path}':force_style='FontName=Noto Sans CJK SC,FontSize=28,PrimaryColour=&H00FFFFFF,Outline=2,OutlineColour=&H00000000,Bold=1'",
        '-t',str(total_dur),video_path], capture_output=True)
    if r.returncode != 0:
        print('  Subtitle error, muxing without:', r.stderr[-200:] if r.stderr else '')
        subprocess.run(['ffmpeg','-y','-i',raw,'-i',mixed,
            '-c:v','libx264','-preset','fast','-crf','20',
            '-c:a','aac','-b:a','192k',
            '-t',str(total_dur),video_path], capture_output=True)

    if os.path.exists(video_path):
        sz = os.path.getsize(video_path)//(1024*1024)
        print(f'  ✓ {video_path} ({sz}MB)')
    else:
        print(f'  ✗ Failed')

    subprocess.run(['rm','-rf',frames_dir], capture_output=True)
    for f in [raw, mixed]:
        subprocess.run(['rm','-f',f], capture_output=True)
    return video_path if os.path.exists(video_path) else None

if __name__ == '__main__':
    ch = int(sys.argv[1]) if len(sys.argv)>1 else 1
    with open(f'{BASE}/chapter{ch}/scenes.json', encoding='utf-8') as f:
        data = json.load(f)
    print(f'Rendering Ch{ch}: {data["title"]}')
    result = render_chapter(ch, data['scenes'], f'{BASE}/chapter{ch}/audio/narration.mp3')
    print('Result:', result)
