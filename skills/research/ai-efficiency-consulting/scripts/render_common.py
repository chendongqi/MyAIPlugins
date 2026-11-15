"""渲染脚本共用的常量、转义与样式。仅标准库,生成自包含 HTML(无外部资源)。"""
from html import escape

STAGES = ["A0", "A1", "A2", "A3", "A4"]
STAGE_TITLES = {
    "A0": "AI 未进场",
    "A1": "人是中台",
    "A2": "Agent 是中台",
    "A3": "Agent 协作",
    "A4": "自我进化",
}
# 阶段之间的分水岭(指南 2.2)
WATERSHEDS = {
    "A0→A1": "AI 进入业务",
    "A1→A2": "谁做中台:人 → Agent",
    "A2→A3": "跨过人与人协作",
    "A3→A4": "变好的来源:人的经验 → 业务结果",
}
LINES = [
    ("tools", "工具与 Skill", True),
    ("workflow", "Workflow 与协作", True),
    ("data", "数据与知识", True),
    ("infra", "基建与平台", True),
    ("governance", "治理与安全", True),
    ("org", "组织与人", False),
    ("metrics", "度量与价值", False),
]
GAP_LABELS = {
    "missing": "不存在",
    "unreachable": "不可达",
    "unusable": "不可用",
    "insufficient": "不够用",
}
GAP_COLORS = {
    "missing": "#b42318",
    "unreachable": "#c4590a",
    "unusable": "#a16207",
    "insufficient": "#1d6fb8",
}
# L0-L4 色阶(浅 -> 深),同时保证深色单元格上文字用白色
LEVEL_FILL = ["#f2f4f7", "#cfe3f5", "#8fbfe6", "#3f8fd2", "#0b4f8f"]
LEVEL_TEXT = ["#475467", "#12395f", "#0b2f52", "#ffffff", "#ffffff"]

CSS = """
:root{--ink:#101828;--sub:#475467;--line:#d0d5dd;--bg:#ffffff;--soft:#f9fafb;--accent:#0b4f8f}
*{box-sizing:border-box}
body{margin:0;font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;color:var(--ink);background:var(--bg)}
main{max-width:1180px;margin:0 auto;padding:32px 24px 64px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:19px;margin:40px 0 12px;padding-top:8px;border-top:2px solid var(--ink)}
h3{font-size:15px;margin:24px 0 8px}
.meta{color:var(--sub);margin-bottom:8px}
.note{background:var(--soft);border:1px solid var(--line);border-left:4px solid var(--accent);padding:10px 14px;margin:12px 0;color:var(--sub)}
.warn{border-left-color:#c4590a}
table{border-collapse:collapse;width:100%;margin:8px 0 16px}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;border:1px solid var(--line);color:var(--sub);margin-right:4px}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin:8px 0;color:var(--sub);font-size:13px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:-1px}
svg{max-width:100%;height:auto;display:block}
.radar{max-width:440px}
svg text{font-family:inherit}
.scroll{overflow-x:auto}
.tiny{font-size:12px;color:var(--sub)}
@media print{main{padding:0}h2{break-after:avoid}svg{break-inside:avoid}}
"""


def esc(s) -> str:
    return escape(str(s if s is not None else ""), quote=True)


def page(title: str, body: str, subtitle: str = "") -> str:
    sub = f'<div class="meta">{esc(subtitle)}</div>' if subtitle else ""
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body><main>"
        f"<h1>{esc(title)}</h1>{sub}{body}</main></body></html>"
    )


def text_px(text: str, size: float = 11) -> float:
    """估算一段文字在给定字号下的像素宽度(CJK 约 1 个字号,ASCII 约 0.55 个字号)。"""
    return sum(size if ord(ch) > 0x2E80 else size * 0.55 for ch in str(text))


def fit_text(text: str, max_px: float, size: float = 11) -> str:
    """把文字截到不超过 max_px,超出部分用省略号。"""
    if text_px(text, size) <= max_px:
        return str(text)
    out, used = "", text_px("…", size)
    for ch in str(text):
        cw = size if ord(ch) > 0x2E80 else size * 0.55
        if used + cw > max_px:
            break
        out += ch
        used += cw
    return out + "…"


def wrap_text(text: str, width: int) -> list:
    """按显示宽度粗略折行(中文按 2,其余按 1),用于 SVG 内的标签。"""
    lines, cur, w = [], "", 0
    for ch in str(text):
        cw = 2 if ord(ch) > 0x2E80 else 1
        if w + cw > width:
            lines.append(cur)
            cur, w = ch, cw
        else:
            cur += ch
            w += cw
    if cur:
        lines.append(cur)
    return lines or [""]
