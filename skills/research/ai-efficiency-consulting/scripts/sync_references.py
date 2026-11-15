#!/usr/bin/env python3
"""把《企业 AI 提效 Roadmap 指南》按章节原样抽取为 references/*.md。

指南是唯一内容来源;references 只是它的切片,修改内容请改指南后重新运行本脚本。

用法: sync_references.py [--guide PATH] [--appendix PATH]
默认路径相对于仓库根目录(从本文件向上查找含 docs/research 的目录)。
"""
import argparse
import re
import sys
from pathlib import Path

# (输出文件名, 章节号, 标题)
SECTIONS = [
    ("foundations", 1, "前提与基本单位(指南第 1 章)"),
    ("stages", 2, "阶段模型 A0–A4(指南第 2 章)"),
    ("capability-lines", 3, "能力线、等级与阶段判定规则(指南第 3 章)"),
    ("data-and-access", 4, "数据与接入(指南第 4 章)"),
    ("platforms", 5, "平台与接入模式(指南第 5 章)"),
    ("scope-selection", 6, "业务范围的选择与分析(指南第 6 章)"),
    ("interview-guide", 7, "诊断方法、访谈提纲与数据结构(指南第 7 章)"),
    ("roadmap-and-plan", 8, "Roadmap 与方案设计(指南第 8 章)"),
    ("failure-modes", 9, "组织、治理与失败模式(指南第 9 章)"),
]

NOTE = (
    "> 本文件由《企业 AI 提效 Roadmap 指南》(docs/research/enterprise-ai-efficiency-guide.md)"
    "对应章节原样抽取,请勿直接修改;修改指南后运行 scripts/sync_references.py 重新生成。"
)


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "research").is_dir():
            return p
    sys.exit("找不到含 docs/research 的仓库根目录")


def split_chapters(text: str) -> dict:
    """按行首的 '## N. ' 切章,返回 {章节号: 正文(含章标题行)}。"""
    lines = text.splitlines()
    starts = []
    for i, line in enumerate(lines):
        m = re.match(r"^## (\d+)\. ", line)
        if m:
            starts.append((int(m.group(1)), i))
    chapters = {}
    for idx, (num, begin) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(lines)
        body = "\n".join(lines[begin:end]).rstrip()
        # 去掉末尾的分隔线
        body = re.sub(r"\n---\s*$", "", body).rstrip()
        chapters[num] = body
    return chapters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guide")
    ap.add_argument("--appendix")
    args = ap.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    root = find_root(skill_dir)
    guide = Path(args.guide) if args.guide else root / "docs/research/enterprise-ai-efficiency-guide.md"
    appendix = Path(args.appendix) if args.appendix else root / "docs/research/enterprise-ai-efficiency-guide-appendix-knowledge.md"
    out = skill_dir / "references"
    out.mkdir(exist_ok=True)

    chapters = split_chapters(guide.read_text(encoding="utf-8"))
    missing = [n for _, n, _ in SECTIONS if n not in chapters]
    if missing:
        sys.exit(f"指南中缺少章节: {missing}")

    for name, num, title in SECTIONS:
        content = f"# {title}\n\n{NOTE}\n\n{chapters[num]}\n"
        (out / f"{name}.md").write_text(content, encoding="utf-8")
        print(f"wrote references/{name}.md ({len(chapters[num].splitlines())} lines)")

    if appendix.exists():
        text = appendix.read_text(encoding="utf-8")
        (out / "knowledge-engineering-line.md").write_text(text, encoding="utf-8")
        print("wrote references/knowledge-engineering-line.md")


if __name__ == "__main__":
    main()
