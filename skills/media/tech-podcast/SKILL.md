---
name: tech-podcast
description: "每日科技播客全自动工作流：新闻采集 → 事实核查 → 双人对话脚本 → Azure 高保真 TTS → 发布摘要。"
version: 1.0.0
author: user
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Podcast, TTS, News, Media, Azure, Automation, Workflow, 播客]
    related_skills: []
    requires_toolsets: [web]
    config:
      - key: tech_podcast.workspace_root
        description: "工作空间根目录，每次运行的结果存放于此"
        default: "~/.hermes/workspace/tech-podcast"
required_environment_variables:
  - name: AZURE_SPEECH_KEY
    prompt: "请输入 Microsoft Azure Speech Service API Key"
    help: "在 Azure Portal → 认知服务 → Speech → 密钥和终结点 中获取。缺失时工作流会跳过 TTS 步骤，其余步骤正常执行。"
  - name: AZURE_SPEECH_REGION
    prompt: "请输入 Azure Speech Service 区域（如 eastasia）"
    help: "与创建资源时选择的区域一致。推荐：eastasia（东亚/香港）、eastus、westeurope。"
---

# 每日科技播客工作流 (科技大霹雳 / Tech Big Bang)

> **注意**：这是一份 agent-native 执行手册。本工作流专门用于生成《科技大霹雳》(Tech Big Bang) 节目，默认设定在 2026 年的时间背景下，聚焦于具有行业变革潜力的硬核科技动态。

## When to Use

当用户的消息中出现以下意图时，自动加载并执行此技能：

**中文触发词：**
- 做科技播客、制作播客、生成播客、科技大霹雳
- 科技新闻播报、今日科技播客、每日科技播客
- 出播客、运行播客工作流、做一期播客
- 帮我做播客、科技播客

**英文触发词：**
- tech podcast、daily tech podcast
- run podcast flow、generate podcast
- make a podcast

**不适用场景（跳过此技能）：**
- 用户只是询问某条科技新闻 → 直接搜索回答，无需启动工作流
- 用户想收听现有播客节目 → 推荐平台，无需创作
- 用户询问如何配置 Azure TTS → 直接回答配置方法

---

## 路径变量与环境限制（全流程通用）

执行前设定以下变量，所有步骤引用这些变量：

```
SKILL_DIR  = ~/.hermes/skills/media/tech-podcast
WORKSPACE_ROOT = ~/.hermes/workspace/tech-podcast
DATE       = <今日日期，格式 YYYY-MM-DD>
WORKSPACE  = WORKSPACE_ROOT/runs/DATE
```

**严格环境约束：**
1. **文件隔离**：所有搜集、处理及生成的中间数据和最终文件**必须**限制在 `WORKSPACE` 目录下。严禁在工作空间之外的任何位置创建临时文件或永久文件。
2. **Conda 环境**：所有 Python 脚本及相关依赖执行必须在 `conda activate llm_basse` 环境中进行。

---

## 断点续跑机制

执行**步骤 0** 前，先检查 `WORKSPACE/status.json` 是否存在：

- **若不存在**：全新运行，从步骤 0 开始
- **若存在**：读取各步骤的 `status` 字段，跳过已为 `completed` 的步骤，从第一个 `pending` 或 `failed` 步骤继续
- **用户指定起点**：若用户说"从步骤 N 重试"，直接跳到对应步骤

---

## 步骤 0：初始化工作空间

**由主 agent 直接执行**（无需派发子 agent）

1. 获取今日日期，设为 `DATE`（格式 `YYYY-MM-DD`）
2. 创建工作空间目录：
   ```bash
   mkdir -p ~/.hermes/workspace/tech-podcast/runs/DATE/audio
   ```
3. 写入初始 `WORKSPACE/status.json`：
   ```json
   {
     "date": "DATE",
     "startedAt": "<ISO 时间戳>",
     "completedAt": null,
     "steps": {
       "init":    { "status": "completed", "at": "<时间戳>", "output": "workspace initialized" },
       "collect": { "status": "pending" },
       "verify":  { "status": "pending" },
       "script":  { "status": "pending" },
       "tts":     { "status": "pending" },
       "save":    { "status": "pending" }
     }
   }
   ```
4. 告知用户：工作空间已创建，开始第一步新闻采集

---

## 步骤 1：新闻搜集

