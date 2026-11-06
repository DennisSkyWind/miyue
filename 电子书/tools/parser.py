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

CJK_ALL = '\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff'

def cjk_spacing(s):
    """中英文/中数字之间加空格（中文出版排版规范）"""
    s = re.sub(r'([' + CJK_ALL + r'])([A-Za-z0-9])', r'\1 \2', s)
    s = re.sub(r'([A-Za-z0-9])([' + CJK_ALL + r'])', r'\1 \2', s)
    return s

def normalize_quotes(s):
    """英文直引号 -> 中文直角引号「」（本书术语强调风格统一）；去除 emoji"""
    out = []; open_q = True
    for ch in s:
        if ch == '"':
            out.append('「' if open_q else '」'); open_q = not open_q
        else:
            out.append(ch)
    s = ''.join(out)
    s = s.replace('\ufe0f', '')
    s = re.sub(r'\s*[\U0001F300-\U0001FAFF\u2B00-\u2BFF]\s*', ' ◆ ', s)
    return s

def post_space(t):
    """对已生成 HTML 的文本节点做中英文空格（跳过标签内部）"""
    parts = re.split(r'(<[^>]*>)', t)
    out = []
    for p in parts:
        if p.startswith('<'):
            out.append(p); continue
        if out and out[-1].startswith('</'):
            j = len(out) - 2
            if j >= 0 and re.search(r'[A-Za-z0-9]\s*$', out[j]):
                p = ' ' + p
        out.append(cjk_spacing(p))
    return ''.join(out)

# ---------- 行内格式 ----------
def inline(s):
    s = normalize_quotes(s)
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return post_space(s)

# ---------- 预处理：修围栏、去内部标注 ----------
MD_STRUCT = re.compile(r'^\s*(#{1,6}\s|\||>\s|[-*]\s|\d+\.\s|---$)', re.M)

def fix_numbered_tables(t):
    """修源文件三类格式错误：
    1) 双层编号误写 '5. 1. xxx'  -> 缩进子项 '    1. xxx'
    2) 表格被误加编号 '9. | 好处 | 说明 |' -> 顶格 '| 好处 | 说明 |'
    3) 普通列表编号原样保留
    """
    lines = t.split('\n'); out = []; i = 0
    while i < len(lines):
        l = lines[i]
        m3 = re.match(r'^(\s*)\d+\.\s+(\d+)\.\s+(.*)$', l)
        if m3 and not m3.group(3).lstrip().startswith('|'):
            out.append(m3.group(1) + '    ' + m3.group(2) + '. ' + m3.group(3))
            i += 1; continue
        m2 = re.match(r'^(\s*)\d+\.\s+(\|.*)$', l)
        if m2:
            out.append(m2.group(1) + m2.group(2).strip())
            i += 1; continue
        m1 = re.match(r'^(\s*)(\d+)\.\s+(.*)$', l)
        if m1:
            ind = m1.group(1); block = []
            while i < len(lines):
                mm = re.match(r'^(\s*)(\d+)\.\s+(.*)$', lines[i])
                if not mm or len(mm.group(1)) != len(ind): break
                if re.match(r'^(\s*)\d+\.\s+\d+\.\s+', lines[i]): break
                if mm.group(3).strip().startswith('|'): break
                block.append((mm.group(2), mm.group(3))); i += 1
            for num, txt in block:
                out.append(ind + num + '. ' + txt)
            continue
        out.append(l); i += 1
    return '\n'.join(out)

BOXCH = set('\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c\u2500\u2502')

