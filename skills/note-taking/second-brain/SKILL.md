---
name: second-brain
description: "Multi-domain personal knowledge base (second-brain monorepo): route via DOMAINS.md to the right domain, then ingest/query using LLM Wiki conventions; manual cross-domain health-check mode for dedup and broken links."
version: 1.0.0
author: Cheson
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, knowledge-base, research, notes, markdown, rag-alternative, multi-domain]
    category: research
    related_skills: [obsidian, arxiv]
---

# Second Brain (multi-domain LLM Wiki)

Build and maintain a persistent, compounding knowledge base as interlinked markdown
files, split across multiple **domains** inside one vault (one git repo). Based on
[Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f),
extended with a top-level routing index so the vault can hold many unrelated subject
areas without every operation having to scan all of them.

Unlike traditional RAG (which rediscovers knowledge from scratch per query), the wiki
compiles knowledge once and keeps it current. Cross-references are already there.
Contradictions have already been flagged. Synthesis reflects everything ingested.

**Division of labor:** The human curates sources and directs analysis. The agent
summarizes, cross-references, files, routes to the correct domain, and maintains
consistency — both within a domain and, when asked, across domains.

This skill supersedes `llm-wiki` for vaults that have outgrown a single flat
structure. If `$WIKI_PATH` has no top-level `DOMAINS.md`, this skill does not
apply — that's a single-domain vault, use `llm-wiki` instead.

## When This Skill Activates

Use this skill when the user:
- Asks to create, build, or start a personal knowledge base / "second brain"
- Asks to ingest, add, or process a source into their wiki, and `$WIKI_PATH`
  contains a `DOMAINS.md`
- Asks a question and the configured wiki is a multi-domain vault (has `DOMAINS.md`)
- Asks to lint, audit, or health-check a domain, or asks for a **cross-domain**
  health check specifically
- References "second brain", "wiki", "knowledge base", or "notes" when the vault
  at `$WIKI_PATH` is multi-domain

## Wiki Location

**Location:** Read via `WIKI_PATH` environment variable (e.g. in `~/.bashrc`).

```bash
echo $WIKI_PATH
```

If unset, ask the user — do not guess a default for a multi-domain vault.

```bash
WIKI="$WIKI_PATH"
```

The wiki is just a directory of markdown files — open it in Obsidian, VS Code, or
any editor. No database, no special tooling required. Obsidian opens `$WIKI_PATH`
itself as the vault root (not any single domain subdirectory), so `[[wikilinks]]`
resolve across domains and the graph view shows the whole vault; use Graph View
groups/filters with `path:` prefixes (e.g. `path:ops-handbook`) to visually
separate domains when needed.

## Architecture: Routing Layer + Per-Domain Three Layers

```
second-brain/                    # vault root = $WIKI_PATH, one git repo
├── DOMAINS.md                   # ROUTING INDEX — read this FIRST, every time
├── ai-intelligence/             # domain
│   ├── SCHEMA.md                # conventions + "Vault Context" note
│   ├── index.md
│   ├── log.md
│   ├── raw/ entities/ concepts/ comparisons/ queries/
├── ops-handbook/                # another domain, same internal shape
│   ├── SCHEMA.md
│   ├── index.md
│   ├── log.md
│   ├── raw/ entities/ concepts/ comparisons/ queries/
└── _inbox/                      # optional: unclassified content awaiting a decision
```

Each domain directory is internally identical to a standalone `llm-wiki` vault:
`SCHEMA.md` / `index.md` / `log.md` + `raw/` / `entities/` / `concepts/` /
`comparisons/` / `queries/`. The only things specific to the multi-domain setup are:

- **`DOMAINS.md`** at the vault root — a short index (a few hundred tokens) listing
  every domain's coverage description, keywords, and path. This is the mechanism
  that keeps token cost and latency low: read this ~instantly, then enter exactly
  one (or a few) domain directories instead of scanning the whole vault.
- **"Vault Context" note** at the top of each domain's `SCHEMA.md` — reminds the
  agent (if it somehow lands inside a domain without having read `DOMAINS.md`
  first) to go check the routing index before assuming the content belongs here.
- **`sources:` frontmatter paths are domain-relative**, e.g. `raw/articles/x.md`
  means `<domain>/raw/articles/x.md`, not `<vault-root>/raw/articles/x.md`.