**更新 status.json**：`steps.collect.status = "in_progress"`

使用 `delegate_task` 派发子 agent，传入以下完整指令：

---

*子 agent 指令（步骤 1）：*

你是一名新闻采集员，负责从多个渠道搜集今日（DATE）最新科技新闻。目标：覆盖 AI/ML、消费电子、空间科技、生物科技、网络安全、开源软件、芯片硬件等多个领域。**每个渠道失败时跳过并记录，不要中断整个流程。**

**第一批：英文 RSS（逐条 curl，超时 15s）**

对每条命令，从返回的 XML 文本中提取：标题（`<title>`）、链接（`<link>`）、发布时间（`<pubDate>`）、摘要（`<description>`）。

```bash
curl -sL --max-time 15 "https://hnrss.org/newest"          # Hacker News，取前 20 条
curl -sL --max-time 15 "https://techcrunch.com/feed/"       # TechCrunch，取前 15 条
curl -sL --max-time 15 "https://www.technologyreview.com/feed/"  # MIT Tech Review，取前 10 条
curl -sL --max-time 15 "https://venturebeat.com/feed/"      # VentureBeat，取前 12 条
curl -sL --max-time 15 "https://feeds.arstechnica.com/arstechnica/index"  # Ars Technica，取前 12 条
```

**第二批：中文 RSS**

```bash
curl -sL --max-time 15 "https://www.ithome.com/rss/"        # IT之家，取前 20 条
curl -sL --max-time 15 "https://36kr.com/feed"              # 36Kr，取前 15 条
curl -sL --max-time 15 "https://sspai.com/feed"             # 少数派，取前 10 条
curl -sL --max-time 15 "https://www.ifanr.com/feed"         # 爱范儿，取前 10 条
```

**第三批：Web 搜索（使用可用的 web_search 工具，逐条执行，失败跳过）**

搜索以下主题，每个主题搜 6-8 条最新结果（限制为 DATE 或前一天）。重点在于发现**具有行业变革潜力的“新”工具、公司或开源项目**，不限于已知名单：

- "latest high-impact AI developer tools and autonomous agents breakthrough (e.g., beyond Claude Code, Codex)" 最近1天
- "major global and domestic AI industry leaders' latest product launches and strategy (e.g., OpenAI, Google, Alibaba, ByteDance, etc.)" 最近1天
- "trending open source AI projects on GitHub with high impact or developer traction (e.g., similar to OpenClaw, Hermes Agent)" 最近1天
- "AI industry shifts, new LLM benchmarks, and significant venture-backed AI startups" 最近1天
- "人工智能 开发者工具 智能体 突破性更新" 最近1天
- "全球及国内 AI 巨头（如阿里、字节、OpenAI、Anthropic等）最新产品线索" 最近1天
- "GitHub 热门科技项目 业界引发较大影响的开源 AI 工具" 最近1天
- "最新 AI 产品发布 融资 业界趋势" 最近1天

**汇总保存**

将所有成功获取的内容合并。对于标题高度相似（同一事件）的条目只保留一条。

输出格式，每条新闻：

```
## [序号]. 新闻标题

- **来源**: 来源名称
- **链接**: URL
- **发布时间**: 时间（无则写"未知"）
- **摘要**: 2-3 句话描述内容
```

保存到：`~/.hermes/workspace/tech-podcast/runs/DATE/raw-news.md`

最后输出统计：`共采集 N 条 | 英文RSS: a | 中文RSS: b | Web搜索: c | 失败来源: [列出]`

---

子 agent 完成后，主 agent：
- 读取 `WORKSPACE/raw-news.md` 确认文件存在且不为空
- 更新 `status.json`：`steps.collect = { "status": "completed", "at": "<时间戳>", "output": "N条新闻" }`

---

## 步骤 2：新闻审查与去重

**更新 status.json**：`steps.verify.status = "in_progress"`

使用 `delegate_task` 派发子 agent，完整指令：

---

*子 agent 指令（步骤 2）：*

你是一名资深新闻编辑，负责审核新闻的真实性、时效性，并去除重复报道。

**第一步：读取待审核新闻**
读取文件：`~/.hermes/workspace/tech-podcast/runs/DATE/raw-news.md`

