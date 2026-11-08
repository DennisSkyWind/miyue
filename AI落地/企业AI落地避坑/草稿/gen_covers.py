#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成两本书的封面图（HTML/CSS 绘制，零外部图片）。
A5 = 148 x 210 mm @96dpi = 559 x 794 px，输出 3x = 1677 x 2382 PNG

★ v2 修订（2026-11-08，据多模态视觉质检）：
  1. 删掉数据治理封面上的内部备注「【书名与定价待老周拍板】」（工作备注不得上封面）
  2. 布局改为「内容块垂直居中 + 底部固定条」，消除下半页掏空 70mm 的失衡
  3. 方案 B 副标题去掉伪破折号、补句末问号、两行左边界对齐
  4. 方案 C 去掉行内粗细交替，改用「——」引出结论行
  5. 数据治理封面消除「数据治理」一词三次重复
视觉禁则：禁 AI 芯片/机器人/大脑图标；禁感叹号、闪电、火箭、"颠覆/必看/收藏"；
         留白充足；衬线(正文感) + 无衬线(标题)
"""
import os, subprocess, sys

OUT = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(OUT, "_cover_tmp")
os.makedirs(TMP, exist_ok=True)

W, H, SCALE = 559, 794, 3

BASE = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden}
.cover{width:%(W)dpx;height:%(H)dpx;position:relative;overflow:hidden;
  font-family:"Noto Serif CJK SC","Source Han Serif SC",serif;}
.main{position:absolute;left:0;right:0;top:0;bottom:132px;
  padding:0 56px;display:flex;flex-direction:column;justify-content:center}
.foot{position:absolute;left:0;right:0;bottom:0;height:132px;
  padding:0 56px;display:flex;align-items:center;justify-content:space-between}
.sans{font-family:"Noto Sans CJK SC","Source Han Sans SC",sans-serif}
.title{font-family:"Noto Sans CJK SC","Source Han Sans SC",sans-serif;
  font-weight:700;letter-spacing:.05em;line-height:1.26}
.sub{font-family:"Noto Serif CJK SC",serif;line-height:1.78}
.author{font-family:"Noto Serif CJK SC",serif;letter-spacing:.24em}
.eyebrow{font-family:"Noto Sans CJK SC",sans-serif;letter-spacing:.40em}
.rule{width:112px;height:2px}
""" % {'W': W, 'H': H}


