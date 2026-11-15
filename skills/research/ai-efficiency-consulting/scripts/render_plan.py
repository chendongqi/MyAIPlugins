#!/usr/bin/env python3
"""由已评分且带 roadmap 的诊断数据生成方案 HTML。

用法: render_plan.py SCORED.json -o plan.html [--unit 周]
包含: 图 4 Roadmap 泳道图(含依赖箭头、关键路径、里程碑)、图 5 现状到目标雷达对比、
      图 6 平台接入架构图、方案文字部分(现状/目标/数据接入/平台/风险/验收)。

roadmap 数据(每个 scope 可选 roadmap 字段):
  tasks: [{id, name, lane, start, duration, deps[], owner, output, acceptance}]
         lane 取能力线 key(tools/workflow/data/infra/governance/org/metrics)。
         start/duration 是相对时间单位(数字),由顾问按客户实际约束填写;指南不提供默认周期。
  milestones: [{name, at, gate}]  gate 写对应阶段门槛。
校验: 依赖必须存在、不得成环、任务不得早于其依赖的结束时间;不通过则报错退出。
关键路径: 以依赖为边、以持续时间为权的最长链。
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_common import (  # noqa: E402
    GAP_LABELS, LINES, STAGES, esc, page, text_px, wrap_text,
)

LINE_NAME = {k: n for k, n, _ in LINES}
LANE_COLOR = {
    "tools": "#1d6fb8", "workflow": "#6941c6", "data": "#0e7c66", "infra": "#475467",
    "governance": "#b54708", "org": "#a11043", "metrics": "#3b6e1f",
}


def validate_roadmap(scope) -> list:
    errs = []
    rm = scope.get("roadmap")
    if not rm:
        return errs
    tag = scope["name"]
    tasks = rm.get("tasks", [])
    ids = {}
    for t in tasks:
        for f in ("id", "name", "lane", "start", "duration"):
            if f not in t:
                errs.append(f"{tag}: 任务缺少 {f}: {t.get('name', t)}")
        if t.get("lane") not in LANE_COLOR:
            errs.append(f"{tag}: 任务 {t.get('id')} 的 lane 必须是 {sorted(LANE_COLOR)}")
        if t.get("id") in ids:
            errs.append(f"{tag}: 任务 id 重复 {t['id']}")
        ids[t.get("id")] = t
    for t in tasks:
        for d in t.get("deps", []):
            if d not in ids:
                errs.append(f"{tag}: 任务 {t['id']} 依赖不存在的任务 {d}")
            elif ids[d]["start"] + ids[d]["duration"] > t["start"]:
                errs.append(f"{tag}: 任务 {t['id']} 开始于 {t['start']},早于其依赖 {d} 的结束 {ids[d]['start'] + ids[d]['duration']}")
    # 成环检测
    color = {}

    def dfs(n, path):
        color[n] = 1
        for d in ids.get(n, {}).get("deps", []):
            if d not in ids:
                continue
            if color.get(d) == 1:
                errs.append(f"{tag}: 依赖成环: {' -> '.join(path + [d])}")
            elif d not in color:
                dfs(d, path + [d])
        color[n] = 2

    for n in ids:
        if n not in color:
            dfs(n, [n])
    return errs


def critical_path(tasks) -> set:
    by = {t["id"]: t for t in tasks}
    memo = {}

    def best(tid):
        if tid in memo:
            return memo[tid]
        t = by[tid]
        cands = [best(d) for d in t.get("deps", []) if d in by]
        prev = max(cands, key=lambda x: x[0], default=(0, []))
        memo[tid] = (prev[0] + t["duration"], prev[1] + [tid])
        return memo[tid]

    if not tasks:
        return set()
    end = max((best(t["id"]) for t in tasks), key=lambda x: x[0])
    return set(end[1])


def gantt_svg(scope, unit) -> str:
    rm = scope["roadmap"]
    tasks = rm["tasks"]
    crit = critical_path(tasks)
    lanes = [k for k, _, _ in LINES if any(t["lane"] == k for t in tasks)]
    horizon = max(t["start"] + t["duration"] for t in tasks)
    horizon = max(horizon, max((m["at"] for m in rm.get("milestones", [])), default=0))
    left, top = 150, 54
    unit_w = max(14, min(40, 880 / max(horizon, 1)))
    bar_h, gap = 22, 8
    # 每条泳道内按开始时间分行,避免重叠
    lane_rows = {}
    pos = {}
    for lane in lanes:
        rows = []
        for t in sorted([t for t in tasks if t["lane"] == lane], key=lambda x: x["start"]):
            for ri, end in enumerate(rows):
                if t["start"] >= end:
                    rows[ri] = t["start"] + t["duration"]
                    pos[t["id"]] = ri
                    break
            else:
                rows.append(t["start"] + t["duration"])
                pos[t["id"]] = len(rows) - 1
        lane_rows[lane] = max(len(rows), 1)
    y = top
    lane_y = {}
    for lane in lanes:
        lane_y[lane] = y
        y += lane_rows[lane] * (bar_h + gap) + 14
    width = left + horizon * unit_w + 40
    height = y + 36
    out = [f'<svg viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="Roadmap 泳道图">',
           '<defs><marker id="dep" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#667085"/></marker></defs>']
    # 时间刻度
    step = 1 if horizon <= 16 else (2 if horizon <= 32 else 4)
    for i in range(0, int(math.ceil(horizon)) + 1, step):
        x = left + i * unit_w
        out.append(f'<line x1="{x}" y1="{top - 8}" x2="{x}" y2="{height - 28}" stroke="#eaecf0"/>')
        out.append(f'<text x="{x}" y="{top - 14}" text-anchor="middle" font-size="11" fill="#667085">{i}</text>')
    out.append(f'<text x="{left}" y="14" font-size="12" fill="#475467">时间(相对{esc(unit)},由顾问按客户约束填写)</text>')
    # 泳道
    for lane in lanes:
        ly = lane_y[lane]
        lh = lane_rows[lane] * (bar_h + gap) + 6
        out.append(f'<rect x="0" y="{ly - 4}" width="{width}" height="{lh}" fill="#f9fafb" opacity="0.7"/>')
        out.append(f'<text x="10" y="{ly + 14}" font-size="13" font-weight="600" fill="{LANE_COLOR[lane]}">{esc(LINE_NAME[lane])}</text>')
    # 里程碑
    for m in rm.get("milestones", []):
        x = left + m["at"] * unit_w
        out.append(f'<line x1="{x}" y1="{top - 8}" x2="{x}" y2="{height - 28}" stroke="#b42318" stroke-dasharray="5 3"/>')
        out.append(f'<path d="M{x} {height - 26} l7 8 l-7 8 l-7 -8 z" fill="#b42318"/>')
        # 靠近右边界时文字放到菱形左侧并右对齐,避免被截断
        tw = text_px(m["name"], 11)
        if x + 12 + tw > width - 6:
            out.append(f'<text x="{x - 12}" y="{height - 14}" text-anchor="end" font-size="11" fill="#b42318">{esc(m["name"])}</text>')
        else:
            out.append(f'<text x="{x + 12}" y="{height - 14}" font-size="11" fill="#b42318">{esc(m["name"])}</text>')
    # 任务条
    geom = {}
    label_right = {}
    for t in tasks:
        x = left + t["start"] * unit_w
        w = max(t["duration"] * unit_w, 6)
        ty = lane_y[t["lane"]] + pos[t["id"]] * (bar_h + gap)
        geom[t["id"]] = (x, ty, w)
        c = LANE_COLOR[t["lane"]]
        is_crit = t["id"] in crit
        stroke = ' stroke="#b42318" stroke-width="2.5"' if is_crit else ""
        out.append(f'<rect x="{x}" y="{ty}" width="{w}" height="{bar_h}" rx="4" fill="{c}" opacity="0.92"{stroke}><title>{esc(t["name"])} | 起 {t["start"]} 持续 {t["duration"]} | 负责: {esc(t.get("owner", ""))} | 产出: {esc(t.get("output", ""))} | 验收: {esc(t.get("acceptance", ""))}</title></rect>')
        label = t["name"]
        if text_px(label, 11) + 20 <= w:
            # 条内放得下:白字;左侧留出依赖箭头头的位置
            out.append(f'<text x="{x + 12}" y="{ty + 15}" font-size="11" fill="#ffffff">{esc(label)}</text>')
        else:
            # 放不下:移到条右侧,深色字加白底,避免被依赖线穿过
            tw = text_px(label, 11)
            out.append(f'<rect x="{x + w + 3}" y="{ty + 2}" width="{tw + 6:.0f}" height="{bar_h - 4}" fill="#ffffff" opacity="0.9"/>')
            out.append(f'<text x="{x + w + 6}" y="{ty + 15}" font-size="11" fill="#344054">{esc(label)}</text>')
            label_right[t["id"]] = x + w + 6 + tw
    # 依赖箭头
    for t in tasks:
        for d in t.get("deps", []):
            if d in geom and t["id"] in geom:
                x1, y1, w1 = geom[d]
                x2, y2, _ = geom[t["id"]]
                sx, sy, ex, ey = x1 + w1, y1 + bar_h / 2, x2, y2 + bar_h / 2
                if abs(sy - ey) < 1:
                    out.append(f'<path d="M{sx} {sy} H{ex - 1}" fill="none" stroke="#667085" stroke-width="1.2" marker-end="url(#dep)"/>')
                else:
                    # 从上游条右端中点出发,在上游结束与下游开始之间的空隙里竖直走,
                    # 再水平进入下游条。空隙足够时竖线落在空隙中点,不压到任何任务条;
                    # 若上游恰好在下游起点结束(无空隙),竖线贴在下游条左侧 6px。
                    gap_w = ex - sx
                    vx = sx + gap_w / 2 if gap_w >= 12 else ex - 6
                    out.append(
                        f'<path d="M{sx} {sy} H{vx} V{ey} H{ex - 1}" fill="none" stroke="#667085" stroke-width="1.2" marker-end="url(#dep)"/>'
                    )
    out.append("</svg>")
    return "".join(out)


def radar_svg(scope) -> str:
    cx, cy, R = 190, 170, 120
    n = len(LINES)

    def pt(i, v):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        r = R * v / 4
        return cx + r * math.cos(ang), cy + r * math.sin(ang)

    out = ['<svg class="radar" viewBox="0 0 380 350" role="img" aria-label="现状与目标雷达">']
    for lv in range(1, 5):
        out.append('<polygon points="' + " ".join(f"{pt(i, lv)[0]:.1f},{pt(i, lv)[1]:.1f}" for i in range(n)) + '" fill="none" stroke="#d0d5dd"/>')
        out.append(f'<text x="{cx + 3}" y="{cy - R * lv / 4 - 2}" font-size="10" fill="#98a2b3">L{lv}</text>')
    for i, (_, name, gating) in enumerate(LINES):
        x, y = pt(i, 4)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#eaecf0"/>')
        lx, ly = pt(i, 4.55)
        anchor = "middle" if abs(lx - cx) < 8 else ("start" if lx > cx else "end")
        out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="11" fill="#344054">{esc(name)}</text>')
    cur = scope["scores"]
    out.append('<polygon points="' + " ".join(f"{pt(i, cur[k])[0]:.1f},{pt(i, cur[k])[1]:.1f}" for i, (k, _, _) in enumerate(LINES)) + '" fill="#0b4f8f" fill-opacity="0.25" stroke="#0b4f8f" stroke-width="2"/>')
    tgt = scope.get("target_scores")
    if tgt:
        out.append('<polygon points="' + " ".join(f"{pt(i, tgt[k])[0]:.1f},{pt(i, tgt[k])[1]:.1f}" for i, (k, _, _) in enumerate(LINES)) + '" fill="none" stroke="#c4590a" stroke-width="2" stroke-dasharray="6 3"/>')
    out.append('<text x="12" y="338" font-size="11" fill="#0b4f8f">■ 当前</text>')
    if tgt:
        out.append('<text x="70" y="338" font-size="11" fill="#c4590a">┅ 目标</text>')
    out.append("</svg>")
    return "".join(out)


def platform_svg(scope) -> str:
    plat = scope["platform"]
    items = scope.get("data_items", [])
    systems = []
    for d in items:
        if d["system"] not in systems:
            systems.append(d["system"])
    methods = []
    for d in items:
        if d["access"] not in methods:
            methods.append(d["access"])
    row = 44
    h = max(len(systems), len(methods), 3) * row + 70
    out = [f'<svg viewBox="0 0 1000 {h}" role="img" aria-label="平台接入架构">']

    def box(x, y, w, hh, text, fill, stroke, dash=False, color="#101828"):
        d = ' stroke-dasharray="5 3"' if dash else ""
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{d}/>'
        lines = wrap_text(text, int(w / 7))[:3]
        for j, ln in enumerate(lines):
            s += f'<text x="{x + w / 2}" y="{y + hh / 2 + 4 - (len(lines) - 1) * 7 + j * 14}" text-anchor="middle" font-size="12" fill="{color}">{esc(ln)}</text>'
        return s

    heads = [(30, "数据源"), (270, "接入方式"), (520, "目标平台(及要补的基建)"), (810, "agent 入口")]
    for x, t in heads:
        out.append(f'<text x="{x}" y="22" font-size="13" font-weight="700" fill="#344054">{t}</text>')
    for i, s in enumerate(systems):
        out.append(box(30, 36 + i * row, 190, 34, s, "#f2f4f7", "#98a2b3"))
    for i, m in enumerate(methods):
        out.append(box(270, 36 + i * row, 190, 34, m, "#eff8ff", "#1d6fb8"))
    # 平台
    if plat["type"] == "I":
        label = f'{plat["name"]}(自带知识基建)'
        build = "补:" + (plat.get("gaps") or "按诊断的治理缺口补强")
        out.append(box(520, 36, 240, 60, label, "#ecfdf3", "#0e7c66"))
        out.append(box(520, 106, 240, 50, build, "#fffaeb", "#c4590a", dash=True))
        out.append(f'<text x="520" y="{h - 12}" font-size="11" fill="#667085">新数据:新建导入配置(profile)/ 增加连接器</text>')
    else:
        route = plat["route"]
        label = f'{plat["name"]}(不带知识基建)'
        out.append(box(520, 36, 240, 50, label, "#f2f4f7", "#667085"))
        if route == "a":
            out.append(box(520, 96, 240, 50, "业务系统自带 MCP", "#ecfdf3", "#0e7c66"))
        elif route == "b":
            out.append(box(520, 96, 240, 60, "自建知识基建 / MCP 网关(需新建:接入、治理、检索、权限)", "#fffaeb", "#c4590a", dash=True))
        else:
            out.append(box(520, 96, 240, 50, "Skill / 文件下发(稳定、量小的内容)", "#ecfdf3", "#0e7c66"))
    out.append(box(810, 36, 170, 50, "用户 / agent 对话入口", "#eff8ff", "#1d6fb8"))
    # 连线(概要)
    out.append('<defs><marker id="pa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#667085"/></marker></defs>')
    out.append(f'<path d="M220 {36 + 17} H270" stroke="#667085" marker-end="url(#pa)" fill="none"/>')
    out.append(f'<path d="M460 {36 + 17} H520" stroke="#667085" marker-end="url(#pa)" fill="none"/>')
    out.append(f'<path d="M760 {36 + 25} H810" stroke="#667085" marker-end="url(#pa)" fill="none"/>')
    out.append('<text x="30" y="%d" font-size="11" fill="#667085">实线框=已有或可直接用;虚线框=需要新建</text>' % (h - 12))
    out.append("</svg>")
    return "".join(out)


def plan_text(scope) -> str:
    p = []
    stage = scope["stage"]
    tgt = scope.get("target_stage", "—")
    p.append(f'<h3>1 现状</h3><p>当前阶段 <b>{stage}</b>。' + (f'瓶颈线:{"、".join(LINE_NAME[b] for b in scope["bottlenecks"])}。' if scope.get("bottlenecks") else "") + "</p>")
    if scope.get("risks"):
        p.append("<ul>" + "".join(f'<li>{esc(r["message"])}</li>' for r in scope["risks"]) + "</ul>")
    p.append(f'<h3>2 目标</h3><p>目标阶段 <b>{tgt}</b>。</p>')
    if scope.get("acceptance"):
        p.append("<ul>" + "".join(f"<li>{esc(a)}</li>" for a in scope["acceptance"]) + "</ul>")
    return "".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--unit", default="周")
    a = ap.parse_args()
    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    scopes = data["scopes"]
    errs = []
    for s in scopes:
        if "stage" not in s:
            sys.exit("输入缺少 stage,请先运行 score.py")
        errs += validate_roadmap(s)
    if errs:
        print("roadmap 校验失败:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    body = []
    planned = [s for s in scopes if not s.get("default_a0")]
    skipped = [s["name"] for s in scopes if s.get("default_a0")]
    if skipped:
        body.append(f'<div class="note warn">以下范围未访谈,默认 A0,未出方案:{esc("、".join(skipped))}。</div>')
    if not planned:
        body.append('<div class="note warn">没有已访谈的业务范围,无方案可出。</div>')
    for s in planned:
        body.append(f'<h2>{esc(s["name"])}:{s["stage"]} → {esc(s.get("target_stage", "—"))}</h2>')
        body.append(plan_text(s))
        if s.get("target_scores"):
            body.append("<h3>图 5 现状到目标</h3>" + radar_svg(s))
        else:
            body.append('<div class="note">未给 target_scores,跳过雷达对比图。</div>')
        if s.get("platform"):
            body.append("<h3>图 6 平台接入架构</h3>" + platform_svg(s))
        if s.get("data_items"):
            body.append("<h3>数据缺口与接入方案</h3><table><tr><th>数据项</th><th>缺口</th><th>接入方式</th><th>平台上的做法</th><th>前提与风险</th></tr>"
                        + "".join(f'<tr><td>{esc(d["name"])}</td><td>{GAP_LABELS[d["gap"]]}</td><td>{esc(d["access"])}</td><td>{esc(d.get("platform_action", ""))}</td><td>{esc(d.get("risk", ""))}</td></tr>' for d in s["data_items"])
                        + "</table>")
        if s.get("roadmap"):
            body.append("<h3>图 4 Roadmap</h3>")
            body.append('<div class="scroll">' + gantt_svg(s, a.unit) + "</div>")
            body.append('<div class="tiny">红框=关键路径;灰色折线箭头=依赖;红色菱形=里程碑(取阶段门槛)。鼠标悬停任务条可看负责人、产出、验收。</div>')
            ms = s["roadmap"].get("milestones", [])
            if ms:
                body.append("<table><tr><th>里程碑</th><th>时间</th><th>对应阶段门槛</th></tr>"
                            + "".join(f'<tr><td>{esc(m["name"])}</td><td>{esc(m["at"])}</td><td>{esc(m.get("gate", ""))}</td></tr>' for m in ms) + "</table>")
        else:
            body.append('<div class="note warn">该范围还没有 roadmap 任务,未画泳道图。</div>')
    Path(a.output).write_text(page(f'{data.get("client", "")} AI 提效方案与 Roadmap', "".join(body), "依据《企业 AI 提效 Roadmap 指南》;时间为相对单位,周期与人力由顾问按客户实际填写"), encoding="utf-8")
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