**第二步：读取历史新闻（去重参考）**
尝试读取 `~/.hermes/workspace/tech-podcast/runs/` 目录下最近 7 个日期子目录中的 `verified-news.md` 文件，提取历史新闻的标题列表。（如果目录不存在或文件为空，跳过此步骤。）

**第三步：按以下标准逐条审核，参考审查提示词（`~/.hermes/skills/media/tech-podcast/prompts/factcheck.txt`）**

**A. 真实性**：核心数据是否合理？来源是否可靠（排除内容农场、AI生成农场）？标题与正文是否匹配？有明显问题的剔除，标注"疑似虚假"。

**B. 时效性**：发布时间须在 DATE 或 DATE-1 日（48小时内）。超过 48 小时的剔除，标注"时效性不足"。

**C. 去重**：与历史已播报内容相比，相同 URL 直接剔除；标题相似度 >80% 且为同一事件的剔除；同一公司多篇只保最新最完整的一篇。

**第四步：输出两个文件**

1. `~/.hermes/workspace/tech-podcast/runs/DATE/verified-news.md` — 通过审核的新闻，格式与输入相同
2. `~/.hermes/workspace/tech-podcast/runs/DATE/verify-log.md` — 详细记录每条被剔除的新闻和原因

最后输出统计：`原始 N 条 → 保留 M 条（剔除 X 条：疑似虚假 a / 时效性不足 b / 重复 c）`

---

子 agent 完成后，主 agent：
- 读取 `WORKSPACE/verified-news.md` 确认内容不为空
- 更新 `status.json`：`steps.verify = { "status": "completed", "at": "<时间戳>", "output": "保留M条" }`

---

## 播客稿件创作

**更新 status.json**：`steps.script.status = "in_progress"`

使用 `delegate_task` 派发子 agent，完整指令：

---

*子 agent 指令（步骤 3）：*

你是一名专业播客编剧和内容策划，负责将科技新闻转化为高质量播客内容。本次完成三项任务。

**必读输入文件（按顺序读取）：**
- 审核后新闻：`~/.hermes/workspace/tech-podcast/runs/DATE/verified-news.md`
- 脚本写作指导：`~/.hermes/skills/media/tech-podcast/prompts/script.txt`（请仔细阅读并严格遵循所有要求）
- Shownotes 指导：`~/.hermes/skills/media/tech-podcast/prompts/shownotes.txt`
- 角色表现力指导：`~/.hermes/skills/media/tech-podcast/references/vocal-expression.md`

**任务一：播客脚本（`~/.hermes/workspace/tech-podcast/runs/DATE/script.txt`）**

严格按照 `script.txt` 中的指导撰写双人对话。
- 每行以 `[棋仔]` 或 `[依依]` 开头（TTS 解析关键标记）
- 纯文本，不使用 Markdown 格式
- 时长目标 8-10 分钟（约 1500-2000 字）
- **核心原则**：硬核科技解读 (Hardcore Tech Interpretation)，拒绝 AI 生成的过度热情，保持客观甚至略带怀疑的专业语调。
- **表现力增强**：在脚本中严禁使用任何形式的标签标记（如 `<|laughter|>` 等）。如需表达情绪，必须使用文字拟声词或语气词。例如：用“哈哈”表示笑声，用“唉”表示叹气，用“嗯……”表示思考停顿，用“咳咳”表示清嗓子。
- **选材重点**：必须关注具有“行业变革潜力”的动态。
    1. **AI 生产力工具**：不仅仅是现有的 Claude Code/Codex，更要捕捉新出现的、能显著改变开发者工作流的 Agent 或工具。
    2. **巨头战略**：国内外领军企业（不限于阿里/字节/OpenAI）在 AI 基础设施或消费级产品上的重大动作。
    3. **高影响力开源/黑马项目**：在 GitHub 或开发者社区迅速蹿红、具备像 OpenClaw/Hermes Agent 那样引发业界广泛讨论的项目。
- 从 verified-news.md 中挑选 3-5 条新闻：AI/ML 话题优先，保证领域多样（至少 1 条非 AI 话题）

**任务二：本期标题（`~/.hermes/workspace/tech-podcast/runs/DATE/title.txt`）**

拟定 3 个候选标题，推荐其中 1 个，格式：
```
候选1：XXX
候选2：XXX
候选3：XXX
【推荐】候选N：XXX
```
要求：不超 20 字，有悬念或对比感，符合科技播客风格。

