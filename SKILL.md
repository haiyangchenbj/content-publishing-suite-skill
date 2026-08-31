---
slug: content-publishing-suite-skill
displayName: Content Publishing Suite
name: content-publishing-suite
not_for:
  - Fact-checking, originality review, or claim verification (use claim-to-source-auditor)
  - Cross-material consistency audits across a finished document set (use cross-material-consistency-auditor)
  - Writing, rewriting, or topic evaluation (use the upstream writing/review pipeline)
  - Auto-publishing to any platform without explicit user confirmation
description: This skill should be used when a fact-checked and compliance-approved final Markdown draft needs to be turned into multi-channel publishing assets — WeChat article (135-editor-compatible inline HTML), WeChat image-summary card (公众号发图/摘要图/图文卡/810×1080), LinkedIn post, standalone responsive HTML page, and an archive ledger (local record plus optional Notion entry). It only orchestrates publishing and format conversion; it does not repeat fact-checking and does not auto-publish. Can optionally pair with a dedicated WeChat-layout skill if one is installed. Trigger keywords: 发布物料, 排版并入库, 多平台发布, 定稿发到微信, 公众号发图, 摘要图, 图文卡, 810×1080, publishing suite, multi-channel publish, final draft to WeChat/LinkedIn, package for publishing.
description_zh: 内容发布套件
description_en: Content publishing suite
version: "1.1.4"
agent_created: true
---

# Content Publishing Suite

将一篇**已审核定稿**稳定转换为多个渠道的发布物料，并生成入库记录。本 Skill 是发布编排层，不做事实核验、原创性复核或跨材料审计（那些由上游 Skill 负责），也不自动执行任何外部发布动作。

> 本文档中 `{SKILL_DIR}` 自动替换为 Skill 实际安装路径。

## When to use

- 用户拥有一篇已通过终检的定稿（industry-deep-dive-pipeline 的 `07-final.md`，或显式标记「已审核」的等价 Markdown），要求产出微信 / LinkedIn / 独立 HTML / 入库物料。
- 用户要求"把这篇发到多个平台""生成发布包""排版并归档"。

## Do not use

- 内容尚未完成事实核验或合规审核 → 先走 industry-deep-dive-pipeline / claim-to-source-auditor / cross-material-consistency-auditor。
- 只需要单纯的微信排版且本地已安装专门的微信排版 Skill / 已有平台建稿流程 → 直接用该工具即可，无需本套件。
- 需要新写正文、改写或补充事实 → 属于写作/核验环节，不属于发布编排。

## Input

```yaml
draft:
  path:                     # 已审核定稿 Markdown
  title:
  author:
  date:
approval_gate:              # 必须满足其一
  final_check_json:         # industry-deep-dive-pipeline 产物；需 Gate B approved、red-line hits 0、credential/privacy P0 0
  reviewed_marker: false    # 或定稿首部带 `状态: 已审核` / `reviewed: true` 且用户确认
channels: [wechat, linkedin, html, archive]
output_dir:
external_action: dry-run    # 默认只生成不发送
read_only_upstream: true    # 不引入上游未覆盖的新事实
```

必须满足其一，否则拒绝进入：

1. 提供 `final-check.json`（industry-deep-dive-pipeline 产物）且 `Gate B: approved`、`red-line hits: 0`、`credential/privacy P0: 0`；或
2. 定稿文件首部带有显式 `状态: 已审核` 或 `reviewed: true` 标记，并由用户在请求中确认"已审核"。

下游若引入任何上游未覆盖的**新事实**，必须暂停并提示回退上游重新核验，不得静默发布。

## Output channels

| 渠道 | 产物 | 说明 |
|------|------|------|
| 微信长文 | `wechat_snippet.html`（可粘贴片段）+ `wechat_preview.html`（手机框预览） | 135 编辑器兼容内联样式；不自动建草稿 |
| 微信发图摘要 | `wechat_summary_card.jpg`（810×1080）+ `wechat_summary_copy.md` | 长文二次分发物料：主题图重排、摘要、关键词和原文链接占位；不替代长文封面 |
| LinkedIn | `linkedin-post.md` | hook + 正文 + 3-5 话题标签；中/英按目标读者 |
| 独立 HTML | `standalone.html` | 响应式单页，含目录与参考链接 |
| 入库 | `archive-ledger.json`（本地）+ 可选 Notion 记录 | 标题/渠道/时间/状态；可选 page ID 写入并回读 |

## Workflow

```
摄入定稿 → 输入门禁 → 逐渠道生成物料 → 输出门禁（脚本校验）→ 生成 package-manifest → 入库台账 → 外部动作门禁（需确认才发送）
```

