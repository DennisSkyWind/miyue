#!/usr/bin/env python3
"""从断点继续截帧（基于已有frame_*.png文件）"""
import subprocess, json, os, time, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright

BASE = "/home/ubuntu/miyue/电子书/video_chapters"
ch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 5
work = f'{BASE}/chapter{ch_num}'
frames_dir = f'{work}/frames'
html_path = f'{work}/html/chapter{ch_num}.html'

with open(f'{work}/scenes.json', encoding='utf-8') as f:
    data = json.load(f)
scenes = data['scenes']

total_dur = sum(s.get('duration',5) for s in scenes)
fps = 8
total_frames = int(total_dur * fps)

existing = set()
for f in os.listdir(frames_dir):
    if f.startswith('frame_'):
        try:
            existing.add(int(f.split('_')[1].split('.')[0]))
        except:
            pass
start_frame = max(existing) + 1 if existing else 0
print(f'Resuming from frame {start_frame} (total needed: {total_frames})')

if start_frame >= total_frames:
    print('All frames already captured.')
    sys.exit(0)

# Build HTML
def build_html(ch_num, scenes):
    FONTS = """@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');"""
    CSS = """*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0a0e1a;font-family:'Noto Sans CJK SC','PingFang SC','Microsoft YaHei',sans-serif;}
#bg-grid{position:fixed;inset:0;opacity:0.05;pointer-events:none;background-image:linear-gradient(rgba(59,130,246,.5) 1px,transparent 1px),linear-gradient(90deg, rgba(59,130,246,.5) 1px,transparent 1px);background-size:60px 60px;}
.accent{position:fixed;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#1e3a6e,#3b82f6,#1e3a6e);z-index:10;}
.badge{position:fixed;bottom:40px;right:60px;font-size:22px;color:rgba(255,255,255,.2);letter-spacing:.2em;z-index:10;}
.scene{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;opacity:0;pointer-events:none;}
.scene.active{opacity:1;pointer-events:auto;}
.title-bg{background:linear-gradient(135deg,#0a1628,#1a3a5c,#0a1628);}
.title-main{font-size:78px;font-weight:900;color:#fff;letter-spacing:.08em;text-align:center;text-shadow:0 0 80px rgba(59,130,246,.4);}
.title-sub{font-size:26px;color:#93c5fd;margin-top:20px;letter-spacing:.3em;}
.title-ch{font-size:20px;color:#60a5fa;margin-top:40px;letter-spacing:.5em;}
.content-bg{background:linear-gradient(180deg,#0f172a,#1e293b);}
.content-inner{max-width:1400px;width:100%;padding:0 80px;}
.content-title{font-size:50px;font-weight:700;color:#fff;margin-bottom:48px;letter-spacing:.05em;position:relative;padding-left:24px;}
.content-title::before{content:'';position:absolute;left:0;top:10%;height:80%;width:6px;background:linear-gradient(180deg,#3b82f6,#60a5fa);border-radius:3px;}
.points-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(580px,1fr));gap:18px;}
.point-card{background:rgba(255,255,255,.04);border:1px solid rgba(59,130,246,.2);border-radius:14px;padding:22px 30px;font-size:28px;color:#e2e8f0;line-height:1.6;display:flex;align-items:flex-start;gap:14px;}
.point-card::before{content:'▶';color:#3b82f6;font-size:18px;margin-top:4px;flex-shrink:0;}
.closing-bg{background:linear-gradient(135deg,#0a1628,#1a2a4a);}
.closing-text{font-size:54px;font-weight:700;color:#fff;text-align:center;letter-spacing:.1em;text-shadow:0 0 40px rgba(59,130,246,.3);}
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
    return f"""<!doctype html><html lang="zh"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920,height=1080"/><title>数据治理实战·第{ch_num}章</title><script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script><style>{FONTS}{CSS}</style></head><body><div id="bg-grid"></div><div class="accent"></div><div class="badge">第{ch_num}/10章</div>{''.join(blocks)}</body></html>"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(build_html(ch_num, scenes))

html_dir = os.path.dirname(os.path.abspath(html_path))
os.chdir(html_dir)

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=html_dir, **kwargs)
    def log_message(self, format, *args):
        pass

server = HTTPServer(('127.0.0.1', 0), QuietHandler)
t_server = Thread(target=server.serve_forever, daemon=True)
t_server.start()
port = server.server_address[1]
print(f'Server on port {port}')

DUR = [s.get('duration',5) for s in scenes]
scene_starts = []
t = 0
for d in DUR:
    scene_starts.append(t)
    t += d
scenes_js = json.dumps(scenes, ensure_ascii=False)

with sync_playwright() as p:
    browser = p.chromium.launch(args=[
        '--no-sandbox','--disable-setuid-sandbox',
        '--use-gl=angle','--enable-webgl','--disable-gpu-sandbox',
        '--disable-dev-shm-usage',
        '--disable-software-rasterizer'])
    ctx = browser.new_context(viewport={'width':1920,'height':1080}, device_scale_factor=1)
    page = ctx.new_page()
    page.goto(f'http://127.0.0.1:{port}/' + os.path.basename(html_path), wait_until='load')
    page.wait_for_timeout(800)
    print(f'Page loaded, resuming from frame {start_frame}...')

    last_si = -1
    t0 = time.time()
    for i in range(start_frame, total_frames):
        elapsed = i / fps
        si = 0
        for si in range(len(DUR)):
            if elapsed < scene_starts[si] + DUR[si]:
                break
        else:
            si = len(DUR) - 1

        if si != last_si:
            scene_time = max(0, elapsed - scene_starts[si])
            try:
                page.evaluate(f'''
                    (function(){{
                        var scenes={scenes_js};
                        var si={si};
                        var sceneT={scene_time};
                        document.querySelectorAll('.scene').forEach(function(s, idx){{s.classList.toggle('active', idx===si);}});
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
                print(f'  [WARN] evaluate error at frame {i}: {e}')
            last_si = si

        page.screenshot(path=f'{frames_dir}/frame_{i:05d}.png', type='png')

        if (i - start_frame + 1) % 20 == 0:
            dt = time.time()-t0
            done = i - start_frame + 1
            remain = total_frames - i - 1
            rate = done/dt if dt > 0 else 0
            eta = remain/rate if rate > 0 else 0
            print(f'  {done}/{total_frames-start_frame} ({(done)*100//(total_frames-start_frame)}%, ETA:{eta:.0f}s)')

    dt = time.time()-t0
    print(f'  Done: {total_frames - start_frame} frames in {dt:.0f}s ({(total_frames-start_frame)/dt:.1f} fps)')
    browser.close()

server.shutdown()
print('Server stopped')