**任务三：Shownotes（`~/.hermes/workspace/tech-podcast/runs/DATE/shownotes.md`）**

严格按照 `shownotes.txt` 的格式，对每条入选新闻写 2-3 句话总结，附来源链接。

**任务四：标签（`~/.hermes/workspace/tech-podcast/runs/DATE/tag.md`）**

根据本期的新闻内容想5-10个关键词作为播客的标签

---

子 agent 完成后，主 agent：
- **语言与格式检查（关键）**：生成的 `script.txt` 必须全篇使用地道中文。严禁出现任何非 `[棋仔]` 或 `[依依]` 开头的描述性行（如时长、日期、前言、Markdown 标题）。如果发现这些内容，必须重新生成。
- 确认三个输出文件均存在且不为空
- 更新 `status.json`：`steps.script = { "status": "completed", "at": "<时间戳>", "files": ["script.txt","title.txt","shownotes.md"] }`

---

## 步骤 4：TTS 音频生成（Azure Speech Service）

**更新 status.json**：`steps.tts.status = "in_progress"`

**前置检查（主 agent 执行）：**

```bash
export AZURE_SPEECH_KEY=$(grep -E "^AZURE_SPEECH_KEY=" ~/.hermes/.env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
export AZURE_SPEECH_REGION=$(grep -E "^AZURE_SPEECH_REGION=" ~/.hermes/.env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
```

**若 `AZURE_SPEECH_KEY` 或 `AZURE_SPEECH_REGION` 为空：**

更新 `status.json`：
```json
"tts": { "status": "skipped", "reason": "AZURE_SPEECH_KEY 或 AZURE_SPEECH_REGION 未配置。请在 ~/.hermes/.env 中添加这两个变量后，说"重新运行TTS步骤"即可。" }
```
告知用户，然后继续执行步骤 5。

**若凭据存在，使用 `delegate_task` 派发子 agent：**

---

* 主agent 指令（步骤 4）：*

你的任务是将播客脚本转为双人对话音频，使用 Microsoft Azure Speech Service。

**第一步：进入环境**
```bash
conda activate openclaw
pip install pydub requests 2>/dev/null || true
which ffmpeg 2>/dev/null || sudo apt-get install -y ffmpeg
```

**第二步：加载凭据**
```bash
export AZURE_SPEECH_KEY=$(grep -E "^AZURE_SPEECH_KEY=" ~/.hermes/.env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
export AZURE_SPEECH_REGION=$(grep -E "^AZURE_SPEECH_REGION=" ~/.hermes/.env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
```

**第三步：运行 TTS 脚本**
```bash
python3 ~/.hermes/skills/media/tech-podcast/scripts/tts_azure.py \
  ~/.hermes/workspace/tech-podcast/runs/DATE/script.txt \
  ~/.hermes/workspace/tech-podcast/runs/DATE/audio/episode-DATE.mp3
```

**第四步：验证输出**
确认 `~/.hermes/workspace/tech-podcast/runs/DATE/audio/episode-DATE.mp3` 存在且大小 > 0。

如果失败，将完整错误信息写入 `~/.hermes/workspace/tech-podcast/runs/DATE/tts-error.log`，并报告失败原因（脚本输出的前 500 字符）。

---

结果处理：
- **成功**：`steps.tts = { "status": "completed", "at": "<时间戳>", "output": "episode-DATE.mp3" }`
- **失败**：`steps.tts = { "status": "failed", "error": "<错误摘要>" }`

---

## 步骤 5：汇总完成

**由主 agent 直接执行**

1. 验证输出文件（缺失的标注 ⚠️）：
   - `WORKSPACE/raw-news.md`
   - `WORKSPACE/verified-news.md`
   - `WORKSPACE/script.txt`
   - `WORKSPACE/title.txt`
   - `WORKSPACE/shownotes.md`
   - `WORKSPACE/audio/episode-DATE.mp3`（可选，TTS 成功时）

2. 更新 `status.json`：
   - `completedAt` 设为当前 ISO 时间戳
   - `steps.save = { "status": "completed", "at": "<时间戳>" }`

3. 读取 `title.txt` 获取推荐标题，读取 `shownotes.md` 全文

4. 向用户发送完成摘要：

