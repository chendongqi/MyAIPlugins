#!/usr/bin/env python3
"""校验诊断数据并按指南 3.3 节规则计算每个业务范围的阶段、瓶颈线和风险提示。

用法: score.py DIAGNOSIS.json [-o OUT.json]
  读取诊断数据(见 assets/diagnosis-schema.json),写回计算结果:
  每个 scope 增加 stage / bottlenecks / risks;未访谈的 scope 固定为 A0。
  校验失败时在 stderr 列出全部问题并以非零状态退出,不写输出。

规则(指南 3.3):
  门控线: tools, workflow, data, infra, governance   支撑线: org, metrics
  1. tools 为 L0 -> A0。
  2. 否则取满足"所有门控线 >= n"的最高 n(A1 只要求 tools >= 1)。
  3. 瓶颈线: 门控线中低于"下一阶段"要求的那些。已是 A4 则无瓶颈线。
  4. 风险提示: 支撑线低于当前阶段 2 级以上。
"""
import argparse
import json
import sys
from pathlib import Path

GATING = ["tools", "workflow", "data", "infra", "governance"]
SUPPORT = ["org", "metrics"]
LINES = GATING + SUPPORT
LINE_NAMES = {
    "tools": "工具与 Skill",
    "workflow": "Workflow 与协作",
    "data": "数据与知识",
    "infra": "基建与平台",
    "governance": "治理与安全",
    "org": "组织与人",
    "metrics": "度量与价值",
}
STAGES = ["A0", "A1", "A2", "A3", "A4"]
GAPS = {"missing", "unreachable", "unusable", "insufficient"}
PLATFORM_TYPES = {"I", "II"}
ROUTES = {"a", "b", "c"}


def stage_index(stage: str) -> int:
    return STAGES.index(stage)


def compute_stage(scores: dict) -> int:
    if scores["tools"] == 0:
        return 0
    best = 1  # tools >= 1 已满足 A1
    for n in range(2, 5):
        if all(scores[k] >= n for k in GATING):
            best = n
        else:
            break
    return best


def bottlenecks(scores: dict, stage: int) -> list:
    if stage >= 4:
        return []
    need = max(stage + 1, 1)
    # A0 -> A1 只看 tools
    if stage == 0:
        return ["tools"]
    return [k for k in GATING if scores[k] < need]


def risks(scores: dict, stage: int) -> list:
    out = []
    for k in SUPPORT:
        if scores[k] <= stage - 2:
            out.append(
                {
                    "line": k,
                    "message": f"{LINE_NAMES[k]}仅 L{scores[k]},低于当前阶段 A{stage} 两级以上,投入产出或责任缺位,容易被砍或失控",
                }
            )
    return out


def validate(data: dict) -> list:
    errs = []
    if not isinstance(data.get("scopes"), list) or not data["scopes"]:
        errs.append("scopes 必须是非空数组")
        return errs
    ids = set()
    for i, s in enumerate(data["scopes"]):
        tag = f"scopes[{i}]({s.get('name', '?')})"
        for f in ("id", "name", "interviewed"):
            if f not in s:
                errs.append(f"{tag}: 缺少字段 {f}")
        if s.get("id") in ids:
            errs.append(f"{tag}: id 重复 {s['id']}")
        ids.add(s.get("id"))
        if s.get("interviewed"):
            sc = s.get("scores")
            if not isinstance(sc, dict):
                errs.append(f"{tag}: 已访谈的范围必须有 scores")
            else:
                for k in LINES:
                    v = sc.get(k)
                    if not isinstance(v, int) or not 0 <= v <= 4:
                        errs.append(f"{tag}: scores.{k} 必须是 0-4 的整数,当前 {v!r}")
            # 每个分数需要证据或标记待证实
            ev = s.get("evidence", {})
            unv = set(s.get("unverified", []))
            for k in LINES:
                if isinstance(sc, dict) and sc.get(k, 0) > 0 and not ev.get(k) and k not in unv:
                    errs.append(f"{tag}: {k} 有分数但既无证据也未标为 unverified(指南 7.3:无证据须标待证实)")
            ts = s.get("target_stage")
            if ts is not None and ts not in STAGES:
                errs.append(f"{tag}: target_stage 必须是 {STAGES}")
        else:
            if s.get("scores"):
                errs.append(f"{tag}: 未访谈的范围不应有 scores(默认 A0)")
        plat = s.get("platform")
        if plat:
            if plat.get("type") not in PLATFORM_TYPES:
                errs.append(f"{tag}: platform.type 必须是 I 或 II")
            if plat.get("type") == "II" and plat.get("route") not in ROUTES:
                errs.append(f"{tag}: II 类平台必须给 route(a/b/c)")
        for j, d in enumerate(s.get("data_items", [])):
            dt = f"{tag}.data_items[{j}]"
            if d.get("gap") not in GAPS:
                errs.append(f"{dt}: gap 必须是 {sorted(GAPS)}")
            for f in ("name", "system", "access"):
                if not d.get(f):
                    errs.append(f"{dt}: 缺少 {f}")
    return errs


def process(data: dict) -> dict:
    for s in data["scopes"]:
        if not s.get("interviewed"):
            s["stage"] = "A0"
            s["bottlenecks"] = []
            s["risks"] = []
            s["default_a0"] = True
            continue
        n = compute_stage(s["scores"])
        s["stage"] = STAGES[n]
        s["bottlenecks"] = bottlenecks(s["scores"], n)
        s["risks"] = risks(s["scores"], n)
        s["default_a0"] = False
        ts = s.get("target_stage")
        if ts and stage_index(ts) < n:
            s.setdefault("warnings", []).append(f"目标阶段 {ts} 低于当前阶段 {STAGES[n]}")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    errs = validate(data)
    if errs:
        print("诊断数据校验失败:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    data = process(data)
    out = Path(args.output) if args.output else Path(args.input)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    for s in data["scopes"]:
        tail = "(未访谈,默认 A0)" if s["default_a0"] else f" 瓶颈线: {','.join(s['bottlenecks']) or '无'}"
        print(f"{s['name']}: {s['stage']}{tail}")


if __name__ == "__main__":
    main()
