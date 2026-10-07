---
name: startup-idea-reviewer
description: Guide for finding and reviewing/screening startup (创业) ideas using YC partner Jared Friedman's idea-finding framework. This skill should be used when a user wants to brainstorm new startup/business ideas, or wants an existing startup idea critically reviewed/vetted before committing to it (checking for founder-market fit, pain point strength, timing/new variables, and common idea-finding traps).
---

# Startup Idea Reviewer

## Overview

This skill applies YC partner Jared Friedman's idea-finding framework to either (1) help a user generate promising startup idea directions, or (2) rigorously review/screen an existing startup idea the user already has. The full framework is detailed in `references/jared-friedman-framework.md` — read it before doing substantive work with this skill.

## When to Use Which Mode

- **Review mode**: Triggered when the user already has a specific idea and wants feedback, validation, or a "gut check" before pursuing it.
- **Discovery mode**: Triggered when the user has no idea yet and wants help finding one, based on their own background/team.

Ask the user which situation they're in if it isn't clear from context.

## Review Mode: Screening an Existing Idea

Walk through the idea against the framework in this order. Do not just summarize the framework back at the user — actually apply each check to the specifics of their idea and give a concrete verdict for each.

1. **Trap check (三个坑)** — For each of the three traps, explicitly state whether the idea falls into it and why:
   - 拿锤子找钉子：Did the idea originate from a technology/solution looking for a problem, or from a real observed problem?
   - 焦油坑：Does this look like an easy, obvious pain point that others have already tried and failed at due to a structural barrier (e.g. network effects, regulation, distribution lock-in)? If the idea resembles a known graveyard category (social apps against WeChat's relationship graph, etc.), explicitly ask/search for who has tried this before and how they failed.
   - 两个极端：Is the user about to go all-in with zero validation, or stuck waiting for a "perfect" idea without shipping anything? Push toward "fire, then aim" — recommend the smallest testable version.

2. **Three hard standards (三个硬标准)** — Score the idea on each, with reasoning, not just a label:
   - 创始人与市场的匹配度：Ask about the user's/team's relevant background. An idea cannot be evaluated in the abstract — tie the verdict to who is actually building it.
   - 痛点够不够痛：Determine if this is a 痒点 (nice-to-have, users have workarounds) or a真正痛点 (users are stuck without it). Ask what the user currently does without this product — if there's an easy workaround, flag it as a 痒点.
   - 新变量：Identify what recent technological, regulatory, or infrastructure shift makes this newly possible or newly necessary now (vs. 5 years ago). If no clear new variable exists, flag this as a risk — the idea may be timing-agnostic noise rather than a real opportunity.

3. **Hidden-gold check (三类被嫌弃的金矿)** — Check if the idea exhibits traits that make it *more* attractive despite looking unattractive on the surface:
   - 高门槛/脏活累活 → protective moat
   - 听起来无聊/土 → low competition, high survival rate
   - 红海但巨头没解决根本问题 → real demand proven, look for the collectively-ignored weakness
   - If the idea has NONE of these traits and is instead easy, trendy, and already crowded with well-funded competitors who ARE solving the core problem, flag this as a serious warning sign.

4. **Verdict** — End with a clear, direct summary: proceed / proceed with a specific pivot / do more validation first / likely a trap — and the single biggest risk to address next. Avoid hedging; give an actual opinion.

## Discovery Mode: Finding a New Idea

1. **盘点基因资产**: Ask the user to list out past jobs, projects, side gigs, and industries they've touched. Push for specifics that are non-obvious to outsiders — industry secrets, broken processes, inefficiencies the user has personally witnessed but most people haven't. Generic "I worked in tech" answers aren't useful; dig for the specific insider knowledge.

2. **用脚跑出点子**: If the user hasn't yet talked to people on the ground in a target industry, recommend concrete field research — specific people/places to go talk to, not desk research. Encourage talking to practitioners directly rather than reading reports.

3. From the gathered background, propose 2-4 candidate directions that connect the user's unique experience to a real-world problem, and run each candidate through the Review Mode checklist above before presenting it — don't suggest ideas that would fail the framework's own tests.

## Reference

See `references/jared-friedman-framework.md` for the complete framework with all examples (京东自建物流, 钉钉, 支付宝担保交易, etc.) — use these examples when explaining a concept to the user, and draw structurally similar analogies for their specific idea.