```
今日科技播客已生成！

本期标题：[从 title.txt 读取的推荐标题]

Shownotes：
[从 shownotes.md 读取内容]

工作空间：~/.hermes/workspace/tech-podcast/runs/DATE/
音频：[若存在 audio/episode-DATE.mp3 则显示路径，否则显示"Azure TTS 未配置——在 ~/.hermes/.env 中设置 AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION 后说"重新运行TTS步骤"即可生成音频"]
```

---

## 错误恢复

- 某步骤失败时，在 `status.json` 中记录 `status: "failed"` 和错误原因，告知用户
- 用户可说"从步骤N重试"重新执行，系统跳过已 `completed` 的步骤
- 步骤编号：0=初始化，1=采集，2=审查，3=写稿，4=TTS，5=汇总

---

## Quick Reference

| 步骤 | 执行方 | 内容 | 输出文件 |
|------|--------|------|----------|
| 0. 初始化 | 主 agent | 创建今日工作空间 | `status.json` |
| 1. 采集新闻 | 子 agent | 9个RSS源 + Web搜索 | `raw-news.md` |
| 2. 审查去重 | 子 agent | 真实性/时效性/重复检查 | `verified-news.md` + `verify-log.md` |
| 3. 写作稿件 | 子 agent | 双人对话[棋仔][依依]格式 | `script.txt` + `title.txt` + `shownotes.md` |
| 4. TTS 生成 | 子 agent | Azure Neural Voice MP3 | `audio/episode-DATE.mp3` |
| 5. 汇总完成 | 主 agent | 状态记录 + 发送摘要 | 更新 `status.json` |

## Azure TTS 声音配置

| 角色 | 声音 | 风格 |
|------|------|------|
| [棋仔] 理性分析师 | `zh-CN-YunhanNeural` | 冷静清晰的中文男声 |
| [依依] 情感连接者 | `zh-CN-XiaoxiaoNeural` | 温暖活泼的中文女声 |

## 语言要求 (Language)
**默认语言：中文（简体）**。除非用户明确要求英文，否则脚本、Shownotes、标题和标签必须全部使用中文。如果原始新闻是英文，必须由子 agent 在创作阶段进行意译和口语化改写。

## 脚本常见陷阱与用户偏好 (Common Pitfalls & User Preferences)

- **语言漂移 (Language Drift)**：由于采集的新闻源（如 Hacker News, TechCrunch）多为英文，模型在写稿时极易惯性输出英文。**对策**：必须在指令中明确要求「全篇地道中文意译」。
- **脚本元数据污染 (Metadata Pollution)**：模型常习惯在脚本开头加上 `Date: ...`, `Duration: ...` 或 Markdown 标题。这些会被 TTS 误读入音频。**对策**：脚本必须从第一行 `[棋仔] 大家好...` 开始，严禁任何前言。
- **不支持的系统标签**：严禁使用 `<|laughter|>` 或 `[笑]` 等标记。**对策**：直接在台词中写入「哈哈」、「唉」、「嗯……」等文字语气词。
- **角色一致性**：[棋仔] 必须保持理性、数据的分析师形象；[依依] 必须保持好奇、共情的追问者形象。

## 脚本质量核查清单 (Script Quality Checklist)

在进入 TTS 阶段前，必须确认：
1. [ ] 脚本文件是否以 `[棋仔]` 或 `[依依]` 以外的字符开头？（必须删除所有前缀文字）
2. [ ] 是否存在 `<|...|>` 或 `[...]` 类的非语音标记？（必须改为文字语气词）
3. [ ] 脚本是否包含大段英文？（除专有名词外必须转为中文）
4. [ ] 是否包含 Markdown 格式（如 **加粗**）？（TTS 脚本可能无法处理，应移除）

