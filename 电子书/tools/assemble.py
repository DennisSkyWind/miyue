#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装自包含出版级 HTML（CSS 内嵌、零外部依赖、零图片引用）"""
import json, re, html

OUT = '/home/ubuntu/miyue/电子书/数据治理实战_出版版.html'
BOOK_TITLE = '数据治理实战：从二级分类到落地执行'
AUTHOR = '米悦说说'
SUBTITLE = '主数据二级分类 · 源端治理四步法 · 从规划到落地的完整路径'

CSS = r"""
:root{
  --ink:#1c1a17; --ink-soft:#4a453d; --ink-mute:#8a8177;
  --paper:#fffdf8; --paper-2:#f8f4ec; --rule:#d9d1c0; --rule-soft:#ebe4d6;
  --accent:#8c3a2e; --accent-soft:#f5e7e1; --gold:#a8791c; --gold-soft:#fdf6e6;
  --serif:"Source Han Serif SC","Noto Serif CJK SC","Songti SC","SimSun",serif;
  --sans:"Source Han Sans SC","Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;
  --gutter:0;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:#e7e1d4; color:var(--ink);
  font-family:var(--serif); font-size:17px; line-height:1.95;
  text-align:justify; text-justify:inter-ideograph;
}
.book{
  max-width:820px; margin:0 auto; background:var(--paper);
  padding:64px 72px 96px; box-shadow:0 1px 3px rgba(0,0,0,.08),0 12px 40px rgba(0,0,0,.10);
  min-height:100vh;
}
/* ---------- 封面 ---------- */
.cover{min-height:76vh;display:flex;flex-direction:column;justify-content:center;text-align:center;
  border-bottom:1px solid var(--rule);margin-bottom:10px;page-break-after:always;break-after:page}
.cover .tag{font-family:var(--sans);font-size:12px;letter-spacing:.34em;color:var(--accent);margin-bottom:40px}
.cover h1{font-size:39px;line-height:1.5;margin:0 0 22px;font-weight:700;letter-spacing:.04em;
  border:0;padding:0;max-width:16em;margin-left:auto;margin-right:auto}
.cover h1 .l2{display:block;margin-top:.18em;font-size:.82em;color:var(--ink-soft);letter-spacing:.06em}
.cover .orn{margin:38px auto 32px;width:72px;height:1px;background:var(--accent);position:relative}
.cover .orn::after{content:"";position:absolute;left:50%;top:-3px;width:7px;height:7px;margin-left:-3.5px;
  background:var(--accent);transform:rotate(45deg)}
.cover .sub{font-size:14.5px;color:var(--ink-soft);line-height:2.1;margin:0 auto 42px;max-width:34em;white-space:nowrap;
  font-family:var(--sans);letter-spacing:.02em}
.cover .author{font-family:var(--sans);font-size:16px;letter-spacing:.3em;color:var(--ink);
  padding-top:26px;border-top:1px solid var(--rule-soft);display:inline-block}
.cover .pub{margin-top:12px;font-family:var(--sans);font-size:12.5px;color:var(--ink-mute);letter-spacing:.1em}
/* ---------- 版权页 ---------- */
.copyright{page-break-after:always;break-after:page;break-inside:avoid;background:var(--paper-2);
  border:1px solid var(--rule-soft);border-radius:3px;padding:32px 36px;margin:40px 0 52px;
  font-family:var(--sans);font-size:14px;line-height:2;color:var(--ink-soft)}
.copyright h2{font-size:15px;margin:0 0 16px;color:var(--accent);letter-spacing:.14em;font-weight:700;
  border:0;padding:0;page-break-before:auto}
.copyright p{margin:0 0 10px;text-align:left;text-indent:0}
.copyright .row{display:flex;justify-content:space-between;align-items:baseline;gap:18px;
  border-bottom:1px dotted var(--rule);padding:6px 0}
.copyright .row span:first-child{color:var(--ink-mute);white-space:nowrap}
.copyright .row span:last-child{color:var(--ink);text-align:left}
/* ---------- 目录 ---------- */
.toc{page-break-after:always;break-after:page;margin:0 0 34px}
.toc h2{font-size:26px;margin:0 0 30px;text-align:center;letter-spacing:.3em;border:0;padding:0;
  page-break-before:auto}
.toc ol{list-style:none;margin:0;padding:0}
.toc li{margin:0;padding:0}
.toc .t2{display:flex;align-items:baseline;gap:.7em;font-weight:700;font-size:16.5px;
  margin:26px 0 9px;padding:0 0 7px 14px;border-left:3px solid var(--accent);
  border-bottom:1px solid var(--rule-soft)}
.toc .t2:first-of-type{margin-top:0}
.toc .t2 .n{color:var(--accent);font-family:var(--sans);font-size:11.5px;letter-spacing:.14em;flex:none;
  border:1px solid var(--accent);border-radius:2px;padding:1px 7px;vertical-align:middle;
  align-self:center;line-height:1.5}
.toc .t3{display:block;font-size:14px;color:var(--ink-soft);padding:4.5px 0 4.5px 40px;font-weight:400}
.toc .t4{display:block;font-size:12.8px;color:var(--ink-mute);padding:2.5px 0 2.5px 62px;font-weight:400}
.toc .t4 a{color:inherit}
.toc a{color:inherit;text-decoration:none}
.toc a:hover{color:var(--accent)}
/* ---------- 正文标题 ---------- */
h1,h2,h3,h4,h5{font-family:var(--sans);font-weight:700;text-align:left;line-height:1.55}
h2{font-size:26px;margin:64px 0 24px;padding:0 0 13px;border-bottom:2px solid var(--accent);
  letter-spacing:.03em;page-break-before:always;break-before:page;page-break-after:avoid;break-after:avoid}
h3{font-size:19.5px;margin:42px 0 15px;color:var(--ink);padding-left:14px;border-left:4px solid var(--accent);
  page-break-after:avoid;break-after:avoid}
h4{font-size:17px;margin:30px 0 11px;color:var(--ink-soft);page-break-after:avoid}
h5{font-size:15.5px;margin:22px 0 9px;color:var(--ink-soft)}
p{margin:0 0 1.05em;text-indent:2em}
strong{color:#8a2c20;font-weight:700}
em{font-style:normal;color:var(--accent);border-bottom:1px solid var(--accent-soft);padding-bottom:1px}
code{font-family:"SF Mono",Consolas,Monaco,monospace;font-size:.88em;background:var(--paper-2);
  padding:1px 5px;border-radius:3px;color:#6b3a1e;border:1px solid var(--rule-soft)}
hr.rule{border:0;height:1px;background:var(--rule-soft);margin:44px 0;width:100%;page-break-after:avoid}
/* ---------- 引用 / 金句 ---------- */
blockquote.quote{margin:24px 0;padding:14px 22px;border-left:3px solid var(--rule);
  background:var(--paper-2);color:var(--ink-soft);font-size:16px;border-radius:0 3px 3px 0}
blockquote.quote p{margin:0 0 .5em;text-indent:0;text-align:left}
blockquote.quote p:last-child{margin:0}
blockquote.gold{border:1px solid #e3d3ab;border-left:4px solid var(--gold);border-radius:0 4px 4px 0;
  box-shadow:inset 4px 0 0 var(--gold);border-left:0;
  background:linear-gradient(100deg,var(--gold-soft) 0%,#fffdf8 55%);color:#6b4e12;
  font-family:var(--sans);font-size:16.5px;padding:20px 26px;margin:30px 0;text-wrap:pretty}
blockquote.gold p{margin:0 0 .7em;text-indent:0;font-weight:600;line-height:1.9;text-align:left}
blockquote.gold p:last-child{margin:0}
blockquote.gold p+p{border-top:1px dotted #e3d3ab;padding-top:.7em}
/* ---------- 树（图示） ---------- */
.tree{margin:24px 0 26px;padding:20px 24px;background:var(--paper-2);
  border:1px solid var(--rule-soft);border-radius:4px;page-break-inside:auto;break-inside:auto;
  font-family:var(--sans)}
.tree ul.tree-list{list-style:none;margin:0;padding-left:1.55em;position:relative}
.tree ul.tree-list.tree-root{padding-left:.15em}
.tree ul.tree-list ul.tree-list{border-left:1px solid var(--rule);margin-left:.62em;padding-left:1.35em}
.tree li{position:relative;margin:0;padding:3.5px 0 3.5px 1.25em;page-break-inside:avoid;break-inside:avoid}
.tree li::before{content:"▸";position:absolute;left:.05em;top:3.5px;color:var(--ink-mute);
  font-size:11.5px;line-height:1.85}
.tree ul.tree-list.tree-root > li::before{color:var(--accent);font-size:12.5px}
.tree .tl{font-size:15.5px;line-height:1.8;color:var(--ink)}
.tree ul.tree-list.tree-root > li > .tl{font-weight:700;font-size:16px;color:var(--ink)}
.tree ul.tree-list.tree-root > li{padding-top:2px;padding-bottom:5px}
.tree ul.tree-list ul.tree-list > li:last-child{padding-bottom:0}

/* ---------- 流程示意（HTML 绘制） ---------- */
.flow{margin:26px 0;padding:18px 24px;background:var(--paper-2);border:1px solid var(--rule-soft);
  border-radius:4px;font-family:var(--sans);page-break-inside:auto;break-inside:auto}
.flow .flow-row{page-break-inside:avoid;break-inside:avoid}
.flow-row{display:flex;align-items:center;gap:10px;padding:7px 0;flex-wrap:wrap}
.flow-row + .flow-row{border-top:1px dashed var(--rule)}
.ftext{font-size:15px;line-height:1.8;color:var(--ink)}
.ftext-lead{font-weight:700;color:var(--ink)}
.fsep{color:var(--accent);font-size:13px;flex:none;letter-spacing:.06em}
.fsep::before{content:"\2192"}
/* 双向箭头：两端真正的三角箭头 */
.farrow{flex:1;min-width:40px;height:0;border-top:2px solid var(--accent);position:relative}
.farrow::before,.farrow::after{content:"";position:absolute;top:-5px;width:0;height:0;
  border-top:5px solid transparent;border-bottom:5px solid transparent}
.farrow::before{left:-1px;border-right:9px solid var(--accent)}
.farrow::after{right:-1px;border-left:9px solid var(--accent)}
/* 纵向连接器 */
.fconn{display:flex;flex-direction:column;align-items:flex-start;padding:3px 0 3px 4px}
.fconn-line{width:0;border-left:2px solid var(--rule);height:16px}
.fconn-tip{width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;
  border-top:9px solid var(--accent)}
.fconn-up{flex-direction:column-reverse}
.fconn-up .fconn-tip{border-top:none;border-bottom:9px solid var(--accent)}

/* ---------- 优先级象限图 ---------- */
.matrix{display:grid;grid-template-columns:auto 1fr 1fr;grid-template-rows:auto auto auto;
  gap:0;margin:26px 0;padding:16px 18px;background:var(--paper-2);border:1px solid var(--rule-soft);
  border-radius:4px;font-family:var(--sans);page-break-inside:avoid;break-inside:avoid}
.mx-corner{}
.mx-ax-h{text-align:center;font-size:12.5px;color:var(--ink-mute);padding:0 0 8px;letter-spacing:.04em;
  border-bottom:1px solid var(--rule)}
.mx-ax-v{display:flex;align-items:center;justify-content:flex-end;text-align:right;font-size:12.5px;
  color:var(--ink-mute);padding:0 12px 0 0;white-space:nowrap;letter-spacing:.04em}
.mx-cell{border:1px solid var(--rule-soft);border-left:0;border-top:0;padding:14px 14px;min-height:62px;
  display:flex;flex-direction:column;justify-content:center;gap:4px;background:#fdfcf8}
.mx-cell:nth-last-child(2),.mx-cell:last-child{border-bottom:0}
.mx-star{background:#f7ece7;border-color:#e3c9c0}
.mx-hard{background:#fbf6ec}
.mx-late{background:#f4f2ec}
.mx-empty{background:transparent}
.mx-tag{font-size:15px;font-weight:700;color:var(--ink)}
.mx-star .mx-tag{color:var(--accent)}
.mx-late .mx-tag{color:var(--ink-mute)}
.mx-note{font-size:12.5px;color:var(--ink-soft);line-height:1.6}
/* ---------- 表格 ---------- */
.table-wrap{margin:26px 0;overflow-x:auto;page-break-inside:avoid;break-inside:avoid}
table{width:100%;border-collapse:collapse;font-family:var(--sans);font-size:14px;line-height:1.72}
th{background:var(--ink);color:var(--paper);font-weight:600;padding:11px 14px;text-align:left;
  border:1px solid var(--ink);border-bottom:3px solid var(--accent);letter-spacing:.04em;white-space:nowrap}
td{padding:10px 14px;border:1px solid var(--rule);vertical-align:middle;text-align:left;color:var(--ink)}
th:first-child,td:first-child{width:1%;white-space:nowrap}
tbody tr:nth-child(even) td{background:#faf7f0}
tbody td:first-child{font-weight:600;color:#5a3b33;background:#f6f1e8}
tbody tr:nth-child(even) td:first-child{background:#efe8da}
td strong{color:#8a2c20}
/* ---------- 框（图示） ---------- */
.frame{margin:26px 0;padding:18px 24px;background:#fbf9f4;border:1px solid var(--rule);
  border-radius:0 4px 4px 0;box-shadow:inset 4px 0 0 var(--accent);
  page-break-inside:avoid;break-inside:avoid}
.frame-row{font-family:var(--sans);font-size:15px;line-height:1.92;color:var(--ink);padding:2px 0}
.frame-row:first-child{font-weight:700;color:var(--accent);margin-bottom:4px;padding-bottom:8px;
  border-bottom:1px dashed var(--rule)}
.frame-row:last-child{margin-top:4px}
/* ---------- 列表 ---------- */
ul.lst,ol.lst{margin:16px 0 20px;padding-left:1.95em}
ol.lst{counter-reset:li}
ol.lst>li{margin:.34em 0}
ul.lst>li{margin:.3em 0}
ul.lst>li::marker{color:var(--accent);font-size:.9em}
ol.lst>li::marker{color:var(--accent);font-family:var(--sans);font-size:.88em;font-weight:600}
.lst li .sub{display:block;color:var(--ink-soft);font-size:.94em;margin-top:2px;padding-left:.2em}
/* ---------- 打印 ---------- */
@page{size:A5;margin:16mm 14mm 15mm}
@media print{
  body{background:#fff;font-size:11pt;line-height:1.72}
  .book{max-width:none;box-shadow:none;padding:0;margin:0}
  .cover{min-height:auto;padding:34mm 0 0}
  .cover h1{font-size:25pt}
  .cover .sub{font-size:9.5pt}
  h2{font-size:17pt;margin:12mm 0 6mm}
  h3{font-size:13.5pt;margin:8mm 0 4mm}
  h4{font-size:12pt}
  p{margin-bottom:.85em}
  .tree,.frame,.table-wrap,blockquote,.copyright{page-break-inside:avoid;break-inside:avoid}
  .tree{padding:12px 14px;margin:16px 0 18px}
  .tree li{padding:1.5px 0 1.5px 1.1em}
  .tree .tl{font-size:10.2pt;line-height:1.55}
  .tree ul.tree-list.tree-root > li > .tl{font-size:10.6pt}
  .frame{padding:11px 14px;margin:16px 0 18px}
  .frame-row{font-size:10.2pt;line-height:1.55;padding:1px 0}
  .flow{padding:11px 14px;margin:16px 0 18px}
  .flow .flow-row{padding:3px 0}
  .ftext{font-size:10.2pt;line-height:1.55}
  table{font-size:9.6pt;line-height:1.5}
  th{padding:6px 8px}td{padding:5px 8px}
  blockquote.quote,blockquote.gold{font-size:10.4pt;padding:10px 14px;margin:16px 0}
  h2{margin:10mm 0 5mm;padding-bottom:9px}
  .toc .t2{font-size:11.5pt}
  .toc .t3{font-size:10.5pt}
  a{color:inherit;text-decoration:none}
}
@media (max-width:700px){ .book{padding:34px 22px 64px} body{font-size:16px} .cover h1{font-size:27px} }
"""

