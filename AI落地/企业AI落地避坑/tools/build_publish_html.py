#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《AI 未成之路》Markdown -> 出版级 HTML 转换器
范式沿用《数据治理实战》出版版：自包含、零外链、零图片引用。
- Markdown 表格 -> HTML 表格
- 围栏块（含引用块内的）-> 按类型渲染
- ASCII 框线图 -> 保留等宽对齐的 box 样式
"""
import re, html, sys, os

SRC = '/home/ubuntu/miyue/AI落地/企业AI落地避坑/AI未成之路_定稿候选版_v1.21_20261106.md'
OUT = '/home/ubuntu/miyue/AI落地/企业AI落地避坑/草稿/AI未成之路_出版版.html'

CJK = '\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef'


def esc(s):
    return html.escape(s, quote=False)


def cjk_spacing(s):
    s = re.sub(r'([' + CJK + r'])([A-Za-z0-9])', r'\1 \2', s)
    s = re.sub(r'([A-Za-z0-9])([' + CJK + r'])(?![，。、；：？！）】》」』%])',
               lambda m: m.group(1) + ' ' + m.group(2), s)
    return s


def norm_quotes(s):
    out = []
    open_q = True
    for ch in s:
        if ch == '"':
            out.append('「' if open_q else '」')
            open_q = not open_q
        else:
            out.append(ch)
    s = ''.join(out)
    s = re.sub(r'\s*[\U0001F300-\U0001FAFF\u2B00-\u2BFF\uFE0F\u200D]\s*', ' ◆ ', s)
    return s


def inline(t):
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', t)
    return t


def split_row(line):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    parts = re.split(r'(?<!\\)\|', line)
    return [p.replace('\\|', '|').strip() for p in parts]


def is_sep(line):
    return bool(re.match(r'^\s*\|?[\s:|-]*-{2,}[\s:|-]*\|?\s*$', line)) and '-' in line


BOX_CHARS = '┌┐└┘├┤┬┴┼─━│═╔╗╚╝║╠╣╦╩╬'


def has_box(text):
    return any(c in text for c in BOX_CHARS)


def render_table(header, rows):
    out = ['<table class="md-table"><thead><tr>']
    out += [f'<th>{inline(c)}</th>' for c in header]
    out.append('</tr></thead><tbody>')
    for r in rows:
        out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out)


def render_fence(lang, body):
    lines = body.rstrip('\n').split('\n')
    if has_box(body):
        return '<div class="box"><pre class="box-pre">' + esc(body.rstrip('\n')) + '</pre></div>'
    if lang in ('mermaid', 'mmd'):
        return '<div class="box"><pre class="box-pre">' + esc(body.rstrip('\n')) + '</pre></div>'
    return '<pre class="code">' + esc(body.rstrip('\n')) + '</pre>'


PROSE_HEAD = re.compile(r'^\*\*(★|\*|★{1,3}|\d)|^#{1,6}\s|^>\s|^\|.*\|$')
BOX_RE = re.compile(r'[┌┐└┘├┤┬┴┼─━│═╔╗╚╝║╠╣╦╩╬]')


def looks_like_prose(lines, i):
    """判断代码块内第 i 行是否是"被误吞进来的散文段落"。

    判据（基于对 v1.21 的实测）：
      1) 该行为一个孤立段落的起始（前有空行）
      2) 段落内至少一行含 Markdown 结构标记（**加粗 / # 标题 / > 引用 / | 表格）
      3) 整段不含 ASCII 框线字符
    实测：书稿代码块内含 '**' 的 1069 行中，带框线字符的为 0 行，
    因此"含 ** 且无框线字符"可以安全地判定为被误吞的散文。
    """
    if i <= 0 or i >= len(lines):
        return False
    cur = lines[i]
    if not cur.strip():
        return False
    if not lines[i - 1].strip():          # 必须前面有空行 = 段落起始
        pass
    else:
        return False
    # 收集整个段落
    j = i
    while j < len(lines) and lines[j].strip():
        j += 1
    para = lines[i:j]
    if not para:
        return False
    # 段落内不能有框线字符
    if any(BOX_RE.search(x) for x in para):
        return False
    # 至少一行带 markdown 结构标记
    has_mark = any('**' in x or PROSE_HEAD.match(x.strip()) for x in para)
    return has_mark


def parse_blocks(lines, h1_seen):
    """把一组行解析为 HTML 块列表"""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        # 围栏
        m = re.match(r'^\s*```(\w*)\s*$', line)
        if m:
            lang = m.group(1)
            buf = []
            i += 1
            while i < n and not re.match(r'^\s*```\s*$', lines[i]):
                buf.append(lines[i])
                i += 1
            has_close = i < n
            i += 1  # 跳过结束围栏
            # ★ 启发式修复：代码块内若出现被误吞的散文段落，在此处闭合代码块
            cut = None
            for k in range(len(buf)):
                if looks_like_prose(buf, k):
                    cut = k
                    break
            if cut is not None:
                out.append(render_fence(lang, '\n'.join(buf[:cut])))
                # 散文部分作为普通块解析，剩下的（从原闭合围栏之后）继续
                rest = buf[cut:]
                inner = parse_blocks(rest, h1_seen)
                out.extend(inner)
            else:
                out.append(render_fence(lang, '\n'.join(buf)))
            continue
        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2).strip()
            if lvl == 1:
                if txt == 'AI 未成之路' and h1_seen[0]:
                    i += 1
                    continue
                h1_seen[0] = True
            cls = {1: 'h1', 2: 'h2', 3: 'h3', 4: 'h4', 5: 'h5', 6: 'h6'}[lvl]
            anchor = re.sub(r'[^\w\u4e00-\u9fff]+', '-', txt).strip('-')[:40]
            out.append(f'<{cls} id="{anchor}">{inline(txt)}</{cls}>')
            i += 1
            continue
        # 分隔线
        if re.match(r'^\s*(-{3,}|\*{3,}|_{3,})\s*$', line):
            out.append('<hr>')
            i += 1
            continue
        # 表格
        if line.strip().startswith('|') and i + 1 < n and is_sep(lines[i + 1]):
            header = split_row(line)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append(split_row(lines[i]))
                i += 1
            out.append(render_table(header, rows))
            continue
        # 引用块
        if re.match(r'^\s*>', line):
            raw = []
            while i < n and (re.match(r'^\s*>', lines[i]) or
                             (raw and lines[i].strip() and
                              not re.match(r'^\s*(#{1,6}\s|```|>|\||[-*+]\s|\d+[.)]\s|-{3,}$)', lines[i]))):
                if re.match(r'^\s*>', lines[i]):
                    raw.append(re.sub(r'^\s*>\s?', '', lines[i]))
                else:
                    raw.append(lines[i])
                i += 1
            inner = parse_blocks(raw, h1_seen)
            out.append('<blockquote>' + '\n'.join(inner) + '</blockquote>')
            continue
        # 列表
        if re.match(r'^\s*([-*+]|\d+[.)])\s+', line):
            ordered = bool(re.match(r'^\s*\d', line))
            items = []
            while i < n and re.match(r'^\s*([-*+]|\d+[.)])\s+', lines[i]):
                items.append(re.sub(r'^\s*([-*+]|\d+[.)])\s+', '', lines[i]).strip())
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
            continue
        # 段落
        buf = []
        while i < n and lines[i].strip() and not re.match(
                r'^\s*(#{1,6}\s|```|>|\||[-*+]\s|\d+[.)]\s|-{3,}$|_{3,}$)', lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append('<p>' + inline(' '.join(buf)) + '</p>')
        else:
            i += 1
    return out


def post_process(html_text):
    """中英空格 + 引号规范化，跳过标签与 <pre> 内部（保护 ASCII 对齐）"""
    parts = re.split(r'(<pre[^>]*>.*?</pre>|<[^>]*>)', html_text, flags=re.S)
    out = []
    for p in parts:
        if not p:
            continue
        if p.startswith('<pre'):
            out.append(p)
        elif p.startswith('<'):
            out.append(p)
        else:
            out.append(cjk_spacing(norm_quotes(p)))
    return ''.join(out)


CSS = """
:root{
  --ink:#1c1a17; --ink-soft:#4a453d; --ink-mute:#8a8177;
  --paper:#fffdf8; --paper-2:#f8f4ec; --rule:#d9d1c0; --rule-soft:#ebe4d6;
  --accent:#8c3a2e; --accent-soft:#f5e7e1; --gold:#a8791c;
  --serif:"Source Han Serif SC","Noto Serif CJK SC","Songti SC","SimSun",serif;
  --sans:"Source Han Sans SC","Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#e7e1d4;color:var(--ink);
  font-family:var(--serif);font-size:17px;line-height:1.95;
  text-align:justify;text-justify:inter-ideograph}