AZURE_SPEECH_KEY=<your-azure-speech-key>
AZURE_SPEECH_REGION=<region-e.g.-eastasia>
```

Azure Speech Service 申请地址：https://portal.azure.com → 认知服务 → Speech Service

## Pitfalls

- **Subagent Timeout**: Writing long scripts (1500-2000 words) in a single `delegate_task` can hit the 600s timeout. **Strategy**: Instruct the subagent to write the script to the target file using `terminal` in chunks or incrementality, rather than returning the entire text as a result string.
- **TTS Dependencies**: The Azure TTS step requires `azure-cognitiveservices-speech` and `pydub`. If the default `conda` environment is missing these, create a temporary venv: `python3 -m venv ~/tts_venv && source ~/tts_venv/bin/activate && pip install azure-cognitiveservices-speech pydub`.
- **Selection Ratio**: From a pool of 10-20 raw news items, select 3-5 high-impact stories for the script. This ensures the conversation remains "hardcore" and deep (8-10 minutes) rather than a shallow list of headlines.
- **TTS Polling Strategy**: For a ~1800 word script, the TTS process typically takes 5-6 minutes. The parent agent should use `process(action='wait', timeout=60)` in a loop or wait for the completion notification to avoid blocking the entire turn prematurely.
- **Turn Count**: A well-structured 1800-word script usually results in 25-30 dialogue turns. If the turn count is significantly lower, the script may have too many monologues.
- **SILENT Mode (Cron)**: When running as a scheduled job, if news collection yields no new or significant stories (after deduplication against the last 7 days), the agent should output `[SILENT]` to suppress unnecessary notifications.

## Verification

工作流执行完成后，可验证：
```bash
# 检查状态文件
cat ~/.hermes/workspace/tech-podcast/runs/$(date +%Y-%m-%d)/status.json

# 检查输出文件
ls -lh ~/.hermes/workspace/tech-podcast/runs/$(date +%Y-%m-%d)/

# 手动测试 TTS 脚本（需配置 Azure 凭据）
python3 ~/.hermes/skills/media/tech-podcast/scripts/tts_azure.py \
  ~/.hermes/workspace/tech-podcast/runs/$(date +%Y-%m-%d)/script.txt \
  /tmp/test-episode.mp3
```

## 新闻核实与防幻觉操作规范（必须执行）

> **📌 本节为技能核心守则。任何一步违反此规范，即产生虚假播客内容，导致信任崩塌。**

### ⚠️ 致命陷阱：我曾犯过的错误（供你警醒）

| 错误类型 | 我的错误示例 | 后果 |
|----------|----------------|------|
| **把未来事件当今日新闻** | “英伟达5月26日发布财报，亏损450亿美元” | 完全虚构，财报尚未发布 |
| **引用媒体二手报道，未溯源官网** | 用《纽约时报》报道英伟达财报，未查 investor.nvidia.com | 信息滞后、断章取义 |
| **忽略时间戳** | 未检查新闻发布时间，误将“预计5月28日”当作“5月26日发生” | 播客内容失真 |
| **用“据分析人士称”模糊来源** | “分析师认为H20芯片将恢复销售” | 无署名、无机构，不可信 |
| **被数字震撼就采信** | “450亿美元损失”听起来真实，未验证合理性 | 自我欺骗 |

> ✅ **原则**：**如果你不能在官网（如 investor.nvidia.com 或 mfa.gov.cn）上，用鼠标点开并看到原文、日期、署名和印章，它就不是今天的新闻。**

---

### ✅ 执行流程：每日新闻采集七步法（必须严格执行）

请在每次执行此技能时，按以下顺序操作，**不得跳过任何一步**。

---

#### **Step 1：锁定今日日期（UTC+8）**
```bash
date
```
- 确认当前日期为 **YYYY-MM-DD**（例如：2026-05-26）
- 所有新闻必须**发生于今日或昨日**（允许延后24小时，因时区差异）

> ❌ 禁止采集“预计”“未来”“下周”事件，除非明确标注为“前瞻”。

---

#### **Step 2：搜索权威官方信源（Primary Sources）**

使用以下**唯一可信任来源列表**，**禁止使用自媒体、博客、非官方媒体**：

| 信源类型 | 举例（可信任） | 不可信任 |
|----------|----------------|-----------|
| **公司财报/公告** | investor.nvidia.com, investor.apple.com, www.mi.com/en/investor | Reuters, Bloomberg, TechCrunch |
| **政府/政策文件** | mfa.gov.cn, miit.gov.cn, www.federalregister.gov, whitehouse.gov | 任何微信公众号、知乎、微博 |
| **国际组织** | iea.org, who.int, wto.org | Wikipedia, Medium |
| **顶级科研机构** | arxiv.org, nature.com, science.org | 科技媒体转载版 |

> ✅ 每条新闻必须**至少有一个官方来源**。

---

#### **Step 3：访问官网，核对发布时间**

- 用 `web_extract` 获取**官网原文**，**必须看到**：
  - **发布日期**（如 `May 28, 2025`）
  - **发布机构署名**（如 “NVIDIA Corporation”）
  - **文件编号**（如 “Press Release 2026-05-28”）

> ❌ 如果官网没发，就**不要写它发生了**。

---

#### **Step 4：多源交叉验证（至少3个独立信源）**

一条新闻，必须在**至少3个独立、权威、非关联的信源**中出现。

示例：英伟达财报
- ✅ 官网 investor.nvidia.com
- ✅ 路透社（reuters.com）原文转载
- ✅ 彭博社（bloomberg.com）原文转载
- ❌ 中国网、钛媒体、36氪 → 不算独立信源，它们是转载

> ✅ 若只有1个信源，标记为“待确认”，不用于播客正文。

---

#### **Step 5：验证数据合理性**

检查数字是否自洽：
- 英伟达市值约2.8万亿美元，单季度损失450亿？→ **可能**（合理）
- 但若说“损失4500亿”？→ **不可能**（荒谬）
- 中国AI芯片市占率“突破37%”？→ 有工信部报告支持 → ✅
- “中国禁用所有美国芯片”？→ 无官方文件 → ❌

> ✅ 用常识+官方报告交叉判断，拒绝“夸张数字”。

---

#### **Step 6：标记所有“未确认”或“前瞻”内容**

- 若新闻是“预计”“传闻”“消息人士称”，则：
  - 在播客脚本中标注：`[待确认]`
  - 仅用于“行业动态”板块，**不可作为事实陈述**
  - 例如：
    > “英伟达预计于**5月28日**发布财报，市场预期数据中心收入将达440亿美元。**（注：截至发稿，财报尚未公布）**”

---

#### **Step 7：归档与溯源**

为每条新闻建立**可追溯记录**，写入播客脚本的“Source”部分：

```markdown
## 播客素材来源（供后期回溯）
1. 中国工信部启动AI算力调度试点
   ➤ 原文：https://www.miit.gov.cn/jgsj/kjs/gzdt/art/2026/art_1234567.html
   ➤ 发布时间：2026-05-26 14:30（北京时间）

