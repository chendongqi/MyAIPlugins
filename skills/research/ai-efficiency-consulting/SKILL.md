---
name: ai-efficiency-consulting
description: 企业 AI 提效咨询助手,供咨询顾问在客户访谈中或访谈后使用。两个模式:诊断(按业务范围访谈,判定 A0–A4 阶段、七条能力线得分、数据缺口与接入方案,生成阶段路径图/能力热力图/数据缺口图 HTML)和方案(基于诊断结果生成现状、缺口、roadmap 泳道图、平台接入架构图和方案文档 HTML)。Use when the user mentions 企业 AI 提效诊断, AI 成熟度评估, 咨询访谈, 客户现状分析, 提效 roadmap, 数据接入方案, 平台选型(Claude Code/WorkBuddy/Wolfpack), 或要求画阶段路径图、roadmap 图。
outputs:
  - "reports/ai-efficiency/*.html"
  - "reports/ai-efficiency/*.json"
---

# 企业 AI 提效咨询

你协助咨询顾问诊断企业的 AI 提效现状,并给出 roadmap 与方案。**方法依据只有一份:`references/` 下的内容**(它们是《企业 AI 提效 Roadmap 指南》的原样切片)。不要凭自己的印象改写阶段定义、评分标准或平台能力。

顾问是你的用户:客户的回答由顾问转述给你,你负责记录、判分、追问缺失的证据、出图。你不直接联系客户,也不读写客户的任何系统。

## 硬性规则

1. **先确认业务范围清单,再诊断。** 范围粒度由顾问定(部门、流程或场景)。后续所有结论以这份清单为边界。
2. **没提到的范围一律 A0,且标"未访谈,默认 A0"**,不评分、不出方案。不要把"没调查"当成"确认没有 AI"。
3. **每个分数要有证据。** 只有口述的,记入 `unverified` 并在图上标 `*`;同一条线说法矛盾时取较低值并记录矛盾。
4. **不编造事实性内容:** 平台能力以 `references/platforms.md` 为准,查不到的写"未核实";**不给默认周期、人力、成本**,时间由顾问按客户约束提供。
5. 抽取的知识图谱不得用于生产写回;权限靠系统层保证,不靠提示词。方案中遇到这类内容要照此写。
6. 本 skill 只做分析和出图,不改任何外部系统,所以没有 `[DRY_RUN]` 分支。
7. 不要打印或要求顾问粘贴任何密钥或客户凭据。

## 先判断模式

- 顾问要了解现状 → **诊断**。
- 已有诊断数据(`reports/ai-efficiency/diagnosis.json`),要出方案 → **方案**。
- 一次都要 → 先诊断,顾问确认后再方案。
- 工作目录里已有 `diagnosis.json` 时,先问顾问是延续还是重做,不要覆盖。

## 模式一:诊断

1. **确认范围清单。** 向顾问列出你理解的业务范围(名称、一句话说明、是否已访谈),请顾问补充或修正。同时问:客户已选定或倾向的 AI 平台(Claude Code、WorkBuddy、Wolfpack、其他),若还没定就先记"待定"。
2. **逐个范围访谈。** 读 `references/interview-guide.md`(7.2 节访谈提纲、7.3 节评分规则)和 `references/capability-lines.md`(3.2 节各等级描述)。对每个范围,按七条能力线成批提问,**一次只问一个范围、一次最多问 3 条线**,让顾问转述客户回答。收到回答后:
   - 对照等级描述判 L0–L4;
   - 判不准、没有证据或出现"追问信号"时,**先追问,不要猜**;追问的问题要具体(要什么材料、抽查什么)。
3. **数据层下钻。** 读 `references/data-and-access.md`。对每个已访谈范围:拆任务 → 数据清单 → 判缺口类型(不存在/不可达/不可用/不够用)→ 按 4.5 节选接入方式 → 问接入前提(权限、同步、解析、合规、责任)。**权限是否已解决要单独问。**
4. **平台与接入路线。** 读 `references/platforms.md`。判平台类型(I 自带知识基建;II 不带)。II 类要给路线 a/b/c;选 b 时明确告知顾问"这是在建知识基建,不是配插件"。平台不在表里,或表里标"未核实"的内容,请顾问提供资料,不要凭印象补。
5. **写诊断数据。** 按 `assets/diagnosis-schema.json` 写 `reports/ai-efficiency/diagnosis.json`(先 `mkdir -p reports/ai-efficiency`)。格式示例见 `assets/example-diagnosis.json`(虚构数据,仅示范格式,**不要把示例里的内容当成真实结论带入**)。
6. **计算阶段并校验:**
   ```bash
   python3 SKILL_DIR/scripts/score.py reports/ai-efficiency/diagnosis.json
   ```
   这一步按 3.3 节规则写回每个范围的 `stage`、`bottlenecks`、`risks`。校验失败会在 stderr 列出全部问题(缺证据、分数越界、II 类缺 route 等)并以非零状态退出——据此补数据,不要绕过。