JS = r"""
(function(){
  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
  var heads=[].slice.call(document.querySelectorAll('main h2[id],main h3[id]'));
  function upd(){
    var y=window.scrollY+140,cur=null;
    heads.forEach(function(h){if(h.offsetTop<=y)cur=h.id});
    links.forEach(function(a){a.style.color='';a.style.fontWeight=''});
    if(cur&&map[cur]){map[cur].style.color='#8c3a2e';}
  }
  window.addEventListener('scroll',upd,{passive:true});upd();
})();
"""

def esc(s):
    return html.escape(s, quote=False)

def build():
    body = open('/tmp/body.html', encoding='utf-8').read()
    toc = json.load(open('/tmp/toc.json', encoding='utf-8'))['toc']
    # 去掉正文里的 <!--BOOKTITLE--> 注释
    body = re.sub(r'<!--BOOKTITLE:.*?-->', '', body, flags=re.S)
    # 目录：h2 章 + h3 节
    o = ['<nav class="toc"><h2>目 录</h2>']
    chap = 0
    for level, text, sid in toc:
        if level == 2:
            chap += 1
            m = re.match(r'^第([一二三四五六七八九十百]+)章', text.strip())
            badge = '<span class="n">第%s章</span>' % m.group(1) if m else ''
            o.append('<div class="t2">%s<a href="#%s">%s</a></div>' % (badge, sid, esc(text)))
        elif level == 3:
            o.append('<div class="t3"><a href="#%s">%s</a></div>' % (sid, esc(text)))
        elif level == 4:
            o.append('<div class="t4"><a href="#%s">%s</a></div>' % (sid, esc(text)))
    o.append('</nav>')
    toc_html = '\n'.join(o)
    doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="author" content="%s">