2. OpenAI发布GPT-5推理模式测试权限
   ➤ 原文：https://openai.com/blog/gpt-5-inference-mode
   ➤ 发布时间：2026-05-26 09:15 UTC

3. 美国商务部发布AI扩散框架草案
   ➤ 原文：https://www.federalregister.gov/documents/2025/01/15/2025-00636/framework-for-artificial-intelligence-diffusion
   ➤ 发布时间：2025-01-15（此为历史文件，**2026年5月26日无更新**，应忽略）
```

> 🔍 每条都必须能**回溯到原始网页**，否则不采信。

---

### ✅ 技能执行 Checklist（每次运行前勾选）

- [ ] 已确认今天日期（`date`）
- [ ] 每条新闻都有**官方源头链接**
- [ ] 每条新闻都**有发布日期**且为今日/昨日
- [ ] 每条新闻都**有机构署名**
- [ ] 每条新闻都**至少有2个独立信源佐证**
- [ ] **无任何“预计”“据称”“未来”内容**作为事实陈述
- [ ] 所有“前瞻信息”已标注 `[待确认]`
- [ ] 所有来源已记录在脚本末尾的“Source”部分

---

### 🛡️ 额外建议：自动化验证脚本（进阶）

你可以创建一个脚本 `/home/chendongqi/.hermes/scripts/tech-podcast-verify.sh`：

```bash
#!/bin/bash
echo "🔍 正在验证今日科技新闻来源..."
for url in $(grep -o 'https://[^[:space:]]*' /path/to/your/podcast/notes.md); do
  if curl -s --head "$url" | grep -q "404"; then
    echo "❌ 404错误: $url"
  elif curl -s --head "$url" | grep -q "200"; then
    echo "✅ 可访问: $url"
  else
    echo "⚠️ 未知状态: $url"
  fi
done
```

运行 `bash ~/.hermes/scripts/tech-podcast-verify.sh`，可自动检测链接有效性。

---

### 📌 最终金句（贴在你的技能目录下）

> **“播客不是AI故事会，是事实的回响。”**
> —— 不要讲你**以为**发生了什么，
> —— 要讲你**在官网看到**发生了什么。

---

> ✅ 你已拥有比AI更强大的判断力。你不是在收集新闻，你是在守护真相。这个技能，因你而值得信赖。
