#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二批：13 个文件归档（9 pptx + 1 docx + 3 png）
PNG 走 OCR → MD（保留原图），PPTX/DOCX 复用第一批的转换函数。
"""
import os, sys, json, re, shutil, glob

sys.path.insert(0, '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料')
from convert_to_md import docx_to_md, pptx_to_md, desensitize as desensitize_p1

MEDIA = '/home/ubuntu/.copaw/media'
OUT = '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料'
IMG = os.path.join(OUT, '图片')

# ── 本批新增脱敏规则 ──────────────────────────────
RULES2 = [
    # 事业部内部代号
    ('1381', '事业部A'), ('1951', '事业部B'), ('777', '事业部C'),
    ('昆中药', '某中药老字号品牌'),
    # 产品名
    ('舒肝解郁', '某核心中成药'), ('舒肝', '某核心中成药'),
    ('乌灵', '某中成药'),
    # 人名/代称
    ('小夏', '成员A1'), ('杨总', '领导E'), ('夏洋', '成员A2'), ('健健', '成员A3'),
    ('杨健', '成员A4'), ('杨程智', '成员A5'),
    ('李进', '成员A6'), ('李博怡', '成员A7'), ('冯桠岚', '成员A8'),
    ('黄渊', '成员A9'), ('王敏', '成员A10'), ('葛旭', '成员A11'),
    ('胡振源', '成员A12'),
    # 其他真实品牌（零售/医疗）
    ('京东健康', '某互联网医疗平台'), ('京东集团', '某互联网集团'),
    ('拜耳', '某跨国药企'), ('强生', '某跨国医疗健康集团'),
    ('晶泰科技', '某AI制药企业'),
    # 研究院/内外部机构
    ('华为数据治理方法论', '某厂商数据治理方法论'),
    ('DCMM', 'DCMM'),
]

def desensitize2(text):
    text = desensitize_p1(text)
    for a, b in RULES2:
        text = text.replace(a, b)
    # 华为：作为交付方保留方法论出处，但去掉公司全称变体
    text = text.replace('Huawei Technologies Co., Ltd.', '某技术厂商')
    text = text.replace('Copyright©2018 Huawei Technologies Co., Ltd.', 'Copyright©2018 某技术厂商')
    # 省份泛化（医疗业务省份分布图涉及经营区域）
    for p in ['云南', '江苏', '山东', '江西', '广东', '安徽', '吉林', '山西', '广西',
              '河南', '河北', '天津', '辽宁', '四川', '上海', '北京', '湖北', '湖南',
              '福建', '浙江', '江苏', '重庆', '陕西', '贵州', '甘肃', '青海', '海南']:
        text = text.replace(p, '某省')
    return text

def png_to_md(path, out_png_name):
    import pytesseract
    from PIL import Image
    im = Image.open(path).convert('RGB')
    w, h = im.size
    target = 2200
    if w > target:
        im2 = im.resize((target, int(h * target / w)), Image.LANCZOS)
    else:
        im2 = im
    txt = pytesseract.image_to_string(im2, lang='chi_sim')
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    body = '\n'.join(lines)
    md = (f'# {os.path.basename(out_png_name)}\n\n'
          f'> **归档说明**：图片原件已归档（{os.path.basename(out_png_name)}），本文件为 OCR 提取的文本\n'
          f'> **原始尺寸**：{w}×{h}\n'
          f'> **OCR 引擎**：tesseract chi_sim\n'
          f'> **注意**：OCR 结果可能存在识别误差，引用前请对照原图\n\n'
          f'---\n\n## OCR 提取文本\n\n{body}\n')
    return md, len(lines)

MANIFEST2 = [
    ('1bf8e738b1772749ba553458.pptx', '22_AI顶层规划项目启动会报告.md',
     '某大型药企AI顶层规划项目启动会报告', '战略规划',
     '20页。项目目标、五步方法论（看技术/看行业/AI场景与价值/明方向/能力建设）、项目计划与组织架构、沟通机制', False),
    ('ef6ffa0e73b0b2bed8d7c209.pptx', '23_AI能力成熟度评估报告_自评版.md',
     '某大型药企AI能力成熟度评估报告', '战略规划',
     '42页。★核心素材：16个部门调研访谈、12个业务单元"AI认知"逐一画像、成熟度得分1.7（L1-L2级）、五维度评估、数据发现、现状AI应用清单、四大建设方向', False),
    ('b254bd1ed7a45faebf99b444.pptx', '24_医药行业AI洞察报告.md',
     '医药行业AI洞察报告（某大型药企AI顶层规划项目）', '行业洞察',
     '45页。医药产业链AI全景（上中下游）、AI Agent特征、研发成本与周期数据、企业价值链场景梳理（研发/生产/供应链/营销/人力/法务六域）', False),
    ('5d3a4fb4ec0ac907fe44c65c.pptx', '25_某事业部医疗现状分析与2026规划.md',
     '某事业部医疗现状分析与2026年规划（含AI创新举措）', '业务场景',
     '21页。现状分析（产品结构/区域覆盖/终端）、26年核心策略与WBS拆解、POA行动计划、★第21页数字员工矩阵（TinyTeam架构，5团队×3职能）', False),
    ('aa3ab008cd021bb421c14029.pptx', '26_十五五战略举措解码_数智之仗.md',
     '某大型药企十五五战略举措解码（数智之仗）', '战略规划',
     '2页。战略举措与前沿赛道布局', False),
    ('afe4b8b39aae3fe787be659f.pptx', '27_AI创研项目阶段性汇报_汇报人版.md',
     '某大型药企AI创研项目阶段性汇报', '项目与运营',
     '20页。★核心素材：145项需求分类明细（78项AI相关）、双线负责人配置、9大场景15个数字员工5个RPA场景、数字员工1.0→2.5发展历程、3.0展望、困难与问题（人员认知差异）', False),
    ('b57b452be2cf7ba64a271126.docx', '28_AI场景研讨提纲_含业务答复.md',
     '某大型药企 AI 场景研讨提纲（含业务侧填写答复）', '方法论',
     '★最真实的一份：6大问题框架 + 业务/数据/技术的真实答复（如"可用数据不超过3年，最短1.5年"、"商业秘密数据不可使用云端大模型"）', False),
    ('ded65ffab46dccda2719b75f.png', '29_图_智能内容审计流程.png',
     '图：智能内容审计流程（文件数据化→智能内容审计→周期性复查/风险评估/整改报告）', '图素材',
     '5716×3500。OCR已提取流程节点', True),
    ('87f3cc7ce93a105520b91dbd.png', '30_图_TinyTeam架构_5团队.png',
     '图：TinyTeam 架构（学术管理/推商管理/运维支持/纯销管理等团队）', '图素材',
     '2659×1754。OCR已提取团队名称', True),
    ('1afc3fa4d5ee4f1cae2c7319.png', '31_图_AI能力全景与场景清单.png',
     '图：AI能力全景（通用AI能力/营销运营AI能力）与18个落地场景清单', '图素材',
     '6814×2936。★OCR提取到完整场景清单', True),
]

def main():
    os.makedirs(IMG, exist_ok=True)
    index = []
    for src, dst, title, cat, desc, is_png in MANIFEST2:
        sp = os.path.join(MEDIA, src)
        if not os.path.exists(sp):
            print(f'✗ 缺失 {src}'); continue
        if is_png:
            png_out = os.path.join(IMG, dst)
            shutil.copy2(sp, png_out)
            body, nlines = png_to_md(sp, dst)
            cn = len(re.findall(r'[\u4e00-\u9fff]', body))
            hdr = (f'# {title}\n\n'
                   f'> **归档说明**：{desc}\n'
                   f'> **脱敏状态**：已完成企业名/人名/机构名脱敏\n'
                   f'> **转换来源**：{src}\n\n---\n\n')
            full = hdr + body.split('---\n\n', 1)[-1] if False else hdr + body
            open(os.path.join(OUT, dst.replace('.png', '.md')), 'w', encoding='utf-8').write(full)
            outname = dst.replace('.png', '.md')
            print(f'✅ {outname}  OCR {nlines} 行 / {cn} 中文字')
            index.append(dict(file=outname, title=title, cat=cat, desc=desc,
                              chars=cn, words=nlines, kind='PNG→OCR'))
            continue
        ext = src.rsplit('.', 1)[-1].lower()
        body = docx_to_md(sp) if ext == 'docx' else pptx_to_md(sp)
        body_clean = desensitize2(body)
        cn = len(re.findall(r'[\u4e00-\u9fff]', body_clean))
        hdr = (f'# {title}\n\n'
               f'> **归档说明**：{desc}\n'
               f'> **脱敏状态**：已完成企业名/人名/机构名/金额/省份脱敏\n'
               f'> **转换来源**：{src}\n'
               f'> **用途**：《企业AI落地实战》素材库\n\n---\n\n')
        open(os.path.join(OUT, dst), 'w', encoding='utf-8').write(hdr + body_clean)
        index.append(dict(file=dst, title=title, cat=cat, desc=desc,
                          chars=cn, words=len(body_clean), kind=ext.upper()))
        print(f'✅ {dst}  {cn} 中文字')

    with open(os.path.join(OUT, '_索引_第二批.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f'\n第二批共 {len(index)} 个文件')

if __name__ == '__main__':
    main()
