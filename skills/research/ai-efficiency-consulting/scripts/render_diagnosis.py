#!/usr/bin/env python3
"""由已评分的诊断数据生成诊断报告 HTML(图 1 阶段路径、图 2 能力热力图、图 3 数据缺口与接入)。

用法: render_diagnosis.py SCORED.json -o diagnosis.html
输入必须是 score.py 的输出(含 stage / bottlenecks / risks)。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_common import (  # noqa: E402
    GAP_COLORS, GAP_LABELS, LEVEL_FILL, LEVEL_TEXT, LINES, STAGES, STAGE_TITLES,
    WATERSHEDS, esc, page, wrap_text,
)

LINE_NAME = {k: n for k, n, _ in LINES}


def stage_path_svg(scopes) -> str:
    """图 1:横轴 A0-A4,每个范围一行;实心=当前,空心=目标,灰虚线=未访谈默认 A0。"""
    left, col_w, row_h, top = 250, 150, 54, 92
    width = left + col_w * 5 + 20
    height = top + row_h * len(scopes) + 20
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="阶段路径图">']
    # 阶段列
    for i, st in enumerate(STAGES):
        x = left + i * col_w
        out.append(f'<rect x="{x}" y="{top - 30}" width="{col_w}" height="{row_h * len(scopes) + 30}" fill="{"#f9fafb" if i % 2 == 0 else "#ffffff"}"/>')
        out.append(f'<text x="{x + col_w / 2}" y="{top - 52}" text-anchor="middle" font-size="15" font-weight="700" fill="#101828">{st}</text>')
        out.append(f'<text x="{x + col_w / 2}" y="{top - 34}" text-anchor="middle" font-size="12" fill="#475467">{esc(STAGE_TITLES[st])}</text>')
    # 分水岭
    for i, (k, v) in enumerate(WATERSHEDS.items()):
        x = left + (i + 1) * col_w
        out.append(f'<line x1="{x}" y1="{top - 28}" x2="{x}" y2="{height - 14}" stroke="#98a2b3" stroke-dasharray="4 3"/>')
    # 行
    for r, s in enumerate(scopes):
        cy = top + r * row_h + row_h / 2
        out.append(f'<line x1="10" y1="{cy + row_h / 2}" x2="{width - 10}" y2="{cy + row_h / 2}" stroke="#eaecf0"/>')
        name_lines = wrap_text(s["name"], 26)[:2]
        for j, ln in enumerate(name_lines):
            out.append(f'<text x="12" y="{cy - 8 + j * 15}" font-size="13" fill="#101828">{esc(ln)}</text>')
        if not s.get("default_a0") and s["bottlenecks"]:
            # 瓶颈线放在行名下方,避免长文字横跨多列压住分水岭
            names = "、".join(LINE_NAME[b] for b in s["bottlenecks"])
            for j, ln in enumerate(wrap_text("瓶颈:" + names, 40)[:2]):
                out.append(f'<text x="12" y="{cy + 8 + len(name_lines) * 15 - 15 + j * 12}" font-size="10.5" fill="#b42318">{esc(ln)}</text>')
        cur = STAGES.index(s["stage"])
        cx = left + cur * col_w + col_w / 2
        tgt = s.get("target_stage")
        if tgt and STAGES.index(tgt) > cur:
            tx = left + STAGES.index(tgt) * col_w + col_w / 2
            out.append(f'<line x1="{cx + 11}" y1="{cy}" x2="{tx - 11}" y2="{cy}" stroke="#0b4f8f" stroke-width="2" marker-end="url(#arr)"/>')
            out.append(f'<circle cx="{tx}" cy="{cy}" r="10" fill="#ffffff" stroke="#0b4f8f" stroke-width="2.5"/>')
        if s.get("default_a0"):
            out.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#e4e7ec" stroke="#667085" stroke-width="2" stroke-dasharray="3 2"/>')
            # 白色底,避免被分水岭虚线截断
            out.append(f'<rect x="{cx + 16}" y="{cy - 9}" width="104" height="18" fill="#ffffff" opacity="0.92"/>')
            out.append(f'<text x="{cx + 20}" y="{cy + 4}" font-size="11" fill="#667085">未访谈,默认 A0</text>')
        else:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#0b4f8f"/>')
    out.insert(1, '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#0b4f8f"/></marker></defs>')
    out.append("</svg>")
    return "".join(out)


def heatmap(scopes) -> str:
    rows = ["<table><tr><th>业务范围</th>"]
    for _, name, gating in LINES:
        rows.append(f'<th>{esc(name)}<br><span class="tiny">{"门控线" if gating else "支撑线"}</span></th>')
    rows.append("<th>阶段</th></tr>")
    for s in scopes:
        rows.append(f'<tr><td>{esc(s["name"])}</td>')
        if s.get("default_a0"):
            rows.append(f'<td colspan="{len(LINES)}" class="tiny" style="background:#f2f4f7">未访谈,默认 A0,不评分</td>')
        else:
            unv = set(s.get("unverified", []))
            risk_lines = {r["line"] for r in s["risks"]}
            for key, _, _ in LINES:
                v = s["scores"][key]
                mark = "*" if key in unv else ""
                border = "outline:2px solid #b42318;outline-offset:-2px;" if key in risk_lines else ""
                rows.append(f'<td style="text-align:center;background:{LEVEL_FILL[v]};color:{LEVEL_TEXT[v]};{border}">L{v}{mark}</td>')
        rows.append(f'<td><b>{s["stage"]}</b></td></tr>')
    rows.append("</table>")
    rows.append('<div class="legend">' + "".join(f'<span><i style="background:{LEVEL_FILL[i]}"></i>L{i}</span>' for i in range(5))
                + '<span>* 待证实(口述,无证据)</span><span><i style="background:#fff;outline:2px solid #b42318"></i>风险提示</span></div>')
    return "".join(rows)


def data_gap_section(scopes) -> str:
    parts = []
    for s in scopes:
        items = s.get("data_items") or []
        if not items and not s.get("platform"):
            continue
        parts.append(f'<h3>{esc(s["name"])}</h3>')
        plat = s.get("platform")
        if plat:
            kind = "自带知识基建(类型 I)" if plat["type"] == "I" else "不带知识基建(类型 II)"
            route = ""
            if plat["type"] == "II":
                route = {"a": ",路线 a:业务系统自带 MCP", "b": ",路线 b:自建知识基建 / MCP 网关", "c": ",路线 c:Skill / 文件下发"}[plat["route"]]
            parts.append(f'<p>目标平台:<b>{esc(plat["name"])}</b> — {kind}{route}</p>')
        if items:
            parts.append("<table><tr><th>数据项</th><th>所在系统</th><th>缺口类型</th><th>接入方式</th><th>平台上的落地做法</th><th>前提与风险</th><th>优先级</th></tr>")
            for d in sorted(items, key=lambda x: x.get("priority", 99)):
                c = GAP_COLORS[d["gap"]]
                parts.append(
                    f'<tr><td>{esc(d["name"])}</td><td>{esc(d["system"])}</td>'
                    f'<td><span class="tag" style="color:{c};border-color:{c}">{GAP_LABELS[d["gap"]]}</span></td>'
                    f'<td>{esc(d["access"])}</td><td>{esc(d.get("platform_action", ""))}</td>'
                    f'<td>{esc(d.get("risk", ""))}</td><td>{esc(d.get("priority", ""))}</td></tr>'
                )
            parts.append("</table>")
    if not parts:
        return '<div class="note">没有记录数据缺口或平台选择。</div>'
    legend = '<div class="legend">' + "".join(f'<span><i style="background:{GAP_COLORS[k]}"></i>{v}</span>' for k, v in GAP_LABELS.items()) + "</div>"
    return legend + "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    scopes = data["scopes"]
    for s in scopes:
        if "stage" not in s:
            sys.exit("输入缺少 stage,请先运行 score.py")

    body = []
    n_default = sum(1 for s in scopes if s.get("default_a0"))
    body.append('<div class="note">图例:<b>实心圆</b>=当前阶段;<b>空心圆</b>=目标阶段;<b>灰色虚线圆</b>=未访谈、默认 A0(不代表确认没有 AI);红字为升到下一阶段的瓶颈线。'
                + (f" 本次共 {len(scopes)} 个范围,其中 {n_default} 个未访谈。" if n_default else "") + "</div>")
    body.append("<h2>图 1 阶段路径</h2>")
    body.append('<div class="scroll">' + stage_path_svg(scopes) + "</div>")
    body.append('<div class="tiny">虚线为分水岭:' + ";".join(f"{k} {v}" for k, v in WATERSHEDS.items()) + "</div>")
    body.append("<h2>图 2 能力热力图</h2>")
    body.append(heatmap(scopes))
    body.append("<h2>风险提示与待证实</h2>")
    notes = []
    for s in scopes:
        for r in s.get("risks", []):
            notes.append(f'<li><b>{esc(s["name"])}</b>:{esc(r["message"])}</li>')
        for u in s.get("unverified", []):
            notes.append(f'<li><b>{esc(s["name"])}</b>:{esc(LINE_NAME[u])} 评分仅来自口述,待证实</li>')
        for w in s.get("warnings", []):
            notes.append(f'<li><b>{esc(s["name"])}</b>:{esc(w)}</li>')
    body.append("<ul>" + "".join(notes) + "</ul>" if notes else '<div class="note">无。</div>')
    body.append("<h2>图 3 数据缺口与接入</h2>")
    body.append(data_gap_section(scopes))
    Path(a.output).write_text(page(f'{data.get("client", "")} AI 提效现状诊断', "".join(body), "依据《企业 AI 提效 Roadmap 指南》"), encoding="utf-8")
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
