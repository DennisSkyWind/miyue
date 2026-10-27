#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四批：9 个文件（3 docx + 3 xlsx + 1 xls + 2 pptx）"""
import os, sys, json, re
sys.path.insert(0, '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料')
from convert_to_md import docx_to_md, pptx_to_md, md_escape_cell
from convert_batch2 import desensitize2

MEDIA = '/home/ubuntu/.copaw/media'
OUT = '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料'


def xls_to_md(path):
    import xlrd
    b = xlrd.open_workbook(path)
    out = []
    for sn in b.sheet_names():
        s = b.sheet_by_name(sn)
        out.append(f'\n## 工作表：{sn}\n')
        rows = []
        for i in range(s.nrows):
            vals = [md_escape_cell(str(v)) if v not in ('', None) else '' for v in s.row_values(i)]
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


MANIFEST4 = [
    ('60fbc880f3cce1fb6a53ef82.docx', '34_制药企业AI合同审核实施方案.md',
     '制药企业AI合同审核实施方案', '技术方案',
     '★核心素材：目标基线（单份审核2-3天→30分钟内、风险识别率60%→95%+）、长文档模型选型（QwQ-32B 13万token / DeepSeek-R1 差异定位）、'
     'Dify工作流三节点设计、75个合同要素提取规则、泛微OA双向集成（createWorkflow/changeFieldValue）、'
     '三级递进审查引擎（字段提取→三维风险→医药专属场景）、审计日志23项元数据与存证、三大自动化场景', 'docx'),
    ('2eccb0431c9e90fd7cc1c99e.xls', '35_岗位需求调研底稿_调研计划与117条需求.md',
     '岗位需求调研底稿（调研计划 + 岗位需求合并表 + 纯销管理需求）', '原始工作底稿',
     '★★★最原始的一手底稿：2025-12-10 逐岗位访谈调研计划（含真实姓名/时间/地点/会议号）、'
     '117 行岗位需求合并表（姓名/岗位/职责/主要工作/工作流程步骤/AI需求）、'
     '纯销管理需求表（含"与医疗场景衔接""智能体的使用建议"列）', 'xls'),
    ('06c6876ad926b78f998b4317.xlsx', '36_岗位工作梳理表_AI需求判断列.md',
     '岗位工作梳理表（含初步判断与AI需求列）', '原始工作底稿',
     '117行×7列。★含"初步判断"列（哪些可RPA、哪些需AI）与"AI需求"列——'
     '这是"AI 需求从岗位层面收集"的第一手判断记录', 'xlsx'),
    ('835cb0d77cbdc643d17f196f.xlsx', '37_岗位工作梳理表_智能体使用建议.md',
     '岗位工作梳理表（含与医疗场景衔接与智能体使用建议）', '原始工作底稿',
     '两个工作表。★含"智能体的使用建议"列（逐岗位给出用什么智能体、怎么用）', 'xlsx'),
    ('c36885aa5163d07c9410a708.xlsx', '38_试点数据情况表_场景数据盘点.md',
     '试点数据情况表（场景所需数据盘点）', '原始工作底稿',
     '★第三章证据：按品规列出内部数据（发货明细表/终端纯销表/经销商进销存报表）、'
     '数据周期、核心字段、数据量、数据质量、数据来源系统', 'xlsx'),
    ('e4b9a6a30c7725f987f49cef.pptx', '39_单一品种AI销售预测试点实施计划书.md',
     '某大型药企单一品种药品 AI 销售预测试点项目实施计划书', '项目与运营',
     '13页。★含真实问题描述：传统Excel预测误差率超25%、80%客户拜访沦为无效拜访；'
     '技术选型与模型架构、测试部署→运行优化、数据需求与来源、资源规划、风险管理、预期成果（定量）', 'pptx'),
    ('54513e2d415e4983231fcf72.pptx', '40_数字人架构与三阶段建设规划.md',
     '数字人架构与建设规划', '产品与商业',
     '3页。数字人"硬底座"、三阶段扩展路线（3个基础场景试点1.0→结合IT系统全场景扩展2.0→联合生态扩展3.0）、'
     '生态合作"服务+医疗+医药"闭环', 'pptx'),
    ('cc7ff67d63581f7e369279e1.docx', '41_销项系统数据库清单.md',
     '销项系统数据库清单（表结构与字段）', '数据资产',
     '44段 + 42张表。发票红字信息主表/明细表、全电发票主信息表、流水单主表/明细表等——'
     '第三章"数据资产盘点"的实物样本', 'docx'),
]


def main():
    idx = []
    for src, dst, title, cat, desc, kind in MANIFEST4:
        sp = os.path.join(MEDIA, src)
        if not os.path.exists(sp):
            print(f'✗ 缺失 {src}'); continue
        if kind == 'docx':
            body = docx_to_md(sp)
        elif kind == 'pptx':
            body = pptx_to_md(sp)
        elif kind == 'xlsx':
            body = xlsx_to_md(sp)
        else:
            body = xls_to_md(sp)
        body = desensitize2(body)
        cn = len(re.findall(r'[\u4e00-\u9fff]', body))
        note = ''
        if '待核实' in title or cat in ('技术方案', '原始工作底稿'):
            note = ('> ⚠️ **数字性质提示**：本文件含大量**目标值/技术指标/调研记录**。'
                    '属设计方案或工作底稿的，进入书稿前须由老周确认哪些是实测、哪些是计划，'
                    '未确认的一律标 `【待核实】`。\n')
        hdr = (f'# {title}\n\n'
               f'> **归档说明**：{desc}\n'
               f'> **脱敏状态**：已完成企业名/人名/机构名脱敏\n'
               f'{note}'
               f'> **转换来源**：{src}\n\n---\n\n')
        open(os.path.join(OUT, dst), 'w', encoding='utf-8').write(hdr + body)
        print(f'✅ {dst}  {cn} 中文字')
        idx.append(dict(file=dst, title=title, cat=cat, desc=desc,
                        chars=cn, words=len(body), kind=kind.upper()))
    p = os.path.join(OUT, '_索引_第二批.json')
    old = json.load(open(p, encoding='utf-8'))
    json.dump(old + idx, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\n第四批 {len(idx)} 个文件')


if __name__ == '__main__':
    main()
