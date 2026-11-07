#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《AI 未成之路》待核实清单（按章分组，逐行扫描）。"""
import re, collections, sys

SRC = 'AI未成之路_定稿候选版_v1.23_20261107.md'
OUT = '待核实清单_对齐v1.23.md'
lines = open(SRC, encoding='utf-8').read().split('\n')
chap = ''
items = []
for i, l in enumerate(lines, 1):
    m = re.match(r'^(#{1,3})\s+(.*)', l)
    if m and len(m.group(1)) == 2 and not m.group(2).startswith('0.'):
        chap = m.group(2).strip()
    for mm in re.finditer(r'【待核实[^】]*】', l):
        items.append({'line': i, 'chap': chap, 'mark': mm.group(), 'ctx': l.strip()})

out = ['# 《AI 未成之路》待核实清单 · 对齐 v1.23\n',
       '> 对应版本：`AI未成之路_定稿候选版_v1.23_20261107.md`｜更新：2026-11-07\n',
       f'> **★ 进展**：原 102 处 → **已消解 {102-len(items)} 处**，剩 **{len(items)} 处**。\n',
       '>\n> **已落地**：① 2.4 九场景卡片 40 格改通用问句（2.4 节 0 处）② 内部自评保留＋免责③ 量级表两处补来源说明 ④ RAG 引文改转述 ⑤ 清 3 处旧标记 ⑥ 补漏 6 处"约为采购两倍"。\n',
       '>\n> **剩余仍需老周回答 10 组**，其余为写作纪律声明（保留即可）。\n', '\n---\n']
order = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '附', '全', '版', 'c']
def key(c):
    for i, p in enumerate(order):
        if c.startswith(p):
            return i
    return 99
g = collections.OrderedDict()
for it in items:
    g.setdefault(it['chap'], []).append(it)
n = 0
for ch, lst in sorted(g.items(), key=lambda kv: key(kv[0])):
    out.append(f'\n## 【{ch}】（{len(lst)} 处）\n')
    out.append('| 序 | 行号 | 标记 | 上下文摘要 | 回复 |')
    out.append('|---|---|---|---|---|')
    for it in lst:
        n += 1
        ctx = it['ctx'].replace('|', '｜')
        if len(ctx) > 110:
            ctx = ctx[:110] + '…'
        out.append(f"| {n} | {it['line']} | {it['mark']} | {ctx} | |")
out.append(f'\n---\n\n**合计 {n} 处。**\n')
open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print(f'✓ {OUT}: {len(items)} 处')
