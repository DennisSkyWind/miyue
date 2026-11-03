#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《AI 未成之路》对外定稿候选版。

与 build_ebook.py 的差别：剥掉所有内部工作痕迹，只留读者要看的正文。
- 删除各章末尾的「本稿为 Dx 初稿」注
- 删除各章末尾的「本章待核实清单」表（正文中的【待核实】标记保留）
- 删除「附：本章素材与来源索引」表
- 删除附录 G.1（内部素材来源对应，标注"定稿前删除"）
- 删除串联稿里的「待定稿清单」与「版本记录」（移到书末内部工作稿）
- 删除串联稿里的「三条主线索引」（内部拆条工具）
用法：python3 build_final.py
"""
import re
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
DRAFT = BASE / "草稿"
OUT = BASE / "AI未成之路_定稿候选版_v1.13_20261103.md"

CHAPTERS = [
    ("引言_AI落地的真相_D1.md", "引言"),
    ("第一章_五个坑.md", "第一章"),
    ("第二章_场景全景.md", "第二章"),
    ("第三章_数据准备.md", "第三章"),
    ("第四章_技术方案.md", "第四章"),
    ("第五章_五步法.md", "第五章"),
    ("第六章_算账.md", "第六章"),
    ("第七章_合规与风险.md", "第七章"),
    ("第八章_真实案例复盘_D3.md", "第八章"),
    ("第九章_数字员工建设_D3.md", "第九章"),
    ("附录_工具箱.md", "附录"),
]

HEADER = """# AI 未成之路

> **一个做了三年 AI 创研的项目负责人，写下的"没做成"记录**
>
> ---

**副标题**：为什么大多数企业的 AI 都没做成，以及怎么认出自己正在哪个坑里

**作者**：某大型制造企业 智能与数字化中心 项目负责人

**版本**：定稿候选稿 v1.13（2026-11-03）｜全书约 15 万中文字

---

## 全书目录

| 章 | 标题 | 这章要回答什么 |
|---|---|---|
| **0** | 引言 | AI 的量级该怎么估，这本书写给谁 |
| **1** | 企业 AI 落地的 5 个坑 | 输的都不是模型不够强 |
| **2** | 场景选择：先选事，再选技术 | 场景选错的代价远大于技术选错 |
| **3** | 数据准备：把数据治理翻译成 AI 能听懂的话 | 数据没准备好就想上 AI |
| **4** | 技术方案：三棵决策树 | "哪个模型更强"是伪问题 |
| **5** | 企业 AI 落地五步法 | 从"方案通过"到"真的有人每天用" |
| **6** | 算账：老板视角的三问 | AI 项目不赚钱就等于没做 |
| **7** | 合规与风险：哪条线不能碰 | AI 的位置必须按出错代价来定 |
| **8** | 真实案例复盘 | 三个成的，一个没成的，一个半失败的 |
| **9** | 数字员工建设 | 数字员工不是系统，是岗位 |
| **附录** | 工具箱 A–H | 能直接抄走的表 |

---

### 阅读提示

- 只想看真相与结论 → 直接读**第八章**
- 正负责一个在跑的 AI 项目 → 读**第五章 5.4 止损条件**
- 在纠结要不要做某个场景 → 读**第二章、第三章**的判断表
- 想知道制造业六个环节各自的 AI 适合度 → 读**第八章 8.0.1**
- 想要能直接抄走的表格 → 读**附录**
- 想要能直接抄走的表格 → 读**附录**
- 手上有个新场景，先问一句"这事该不该做" → 读**附录 H 场景筛选表**（12 问，5 分钟）
---

### 本书纪律

不编造未确认的案例、金额与效果数字；不确定处一律标注【待核实】；企业名、人名、产品名、金额与内部精确数字已做泛化处理。

**本书结论不是任何一家企业的专利**——素材来自一家大型制造企业三年的实践，但书里讲的是制造业六个环节的共性规律。

"""

FOOTER = """

---

