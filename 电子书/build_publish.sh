#!/usr/bin/env bash
# 《数据治理实战》出版形态构建脚本（可复现）
# 用法：bash 电子书/build_publish.sh
# 产出：数据治理实战_出版版.html（由 tools/parser.py + tools/assemble.py 生成）
#       数据治理实战_出版版.epub
#       数据治理实战_出版版_A5.pdf
set -euo pipefail
cd "$(dirname "$0")"

echo "▶ 1/4 Markdown → HTML"
python3 tools/parser.py
python3 tools/assemble.py

echo "▶ 2/4 HTML → EPUB3"
pandoc 数据治理实战_出版版.html \
  --from=html --to=epub3 \
  --split-level=2 \
  --toc --toc-depth=3 \
  --css=epub_style.css \
  --lua-filter=flatten_div.lua \
  --metadata title="数据治理实战：从二级分类到落地执行" \
  --metadata author="米悦说说" \
  --metadata lang="zh-CN" \
  --metadata description="主数据二级分类 · 源端治理四步法 · 从规划到落地的完整路径" \
  -o 数据治理实战_出版版.epub

echo "▶ 3/4 HTML → PDF (A5)"
chromium-browser --headless=new --no-sandbox --disable-gpu \
  --disable-dev-shm-usage --hide-scrollbars \
  --no-pdf-header-footer \
  --print-to-pdf-no-header \
  --virtual-time-budget=15000 \
  --print-to-pdf=数据治理实战_出版版_A5.pdf \
  "file://$(pwd)/数据治理实战_出版版.html" 2>/dev/null

echo "▶ 4/4 核验"
python3 - << 'PYEOF'
import re, zipfile, os, struct
h = open('数据治理实战_出版版.html', encoding='utf-8').read()
t = re.sub(r'<[^>]+>', '', re.sub(r'<style.*?</style>', '', h, flags=re.S))
print(f"  HTML  {os.path.getsize('数据治理实战_出版版.html')//1024}KB  外链{len(re.findall(r'https?://', h))}  img{h.count('<img')}  中文字{len(re.findall(r'[一-鿿]', t))}")
print(f"  ★脱敏扫描: 老周{len(re.findall('老周', t))}  待核实{len(re.findall(r'【待核实', t))}")
z = zipfile.ZipFile('数据治理实战_出版版.epub')
chs = [n for n in z.namelist() if re.match(r'EPUB/text/ch\d+\.xhtml$', n)]
et = ''.join(re.sub(r'<[^>]+>', '', z.read(n).decode('utf-8', 'replace')) for n in chs)
nav = z.read('EPUB/nav.xhtml').decode('utf-8', 'replace')
print(f"  EPUB  {os.path.getsize('数据治理实战_出版版.epub')//1024}KB  {len(chs)}章  目录{len(re.findall('<li', nav))}条  {len(et)}字")
d = open('数据治理实战_出版版_A5.pdf', 'rb').read()
m = re.search(rb'/MediaBox\s*\[([^\]]+)\]', d); v = [float(x) for x in m.group(1).split()]
print(f"  PDF   {os.path.getsize('数据治理实战_出版版_A5.pdf')//1024}KB  {len(re.findall(rb'/Type\s*/Page[^s]', d))}页  {(v[2]-v[0])/72*25.4:.0f}x{(v[3]-v[1])/72*25.4:.0f}mm")
PYEOF
echo "✅ 完成"