### Step 1: [Deterministic + LLM] Ingest and input gate

读取定稿 Markdown，确认满足输入门禁。记录标题、作者、日期、核心判断。未通过门禁立即停止。

### Step 2: [LLM] Generate per-channel assets

- **微信长文**：依 `references/wechat-style.md` 将 Markdown 转为全内联 `<section>` HTML。标题 22px 居中、小标题 17px 加粗 `#1a3a5c`、正文 16px / 行高 1.8 / `#333`、关键句 `<strong style="color:#1a3a5c;">`、表格深蓝表头白字 + 斑马纹。文末必须加 `<v2></v2>`。绝不使用 `<style>`、`<script>`、外联 class、外层 `<div>` 容器。模板见 `templates/wechat-snippet.html`。
- **微信发图摘要**：生成前必须加载 `tech-writing-pipeline`，并以其 **6.1「公众号发图摘要卡：固定骨架，有限自适应」**作为唯一完整视觉规范；本 skill 只负责编排、交付与台账，不能用本段摘要替代 6.1。同步生成 `wechat_summary_card.jpg`（810×1080、3:4）和 `wechat_summary_copy.md`。卡片必须执行 A/B/C/D 四区、56px 左右安全边距、左对齐阅读路径、上暖下冷、三色上限、一个主体结构加一个对照状态、主题行与一条最多三行的核心判断；仅能在主题隐喻、主体位置、同系列色盘微调、主题行和核心判断五项中自适应。不得把 2.35:1 长文封面硬裁或复用。文案应保留长文的判断闭环，而不是只写一句口号；包含短摘要、关键词/Hashtags、`【原文链接：待填】`和后台使用说明。图片不预制公众号账号水印，平台上传后的自动标识即可。
- **LinkedIn**：依 `templates/linkedin-post.md`，取核心判断作 hook，正文压缩到 200-300 字，末尾 3-5 个话题标签。无 Markdown、无内部备注、无未公开数据、无流程元信息。
- **独立 HTML**：依 `templates/standalone.html`，生成响应式单页，含标题/作者/日期/目录/正文/参考链接。平涂风格、大量留白、**绝对排除科技电路风、发光、数字网格**。
- **入库台账**：追加一条记录到 `archive-ledger.json`（不存在则新建），字段见 `templates/archive-record.json`。

### Step 3: [Deterministic] Output gate (script validation)

运行确定性脚本校验每个渠道文件是否满足格式合约：

```bash
python3 {SKILL_DIR}/scripts/validate_publish_output.py --package <output_dir> --enforce
```

P0 阻断（如微信缺 `<section>`/`<v2>`、含 `<script>`、HTML 无结构、台账缺字段）；P1 提示（如 LinkedIn 超长）。脚本退出码 2 表示存在 P0。作者内部笔名清单通过环境变量 `PUBLISH_PEN_NAMES`（逗号分隔）传入，不硬编码。

### Step 4: [Deterministic] Package and ledger

```bash
python3 {SKILL_DIR}/scripts/build_publish_package.py \
  --draft <定稿.md> \
  --approved-gate <final-check.json 或 --approved 标志> \
  --channels wechat,linkedin,html,archive \
  --output <output_dir>
```

脚本产出各渠道文件、更新 `archive-ledger.json`、输出 `package-manifest.json`。

### Step 5: [Human] External-action gate

任何实际推送、经文章管理平台建草稿、写 Notion 的动作前，**必须列出目标并取得用户确认**。默认只生成不发送（`--dry-run`）。确认后才执行，且写后必须回读核验（Notion 用 page ID 写入、幂等键防重复）。

## Hard Rules

1. 未通过输入门禁（无 `final-check.json` approved 或无显式"已审核"标记）一律拒绝进入，不得代替上游做核验。
2. 发布物料中零对话痕迹、零流程元信息、零内部备注/笔名/未授权数据。
3. 微信物料必须全内联样式、`<section>` 包裹、文末带 `<v2></v2>`；禁止 `<style>`/`<script>`/外联 class/外层 `<div>`。
4. 工作文档与发布物中人名一律用真实姓名或中性表达；作者内部笔名从 `PUBLISH_PEN_NAMES` 读取用于拦截，不硬编码进本 Skill。
5. 任何外部动作（推送、建草稿、写 Notion）默认 `--dry-run`，必须先列目标并取得用户确认；写后必须回读核验。
6. 凭据只走环境变量（Notion 用 `NOTION_TOKEN`、库 ID 用 `NOTION_DB_ID`；文章管理平台经既有 MCP/连接器），绝不硬编码。
7. 微信发图摘要卡必须为 810×1080（3:4），且图与文案都围绕同一篇已审核长文；图中不重复添加公众号账号水印。台账需记录 `summary_card` 路径。
8. 一旦交付包含微信发图摘要，必须先完整加载 `tech-writing-pipeline` 并逐项执行其 6.1；未加载或无法访问时，停止摘要卡制作并说明缺少的规范，不能凭本 skill 的简写规则自行补全。
9. 脚本只读取用户指定的定稿、写入用户指定的输出目录；不引入网络外送。