<meta name="description" content="%s">
<title>%s</title>
<style>%s</style>
</head>
<body>
<div class="book">
  <section class="cover">
    <div class="tag">数据治理实战</div>
    <h1>数据治理实战：<span class="l2">从二级分类到落地执行</span></h1>
    <div class="orn"></div>
    <p class="sub">%s</p>
    <div class="author">%s</div>
    <div class="pub">副业电子书 · 永久更新</div>
  </section>
  <section class="copyright">
    <h2>出版说明</h2>
    <div class="row"><span>书名</span><span>%s</span></div>
    <div class="row"><span>作者</span><span>%s</span></div>
    <div class="row"><span>版本</span><span>出版版 v1.0</span></div>
    <div class="row"><span>体裁</span><span>管理实践 · 企业数据治理</span></div>
    <p style="margin-top:16px">本书案例均已做脱敏处理，涉及真实企业名称、内部数据金额、组织代称等一律泛化表述，
    仅保留可迁移的方法论与判断依据，供企业数据治理从业者参考。</p>
    <p>文中所有图示、表格均由文字结构化绘制，不依赖外部图片，便于在多种阅读器与电子书中保持一致的排版效果。</p>
  </section>
  %s
  <main>
  %s
  </main>
</div>
<script>%s</script>
</body>
</html>""" % (esc(AUTHOR), esc(SUBTITLE), esc(BOOK_TITLE), CSS, esc(SUBTITLE),
                 esc(AUTHOR), esc(BOOK_TITLE), esc(AUTHOR), toc_html, body, JS)
    open(OUT, 'w', encoding='utf-8').write(doc)
    return len(doc)

if __name__ == '__main__':
    n = build()
    print('生成:', OUT, '| 字节:', n, '| 行数:', open(OUT,encoding='utf-8').read().count('\n'))
