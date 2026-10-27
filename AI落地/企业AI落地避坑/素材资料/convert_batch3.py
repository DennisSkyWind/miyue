#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三批：33 号 AI 陪伴产品设计路线报告（docx）"""
import os, sys, json, re
sys.path.insert(0, '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料')
from convert_to_md import docx_to_md
from convert_batch2 import desensitize2

MEDIA = '/home/ubuntu/.copaw/media'
OUT = '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料'

src = 'fc6d1082f3321ac389afe512.docx'
dst = '33_AI陪伴产品设计路线报告.md'
title = '某大型药企 AI 陪伴产品设计路线报告（银发健康硬件 + 陪伴IP）'

body = docx_to_md(os.path.join(MEDIA, src))

# 本文件专属规则：公司自身的经营目标值模糊化；竞争对手公开市场售价保留
RULES_LOCAL = [
    # 陪伴IP 与数字员工区分（本文件语境下 IP 需可读）
    ('数字员工B', '陪伴IP'),
    # 公司自身成本/毛利/留存等目标值 → 模糊化
    ('BOM成本严格控制在¥210.00以内', 'BOM成本控制在约200元以内'),
    ('毛利率控制在45%以上', '毛利率目标在40%以上'),
    ('5-8%净利润', '约5-8%净利润'),
    ('提升用户付费意愿25%', '提升用户付费意愿约25%'),
    ('留存率达80%', '留存率目标约80%'),
    ('首批采购量10万颗', '首批采购量10万颗量级'),
    ('销量突破5万台', '销量目标约5万台'),
    ('B端合作机构≥100家', 'B端合作机构目标约100家'),
    ('MTBF>5000 小时', 'MTBF目标约5000小时'),
]
for a, b in RULES_LOCAL:
    body = body.replace(a, b)

body = desensitize2(body)

cn = len(re.findall(r'[\u4e00-\u9fff]', body))
hdr = (
    f'# {title}\n\n'
    f'> **归档说明**：AI 陪伴产品（银发健康）设计路线报告。含市场分析、产品矩阵（低端戒指/手环/音响 + '
    f'中高端陪伴智能屏/医药销售智能屏/可移动机器人）、技术架构（端侧推理、知识图谱、跨设备协同）、'
    f'三阶段演进计划、商业闭环与生态构建\n'
    f'> ⚠️ **重要标注**：本文件是**产品设计/商业规划稿**，其中绝大多数数字是**设计目标、假设值或第三方市场预测**，'
    f'**不是实际经营数据**。任何数字进入书稿前必须标 `【待核实】` 并由老周确认。\n'
    f'> **脱敏状态**：企业名/人名/机构名已脱敏；公司自身成本与经营目标值已模糊化；'
    f'竞争对手公开市场售价（如某品牌智能戒指 199/999/2480 元）作为公开市场信息保留\n'
    f'> **转换来源**：{src}\n\n---\n\n')

open(os.path.join(OUT, dst), 'w', encoding='utf-8').write(hdr + body)
print(f'✅ {dst}  {cn} 中文字')

idx = json.load(open(os.path.join(OUT, '_索引_第二批.json'), encoding='utf-8'))
idx.append(dict(file=dst, title=title, cat='产品与商业',
                desc='AI陪伴产品设计路线报告：市场分析/六类硬件产品矩阵/技术架构/三阶段演进/商业闭环',
                chars=cn, words=len(body), kind='DOCX'))
json.dump(idx, open(os.path.join(OUT, '_索引_第二批.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('索引已更新')