def ascii_table_to_md(t):
    """ASCII 框线图形分类还原：
       - 多列且无箭头 -> 标准 markdown 表格
       - 含箭头 / 单列   -> @@FLOW@@ 流程示意块（保留箭头语义）
       - 单独一条带 ─┼─ 的横线 -> @@FLOWARROW@@
    """
    lines = t.split('\n'); out = []; i = 0; n = len(lines)
    def is_box(l):
        return any(c in BOXCH for c in l)
    def is_arrow_line(l):
        t = re.sub(r'^[\u25b8\s]*', '', l.strip())
        return bool(t) and set(t) <= set('\u2190\u2191\u2192\u2193\u2500\u2502\u253c\u25b8')
    def strip_marks(l):
        s = l.strip()
        s = re.sub(r'^[\u25b8\s]*', '', s)
        return s.rstrip()
    def cells_of(b):
        c = [x.strip() for x in b.strip('\u2502').split('\u2502')]
        return [x for x in c]
    while i < n:
        l = lines[i]
        # 单独横线示意：优先做  <----+---->  后做
        if re.search(r'[\u2500]{2,}[\u253c\u2502][\u2500]{2,}', l) and '\u2502' not in l.replace('\u253c',''):
            s = strip_marks(l)
            m = re.match(r'^(.*?)[\u2500\u253c\u2502]{2,}(.*)$', s)
            if m and (m.group(1).strip() or m.group(2).strip()):
                out.append('@@FLOWARROW@@' + m.group(1).strip() + '\u0001' + m.group(2).strip())
                i += 1
                continue
        if is_box(l) and ('\u2502' in l or '\u250c' in l or '\u251c' in l or '\u2514' in l):
            blk = []
            while i < n and (is_box(lines[i]) or is_arrow_line(lines[i]) or not lines[i].strip()):
                if is_box(lines[i]) or is_arrow_line(lines[i]): blk.append(strip_marks(lines[i]))
                i += 1
            rows = []
            for b in blk:
                b = b.strip()
                if not b or set(b) <= set('\u2500\u2502\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c'):
                    continue
                if b in ('\u2193', '\u2191', '\u2192', '\u2190'):
                    rows.append(['\u0002' + b]); continue
                mb = re.match(r'^/\s*(.*?)\s*\\\s*(.*)$', b)
                if mb:
                    rows.append([mb.group(1) or '', mb.group(2) or '']); continue
                if '\u2502' in b:
                    if b.count('\u2502') >= 2:
                        rows.append(cells_of(b)); continue   # 多列 -> 按列切分
                    inner = b.strip('\u2502').strip()          # 单竖线 -> 框内文字
                    inner = re.sub(r'[\u2500\u2502\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c]+$', '', inner).strip()
                    inner = re.sub(r'^[\u2500\u2502\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c]+', '', inner).strip()
                    if inner:
                        rows.append([inner]); continue
                    continue
            if not rows:
                continue
            ncol = max(len(r) for r in rows)
            rows = [r + [''] * (ncol - len(r)) for r in rows]
            has_arrow = any(re.search(r'[\u2190\u2192]', ' '.join(r)) for r in rows)
            if ncol >= 2 and not has_arrow:
                out.append('| ' + ' | '.join(rows[0]) + ' |')
                out.append('|' + '---|' * ncol)
                for r in rows[1:]:
                    out.append('| ' + ' | '.join(r) + ' |')
                out.append('')
            else:
                # 单列/带箭头 -> 还原为平级树节点（剥掉全部框线字符）
                out.append('@@TREEASCII@@')
                for r in rows:
                    if r and r[0].startswith('\u0002'):
                        out.append('\u25b8 \u0003' + r[0][1:]); continue
                    txt = ' '.join(x for x in r if x).strip()
                    txt = re.sub(r'[\u2500\u2502\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c]', '', txt)
                    txt = txt.replace('\u2190', '').replace('\u2192', '').strip()
                    txt = re.sub(r'\s{2,}', ' ', txt)
                    if txt:
                        out.append('\u25b8 ' + txt)
                out.append('@@ENDTREEASCII@@')
            continue
        out.append(l); i += 1
    return '\n'.join(out)

