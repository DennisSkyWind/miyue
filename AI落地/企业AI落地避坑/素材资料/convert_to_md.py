#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业AI落地文档资料：批量归档 + 脱敏 + MD 转换

用法：python3 convert_to_md.py <media_dir> <out_dir>

处理对象：docx / pptx / pdf / xlsx
脱敏策略见 DESENSITIZE_RULES.md
"""
import os, sys, re, json, hashlib

MEDIA = sys.argv[1] if len(sys.argv) > 1 else '/home/ubuntu/.copaw/media'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料'

# ────────────────────────── 脱敏规则 ──────────────────────────
# 顺序敏感：长词优先替换
RULES = [
    # 企业名
    ('华润三九研究院AI工程昆明分中心', '某集团研究院AI工程分中心'),
    ('华润三九研究院', '某集团研究院'),
    ('华润三九', '某头部医药集团'),
    ('昆药集团', '某大型药企'),
    ('昆药', '该药企'),
    ('国双科技', '某第三方技术服务商'),
    ('影刀RPA', '某RPA厂商RPA'),
    ('影刀', '某RPA厂商'),
    ('南方科技大学', '某高校'),
    ('深南科大', '某高校'),
    # 组织/部门
    ('智能与数字化中心', '数字化中心'),
    ('智数中心', '数字化中心'),
    ('营销中台运营中心', '营销中台'),
    ('生产运营中心', '生产运营部门'),
    ('集团审计部+合规部', '审计与合规部门'),
    ('乐成文化', '某文化业务品牌'),
    # 产品/人名
    ('昆小智', '数字员工A'),
    ('乐小智', '数字员工B'),
    ('周泓武', '项目负责人'),
    ('王克', '领导A'), ('蔡金勇', '领导B'), ('钟江', '领导C'), ('宋良玉', '领导D'),
    ('涂菲娜', '成员E'), ('原京', '成员F'), ('冯海洋', '成员G'), ('单海东', '成员H'),
    ('钱伟', '成员I'), ('黄相', '成员J'), ('段宏莉', '成员K'), ('李士峰', '成员L'),
    ('杨萌', '成员M'), ('李蕾', '成员N'), ('许睿', '成员O'),
    ('刘一凡', '成员P'), ('赵亚泉', '成员Q'),
    ('米妮', '家属'),
    # 金额模糊化（保留量级，去掉精确值）
    ('388万', '约400万'), ('9.4万', '约10万'), ('30万', '约30万'), ('48万', '约50万'),
    ('50万', '约50万'), ('5000元/花', '约5千元/节点'),
]
# 正则补充规则
REGEX_RULES = [
    (re.compile(r'\d{6,}'), 'XXXXXX'),                    # 长数字（编号/金额）
    (re.compile(r'1[3-9]\d{9}'), 'XXXX'),                # 手机号
    (re.compile(r'[\w.\-]+@[\w.\-]+'), 'xxx@xxx.com'),    # 邮箱
]

def desensitize(text):
    if not text:
        return text
    for a, b in RULES:
        text = text.replace(a, b)
    for pat, rep in REGEX_RULES:
        text = pat.sub(rep, text)
    return text

def md_escape_cell(s):
    return s.replace('|', '\\|').replace('\n', '<br>').strip()

# ────────────────────────── DOCX ──────────────────────────
def docx_to_md(path):
    import docx
    d = docx.Document(path)
    out = []
    body = d.element.body
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for child in body.iterchildren():
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            p = Paragraph(child, d)
            t = p.text.strip()
            if not t:
                continue
            style = (p.style.name or '')
            lvl = 0
            if style.startswith('Heading'):
                m = re.search(r'(\d+)', style)
                lvl = int(m.group(1)) if m else 1
            if lvl:
                out.append('#' * min(lvl + 1, 6) + ' ' + t)
            else:
                out.append(t)
            out.append('')
        elif tag == 'tbl':
            tb = Table(child, d)
            rows = []
            for r in tb.rows:
                cells = [md_escape_cell(c.text.replace('\n', ' ')) for c in r.cells]
                if any(cells):
                    rows.append(cells)
            if rows:
                ncol = max(len(r) for r in rows)
                rows = [r + [''] * (ncol - len(r)) for r in rows]
                out.append('| ' + ' | '.join(rows[0]) + ' |')
                out.append('|' + '---|' * ncol)
                for r in rows[1:]:
                    out.append('| ' + ' | '.join(r) + ' |')
                out.append('')
    return '\n'.join(out)

# ────────────────────────── PPTX ──────────────────────────
def _iter_shapes(shapes):
    """递归展开组合形状(group shape)，否则 PPT 中的分组文本会整段丢失。"""
    for sh in shapes:
        yield sh
        try:
            sub_shapes = getattr(sh, 'shapes', None)
        except Exception:
            sub_shapes = None
        if sub_shapes is not None:
            try:
                for sub in _iter_shapes(sub_shapes):
                    yield sub
            except Exception:
                pass


def pptx_to_md(path):
    from pptx import Presentation
    prs = Presentation(path)
    out = []
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for sh in _iter_shapes(slide.shapes):
            if sh.has_table:
                trows = []
                for r in sh.table.rows:
                    cells = [md_escape_cell(c.text.replace('\n', ' ')) for c in r.cells]
                    if any(cells):
                        trows.append(cells)
                if trows:
                    texts.append(('TBL', trows))
            elif sh.has_text_frame:
                t = sh.text_frame.text.strip()
                if t:
                    texts.append(('TXT', t))
        if not texts:
            continue
        out.append(f'\n## 第 {i} 页\n')
        for kind, val in texts:
            if kind == 'TXT':
                for ln in val.split('\n'):
                    ln = ln.strip()
                    if ln:
                        out.append(ln)
                        out.append('')
            else:
                ncol = max(len(r) for r in val)
                out.append('| ' + ' | '.join(val[0] + [''] * (ncol - len(val[0]))) + ' |')
                out.append('|' + '---|' * ncol)
                for r in val[1:]:
                    out.append('| ' + ' | '.join(r + [''] * (ncol - len(r))) + ' |')
                out.append('')
    return '\n'.join(out)

# ────────────────────────── PDF ──────────────────────────
def pdf_to_md(path):
    import fitz
    doc = fitz.open(path)
    out = []
    for i, page in enumerate(doc, 1):
        t = page.get_text().strip()
        if not t:
            continue
        out.append(f'\n## 第 {i} 页\n')
        out.append(t)
        out.append('')
    return '\n'.join(out)

# ────────────────────────── XLSX ──────────────────────────
def xlsx_to_md(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    out = []
    for sn in wb.sheetnames:
        ws = wb[sn]
        out.append(f'\n## 工作表：{sn}\n')
        rows = []
        for r in ws.iter_rows(values_only=True):
            vals = [md_escape_cell(str(c)) if c is not None else '' for c in r]
            while vals and not vals[-1]:
                vals.pop()
            if any(vals):
                rows.append(vals)
        if not rows:
            continue
        ncol = max(len(r) for r in rows)
        rows = [r + [''] * (ncol - len(r)) for r in rows]
        out.append('| ' + ' | '.join(rows[0]) + ' |')
        out.append('|' + '---|' * ncol)
        for r in rows[1:]:
            out.append('| ' + ' | '.join(r) + ' |')
        out.append('')
    return '\n'.join(out)

# ────────────────────────── 主流程 ──────────────────────────
# (源文件, 输出名, 标题, 分类, 说明)
MANIFEST = [
    ('035c6b19e3d56d89e0c388e9.docx', '01_数字员工大赛方案_2026第二届.md',
     '某大型药企 2026年（第二届）数字员工大赛方案', '组织与激励',
     '赛事背景、赛程安排、参赛价值与权益'),
    ('624789e1ea00d503c5aa1d8d.pptx', '02_数字员工大赛方案汇报_2026.md',
     '关于2026年某大型药企第二届数字员工大赛方案的汇报', '组织与激励',
     '含第一届大赛回顾与成果数据（报名队数、获奖数、上线机器人数量）'),
    ('3e8eb1d05b31c01b77756921.pdf', '03_数字员工大赛综合分析报告_第三方视角.md',
     '某大型药企AI创研数字员工大赛综合分析报告（第三方RPA厂商视角）', '外部评估',
     '25页。行业背景、项目难度与可行性分析、问题与建议。含第三方对参赛部门的独立统计'),
    ('45cbc23992e60bb656fd5999.docx', '04_数字员工管理指南V1.0.md',
     '某大型药企数字员工管理指南 V1.0', '组织与激励',
     '命名规范、身份与职责定义——RPA数字员工的"产品化"管理制度'),
    ('f763a9bcf434347beff9e6d5.docx', '05_AI创研项目激励实施方案.md',
     '某大型药企AI创研项目激励实施方案', '组织与激励',
     '评选范围、评选标准与流程、激励形式与兑现、风险控制与动态管理'),
    ('504ff2ca39e6c39e14d95e7a.docx', '06_AI创研项目激励计划.md',
     '某大型药企AI创研项目激励计划', '组织与激励',
     '计划框架、评选维度与权重（成果达成度60%/创新性20%/协作贡献20%）、季度节奏'),
    ('0cae911c3009e63c947c277a.docx', '07_项目管理考核激励方案试行.md',
     '某大型药企项目管理考核激励方案（试行）', '组织与激励',
     '过程考核/评优激励/结项考核三段式，里程碑节点激励与延期处置机制'),
    ('2b04257f8166049be5346871.pptx', '08_AI创研第一次大会_创研项目宣贯.md',
     '某大型药企AI创研第一次大会（创研项目宣贯）', '项目与运营',
     '4大目标、2大方向、5大板块、10领域；DeepSeek导入背景与宣贯安排'),
    ('db82d6321a1d44b060deb4b6.pptx', '09_AI创研项目工作方案_汇报.md',
     '关于某大型药企AI创研项目工作方案的汇报', '项目与运营',
     '背景/目标方向/实施路径方法/项目架构预算'),
    ('1befb1f956fb6b9ecb28324c.pptx', '10_AI创研项目阶段性汇报.md',
     '某大型药企AI创研项目阶段性汇报', '项目与运营',
     '各领域解决方案、DeepSeek导入研讨参与人次、下一阶段核心工作'),
    ('725ebaacd10b97b3a71c89e5.pptx', '11_项目阶段性复盘与规划_25年规划版.md',
     '24年项目阶段性复盘和25年项目规划（智能与数字化中心）', '项目与运营',
     '含预算说明与风险评估应对'),
    ('35f4255db023b60326af046f.pptx', '12_项目阶段性复盘与规划_含24年复盘版.md',
     '24年项目阶段性复盘和25年项目规划（含24年开展情况）', '项目与运营',
     '流程梳理成果（流程数量缩减/新增）、阶段成果投入费用'),
    ('82d6a276a948dbca16dd7557.pptx', '13_智数化顶层规划_使命愿景目标举措.md',
     '某大型药企智数化顶层规划（使命/愿景/目标/关键举措/能力支撑/组织体系）', '战略规划',
     '16页。使命愿景目标、关键举措、五大能力、支撑体系与组织升级'),
    ('72a232313794bc0d66b2e686.pptx', '14_某头部医药集团AI战略场景应用梳理_立项汇报.md',
     '某头部医药集团AI战略场景应用梳理项目 立项汇报', '战略规划',
     '28页。AI愿景蓝图解码、AI组织进化与架构升级、工作坊+战略解码+原型验证三位一体、项目预算与实施计划'),
    ('7698151a23214eb2372716ab.docx', '15_某集团研究院AI工程分中心章程V2.0.md',
     '某集团研究院AI工程分中心章程 V2.0（密级：内部资料）', '组织与制度',
     '161段。名称与性质、宗旨使命定位、职责分工——AI工程化组织落地样本'),
    ('03238d7645f65ff85695be21.docx', '16_会议议案签报单模板.md',
     '会议议案签报单（模板）', '组织与制度',
     '议题申报模板，含议题类型/列席人员/需审议会议类型字段'),
    ('bf55fd0dfa2f78440f42bb83.xlsx', '17_会议议题申报表_AI创研阶段性汇报.md',
     '某大型药企会议议题申报表（含AI创研项目阶段性汇报议题）', '组织与制度',
     '议题申报表结构与字段定义'),
    ('002377b810b780dc6a6f2400.docx', '18_会议议题申报表_空白模板.md',
     '会议议题申报表（空白模板）', '组织与制度',
     '表格模板，8列字段定义'),
    ('d68d67df02c207bbd49785a9.pptx', '19_数字员工形象统计结果.md',
     '某大型药企数字员工形象统计结果', '数据素材',
     '7页。性别与年龄分布、姓名统计——RPA命名偏好的一手数据'),
    ('06fe208e0c776778bd8e78a5.png', '20_图_数字员工相关长图A.png', '（图片）', '图素材',
     '原始图片，尺寸7538x4708。未做内容识别，需人工确认'),
    ('95e58046fd4b600f302bfaf6.png', '21_图_数字员工相关长图B.png', '（图片）', '图素材',
     '原始图片，尺寸10776x4958。未做内容识别，需人工确认'),
]

def main():
    os.makedirs(OUT, exist_ok=True)
    index = []
    for src, dst, title, cat, desc in MANIFEST:
        sp = os.path.join(MEDIA, src)
        if not os.path.exists(sp):
            print(f'✗ 缺失 {src}')
            continue
        ext = src.rsplit('.', 1)[-1].lower()
        try:
            if ext == 'docx':
                body = docx_to_md(sp)
            elif ext == 'pptx':
                body = pptx_to_md(sp)
            elif ext == 'pdf':
                body = pdf_to_md(sp)
            elif ext == 'xlsx':
                body = xlsx_to_md(sp)
            else:
                shutil_copy(sp, os.path.join(OUT, dst))
                index.append(dict(file=dst, title=title, cat=cat, desc=desc,
                                  chars=0, words=0, kind='图片原文件'))
                print(f'📷 {dst} (图片直存)')
                continue
        except Exception as e:
            print(f'✗ 转换失败 {src}: {e}')
            continue
        body_clean = desensitize(body)
        cn = len(re.findall(r'[\u4e00-\u9fff]', body_clean))
        hdr = (f'# {title}\n\n'
               f'> **归档说明**｜来源：{desc}｜分类：{cat}\n'
               f'> **脱敏状态**：已完成企业名/人名/金额脱敏，真实名统一替换为泛化表述\n'
               f'> **转换来源**：{src}\n'
               f'> **用途**：《企业AI落地实战》素材库\n\n---\n\n')
        full = hdr + body_clean
        with open(os.path.join(OUT, dst), 'w', encoding='utf-8') as f:
            f.write(full)
        index.append(dict(file=dst, title=title, cat=cat, desc=desc,
                          chars=cn, words=len(body_clean), kind=ext.upper()))
        print(f'✅ {dst}  {cn} 中文字')

    with open(os.path.join(OUT, '_索引.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f'\n共 {len(index)} 个文件归档到 {OUT}')

def shutil_copy(a, b):
    import shutil
    shutil.copy2(a, b)

if __name__ == '__main__':
    main()
