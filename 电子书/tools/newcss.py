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
.cover .sub{font-size:14.5px;color:var(--ink-soft);line-height:2.1;margin:0 auto 42px;max-width:24em;
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
  border:1px solid var(--accent);border-radius:2px;padding:1px 7px}
.toc .t3{display:block;font-size:14px;color:var(--ink-soft);padding:4.5px 0 4.5px 40px;font-weight:400}
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
hr.rule{border:0;height:1px;background:var(--rule);margin:42px auto;width:44%;page-break-after:avoid}
/* ---------- 引用 / 金句 ---------- */
blockquote.quote{margin:24px 0;padding:14px 22px;border-left:3px solid var(--rule);
  background:var(--paper-2);color:var(--ink-soft);font-size:16px;border-radius:0 3px 3px 0}
blockquote.quote p{margin:0 0 .5em;text-indent:0;text-align:left}
blockquote.quote p:last-child{margin:0}
blockquote.gold{border:1px solid #e3d3ab;border-left:4px solid var(--gold);border-radius:0 4px 4px 0;
  background:linear-gradient(100deg,var(--gold-soft) 0%,#fffdf8 55%);color:#6b4e12;
  font-family:var(--sans);font-size:16.5px;padding:20px 26px;margin:30px 0}
blockquote.gold p{margin:0 0 .7em;text-indent:0;font-weight:600;line-height:1.9;text-align:left}
blockquote.gold p:last-child{margin:0}
blockquote.gold p+p{border-top:1px dotted #e3d3ab;padding-top:.7em}
/* ---------- 树（图示） ---------- */
.tree{margin:24px 0 26px;padding:20px 24px;background:var(--paper-2);
  border:1px solid var(--rule-soft);border-radius:4px;page-break-inside:avoid;break-inside:avoid;
  font-family:var(--sans)}
.tree ul.tree-list{list-style:none;margin:0;padding-left:1.55em;position:relative}
.tree ul.tree-list.tree-root{padding-left:.15em}
.tree ul.tree-list ul.tree-list{border-left:1px solid var(--rule);margin-left:.62em;padding-left:1.35em}
.tree li{position:relative;margin:0;padding:3.5px 0 3.5px 1.25em}
.tree li::before{content:"▸";position:absolute;left:.05em;top:3.5px;color:var(--accent);
  font-size:11.5px;line-height:1.85}
.tree ul.tree-list ul.tree-list li::before{color:var(--ink-mute);font-size:10.5px;left:.05em;top:4px}
.tree ul.tree-list ul.tree-list ul.tree-list li::before{color:#b3aa9c;font-size:9.5px}
.tree .tl{font-size:15.5px;line-height:1.8;color:var(--ink)}
.tree ul.tree-list.tree-root > li > .tl{font-weight:700;font-size:16px;color:var(--ink)}
.tree ul.tree-list.tree-root > li{padding-top:2px;padding-bottom:5px}
/* ---------- 表格 ---------- */
.table-wrap{margin:26px 0;overflow-x:auto;page-break-inside:avoid;break-inside:avoid}
table{width:100%;border-collapse:collapse;font-family:var(--sans);font-size:14px;line-height:1.72}
th{background:var(--ink);color:var(--paper);font-weight:600;padding:11px 14px;text-align:left;
  border:1px solid var(--ink);border-bottom:3px solid var(--accent);letter-spacing:.04em;white-space:nowrap}
td{padding:10px 14px;border:1px solid var(--rule);vertical-align:middle;text-align:left;color:var(--ink)}
tbody tr:nth-child(even) td{background:#faf7f0}
tbody td:first-child{font-weight:600;color:#5a3b33;background:#f6f1e8}
tbody tr:nth-child(even) td:first-child{background:#efe8da}
td strong{color:#8a2c20}
/* ---------- 框（图示） ---------- */
.frame{margin:26px 0;padding:18px 24px;background:#fbf9f4;border:1px solid var(--rule);
  border-left:4px solid var(--accent);border-radius:0 4px 4px 0;page-break-inside:avoid;break-inside:avoid}
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
@page{size:A5;margin:17mm 15mm 18mm}
@media print{
  body{background:#fff;font-size:11.4pt;line-height:1.85}
  .book{max-width:none;box-shadow:none;padding:0;margin:0}
  .cover{min-height:auto;padding:34mm 0 0}
  .cover h1{font-size:25pt}
  .cover .sub{font-size:9.5pt}
  h2{font-size:17pt;margin:12mm 0 6mm}
  h3{font-size:13.5pt;margin:8mm 0 4mm}
  h4{font-size:12pt}
  p{margin-bottom:.85em}
  .tree,.frame,.table-wrap,blockquote,.copyright{page-break-inside:avoid;break-inside:avoid}
  .toc .t2{font-size:11.5pt}
  .toc .t3{font-size:10.5pt}
  a{color:inherit;text-decoration:none}
}
@media (max-width:700px){ .book{padding:34px 22px 64px} body{font-size:16px} .cover h1{font-size:27px} }
"""
