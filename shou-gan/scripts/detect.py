#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shou-gan detect.py — 中文写作去AI味检测脚本
无模型、纯正则、结果可复现。
用法: python detect.py <文件路径或直接传入文本>
"""

import sys
import re
import os

# ============================================================
# 规则定义：每条规则有 id、严重级别、名称、正则模式
# ============================================================

RULES = [
    # ---- P0: 一眼假 ----
    {
        "id": "P0-01",
        "level": "P0",
        "name": "时代背景开场白",
        "patterns": [
            r"在这个.{0,10}(时代|社会|世界|年代|快节奏)",
            r"随着.{0,15}(发展|进步|变化|推进|不断)",
            r"^如今[，,]",
            r"^当下[，,]",
        ],
    },
    {
        "id": "P0-02",
        "level": "P0",
        "name": "万能结尾口号",
        "patterns": [
            r"让我们一起",
            r"未来可期",
            r"拭目以待",
            r"共同期待",
            r"一起加油",
            r"更加美好的明天",
        ],
    },
    {
        "id": "P0-03",
        "level": "P0",
        "name": "四段式编号",
        "patterns": [
            r"首先[，,]",
            r"其次[，,]",
            r"再次[，,]",
            r"最后[，,]",
        ],
    },
    {
        "id": "P0-04",
        "level": "P0",
        "name": "聊天机器人残留",
        "patterns": [
            r"希望对你有帮助",
            r"以上就是",
            r"如有疑问",
            r"欢迎咨询",
            r"祝你.{0,5}(顺利|愉快|开心)",
        ],
    },
    {
        "id": "P0-05",
        "level": "P0",
        "name": "假大空黑话",
        "patterns": [
            r"赋能",
            r"抓手",
            r"闭环",
            r"链路",
            r"矩阵",
            r"打法",
            r"心智",
            r"颗粒度",
        ],
    },
    {
        "id": "P0-06",
        "level": "P0",
        "name": "权威感开头",
        "patterns": [
            r"众所周知",
            r"毋庸置疑",
            r"不可否认",
            r"客观上来说",
        ],
    },
    # ---- P1: 很明显 ----
    {
        "id": "P1-01",
        "level": "P1",
        "name": "对仗关联词",
        "patterns": [
            r"不仅.{0,15}而且",
            r"既.{0,10}又.{0,10}",
            r"一方面.{0,20}另一方面",
            r"与其.{0,10}不如",
        ],
    },
    {
        "id": "P1-02",
        "level": "P1",
        "name": "形容词堆砌(的的)",
        "patterns": [
            r"[\u4e00-\u9fa5]{2,4}的[\u4e00-\u9fa5]{2,4}的[\u4e00-\u9fa5]{2,4}",
        ],
    },
    {
        "id": "P1-03",
        "level": "P1",
        "name": "万能过渡词开头",
        "patterns": [
            r"^此外[，,]",
            r"^另外[，,]",
            r"^值得一提的是",
            r"^需要注意的是",
            r"^与此同时",
            r"^不仅如此",
            r"^更重要的是",
        ],
    },
    {
        "id": "P1-04",
        "level": "P1",
        "name": "伪深刻总结句",
        "patterns": [
            r"这不仅仅是.{0,15}更是",
            r"这不只是.{0,15}更是",
        ],
    },
    {
        "id": "P1-05",
        "level": "P1",
        "name": "未来叙事",
        "patterns": [
            r"在未来[，,]",
            r"必将",
            r"势必",
            r"有望成为",
        ],
    },
    {
        "id": "P1-06",
        "level": "P1",
        "name": "万能副词",
        "patterns": [
            r"非常",
            r"十分",
            r"极其",
            r"格外",
            r"尤为",
        ],
    },
    # ---- P2: 小瑕疵 ----
    {
        "id": "P2-01",
        "level": "P2",
        "name": "名词化癖",
        "patterns": [
            r"进行了",
            r"做出了",
            r"给予了",
            r"加以",
            r"予以",
        ],
    },
    {
        "id": "P2-02",
        "level": "P2",
        "name": "双重否定",
        "patterns": [
            r"不是不",
            r"并非不",
            r"不能不",
            r"不可不",
        ],
    },
]


def detect(text: str) -> dict:
    """检测文本中的AI味模式，返回结果字典。"""
    results = []
    total_hits = 0

    for rule in RULES:
        hits = []
        for pattern in rule["patterns"]:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for m in matches:
                # 找到所在句子
                start = max(0, m.start() - 15)
                end = min(len(text), m.end() + 15)
                context = text[start:end].replace("\n", " ").strip()
                hits.append({
                    "match": m.group(),
                    "context": f"...{context}...",
                    "position": m.start(),
                })

        if hits:
            results.append({
                "id": rule["id"],
                "level": rule["level"],
                "name": rule["name"],
                "count": len(hits),
                "hits": hits,
            })
            total_hits += len(hits)

    # 额外统计项（非正则）
    char_count = len(text)
    dash_count = text.count("——") + text.count("—")
    dash_per_1000 = (dash_count / max(char_count, 1)) * 1000

    # 加粗统计（markdown）
    bold_count = len(re.findall(r"\*\*[^*]+\*\*", text))
    bold_per_1000 = (bold_count / max(char_count, 1)) * 1000

    # 段落均匀度
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    para_lengths = [len(p) for p in paragraphs]
    para_std = 0
    if len(para_lengths) >= 3:
        mean_len = sum(para_lengths) / len(para_lengths)
        variance = sum((l - mean_len) ** 2 for l in para_lengths) / len(para_lengths)
        para_std = variance ** 0.5

    extra_stats = {
        "char_count": char_count,
        "dash_count": dash_count,
        "dash_per_1000": round(dash_per_1000, 1),
        "bold_count": bold_count,
        "bold_per_1000": round(bold_per_1000, 1),
        "paragraph_count": len(paragraphs),
        "para_std": round(para_std, 1),
    }

    # 评分：P0每个扣8分，P1每个扣4分，P2每个扣2分，从100分起
    score = 100
    for r in results:
        if r["level"] == "P0":
            score -= r["count"] * 8
        elif r["level"] == "P1":
            score -= r["count"] * 4
        elif r["level"] == "P2":
            score -= r["count"] * 2

    # 额外扣分
    if dash_per_1000 > 3:
        score -= min(10, int(dash_per_1000 - 3) * 2)
    if bold_per_1000 > 2:
        score -= min(10, int(bold_per_1000 - 2) * 3)
    if para_std < 30 and len(paragraphs) >= 5:
        score -= 5  # 段落太均匀

    score = max(0, min(100, score))

    return {
        "score": score,
        "total_hits": total_hits,
        "rules_triggered": results,
        "stats": extra_stats,
    }


def print_report(result: dict):
    """打印检测报告。"""
    score = result["score"]

    # 评分等级
    if score >= 80:
        grade = "干净"
        emoji = "✅"
    elif score >= 60:
        grade = "有点味道"
        emoji = "⚠️"
    elif score >= 40:
        grade = "AI味明显"
        emoji = "🤖"
    else:
        grade = "一眼AI"
        emoji = "🚨"

    print("=" * 50)
    print(f"  手感检测报告 | AI味评分: {score}/100  {emoji} {grade}")
    print("=" * 50)
    print()

    stats = result["stats"]
    print(f"  字数: {stats['char_count']}  |  段落: {stats['paragraph_count']}")
    print(f"  破折号: {stats['dash_count']}个 ({stats['dash_per_1000']}/千字)")
    print(f"  加粗: {stats['bold_count']}处 ({stats['bold_per_1000']}/千字)")
    print(f"  段落长度标准差: {stats['para_std']}")
    print()

    # 按级别分组
    by_level = {"P0": [], "P1": [], "P2": []}
    for r in result["rules_triggered"]:
        by_level[r["level"]].append(r)

    level_names = {
        "P0": "🔴 P0 — 一眼假（必须改）",
        "P1": "🟡 P1 — 很明显（建议改）",
        "P2": "🔵 P2 — 小瑕疵（有空再改）",
    }

    for level in ["P0", "P1", "P2"]:
        rules = by_level[level]
        if not rules:
            continue
        print(f"\n{level_names[level]}")
        print("-" * 40)
        for r in rules:
            print(f"  [{r['id']}] {r['name']} — 命中{r['count']}次")
            for h in r["hits"][:3]:  # 每个规则最多显示3条
                print(f"      → {h['context']}")
            if r["count"] > 3:
                print(f"      ... 还有 {r['count'] - 3} 处")

    print()
    print("=" * 50)
    if score >= 80:
        print("  结论：文字比较干净，AI味不重。")
    elif score >= 60:
        print("  结论：有一些AI痕迹，改一改会更好。")
    elif score >= 40:
        print("  结论：AI味比较明显，建议做一次系统改写。")
    else:
        print("  结论：一眼就是AI写的，需要大改。")
    print("=" * 50)


def main():
    if len(sys.argv) < 2:
        print("用法: python detect.py <文件路径或直接传入文本>")
        print("示例: python detect.py my_article.txt")
        print('示例: python detect.py "在这个快节奏的时代..."')
        sys.exit(1)

    arg = sys.argv[1]

    # 判断是文件路径还是直接文本
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = arg

    result = detect(text)
    print_report(result)


if __name__ == "__main__":
    main()
