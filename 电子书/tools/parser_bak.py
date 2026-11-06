#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《数据治理实战》Markdown -> 出版级 HTML 转换器
所有图示（树/框/表）均以 HTML+CSS 绘制，不引用任何图片文件。
"""
import re, html, json, sys

SRC = '/home/ubuntu/miyue/电子书/数据治理实战：竖版_带文字树.md'
OUT = '/home/ubuntu/miyue/电子书/数据治理实战_出版版.html'

TREE_PREFIX = '▸'

def esc(s):
    return html.escape(s, quote=False)

# ---------- 行内格式 ----------
def inline(s):
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s

# ---------- 预处理：修围栏、去内部标注 ----------
MD_STRUCT = re.compile(r'^\s*(#{1,6}\s|\||>\s|[-*]\s|\d+\.\s|---$)', re.M)

def preprocess(text):
    lines = text.split('\n')
    out, i, n = [], 0, len(lines)
    # 记录原始围栏块
    while i < n:
        if lines[i].strip().startswith('```'):
            j = i + 1
            while j < n and not lines[j].strip().startswith('```'):
                j += 1
            body = '\n'.join(lines[i+1:j])
            if MD_STRUCT.search(body):
                # 围栏误包正文 -> 拆出当正文
                out.extend(lines[i+1:j])
            else:
                out.append('@@FRAME@@' + body + '@@ENDFRAME@@')
            i = j + 1
        else:
            out.append(lines[i]); i += 1
    t = '\n'.join(out)
    # 内部标注
    t = t.replace('# 【新增核心章节】', '# ').replace('# 【新增】', '# ')
    t = re.sub(r'(?<=\s)新增$', '', t, flags=re.M)
    return t

# ---------- 标题锚点 ----------
class Slug:
    def __init__(self): self.n = 0; self.map = {}; self.toc = []
    def make(self, text, level):
        self.n += 1
        sid = 's%03d' % self.n
        self.map[sid] = text
        self.toc.append((level, text, sid))
        return sid

def render_tree(lines):
    """缩进树 -> 嵌套 <ul>。按实际出现的缩进值排序映射层级。"""
    items = []
    for l in lines:
        m = re.match(r'^(\s*)' + re.escape(TREE_PREFIX) + r'\s*(.*)$', l)
        if not m: continue
        items.append((len(m.group(1)), m.group(2).strip()))
    if not items: return ''
    widths = sorted({w for w, _ in items})
    lv = {w: i for i, w in enumerate(widths)}
    html_out = []
    stack = []  # (level, opened)
    def close_to(target):
        while stack and stack[-1] >= target:
            stack.pop(); html_out.append('</ul></li>')
    open_li = False
    for w, txt in items:
        level = lv[w]
        if open_li:
            html_out.append('</li>'); open_li = False
        close_to(level)
        while len(stack) < level:
            html_out.append('<ul class="tree-list">'); stack.append(level)
        html_out.append('<li><span class="tl">%s</span>' % inline(txt))
        open_li = True
    if open_li: html_out.append('</li>')
    while stack:
        stack.pop(); html_out.append('</ul></li>')
    return '<div class="tree">%s</div>' % ''.join(html_out)

def render_table(rows):
    def cells(l):
        return [c.strip() for c in l.strip().strip('|').split('|')]
    head = cells(rows[0])
    body = [cells(r) for r in rows[2:] if r.strip().strip('|')]
    o = ['<div class="table-wrap"><table><thead><tr>']
    o += ['<th>%s</th>' % inline(c) for c in head]
    o.append('</tr></thead><tbody>')
    for r in body:
        o.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>')
    o.append('</tbody></table></div>')
    return ''.join(o)

def render_frame(body):
    o = ['<div class="frame">']
    for l in body.split('\n'):
        if not l.strip(): continue
        o.append('<div class="frame-row">%s</div>' % inline(l.rstrip()))
    o.append('</div>')
    return ''.join(o)

def convert(text):
    slug = Slug()
    body = []
    lines = text.split('\n')
    i, n = 0, len(lines)
    h1_seen = False
    while i < n:
        l = lines[i]
        s = l.strip()
        if not s:
            i += 1; continue
        # frame
        if s.startswith('@@FRAME@@'):
            j = i + 1; buf = []
            while j < n and not lines[j].strip().startswith('@@ENDFRAME@@'):
                buf.append(lines[j]); j += 1
            body.append(render_frame('\n'.join(buf))); i = j + 1; continue
        # heading
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            hraw = len(m.group(1)); txt = m.group(2).strip()
            if hraw == 1 and not h1_seen:
                h1_seen = True; body.append('<!--BOOKTITLE:%s-->' % txt); i += 1; continue
            lvl = hraw if hraw == 1 else hraw + 1
            if hraw == 1: lvl = 2
            sid = slug.make(txt, lvl)
            cls = ' class="chapter"' if lvl == 2 else ''
            body.append('<h%d id="%s"%s>%s</h%d>' % (lvl, sid, cls, inline(txt), lvl))
            i += 1; continue
        # hr
        if re.match(r'^-{3,}$', s):
            body.append('<hr class="rule">'); i += 1; continue
        # table
        if s.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append(lines[i]); i += 1
            body.append(render_table(rows)); continue
        # tree block
        if re.match(r'^\s*' + re.escape(TREE_PREFIX), l):
            blk = []
            while i < n and (re.match(r'^\s*' + re.escape(TREE_PREFIX), lines[i]) or not lines[i].strip()):
                blk.append(lines[i]); i += 1
            body.append(render_tree(blk)); continue
        # quote block
        if s.startswith('>'):
            blk = []
            while i < n and (lines[i].strip().startswith('>') or not lines[i].strip()):
                blk.append(lines[i]); i += 1
            qlines = [re.sub(r'^\s*>\s?', '', b) for b in blk]
            qlines = [b for b in qlines if b.strip()]
            gold = all(('**' in b) for b in qlines) and len(qlines) <= 4
            cls = 'quote gold' if gold else 'quote'
            body.append('<blockquote class="%s">' % cls +
                        ''.join('<p>%s</p>' % inline(b) for b in qlines) + '</blockquote>')
            continue
        # list
        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', l)
        if m:
            ordered = bool(re.match(r'\d', m.group(2)))
            items = []
            base = len(m.group(1))
            while i < n:
                mm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', lines[i])
                if not mm:
                    if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) > base:
                        if items: items[-1] = (items[-1][0], items[-1][1] + ' ' + lines[i].strip())
                        i += 1; continue
                    break
                ind = len(mm.group(1))
                if ind < base: break
                txt = mm.group(3).strip()
                if ind > base and items:
                    items[-1] = (items[-1][0], items[-1][1] + '<span class="sub">' + inline(txt) + '</span>')
                else:
                    items.append((bool(re.match(r'\d', mm.group(2))), txt))
                i += 1
            tag = 'ol' if ordered else 'ul'
            o = ['<%s class="lst">' % tag]
            for _, txt in items:
                o.append('<li>%s</li>' % inline(txt))
            o.append('</%s>' % tag)
            body.append(''.join(o)); continue
        # paragraph
        para = [s]
        i += 1
        while i < n and lines[i].strip() and not re.match(r'^\s*(#{1,6}\s|\||>|[-*]\s|\d+\.\s|```|@@FRAME@@)', lines[i]) and not re.match(r'^\s*'+re.escape(TREE_PREFIX), lines[i]):
            para.append(lines[i].strip()); i += 1
        body.append('<p>%s</p>' % inline(' '.join(para)))
    return slug, '\n'.join(body)

if __name__ == '__main__':
    raw = open(SRC, encoding='utf-8').read()
    slug, body = convert(preprocess(raw))
    json.dump({'toc': slug.toc}, open('/tmp/toc.json', 'w'), ensure_ascii=False)
    open('/tmp/body.html', 'w', encoding='utf-8').write(body)
    print('TOC条目:', len(slug.toc), '| body字节:', len(body))