.book{max-width:820px;margin:0 auto;background:var(--paper);
  padding:64px 72px 96px;box-shadow:0 1px 3px rgba(0,0,0,.08),0 12px 40px rgba(0,0,0,.10);
  min-height:100vh}
h1{font-size:34px;line-height:1.5;margin:0 0 30px;text-align:center;letter-spacing:.06em;
  font-weight:700;border:0;padding:0;page-break-before:always;break-before:page}
h2{font-size:25px;line-height:1.55;margin:56px 0 22px;font-weight:700;
  border-bottom:2px solid var(--accent);padding-bottom:10px;
  page-break-before:always;break-before:page}
h3{font-size:20px;line-height:1.6;margin:38px 0 14px;font-weight:700;color:var(--accent)}
h4{font-size:17.5px;line-height:1.65;margin:28px 0 10px;font-weight:700;color:var(--ink-soft)}
h5,h6{font-size:16px;margin:22px 0 8px;font-weight:700;color:var(--ink-soft);font-family:var(--sans)}
p{margin:0 0 15px;text-indent:2em}
strong{font-weight:700;color:var(--ink)}
em{font-style:normal;color:var(--accent)}
del{color:var(--ink-mute)}
code{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:.88em;background:var(--paper-2);
  border:1px solid var(--rule-soft);border-radius:3px;padding:1px 5px;color:var(--accent)}