def build(name, css, body):
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE}</style><style>{css}</style></head>
<body><div class="cover">{body}</div></body></html>"""
    p = os.path.join(TMP, name + ".html")
    open(p, "w", encoding="utf-8").write(html)
    png = os.path.join(OUT, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    subprocess.run([
        "chromium-browser", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", "--hide-scrollbars",
        f"--force-device-scale-factor={SCALE}",
        f"--window-size={W},{H}", f"--screenshot={png}",
        "--virtual-time-budget=8000", "file://" + p],
        capture_output=True, text=True, timeout=120)
    ok = os.path.exists(png) and os.path.getsize(png) > 5000
    print(f"{'✅' if ok else '❌'} {name}.png  {os.path.getsize(png)//1024 if ok else 0}KB")
    return ok


# ══════════《AI 未成之路》 方案 A：极简书名型（暖白底 · 深墨字） ══════════
CSS_A = """
.cover{background:#f7f5f0;color:#1f1d1a}
.eyebrow{font-size:15px;color:#8a8378;margin-bottom:50px}
.title{font-size:58px;margin-bottom:30px}
.sub{font-size:21px;color:#4a453d;margin-bottom:46px}
.rule{background:#1f1d1a;margin-bottom:32px}
.author{font-size:20px}
.foot .cat{font-size:13px;color:#a8a196;letter-spacing:.30em}
"""
BODY_A = """
<div class="main">
  <div class="eyebrow">企业 AI 落地复盘</div>
  <div class="title">AI<br>未成之路</div>
  <div class="sub">为什么大多数企业的 AI 都没做成，<br>以及怎么认出自己正在哪个坑里</div>
  <div class="rule"></div>
  <div class="author">米悦说说</div>
</div>
<div class="foot"><span class="cat">复盘笔记</span><span class="cat">米悦说说</span></div>
"""

# ══════════《AI 未成之路》 方案 B：反差型（真破折号 + 问句收尾） ══════════
CSS_B = """
.cover{background:#f7f5f0;color:#1f1d1a}
.eyebrow{font-size:15px;color:#8a8378;margin-bottom:50px}
.title{font-size:58px;margin-bottom:40px}
.sub{font-size:23px;color:#2c2823;line-height:1.95;margin-bottom:46px}
.sub .dash{color:#8a8378;margin-right:6px}
.rule{background:#1f1d1a;margin-bottom:32px}
.author{font-size:20px}
.foot .cat{font-size:13px;color:#a8a196;letter-spacing:.30em}
"""
BODY_B = """
<div class="main">
  <div class="eyebrow">企业 AI 落地复盘</div>
  <div class="title">AI<br>未成之路</div>
  <div class="sub"><span class="dash">——</span>都做成的那几个，<br>怎么没成的？</div>
  <div class="rule"></div>
  <div class="author">米悦说说</div>
</div>
<div class="foot"><span class="cat">复盘笔记</span><span class="cat">米悦说说</span></div>
"""

# ══════════《AI 未成之路》 方案 C：数字型（无行内粗细交替） ══════════
CSS_C = """
.cover{background:#f7f5f0;color:#1f1d1a}
.eyebrow{font-size:15px;color:#8a8378;margin-bottom:50px}
.title{font-size:58px;margin-bottom:38px}
.nums{font-family:"Noto Serif CJK SC",serif;font-size:22px;line-height:2.0;
  color:#2c2823;margin-bottom:46px}
.nums .concl{color:#8a8378;font-size:20px}
.rule{background:#1f1d1a;margin-bottom:32px}
.author{font-size:20px}
.foot .cat{font-size:13px;color:#a8a196;letter-spacing:.30em}
"""
BODY_C = """
<div class="main">
  <div class="eyebrow">企业 AI 落地复盘</div>
  <div class="title">AI<br>未成之路</div>
  <div class="nums">数百人参与 · 数十支队伍<br>一百五十余项需求<br>
    <span class="concl">—— 最终落地：数个场景</span></div>
  <div class="rule"></div>
  <div class="author">米悦说说</div>
</div>
<div class="foot"><span class="cat">复盘笔记</span><span class="cat">米悦说说</span></div>
"""

# ══════════《数据治理实战》 方案 A：定位直给型（深墨绿底 · 米白字） ══════════
CSS_D = """
.cover{background:#1e3a33;color:#f2efe6}
.eyebrow{font-size:15px;color:#8faaa2;margin-bottom:48px}
.title{font-size:52px;margin-bottom:24px}
.sub{font-size:23px;color:#cfc9bb;line-height:1.6;margin-bottom:40px}
.feat{font-family:"Noto Serif CJK SC",serif;font-size:19px;line-height:1.95;
  color:#e6e0d2;margin-bottom:46px}
.rule{background:#cfc9bb;margin-bottom:30px}
.author{font-size:20px;color:#f2efe6}
.foot .cat{font-size:13px;color:#7e978f;letter-spacing:.30em}
"""
BODY_D = """
<div class="main">
  <div class="eyebrow">企业数据治理方法</div>
  <div class="title">数据治理实战</div>
  <div class="sub">从二级分类到落地执行</div>
  <div class="feat">主数据二级分类 · 源端治理四步法</div>
  <div class="rule"></div>
  <div class="author">米悦说说</div>
</div>
<div class="foot"><span class="cat">管理实践</span><span class="cat">操作手册</span></div>
"""

JOBS = [
    ("封面_AI未成之路_方案A_极简书名型", CSS_A, BODY_A),
    ("封面_AI未成之路_方案B_反差型", CSS_B, BODY_B),
    ("封面_AI未成之路_方案C_数字型", CSS_C, BODY_C),
    ("封面_数据治理实战_方案A_定位直给型", CSS_D, BODY_D),
]

if __name__ == "__main__":
    bad = [n for n, c, b in JOBS if not build(n, c, b)]
    print("\n全部完成 ✓" if not bad else f"\n失败: {bad}")
    sys.exit(1 if bad else 0)