def strip_remaining_box(t):
    """兜底：把任何仍残留框线字符的行转成 frame 卡片，确保 HTML 里 0 残留。"""
    out = []
    for l in t.split('\n'):
        if not any(c in BOXCH for c in l):
            out.append(l); continue
        s = re.sub(r'^[\u25b8\s]*', '', l.strip())
        cells = [c.strip() for c in s.split('\u2502')]
        cells = [re.sub(r'[\u2500\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c]+', '', c).strip()
                 for c in cells]
        cells = [c for c in cells if c]
        cells = [c.replace('\u2190', '').replace('\u2192', '').strip() for c in cells]
        cells = [c for c in cells if c]
        if cells:
            txt = ' '.join(cells)
            txt = re.sub(r'\s{2,}', ' ', txt).strip()
            if txt:
                out.append('\u25b8 ' + txt)
        else:
            out.append('')
    return '\n'.join(out)

MATRIX_RE = re.compile(
    r'[ \t\u25b8]*\u4e1a\u52a1\u4ef7\u503c\u9ad8[\s\S]{0,400}?'
    r'[ \t\u25b8]*\u4f18\u5148\u505a[\s\S]{0,200}?\u540e\u505a[\s\S]{0,400}?'
    r'[ \t\u25b8]*\u4e1a\u52a1\u4ef7\u503c\u4f4e')

def preprocess(text):
    text = fix_numbered_tables(text)
    # 优先级象限图（业务价值 x 治理难度）-> 专用组件标记（须在 ASCII 处理之前）
    text = MATRIX_RE.sub('@@MATRIX@@', text)
    text = ascii_table_to_md(text)
    text = strip_remaining_box(text)
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
                out.append('@@FRAME@@')
                out.extend(body.split('\n'))
                out.append('@@ENDFRAME@@')
            i = j + 1
        else:
            out.append(lines[i]); i += 1
    t = '\n'.join(out)
    # 内部标注
    t = t.replace('# 【新增核心章节】', '# ').replace('# 【新增】', '# ')
    t = re.sub(r'(?<=\s)新增$', '', t, flags=re.M)
    # 脱敏：真实企业名统一改为泛称
    for real, safe in [('昆药集团','某药企'),('昆药','某药企'),('云药集团','某药企')]:
        t = t.replace(real, safe)
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
    """缩进树 -> 严格合法的嵌套 HTML（ul 必须是 li 的子元素）"""
    items = []
    for l in lines:
        m = re.match(r'^(\s*)' + re.escape(TREE_PREFIX) + r'\s*(.*)$', l)
        if not m:
            continue
        items.append((len(m.group(1)), m.group(2).strip()))
    if not items:
        return ''
    widths = sorted({w for w, _ in items})
    lv = {w: i for i, w in enumerate(widths)}
    levels = [lv[w] for w, _ in items]
    out = []

    def rec(pos, level):
        while pos < len(items) and levels[pos] == level:
            _, txt = items[pos]
            out.append('<li><span class="tl">%s</span>' % inline(txt))
            pos += 1
            if pos < len(items) and levels[pos] > level:
                out.append('<ul class="tree-list">')
                pos = rec(pos, level + 1)
                out.append('</ul>')
            out.append('</li>')
        return pos

    rec(0, 0)
    return ('<div class="tree"><ul class="tree-list tree-root">' + ''.join(out)
            + '</ul></div>')

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

CHAP_RE = re.compile(r'^第[一二三四五六七八九十百]+章')
DUP_SKIP_TITLES = {'附录'}

def is_chapter(txt):
    t = txt.strip()
    return bool(CHAP_RE.match(t))

