#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脱敏第二遍：补齐第一遍未覆盖的人名、剩余真实企业名、机构名。
人名按稳定编号替换为「成员NN」，编号由姓名排序决定，保证可重复、可反查。
"""
import re, glob, os, json

OUT = '/home/ubuntu/miyue/AI落地/企业AI落地避坑/素材资料'

# ── 剩余真实企业/机构/品牌名 ─────────────────────────────
ORG_RULES = [
    ('天士力', '某医药集团'),
    ('上药', '某医药集团'),
    ('三九', '该集团'),
    ('乐成', '某文化品牌'),
    ('中邮证券', '某证券研究机构'),
    ('云南省昆明市', '某省某市'),
    ('云南省', '某省'),
    ('云南', '某省'),
]

# ── 确认的人名清单 ────────────────────────────────────────
NAMES = """陈娇 毛健 刘晋宇 杨泽标 赵威 黄思杰 左婕 马瑞 鲁梦杰 李景涛 董雷
余汇涓 张然 赵小康 余方元 李双凤 郭晓蓉 吴娜 罗慧 李芸莹 程丽敏 李鸿飞 王瑞
张栋奎 耿昕 唐蓉 张瀚文 范礼博 魏宇伦 唐艺展 徐少鹏 杨晓柔 毛宇 王秋晔
王耀龄 陆锴馨 卢怿 孙志强 孙成 孙星亮 张新钰 王璐阳 管育超 邓畅 伍习武 何满
余锦 刘俊 刘军锋 刘秦 史博宇 孟丽 席凯 张学飞 张梦珣 徐小钟 李志达 李振
李明 李瑞丽 李盼 李立春 杨昭 林涛 林鹏飞 梁化成 江山 王淇 胡晓曦 谢彤衢
贺明 赵园 赵飞 郭丰泳 陈坚 韩璐尧 颜炜 高童 黄元红 黄楷浩 黄爱苏 王克 刘富贵
蔡金勇 钟江 宋良玉 涂菲娜 原京 冯海洋 单海东 钱伟 黄相 段宏莉 李士峰
杨萌 李蕾 刘一凡 赵亚泉 杨晓柔 蒋腾云 杨继尧 李润祥 邵凯丽 李婵 许睿
王秋 李思凡 沈棋帆 严宗明 张浩鹏 庄兴巧 包广昆 杨兴宇 杨树文 王非
冯雪婷 郭姜福 李瑞丽 杨泽 赵威 李博珩 张轶博 栾可 朱林岗 马旭平 程艳琴
冉现超 牟芃颖 范麒波 江炜 李芸莹 余亚卓 周慧敏 王友祥 李小琦 黄红峰
赵珍妮 王辉耀""".split()

# 长名优先，避免子串误替换
NAMES = sorted(set(NAMES), key=len, reverse=True)
ALIAS = {n: f'成员{idx:02d}' for idx, n in enumerate(NAMES, 1)}

def desensitize(text):
    for a, b in ORG_RULES:
        text = text.replace(a, b)
    for n in NAMES:
        text = text.replace(n, ALIAS[n])
    # 长数字/手机/邮箱
    text = re.sub(r'1[3-9]\d{9}', 'XXXX', text)
    text = re.sub(r'[\w.\-]+@[\w.\-]+', 'xxx@xxx.com', text)
    return text

def main():
    total = 0
    for f in sorted(glob.glob(os.path.join(OUT, '*.md'))):
        if os.path.basename(f).startswith('00_'):
            continue
        s = open(f, encoding='utf-8').read()
        orig = s
        s = desensitize(s)
        if s != orig:
            open(f, 'w', encoding='utf-8').write(s)
            total += 1
            print(f'✅ {os.path.basename(f)}')
    # 人名映射表（供内部反查，不对外）
    with open(os.path.join(OUT, '_人名映射表_内部勿外传.json'), 'w', encoding='utf-8') as fp:
        json.dump(ALIAS, fp, ensure_ascii=False, indent=2)
    print(f'\n处理 {total} 个文件；人名映射 {len(ALIAS)} 条已存内部映射表')

if __name__ == '__main__':
    main()