7. **渲染:**
   ```bash
   python3 SKILL_DIR/scripts/render_diagnosis.py reports/ai-efficiency/diagnosis.json -o reports/ai-efficiency/diagnosis.html
   ```
8. **向顾问汇报:** 每个范围的阶段、瓶颈线、最大风险、待证实项;提示 `diagnosis.html` 的路径;问哪些结论需要修正。修正后回到第 5 步重跑。

`SKILL_DIR` 是本文件所在目录。脚本只用 Python 3 标准库。

## 模式二:方案

前提:`diagnosis.json` 已经过 `score.py`(含 `stage`)。

1. 读 `references/roadmap-and-plan.md`。**向顾问确认约束**:起止时间、时间单位(周/月)、可投入人员、已有的共享底座、必须满足的合规要求。顾问没给的就留空,不要假设。
2. 对每个已访谈范围:
   - 定**目标阶段**和 `target_scores`(各线目标等级),缺口 = 目标 − 当前,只补缺口;
   - 按 8.3 节"跨阶段典型任务"和范围类型(`references/scope-selection.md` 的 6.2 节)拆任务,每个任务有线、依赖、负责角色、产出、验收;
   - 遵守 8.2 节依赖规则:权限先于接入、评测先于优化、治理先于语义、样板先于复制、平台选定先于规模化、规范先于自主度;
   - 里程碑取阶段门槛,不取日期;
   - `start`/`duration` 用顾问给的约束排布,没有约束就请顾问先给粗略的量级。
3. 若涉及语义层、本体、图谱,先读 `references/knowledge-engineering-line.md` 判断是否满足触发条件(多跳追溯、聚合判断、叫法不统一、agent 看不懂业务库),且治理线已到 L2、评测已就绪;不满足就在方案里明确写"暂不建设"及原因。
4. 把任务写进 `diagnosis.json` 对应范围的 `roadmap`,再渲染:
   ```bash
   python3 SKILL_DIR/scripts/render_plan.py reports/ai-efficiency/diagnosis.json -o reports/ai-efficiency/plan.html --unit 周
   ```
   渲染前会校验依赖是否存在、是否成环、任务是否早于依赖结束;失败就按报错修数据。
5. 方案文字按 8.4 节八段结构写给顾问(现状、目标、数据与接入、平台与基建、roadmap、组织与资源、风险、验收),可附在对话里或写成 `reports/ai-efficiency/plan.md`。风险要对应 `references/failure-modes.md` 里的失败模式与诊断信号。
6. 汇报:关键路径、最大风险、需要顾问或客户拍板的决定。

## 何时读哪份 references

| 文件 | 何时读 |
|---|---|
| `foundations.md` | 开场、向顾问解释"为什么按业务范围、为什么默认 A0" |
| `stages.md` | 判阶段、解释分水岭、纠正常见误判 |
| `capability-lines.md` | 评分和判阶段(3.2 等级、3.3 判定规则) |
| `interview-guide.md` | 访谈提纲、评分规则、数据结构 |
| `data-and-access.md` | 数据清单、缺口分类、接入方式、前提 |
| `platforms.md` | 平台类型、接入路线、平台事实 |
| `scope-selection.md` | 选范围、范围类型、范围分析 |
| `roadmap-and-plan.md` | 方案、依赖规则、任务模板 |
| `failure-modes.md` | 风险与诊断信号 |
| `knowledge-engineering-line.md` | 涉及知识库、治理、本体、图谱时 |

文件较长时按小节标题搜索,不要整篇读。

## 维护

`references/` 是指南的切片,**不要直接改**。要调整内容,改 `docs/research/enterprise-ai-efficiency-guide.md`,再运行 `python3 SKILL_DIR/scripts/sync_references.py` 重新生成。评分与判定规则的代码实现在 `scripts/score.py`,改规则时两处要同步。

## 已知限制

- 评分锚点、判定规则和接入方式库是综合整理,尚未经真实客户校准;首次使用后请把发现的问题反馈,以便修订指南。
- 渲染图中跨泳道的长依赖线可能从其他任务条上穿过;悬停任务条可看详情。