def convert(text):
    slug = Slug()
    body = []
    lines = text.split('\n')
    i, n = 0, len(lines)
    h1_seen = False
    seen_h = set()
    skip_until_heading = False
    while i < n:
        l = lines[i]
        s = l.strip()
        if not s:
            i += 1; continue
        if skip_until_heading:
            if re.match(r'^(#{1,6})\s+', s):
                skip_until_heading = False
            else:
                i += 1; continue
        # 优先级象限图
        if s.startswith('@@MATRIX@@'):
            body.append(
                '<div class="matrix">'
                '<div class="mx-corner"></div>'
                '<div class="mx-ax-h">治理难度 低</div>'
                '<div class="mx-ax-h">治理难度 高</div>'
                '<div class="mx-ax-v">业务价值 高</div>'
                '<div class="mx-cell mx-star"><span class="mx-tag">优先做</span>'
                '<span class="mx-note">高价值 + 低难度（打鸡血）</span></div>'
                '<div class="mx-cell mx-hard"><span class="mx-tag">啃硬骨头</span>'
                '<span class="mx-note">高价值 + 高难度</span></div>'
                '<div class="mx-ax-v mx-low">业务价值 低</div>'
                '<div class="mx-cell mx-empty"></div>'
                '<div class="mx-cell mx-late"><span class="mx-tag">后做</span></div>'
                '</div>')
            i += 1; continue
        # ASCII 图形还原块 -> 树
        if s.startswith('@@TREEASCII@@'):
            j = i + 1; buf = []
            while j < n and not lines[j].strip().startswith('@@ENDTREEASCII@@'):
                buf.append(lines[j]); j += 1
            items_buf = [b.strip() for b in buf if b.strip()]
            while items_buf and items_buf[-1].startswith('\u25b8 \u0003'):
                items_buf.pop()
            buf = items_buf
            o = ['<div class="frame">']
            for b in buf:
                b = b.strip()
                if not b or not b.startswith('\u25b8'):
                    continue
                body_txt = b[1:].strip()
                if body_txt.startswith('\u0003'):
                    d = 'up' if body_txt[1] == '\u2191' else 'down'
                    o.append('<div class="fconn fconn-%s"><span class="fconn-line"></span>'
                             '<span class="fconn-tip"></span></div>' % d)
                    continue
                o.append('<div class="frame-row">%s</div>' % inline(body_txt))
            o.append('</div>')
            body.append(''.join(o)); i = j + 1; continue
        # flow 块
        if s.startswith('@@FLOW@@'):
            j = i + 1; buf = []
            while j < n and not lines[j].strip().startswith('@@ENDFLOW@@'):
                buf.append(lines[j]); j += 1
            o = ['<div class="flow">']
            for b in buf:
                if b.startswith('\u0003'):
                    d = 'up' if b[1] == '\u2191' else 'down'
                    o.append('<div class="fconn fconn-%s"><span class="fconn-line"></span>'
                             '<span class="fconn-tip"></span></div>' % d)
                    continue
                parts = [x for x in b.split('\u0001') if x and x != '-']
                if not parts:
                    continue
                txts = []
                for k, x in enumerate(parts):
                    x = x.replace('\u2190', '').replace('\u2192', '').strip()
                    if not x:
                        continue
                    txts.append('<span class="ftext%s">%s</span>'
                                % (' ftext-lead' if k == 0 else '', inline(x)))
                if not txts:
                    continue
                o.append('<div class="flow-row">' + '<span class="fsep"></span>'.join(txts) + '</div>')
            o.append('</div>')
            body.append(''.join(o)); i = j + 1; continue
        # flow 横线示意
        if s.startswith('@@FLOWARROW@@'):
            a, b = s[len('@@FLOWARROW@@'):].split('\u0001')
            a = re.sub(r'[\u2190\u2192\u21d0\u21d2]', '', a).strip()
            b = re.sub(r'[\u2190\u2192\u21d0\u21d2]', '', b).strip()
            body.append('<div class="flow"><div class="flow-row"><span class="ftext">%s</span>'
                        '<span class="farrow"></span><span class="ftext">%s</span></div></div>'
                        % (inline(a), inline(b)))
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
            if hraw == 1:
                lvl = 2
            elif hraw == 2:
                lvl = 2 if is_chapter(txt) else 3
            else:
                lvl = hraw + 1
            # 手工目录节 -> 交给自动 TOC
            if txt.strip() == '目录':
                skip_until_heading = True; i += 1; continue
            # 仅"附录"整节重复 -> 跳过整节；其他同名小标题(如"核心金句")必须保留
            if txt.strip() in DUP_SKIP_TITLES and txt.strip() in seen_h:
                skip_until_heading = True; i += 1; continue
            seen_h.add(txt.strip())
            skip_until_heading = False
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
                    if (lines[i].strip() and not lines[i].strip().startswith('|')
                            and len(lines[i]) - len(lines[i].lstrip()) > base):
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
