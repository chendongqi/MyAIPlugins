---
name: content-opensource-project-article-writer
description: 生成"一天一个开源项目"系列的技术文章。当用户需要创建或生成关于开源项目的技术文章时使用此技能，包括项目介绍、背景、功能分析、详细剖析等内容。适用于内容创作、技术博客写作、开源项目推广等场景。
---

# 一天一个开源项目 - 文章生成技能

本技能用于生成"一天一个开源项目"系列的技术文章，帮助读者深入了解优秀的开源项目。

## 工作流程

### Step 1: 收集项目信息

询问用户或从提供的链接获取：
- 项目名称（中英文）和 GitHub/GitLab 地址
- 系列序号（这是第几篇文章）
- 项目类型/分类、编程语言/技术栈
- 项目背景信息（作者、创建时间、统计数据等，可选）

### Step 2: 研究项目

1. 访问项目 GitHub 页面，阅读 README 和文档
2. 查看项目结构和主要功能
3. 了解作者/团队信息和项目统计数据
4. 查找同类项目进行对比

### Step 3: 生成文章

按照模板结构生成文章，确保包含所有必需部分。详细模板和格式要求见 [文章模板](references/article-template.md)。

## 文章结构要求

文章必须包含以下部分：

1. **YAML Front Matter** - 包含 title、date、description、tags、category
2. **引言部分** - 介绍项目、学习要点、前置知识
3. **项目背景** - 项目简介、作者/团队、项目数据
4. **主要功能** - 核心作用、使用场景、快速开始、核心特性、项目优势
5. **项目详细剖析** - 深入分析项目的架构、设计、实现等
6. **项目地址与资源** - GitHub、文档、社区等链接
7. **总结与展望** - 核心要点、适用人群、学习建议
8. **结尾** - 个人网站链接和系列文章导航

## 内容要求

### 写作风格

- 使用中文，语言自然流畅
- 技术术语保持英文原文，必要时加中文解释
- 代码示例必须可运行（或接近可运行），添加必要注释
- 使用多级标题组织内容，重要信息使用列表或表格

### 内容深度

- **入门友好**：解释必要的背景知识，提供足够的上下文
- **实用性强**：提供实际的使用示例和常见场景
- **深入剖析**：不仅介绍如何使用，还要解释原理和设计思路

## 格式避坑（构建会因此失败）

这个站点用 `next-mdx-remote` 渲染，文章一旦写出下面的内容，`pnpm run build` 会失败或文章被静默丢弃。

### 1. 不要在正文里用 HTML 注释

- ❌ `<!-- 图片位置：xxx -->` → MDX 报 `Unexpected character '!' before name`，**整个页面预渲染失败，构建中断**
- ✅ 需要占位说明时用 MDX 注释 `{/* 图片位置：xxx */}`，或者直接不写
- 同理，正文里不要出现未闭合的 `<标签>`、裸的 `{`、`}`（行内代码和代码块里除外）

### 2. frontmatter 的 description / title 里不要嵌套英文双引号

- ❌ `description: "…只验证"能装上"…"` → 内层引号提前结束字符串，YAMLException
- 这类错误**不会让构建失败**，只会在日志里出现 `Skipping file with invalid date`，**文章悄悄消失**，所以最容易漏
- ✅ 内层引用统一用中文引号 `「」` 或 `“”`，或者整段 description 不加引号
- 值里含冒号 `: ` 或以 `[`、`{`、`*`、`&` 开头时，也必须加引号
- 写完用 gray-matter 验证一遍（见质量检查）

### 3. 每篇必须同时写中英文两个版本

站点按语言分目录，**只写中文版会导致英文站缺文章**：

- 中文：`apps/wonderlab/content/blog/open-source-projects/<序号>-<slug>.md`
- 英文：`apps/wonderlab/content/blog-en/open-source-projects/<序号>-<slug>.md`
- 文件名（序号-slug）两边必须一致；英文版 title 用 `Open Source Project #<序号>: …`，tags 用英文
- 两个版本都要遵守上面两条格式规则：之前就是只改了中文版，英文版同样的注释导致 `/en` 页面构建失败

### 4. 图片

- 图片放在文章同目录的 `images/` 下，用 `./images/xxx.png` 引用；**不要用 `../../` 向上跳**，渲染时会报 `Path attempts to escape blog directory`
- 中英文两个目录各放一份
- 截图里如果有真实工单号、用户名、内网地址等，先问用户是否打码

## 取数方式（访问 GitHub）

- WebFetch 访问 github.com 可能被网络策略拦截（`Unable to verify if domain github.com is safe`）。此时改用 `curl`：
  - 元数据：`curl -sS https://api.github.com/repos/<owner>/<repo>`（Stars、Forks、语言、创建时间、topics、license）
  - README：`curl -sS -H 'Accept: application/vnd.github.raw' https://api.github.com/repos/<owner>/<repo>/readme`（比 raw.githubusercontent.com 稳定）
  - 发布版本：`/releases`；语言占比：`/languages`；目录结构：`/git/trees/HEAD?recursive=1`
- 本机未必有 `gh`，不要依赖
- 大文件（README 数百 KB、文件树近 1 MB）直接落盘到 `/tmp/<项目名>/` 再用脚本或分段读取，不要直接打印；网络慢时命令会超时，改成落盘 + 重试
- 抓不到的文件（例如 PROMPT.md、LICENSE）**不要凭印象写**，文中涉及时标注"据 README 转述"，并在最后告诉用户哪些没读到
- README 里的自述数据（浏览量、贡献者数、覆盖机型数等）写成"据 README 自述"，不要当作已核实的事实
- Stars、Forks、版本号增长很快，文中注明取数日期

## 质量检查

生成文章后，检查以下项目：

- [ ] YAML front matter 格式正确，包含所有必需字段
- [ ] 用 gray-matter 验证 frontmatter 能解析（在 `apps/wonderlab` 下）：`node -e "const m=require('gray-matter');const r=m(require('fs').readFileSync('<文件>','utf8'));console.log(r.data.title,r.data.date,r.data.tags.length)"`
- [ ] 全文没有 `<!--`：`grep -c '<!--' <文件>` 结果为 0
- [ ] 中英文两个版本都已创建，文件名一致
- [ ] 图片路径都是 `./images/…` 且文件存在
- [ ] 引言部分明确说明这是第X篇
- [ ] 项目背景信息完整
- [ ] 主要功能部分包含：作用、场景、快速开始、特性、优势
- [ ] 项目详细剖析部分有足够深度
- [ ] 包含项目地址（GitHub链接）
- [ ] 结尾包含个人网站链接
- [ ] 代码示例格式正确，可读性强
- [ ] 文章结构清晰，逻辑连贯

## 参考资源

- **详细模板**：见 [references/article-template.md](references/article-template.md) - 包含完整的文章结构模板和示例
- **示例文章**：参考 `apps/wonderlab/content/blog/open-source-projects/` 目录下的现有文章

## 注意事项

1. **不要修改现有文件**：除非用户明确要求，否则只创建新文件
2. **保持客观**：客观评价项目，既说明优点也指出可能的局限性
3. **时效性**：注意项目信息的时效性，使用最新的版本和特性
4. **准确性**：确保技术信息的准确性，不确定的内容要标注
5. **改完要验证**：修改或新增文章后，如果用户没有说"我自己构建"，就在 `apps/wonderlab` 下跑 `pnpm run build`，过滤掉 `LaTeX-incompatible` 和 `MDX Image` 两类 warning 再看结果，它们不影响构建；重点看 `Failed to parse MDX file`、`Skipping file with invalid date` 和 `Export encountered errors`