hr{border:0;border-top:1px solid var(--rule);margin:40px 0}
ul,ol{margin:0 0 16px;padding-left:2.2em}
li{margin:0 0 7px}
blockquote{margin:22px 0;padding:18px 24px;background:var(--paper-2);
  border-left:4px solid var(--accent);border-radius:0 4px 4px 0;
  font-size:16.5px;line-height:1.9;page-break-inside:avoid;break-inside:avoid}
blockquote p{text-indent:0;margin:0 0 10px}
blockquote p:last-child{margin:0}
blockquote strong{color:var(--accent)}
blockquote h1,blockquote h2,blockquote h3,blockquote h4{margin:14px 0 8px;font-size:17px;
  border:0;padding:0;page-break-before:auto;break-before:auto;color:var(--ink)}
blockquote table.md-table{font-size:14px}
table.md-table{width:100%;border-collapse:collapse;margin:22px 0;font-size:15px;
  font-family:var(--sans);line-height:1.7;page-break-inside:avoid;break-inside:avoid}
table.md-table th{background:var(--accent-soft);color:var(--accent);font-weight:700;
  text-align:left;padding:10px 12px;border:1px solid var(--rule)}
table.md-table td{padding:9px 12px;border:1px solid var(--rule-soft);vertical-align:top}
table.md-table tbody tr:nth-child(even){background:#fcfaf4}
.box{margin:26px 0;padding:20px 22px;background:var(--paper-2);
  border:1px solid var(--rule);border-radius:5px;overflow-x:auto;
  page-break-inside:avoid;break-inside:avoid}
.box-pre{margin:0;font-family:"SF Mono",Menlo,Consolas,"Courier New",monospace;
  font-size:13px;line-height:1.6;white-space:pre;color:var(--ink-soft);letter-spacing:0}
pre.code{margin:22px 0;padding:16px 18px;background:var(--paper-2);
  border:1px solid var(--rule);border-radius:5px;overflow-x:auto;
  font-family:"SF Mono",Menlo,Consolas,monospace;font-size:13px;line-height:1.6;
  white-space:pre;page-break-inside:avoid;break-inside:avoid}
@media print{
  body{background:#fff;font-size:11.2pt}
  .book{max-width:none;box-shadow:none;padding:0}
  h2{page-break-before:always;break-before:page}
  h3,h4{page-break-after:avoid;break-after:avoid}
  p,li{orphans:3;widows:3}
}
@page{size:A5;margin:16mm 14mm 18mm}
@media screen and (max-width:720px){
  .book{padding:30px 20px 60px;font-size:16px}
  h1{font-size:27px}h2{font-size:21px}h3{font-size:18px}
}
"""


def main():
    src = open(SRC, encoding='utf-8').read()
    body = '\n'.join(parse_blocks(src.split('\n'), [False]))
    body = post_process(body)
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="author" content="米悦说说">
<meta name="description" content="企业 AI 落地实战：五个坑、九个场景、算账方法论与数字员工建设">
<title>AI 未成之路：为什么大多数企业的 AI 都没做成</title>
<style>{CSS}</style>
</head>
<body>
<div class="book">
{body}
</div>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(doc)
    print('written', OUT, os.path.getsize(OUT), 'bytes')


if __name__ == '__main__':
    main()