Everything else — frontmatter schema, `[[wikilinks]]`, provenance markers, page
thresholds, tag taxonomy discipline — is unchanged from `llm-wiki` and documented
per-domain in that domain's own `SCHEMA.md`.

## Resuming a Session (CRITICAL — do this every time, before Ingest or Query)

**Never scan all domains.** Always route first:

① **Read `$WIKI_PATH/DOMAINS.md`** — a few hundred tokens, lists every domain's
   coverage + keywords + path. This alone tells you where to go.
② **Match the task's topic against each domain's coverage/keywords** to pick one,
   several, or zero candidate domains (see Ingest/Query sections below for what
   to do in each case).
③ **Only then enter the candidate domain directory** and read its `SCHEMA.md`
   (note the "Vault Context" block, then the rest) + `index.md`.
④ **For a domain with 100+ pages**, also run `search_files` scoped to that domain's
   path before creating anything new.

Skipping step ① and scanning everything defeats the entire purpose of splitting
into domains — don't do it, even "just to be thorough." If `DOMAINS.md` doesn't
clearly resolve the task, that itself is the zero/multi-match case below — handle
it there, don't fall back to a full scan.

## Initializing a New Vault

When the user asks to create a second-brain-style vault from scratch:

1. Determine the vault path (from `$WIKI_PATH`, or ask the user)
2. Create `DOMAINS.md` at the root (template below) with the user's first domain(s)
3. For each initial domain, create the per-domain structure (same as `llm-wiki`'s
   `SCHEMA.md` / `index.md` / `log.md` template, plus the "Vault Context" block)
4. Confirm the vault is ready and suggest first sources to ingest

### DOMAINS.md Template

```markdown
# Wiki Domains

> Read this file FIRST to pick a domain, before entering any subdirectory.
> Do not scan all domains at once — this is what keeps token cost and query
> latency low.
> Each domain's `sources:` frontmatter paths (e.g. `raw/articles/x.md`) are
> relative to that domain's directory, not the vault root.

## <domain-slug>/
Coverage: <one or two sentences describing what this domain covers>
Keywords: <comma-separated terms a classifier would match on>
Path: <domain-slug>/
```

Add one section per domain. Keep each domain's description and keyword list tight
enough that a quick skim resolves most incoming content unambiguously.

### Per-domain SCHEMA.md Template

Identical to `llm-wiki`'s template, with one addition at the top:

```markdown
# Wiki Schema

## Vault Context
This directory is one domain inside the second-brain vault. If the content being
ingested/queried clearly doesn't belong here, check the top-level `DOMAINS.md`
first to find the right domain.

## Domain
[What this domain covers — be specific]

## Conventions
[... same as llm-wiki SCHEMA.md: file naming, frontmatter, wikilinks, provenance
markers, index/log update rules ...]

## Frontmatter
[... same as llm-wiki: title/created/updated/type/tags/sources/confidence/
contested/contradictions ...]

## Tag Taxonomy
[... domain-specific tags ...]

## Page Thresholds
[... same rules as llm-wiki ...]

## Entity Pages / Concept Pages / Comparison Pages
[... same as llm-wiki ...]

## Update Policy
[... same as llm-wiki ...]
```

`index.md` and `log.md` templates are unchanged from `llm-wiki` — see that skill's
SKILL.md if a byte-for-byte template is needed; the shape is identical, just scoped
to one domain's content instead of a whole vault.

## Core Operations

### 1. Ingest — classify into a domain, then ingest normally

① **Capture the raw source** exactly as in `llm-wiki` (web_extract / paste →
   `raw/<subtype>/`, with `source_url` / `ingested` / `sha256` frontmatter) —
   but do this *after* step ② below has picked the domain, so the raw file lands
   in the right domain's `raw/` directory.

