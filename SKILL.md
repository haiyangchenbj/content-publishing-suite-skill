---
name: content-publishing-suite
description: Turn a fact-checked and compliance-approved final Markdown draft into multi-channel publishing assets — WeChat article, LinkedIn post, standalone responsive HTML, and an archive ledger. It only orchestrates publishing and format conversion; it does not repeat fact-checking and does not auto-publish.
description_zh: 内容发布套件
description_en: Content publishing suite
version: 1.1.1
disable: false
agent_created: true
---

# Content Publishing Suite

Convert a **reviewed, approved final draft** into multi-channel publishing assets and generate an archive ledger. This skill is the publishing-orchestration layer — it does not repeat fact-checking, originality review, or cross-material auditing (those are upstream skills), and it never performs any external publish action automatically.

> In this document `{SKILL_DIR}` is replaced automatically with the skill's actual install path.

## When to use

- The user has a final draft that passed final check (`07-final.md` from `industry-deep-dive-pipeline`, or an equivalent Markdown explicitly marked "已审核 / reviewed"), and wants WeChat / LinkedIn / standalone HTML / archive assets.
- The user asks to "publish this to multiple platforms", "generate a publish package", or "lay out and archive".

## Do not use

- Content that has not completed fact-checking or compliance review → run `industry-deep-dive-pipeline` / `claim-to-source-auditor` / `cross-material-consistency-auditor` first.
- Pure WeChat layout with a dedicated WeChat-layout skill already installed, or an existing platform drafting flow → use that tool directly; this suite is unnecessary.
- Writing new body text, rewriting, or adding facts → that belongs to the writing / verification stage, not publishing orchestration.

## Input

```yaml
draft:
  path:                     # reviewed final Markdown
  title:
  author:
  date:
approval_gate:              # one of these must be satisfied
  final_check_json:         # product of industry-deep-dive-pipeline; needs Gate B approved, red-line hits 0, credential/privacy P0 0
  reviewed_marker: false    # or draft header carries `状态: 已审核` / `reviewed: true` AND user confirms
channels: [wechat, linkedin, html, archive]
output_dir:
external_action: dry-run    # default: generate only, do not send
read_only_upstream: true    # do not introduce new facts not covered upstream
```

One of the two gates must be satisfied, otherwise refuse to enter:

1. Provide `final-check.json` (product of `industry-deep-dive-pipeline`) with `Gate B: approved`, `red-line hits: 0`, `credential/privacy P0: 0`; or
2. The final draft header carries an explicit `状态: 已审核` or `reviewed: true` marker, AND the user confirms "已审核" in the request.

If the downstream introduces any **new fact** not covered upstream, pause and prompt to roll back to upstream for re-verification — never publish silently.

## Output channels

| Channel | Artifact | Notes |
|---------|----------|-------|
| WeChat | `wechat_snippet.html` (paste-ready fragment) + `wechat_preview.html` (mobile-frame preview) | 135-editor-compatible inline styles; does not auto-create draft |
| LinkedIn | `linkedin-post.md` | hook + body + 3–5 hashtags; Chinese/English by target audience |
| Standalone HTML | `standalone.html` | responsive single page with TOC and reference links |
| Archive | `archive-ledger.json` (local) + optional Notion entry | title/channel/time/status; optional page-ID write with readback |

## Workflow

```
ingest final draft → input gate → generate per-channel assets → output gate (script validation) → package-manifest → archive ledger → external-action gate (confirm before send)
```

### Step 1: [Deterministic + LLM] Ingest and input gate

Read the final draft Markdown and confirm the input gate is satisfied. Record title, author, date, and core judgment. Stop immediately if the gate fails.

### Step 2: [LLM] Generate per-channel assets

- **WeChat**: per `references/wechat-style.md`, convert Markdown to fully-inline `<section>` HTML. Title 22px centered, subhead 17px bold `#1a3a5c`, body 16px / line-height 1.8 / `#333`, key sentences `<strong style="color:#1a3a5c;">`, table with dark-blue header + white text + zebra rows. Must end with `<v2></v2>`. Never use `<style>`, `<script>`, external class, or an outer `<div>` container. Template: `templates/wechat-snippet.html`.
- **LinkedIn**: per `templates/linkedin-post.md`, take the core judgment as the hook, compress body to 200–300 words, end with 3–5 hashtags. No Markdown, no internal notes, no unpublished data, no process meta.
- **Standalone HTML**: per `templates/standalone.html`, generate a responsive single page with title/author/date/TOC/body/reference links. Flat-fill style, generous whitespace, **absolutely no tech-circuit motifs, glow, or digital-grid patterns**.
- **Archive ledger**: append one record to `archive-ledger.json` (create if missing); fields per `templates/archive-record.json`.

### Step 3: [Deterministic] Output gate (script validation)

Run the deterministic script to verify each channel file meets its format contract:

```bash
python3 {SKILL_DIR}/scripts/validate_publish_output.py --package <output_dir> --enforce
```

P0 blocks (e.g. WeChat missing `<section>`/`<v2>`, contains `<script>`, HTML without structure, ledger missing fields); P1 warnings (e.g. LinkedIn too long). Exit code 2 means a P0 exists. The author's internal pen-name list is passed via the `PUBLISH_PEN_NAMES` environment variable (comma-separated), never hardcoded.

### Step 4: [Deterministic] Package and ledger

```bash
python3 {SKILL_DIR}/scripts/build_publish_package.py \
  --draft <final.md> \
  --approved-gate <final-check.json or --approved flag> \
  --channels wechat,linkedin,html,archive \
  --output <output_dir>
```

The script produces each channel file, updates `archive-ledger.json`, and outputs `package-manifest.json`.

### Step 5: [Human] External-action gate

