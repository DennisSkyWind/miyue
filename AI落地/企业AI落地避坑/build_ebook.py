#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建《AI 未成之路》合订稿：从 草稿/ 各章文件拼接，输出 AI未成之路_合订稿_v1.0.md
用法：python3 build_ebook.py
"""
import re
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
DRAFT = BASE / "草稿"
OUT = BASE / "AI未成之路_合订稿_v1.0.md"

CHAPTERS = [
    ("引言_AI落地的真相_D1.md", None),
    ("第一章_五个坑.md", None),
    ("第二章_场景全景.md", None),
    ("第三章_数据准备.md", None),
    ("第四章_技术方案.md", None),
    ("第五章_五步法.md", None),
    ("第六章_算账.md", None),
    ("第七章_合规与风险.md", None),
    ("第八章_真实案例复盘_D3.md", None),
    ("第九章_数字员工建设_D3.md", None),
    ("附录_工具箱.md", None),
]

HEADER = """# AI 未成之路

> **一个做了三年 AI 创研的项目负责人，写下的"没做成"记录**
>
> ---
>
> **副标题**：为什么大多数企业的 AI 都没做成，以及怎么认出自己正在哪个坑里
>
> **形态**：电子书（本稿）→ 后续拆条做短视频 → 丰富后出版/售卖
> **版本**：v1.2 修订稿（2026-10-31）｜全书约 11 万字
> **作者**：某大型制造企业 智能与数字化中心 项目负责人
>
> ---
## 全书目录

0. 引言
1. 第一章 企业 AI 落地的 5 个坑
2. 第二章 场景选择
3. 第三章 数据准备
4. 第四章 技术方案
5. 第五章 企业 AI 落地五步法
6. 第六章 算账
7. 第七章 合规与风险
8. 第八章 真实案例复盘
9. 第九章 数字员工建设
10. 附录 工具箱（A-G：场景评估表 / ROI 表 / 模型台账 / 三张清单 / 风险自查 / 名词速查 / 延伸阅读）

> **阅读提示**
> · 只想看真相与结论 → 直接读**第八章**
> · 正负责一个在跑的 AI 项目 → 读**第五章 5.4 止损条件**
> · 在纠结要不要做某个场景 → 读**第二章、第三章**的判断表
> · 想知道制造业六个环节各自的 AI 适合度 → 读**第八章 8.0.1**
> · 想要能直接抄走的表格 → 读**附录**
>
> **本书纪律**：不编造未确认的案例、金额与效果数字；不确定处一律标注【待核实】；企业名、人名、产品名、金额与内部精确数字已做泛化处理。
>
> **本书结论不是任何一家企业的专利**——素材来自一家大型制造企业三年的实践，但书里讲的是制造业六个环节的共性规律。
"""

FOOTER = """
---

## 版权与免责声明

- 本书案例均来自作者亲历项目与企业内部实践，已对真实企业名、人名、产品名、金额与内部精确数字做泛化处理，仅保留可公开的量级、比例与效益指标。
- 书中标注【待核实】的内容为作者尚未最终确认的部分，正式出版前将逐条校订。
- 书中涉及合规、数据分级与 AI 输出的责任划分，仅为工程与管理层面的经验总结，**不构成法律或合规意见**；具体项目请与本公司法务、质量、信息安全部门共同确认。
- "某大型制造企业""某制造业集团""某头部医药集团"等均为泛化称呼，与任何具体企业无对应关系。
"""


def strip_h1(text: str) -> str:
    """去掉文件开头的一级标题（章名），保留正文与元信息块。"""
    lines = text.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("# "):
        lines = lines[i + 1:]
    # 去掉紧随其后的空行
    while lines and not lines[0].strip():
        lines = lines[1:]
    return "\n".join(lines)


def main():
    parts = [HEADER.rstrip(), ""]
    for fname, _ in CHAPTERS:
        p = DRAFT / fname
        if not p.exists():
            print(f"!! 缺失: {p}")
            continue
        body = strip_h1(p.read_text(encoding="utf-8"))
        parts.append("\n---\n")
        parts.append(body.rstrip())
        parts.append("")
    parts.append(FOOTER)
    out = "\n".join(parts)
    OUT.write_text(out, encoding="utf-8")
    cn = len(re.findall(r"[\u4e00-\u9fff]", out))
    print(f"✅ {OUT.name}  总行数 {out.count(chr(10)) + 1}  中文字 {cn:,}")


if __name__ == "__main__":
    main()