② **Classify against `DOMAINS.md`** — compare the source's subject matter to each
   domain's coverage description and keywords:

   - **Single clear match** → proceed into that domain, run the rest of Ingest
     exactly as `llm-wiki` describes it (check existing pages, create/update
     entity/concept/comparison pages per that domain's `SCHEMA.md` Page
     Thresholds, cross-reference, tag from that domain's taxonomy, provenance
     markers, confidence), then update that domain's `index.md` and `log.md`.

   - **Multiple domains plausible** (e.g. an AI-agent deployment tool that is
     both an AI-tooling topic and an ops/deployment topic) → tell the user which
     domains are candidates and why, let them pick the primary domain. Write the
     full page only in the primary domain. In the non-primary domain's `index.md`,
     add a single one-line cross-reference entry pointing at the primary page
     (e.g. `- [[../ai-intelligence/entities/foo|foo]] — primarily filed under
     ai-intelligence; see there for details`) instead of duplicating content.

   - **Zero match** (doesn't fit any domain's coverage/keywords) → **stop
     immediately and ask the user.** Do not wait for repeated occurrences, do
     not count how many times similar content has shown up, do not park it
     silently — surface it the very first time. Present three options:
     1. File it into the existing domain that's the closest fit, even if imperfect
     2. Create a new domain: new `<slug>/SCHEMA.md` + `index.md` + `log.md`
        (using the per-domain template above, customized), and append a new
        section to `DOMAINS.md` with its coverage/keywords/path
     3. Park it in a top-level `_inbox/` (plain file, no domain structure) for
        the user to decide on later
     Proceed only after the user picks.

③ **Update navigation** inside the chosen domain only: `index.md` entry +
   "Total pages"/"Last updated" header bump, `log.md` append — exactly as
   `llm-wiki` describes, scoped to that one domain.

④ **Report what changed**, including which domain it landed in and why, so the
   user can correct a bad classification immediately rather than discovering it
   during a later health check.

### 2. Query — route, then answer from inside the matched domain(s)

① **Read `DOMAINS.md`**, pick candidate domain(s) for the question.
② **Read only those domains' `index.md`** — not every domain's.
③ Read the specific relevant pages, synthesize an answer, cite pages as
   `[[page-a]]` / `[[page-b]]` as in `llm-wiki`.
④ If the question is explicitly cross-domain (asks to compare something that
   lives in two different domains), it's fine to open index.md for each of those
   specific domains — this is still "enter only what's needed," not a full scan.
⑤ File substantial synthesized answers into `queries/` or `comparisons/` inside
   whichever domain the answer most belongs to (same filing judgment as
   `llm-wiki`). If it's genuinely a cross-domain synthesis with no obvious home,
   ask the user which domain should own it, or default to `_inbox/`.
⑥ Append to that domain's `log.md`.

### 3. Lint — single domain only, no cross-domain checks

When the user asks to lint/audit/health-check **a domain** (not the whole vault):

Run the same checks `llm-wiki` runs (orphan pages, broken wikilinks, index
completeness, frontmatter validation, stale content, contradictions, quality
signals, source drift, page size, tag audit, log rotation) — **scoped strictly
to that one domain's directory.** Do not look at other domains, and do not run
duplicate detection against other domains here — that's a different operation
(below). Append findings to that domain's `log.md`.

### 4. Health Check — manual, cross-domain, NOT run automatically

A distinct fourth operation. **Only run this when the user explicitly asks for
it** (e.g. "do a wiki health check", "check for duplicates across domains") —
never as a side effect of Ingest, Query, or a per-domain Lint. This is deliberately
separated out because it's more expensive (reads across every domain) and isn't
needed on every task.

① **Read `DOMAINS.md`** to enumerate every domain. For each domain, read its
   `index.md` and the frontmatter (title/tags/sources — not full body text) of
   every page, to keep cost down.

② **Cross-domain duplicate detection:**
   - **Deterministic:** the same filename exists under more than one domain
     (e.g. `entities/openship.md` present in both `ai-intelligence/` and
     `ops-handbook/`) → flag as a confirmed duplicate.
   - **Heuristic:** different filenames but near-identical `title`/`tags` →
     flag as "suspected duplicate" for the user to confirm; never auto-merge these.
   - **Resolution for confirmed duplicates:** compare `confidence`, `contested`,
     `updated` date, and source count on both sides; recommend the more
     thorough/recent one as canonical (e.g. a page updated more recently with
     more sources and an explicit contradictions section beats an older,
     single-source version covering the same entity).
   - **Mechanism:** reuse the existing in-domain stub pattern (a short page whose
     body is just a redirect note), but because the canonical page lives in a
     *different* domain, filenames are identical across domains — a bare
     `[[openship]]` wikilink is ambiguous in Obsidian (resolves by basename).
     Stub bodies in this cross-domain case **must use an explicit relative path
     + alias**, e.g.:
     ```markdown
     ## Redirect
     Canonical page: [[../ops-handbook/entities/openship|openship (ops-handbook)]]
     ```
     Also update both domains' `index.md` entries to note the merge (keep an
     entry in the non-canonical domain's index pointing at the canonical one,
     don't just delete it silently).
   - **Never auto-merge** — present a report and wait for confirmation, unless
     the user explicitly said "just fix it" when triggering the health check.