Before any actual push, article-platform draft creation, or Notion write, **list the targets and obtain user confirmation**. Default is generate-only (`--dry-run`). Execute only after confirmation, and always read back to verify after writing (Notion uses page-ID writes, idempotency key prevents duplicates).

## Hard Rules

1. Refuse to enter if the input gate is not satisfied (no `final-check.json` approved, no explicit "已审核" marker) — never substitute for upstream verification.
2. Zero conversation traces, zero process meta, zero internal notes / pen-names / unauthorized data in any publish asset.
3. WeChat assets must be fully inline-styled, wrapped in `<section>`, and end with `<v2></v2>`; forbid `<style>`/`<script>`/external class/outer `<div>`.
4. Use the real name or neutral phrasing for any person in working docs and publish assets; the author's internal pen-name is read from `PUBLISH_PEN_NAMES` for blocking only, never hardcoded into this skill.
5. Any external action (push, draft creation, Notion write) defaults to `--dry-run`; list targets and get user confirmation first; read back after writing.
6. Credentials come only from environment variables (Notion uses `NOTION_TOKEN`, database ID uses `NOTION_DB_ID`; article platforms via their existing MCP/connectors) — never hardcoded.
7. Scripts only read the user-specified final draft and write to the user-specified output directory; no network egress.

## Failure Handling

| Scenario | Action |
|---|---|
| Input gate not satisfied | Stop; list missing items, prompt to finish upstream verification |
| Output gate hits P0 (exit code 2) | Do not generate manifest; list each P0 and its file, fix and re-run |
| Downstream finds a new fact not covered upstream | Pause publishing, roll back upstream for re-verification, never publish silently |
| External write fails | Retry once and cross-verify; if still failing, keep the local ledger, report the reason, leave no half-written state |
| Final draft has unparseable embedded content (charts/image-with-text) | Mark as unparseable, request text extraction or manual confirmation |
| Target channel unspecified | Default to generating all four channels and prompt |

## Output Format

```text
<output_dir>/
├── wechat_snippet.html
├── wechat_preview.html
├── linkedin-post.md
├── standalone.html
├── archive-ledger.json        # append-style archive ledger
└── package-manifest.json      # this publish package manifest (file paths + gate results)
```

Gate report: P0/P1 list; when a P0 exists, explicitly mark "未通过、禁止发布 / failed, publishing forbidden".

## References

| Resource | Purpose |
|----------|---------|
| `references/wechat-style.md` | WeChat 135 inline-style spec and component styles |
| `references/channel-contracts.md` | Output-format contracts per channel (validation basis) |
| `templates/wechat-snippet.html` | WeChat fragment template |
| `templates/linkedin-post.md` | LinkedIn post template |
| `templates/standalone.html` | Standalone HTML single-page template |
| `templates/archive-record.json` | Archive ledger entry template |
| `templates/notion-mapping.example.json` | Notion mapping example (credentials via `NOTION_TOKEN` env var; database ID placeholder, never real value) |
| `scripts/build_publish_package.py` | Organize artifacts, update ledger, output manifest |
| `scripts/validate_publish_output.py` | Per-channel format-contract validation, outputs P0/P1 gate |

## Verification

- [ ] `validate_publish_output.py --enforce` exits 0 (no P0).
- [ ] WeChat fragment contains `<section>`, ends with `<v2></v2>`, no `<script>`/`<style>`/outer class.
- [ ] LinkedIn has no Markdown markers, no internal notes / pen-names.
- [ ] Standalone HTML starts with `<!DOCTYPE html>`, no tech-circuit / glow / digital-grid motifs.
- [ ] `package-manifest.json` generated for all channels, `archive-ledger.json` appended one entry.
- [ ] User confirmation obtained before any external action; default dry-run.

## Pitfalls

- Treating an unreviewed draft as reviewed and publishing directly — must pass the input gate first.
- WeChat asset accidentally gets `<style>`/outer `<div>`, then the 135 editor strips the styles on paste.
- LinkedIn retains Markdown bold/list symbols or an internal pen-name — the platform won't render it or it leaks internal info.
- Writing a real Notion database ID or credential in an example/template — always use placeholders and environment variables.
- External write without readback verification, causing duplicate writes or half-written state.
- Downstream silently adds a "new fact" that bypasses upstream verification — any new fact must roll back upstream.

---

## 中文摘要（Chinese Summary）

本 Skill 是**发布编排层**：把一篇已通过终检的定稿（如 `industry-deep-dive-pipeline` 的 `07-final.md`，或显式标记「已审核」的等价 Markdown）稳定转换为微信 / LinkedIn / 独立 HTML / 入库四类物料，并生成入库台账。

**关键约束（双语要点 / Bilingual key points）：**

- **输入门禁 Input gate**：必须提供 `final-check.json`（Gate B approved、红线 0、凭据/隐私 P0 0）或定稿头部显式「已审核」标记且用户确认；否则拒绝进入。
- **零泄漏 Zero leakage**：发布物料中零对话痕迹、零流程元信息、零内部备注/笔名；作者笔名仅经 `PUBLISH_PEN_NAMES` 环境变量传入用于拦截，绝不硬编码。
- **微信硬规则 WeChat hard rule**：全内联样式、`<section>` 包裹、文末 `<v2></v2>`；禁止 `<style>`/`<script>`/外联 class/外层 `<div>`。
- **外部动作门禁 External-action gate**：任何推送、建草稿、写 Notion 默认 `--dry-run`，须列目标并取得用户确认，写后必须回读核验。
- **凭据 Credentials**：只走环境变量（`NOTION_TOKEN` / `NOTION_DB_ID`），绝不硬编码。

它不重复事实核验、原创性复核或跨材料审计，也不自动执行任何发布动作。