## 版权与免责声明

- 本书案例均来自作者亲历项目与企业内部实践，已对真实企业名、人名、产品名、金额与内部精确数字做泛化处理，仅保留可公开的量级、比例与效益指标。
- 书中标注【待核实】的内容为作者尚未最终确认的部分，正式出版前将逐条校订。
- 书中涉及合规、数据分级与 AI 输出的责任划分，仅为工程与管理层面的经验总结，**不构成法律或合规意见**；具体项目请与贵公司的法务、质量、信息安全部门共同确认。
- "某大型制造企业""某制造业集团""某头部医药集团"等均为泛化称呼，与任何具体企业无对应关系。
- 文中出现的开源系统与商业平台名称，用于说明技术路线形态，不构成对任何产品的推荐或评价。

---

*《AI 未成之路》定稿候选稿 v1.13｜2026-11-03*
"""


def strip_internal(md: str) -> str:
    """剥掉章末的工作痕迹。"""
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # 1) 「本章待核实清单」及其后的表格 → 整节删除
        if re.match(r"^#{2,4}\s*.*待核实清单", line):
            i += 1
            # 跳过到下一个标题
            while i < n and not re.match(r"^#{1,4}\s", lines[i]):
                i += 1
            continue

        # 2) 「附：本章素材与来源索引」→ 整节删除
        if re.match(r"^#{2,4}\s*附[:：]\s*本章素材与来源索引", line):
            i += 1
            while i < n and not re.match(r"^#{1,4}\s", lines[i]):
                i += 1
            continue

        # 3) 章末初稿注（斜体一行，含"初稿"/"本稿为 D"）
        if re.match(r"^\*.*(初稿|本稿为 D|增补初稿).*\*$", line.strip()) and i > n - 8:
            i += 1
            continue

        out.append(line)
        i += 1
    return "\n".join(out)


def strip_connect(md: str) -> str:
    """串联稿：删内部工作工具节。"""
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if re.match(r"^#{2,3}\s*(待定稿清单|版本记录|三条主线的章节索引|使用说明)", line):
            i += 1
            while i < n and not re.match(r"^#{1,2}\s", lines[i]):
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def strip_appendix_g(md: str) -> str:
    """附录 G.1 内部素材来源表 → 删除（保留 G.2/G.3）。"""
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if re.match(r"^###\s*G\.1\s", lines[i]):
            i += 1
            while i < n and not re.match(r"^#{2,3}\s", lines[i]):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def main():
    parts = [HEADER]
    for fn, label in CHAPTERS:
        p = DRAFT / fn
        if not p.exists():
            print(f"!! 缺文件 {fn}")
            continue
        body = p.read_text(encoding="utf-8")
        # 去掉文件自身的一级标题
        body = re.sub(r"^#\s+.*\n", "", body, count=1)
        body = strip_internal(body)
        if fn == "附录_工具箱.md":
            body = strip_appendix_g(body)
        parts.append(body.strip() + "\n")

    # 串联稿（阅读指南）
    cf = DRAFT / "全书串联稿.md"
    if cf.exists():
        body = cf.read_text(encoding="utf-8")
        body = re.sub(r"^#\s+.*\n", "", body, count=1)
        body = strip_connect(body)
        parts.append(
            "\n---\n\n## 阅读指南：本书怎么读\n\n" + body.strip() + "\n"
        )

    parts.append(FOOTER)
    text = "\n".join(parts)

    # 清理多余空行
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    OUT.write_text(text, encoding="utf-8")

    cn = len(re.findall(r"[一-鿿]", text))
    print(f"✅ {OUT.name}  总行数 {text.count(chr(10))}  中文字 {cn:,}")
    print(f"   待核实 {text.count('【待核实】')}  老周 {text.count('老周')}")
    for kw in ["周泓武", "米妮", "云南大学", "猫群"]:
        if kw in text:
            print(f"   !! 敏感命中: {kw}")


if __name__ == "__main__":
    main()
