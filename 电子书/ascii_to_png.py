#!/usr/bin/env python3
"""
ASCII 图 → Graphviz DOT (portrait) → PNG via Kroki.io
生成 with_images 版电子书 MD。

要点：
1. 图片输出到 miyue/电子书/diagram-img/，并使用**相对路径**（diagram-img/xxx.png），
   这样 MD 随仓库分发后图片仍可正常显示（绝对 file:/// 路径在别人机器上必然失效）。
2. 步骤型代码块（含"第N步"或①②③编号）**不做树形转换**——它们是流程步骤而非树，
   转成树会丢失"先后顺序"语义（第一步/第二步并列成兄弟节点）。这类块保留原文，
   由 md_to_ebook.py 的步骤转换或纯文本呈现。
3. 树型块才渲染为 PNG。
"""
import re, os, subprocess

MD_PATH = "/home/ubuntu/miyue/电子书/数据治理实战：从二级分类到落地执行.md"
OUT_MD = "/home/ubuntu/miyue/电子书/数据治理实战：从二级分类到落地执行_with_images.md"
IMG_DIR = "/home/ubuntu/miyue/电子书/diagram-img"
os.makedirs(IMG_DIR, exist_ok=True)

KROKI_PNG = "https://kroki.io/graphviz/png"


# ─── Detection ───────────────────────────────────────────────────────────────

def is_tree_block(block):
    tree_chars = set('├──└│├┼┬┴─')
    lines = block.strip().splitlines()
    if not lines:
        return False
    score = sum(1 for ln in lines for c in tree_chars if c in ln)
    return score >= 2


def is_step_block(block):
    """步骤型块：含"第N步"或①②③等顺序编号 —— 不转树"""
    return bool(re.search(r'(第[一二三四五六七八九十]+步\s*[:：]|^[①②③④⑤⑥⑦⑧⑨⑩]\s)',
                          block, re.M))


# ─── Parser ──────────────────────────────────────────────────────────────────

def parse_tree_lines(block):
    result = []
    for ln in block.strip().splitlines():
        if not ln.strip():
            continue
        i = 0
        for c in ln:
            if c in ' │├└┬┴┼─' or c.isspace():
                i += 1
            else:
                break
        indent = i
        text = ln[i:].strip()
        text = re.sub(r'^[\s│─├└┬┴┼├]+', '', text)
        if text:
            result.append((indent, text))
    return result


# ─── DOT generator ───────────────────────────────────────────────────────────

def tree_to_dot_portrait(tree_data):
    lines = [
        'digraph G {',
        '  rankdir=TB;',
        '  nodesep=0.25;',
        '  ranksep=0.3;',
        '  node [shape=rect, style="rounded,filled", fillcolor="#EEF2FF",',
        '       color="#4F46E5", fontname="Helvetica", fontsize=10,',
        '       width=2.0, height=0.32, margin="0.1,0.06"];',
        '  edge [color="#94A3B8", arrowsize=0.5];',
        '  graph [bgcolor="transparent", dpi=150, size="4,5.5!", ratio=fill];',
        '']

    for i, (indent, text) in enumerate(tree_data):
        if len(text) > 26:
            text = text[:24] + '..'
        text = text.replace('"', "'").replace('\\', '\\\\')
        is_root = (i == 0)
        if is_root:
            lines.append(f'  n{i}[label="{text}", fillcolor="#4F46E5", fontcolor="white", fontsize=12, width=1.4, height=0.35];')
        else:
            lines.append(f'  n{i}[label="{text}"];')

    nodes = list(enumerate(tree_data))
    root_indent, _ = nodes[0]
    stack = [(root_indent, 0)]
    for i, (indent, _) in nodes[1:]:
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            lines.append(f'  n{stack[-1][1]} -> n{i};')
        stack.append((indent, i))

    lines.append('}')
    return '\n'.join(lines)


# ─── Render via Kroki ────────────────────────────────────────────────────────

def render_kroki(dot_src, diag_id):
    out_png = f"{IMG_DIR}/{diag_id}.png"
    dot_file = f"/tmp/{diag_id}.dot"
    with open(dot_file, 'w') as f:
        f.write(dot_src)
    r = subprocess.run(
        ['curl', '-s', '-X', 'POST', KROKI_PNG,
         '-H', 'Content-Type: text/plain', '-d', f'@{dot_file}',
         '-o', out_png, '-w', '%{http_code}', '--max-time', '30'],
        capture_output=True, text=True)
    os.unlink(dot_file)
    code = r.stdout.strip()
    if code == '200' and os.path.exists(out_png):
        print(f"  ✅ {diag_id} ({os.path.getsize(out_png)//1024}KB)")
        return out_png
    else:
        print(f"  ❌ {diag_id} HTTP {code}")
        return None


# ─── Main ────────────────────────────────────────────────────────────────────

def process():
    with open(MD_PATH, encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(r'```(?:\w*)\n(.*?)```', re.DOTALL)
    blocks = list(pattern.finditer(content))

    counter = 0
    success = 0
    skipped_step = 0
    new_content = content

    for m in blocks:
        block = m.group(1)
        if not is_tree_block(block):
            continue
        # 步骤型块保留原文，不转树（转树会丢失先后顺序语义）
        if is_step_block(block):
            skipped_step += 1
            continue
        counter += 1
        diag_id = f"diag_{counter:03d}"

        tree_data = parse_tree_lines(block)
        if not tree_data:
            continue

        dot_src = tree_to_dot_portrait(tree_data)
        img_path = render_kroki(dot_src, diag_id)

        if img_path:
            # 相对路径，随仓库分发后仍可显示
            img_ref = f'\n\n![{diag_id}](diagram-img/{diag_id}.png)\n\n'
            new_content = new_content.replace(m.group(0), img_ref, 1)
            success += 1

    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"\n完成: {success}/{counter} 图成功（跳过步骤型块 {skipped_step} 个，保留原文）→ {OUT_MD}")
    return success, counter, skipped_step


if __name__ == '__main__':
    process()