③ **Broken wikilinks:** scan every `[[name]]` / `[[path|alias]]` across all
   domains, check the target resolves to a real file anywhere in the vault
   (same-domain or cross-domain), list unresolved ones.

④ **Orphan pages across domains:** pages that exist on disk in some domain but
   are not referenced by that domain's own `index.md`.

⑤ **Report**, grouped by category (confirmed duplicates / suspected duplicates /
   broken links / orphan pages), each with a suggested action. Wait for the
   user's go-ahead before writing any fix, unless told to apply fixes directly.

⑥ Log the health check and its outcome — in the `log.md` of whichever domain(s)
   were actually modified as a result, or in a vault-root note if nothing else
   fits (don't invent a new always-on cross-domain log file for this; it's
   infrequent enough that per-domain logging of the fix is enough).

## Working with the Wiki

### Searching

```bash
# Scope every search to a specific domain once DOMAINS.md has picked one
search_files "transformer" path="$WIKI_PATH/ai-intelligence" file_glob="*.md"

# Only search the whole vault during an explicit Health Check
search_files "openship" path="$WIKI_PATH" file_glob="*.md"
```

### Bulk Ingest

Same batching approach as `llm-wiki`, but classify once per batch:
1. Read all sources first
2. Classify the batch against `DOMAINS.md` — group sources by domain (and flag
   any zero-match ones immediately, per the Ingest rules above, don't batch
   those into a "decide later" pile)
3. Within each domain group, check existing pages once, then create/update in
   one pass
4. Update each affected domain's `index.md` once at the end
5. One log entry per affected domain's `log.md`

### Archiving

Same as `llm-wiki`, scoped to the owning domain: move to `<domain>/_archive/`,
remove from that domain's `index.md`, fix inbound links, log it.

### Obsidian Integration

Open `$WIKI_PATH` itself (the vault root containing `DOMAINS.md`) as the Obsidian
vault — not an individual domain subdirectory. This keeps `[[wikilinks]]` resolving
vault-wide (needed for the cross-domain stub links in Health Check) and the graph
view complete. Use Graph View filters/groups with `path:<domain>` to visually
isolate a domain when working inside it.

Everything else (Dataview, headless sync, attachment folder conventions) is
unchanged from `llm-wiki` — see that skill's SKILL.md for the setup details if
needed.

## Pitfalls

- **Never scan all domains for Ingest/Query** — always read `DOMAINS.md` first
  and enter only the matched domain(s). This is the entire point of the
  multi-domain structure; skipping it reintroduces the token/latency cost the
  split was meant to avoid.
- **Don't gate new-domain creation on an occurrence count** — a zero-match
  source gets surfaced to the user immediately, every time. Silently parking
  content "until it happens a few more times" loses it.
- **Don't run cross-domain duplicate detection automatically** — it's a distinct,
  user-triggered Health Check operation, not a step inside Ingest/Query/Lint.
- **Don't duplicate full pages across domains** for multi-domain-plausible
  content — pick one primary domain, cross-reference lightly from the others.
- **Cross-domain stub links need explicit relative paths + alias**, never a bare
  `[[name]]`, because the same filename can legitimately exist in two domains.
- **Never modify files in any domain's `raw/`** — sources are immutable.
- **Always update the owning domain's `index.md` and `log.md`** — skipping this
  degrades that domain's navigability.
- **Tags must come from that domain's own taxonomy** — don't reuse another
  domain's tag vocabulary without adding it to the current domain's `SCHEMA.md`.
- **Ask before mass-updating** — if an ingest would touch 10+ pages (within a
  domain, or across the multi-domain cross-reference), confirm scope first.
- **Handle contradictions explicitly**, same as `llm-wiki` — note both claims,
  mark frontmatter, flag for review; don't silently overwrite.

## Related

This skill assumes a vault that already has (or is being created with) a
top-level `DOMAINS.md`. For a single flat vault with no domain routing, use the
sibling `llm-wiki` skill instead — its three-layer architecture
(`raw/`/`entities/`/`concepts/`/`comparisons/`/`queries/` + `SCHEMA.md`) is what
each domain directory here reuses internally.