## Failure Handling

| Scenario | Action |
|---|---|
| 输入门禁不满足 | 停止；输出缺失项清单并提示先完成上游核验 |
| 输出门禁出现 P0（退出码 2） | 不生成 manifest；列出每条 P0 及所在文件，修复后重跑 |
| 下游发现上游未覆盖的新事实 | 暂停发布，回退上游重新核验，不得静默发布 |
| 外部写入失败 | 先重试一次并交叉验证；仍失败则保留本地台账、报告原因，不留半写状态 |
| 定稿含未解析的复杂内嵌内容（图表/带字图片） | 标记为不可解析，请求文本抽取或人工确认 |
| 目标渠道未指定 | 默认生成全部四渠道并提示 |

## Output Format

```text
<output_dir>/
├── wechat_snippet.html
├── wechat_preview.html
├── wechat_summary_card.jpg
├── wechat_summary_copy.md
├── linkedin-post.md
├── standalone.html
├── archive-ledger.json        # 追加式入库台账
└── package-manifest.json      # 本次发布包清单（各文件路径 + 门禁结果）
```

gate 报告：P0/P1 列表；有 P0 时明确标注"未通过、禁止发布"。

## References

| 资源 | 用途 |
|------|------|
| `references/wechat-style.md` | 微信 135 内联样式规范、组件样式代码 |
| `references/channel-contracts.md` | 各渠道输出格式合约（校验规则依据） |
| `templates/wechat-snippet.html` | 微信片段模板 |
| `templates/linkedin-post.md` | LinkedIn 帖子模板 |
| `templates/standalone.html` | 独立 HTML 单页模板 |
| `templates/archive-record.json` | 入库台账条目模板 |
| `templates/notion-mapping.example.json` | Notion 映射样例（凭据走 `NOTION_TOKEN` 环境变量，库 ID 占位符不写真实值） |
| `scripts/build_publish_package.py` | 组织产物、更新台账、输出 manifest |
| `scripts/validate_publish_output.py` | 各渠道格式合约校验，输出 P0/P1 gate |

## Verification

- [ ] 运行 `validate_publish_output.py --enforce`，退出码 0（无 P0）。
- [ ] 微信片段含 `<section>`、文末 `<v2></v2>`、无 `<script>`/`<style>`/外层 class。
- [ ] 微信发图摘要卡为 810×1080（3:4）、主题图为竖幅重排而非横版硬裁、无重复账号水印；摘要副本含关键词和原文链接占位。
- [ ] LinkedIn 无 Markdown 标记、无内部备注/笔名。
- [ ] 独立 HTML 以 `<!DOCTYPE html>` 开头，无科技电路风/发光/数字网格。
- [ ] `package-manifest.json` 各渠道均生成，`archive-ledger.json` 已追加一条。
- [ ] 外部动作前已取得用户确认；默认 dry-run。

## Pitfalls

- 把未审核稿当作已审核直接发布——必须先过输入门禁。
- 微信物料误加 `<style>`/外层 `<div>`，粘贴进 135 编辑器后样式被剥离。
- LinkedIn 残留 Markdown 加粗/列表符号或内部笔名，平台不渲染或泄漏内部信息。
- 在 example/模板里写真实 Notion 库 ID 或凭据——一律用占位符与环境变量。
- 外部写入未回读核验，导致重复写入或半写状态。
- 下游悄悄补一句"新事实"绕过上游核验——任何新事实都要回退上游。
- 把横版封面当公众号发图摘要卡——长文封面是 2.35:1；发图摘要是 810×1080 的独立二次分发物料，需主题图重排、长文摘要、关键词和原文链接占位。
- 在摘要图里再加“公众号·账号名”水印——上传后平台会自动显示账号标识，设计图不重复加，避免视觉重叠。
- 只加载发布套件并按其中的短说明制作摘要卡——这会遗漏 A/B/C/D 分区、固定文字层级、有限自适应边界和手机缩略验收。只要交付摘要卡，就必须额外完整加载 `tech-writing-pipeline` 的 6.1；发布套件不再作为摘要卡视觉规范的替代品。
