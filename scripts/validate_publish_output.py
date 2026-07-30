#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容发布套件 - 各渠道输出格式合约校验器。

依据 references/channel-contracts.md 逐渠道检查生成的发布物料。
P0 阻断发布；P1 提示人工决定。
--enforce 时若存在 P0，进程退出码为 2。
"""
import argparse
import json
import os
import re
import sys

CONVO_TRACE = ["好的，", "我来", "，以下是", "本文档旨在", "下文将"]
CRED_PREFIX = ["ntn_", "sk-", "ghp_", "gho_", "ghu_", "ghs_", "ghr_"]

# 内部标记（发布物中不应出现）。作者内部笔名/代号不硬编码在通用引擎里，
# 由私有配置通过环境变量 PUBLISH_PEN_NAMES（逗号分隔）传入，默认为空。
INTERNAL_MARKERS = ["【内部】", "内部备注", "待定", "Gate", "审核过程"]
PEN_NAMES = [n.strip() for n in os.environ.get("PUBLISH_PEN_NAMES", "").split(",") if n.strip()]


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_wechat(text, issues):
    if "<section" not in text:
        issues.append(("P0", "wechat", "缺少 <section> 包裹块"))
    if "<v2></v2>" not in text:
        issues.append(("P0", "wechat", "文末缺少 <v2></v2> 版本标记"))
    if re.search(r"<script|<style", text):
        issues.append(("P0", "wechat", "含 <script> 或 <style>"))
    if "position:fixed" in text or "position:absolute" in text:
        issues.append(("P0", "wechat", "含 position:fixed/absolute"))
    for m in re.finditer(r'class="([^"]*)"', text):
        if m.group(1) != "_135editor":
            issues.append(("P0", "wechat", "含外联 class=%r（可粘贴模式应无 class）" % m.group(1)))
            break
    if "font-size:16px" not in text and "line-height:1.8" not in text:
        issues.append(("P1", "wechat", "正文疑似未应用 16px/1.8 样式"))


def check_linkedin(text, issues):
    if re.search(r"^\s*#\s", text, re.M):
        issues.append(("P0", "linkedin", "含 Markdown 标题 #"))
    if "**" in text or "```" in text:
        issues.append(("P0", "linkedin", "含 Markdown 加粗 ** 或代码块 ```"))
    if re.search(r"^\s*-\s", text, re.M):
        issues.append(("P0", "linkedin", "含 Markdown 列表 - "))
    for marker in INTERNAL_MARKERS + PEN_NAMES:
        if marker in text:
            issues.append(("P0", "linkedin", "含内部备注标记/笔名 %r" % marker))
            break
    if len(text) > 3000:
        issues.append(("P1", "linkedin", "字符数 %d > 3000" % len(text)))
    if not re.search(r"#\w|#[\u4e00-\u9fff]", text):
        issues.append(("P1", "linkedin", "末尾未出现 #话题 标签"))


def check_standalone(text, issues):
    if not (text.lstrip().lower().startswith("<!doctype html") or "<html" in text.lower()):
        issues.append(("P0", "standalone", "非 HTML 文档结构"))
        return
    m = re.search(r"<title>(.*?)</title>", text, re.S)
    if not m or not m.group(1).strip():
        issues.append(("P0", "standalone", "缺少非空 <title>"))
    for kw in ["circuit", "grid-glow", "neon", "linear-gradient"]:
        if kw in text.lower():
            issues.append(("P0", "standalone", "疑似科技电路风关键词 %r" % kw))
            break
    if "<nav" not in text and 'id="toc"' not in text:
        issues.append(("P1", "standalone", "缺少目录（<nav> 或 id=toc）"))


def check_ledger(text, issues):
    try:
        data = json.loads(text)
    except Exception as e:
        issues.append(("P0", "archive", "JSON 解析失败: %s" % e))
        return
    entries = data if isinstance(data, list) else data.get("entries", [])
    if not entries:
        issues.append(("P0", "archive", "台账为空"))
        return
    last = entries[-1]
    for field in ["title", "channels", "generated_at", "status"]:
        if field not in last:
            issues.append(("P0", "archive", "最新记录缺字段 %r" % field))
    if last.get("status") not in ["draft", "published", "archived"]:
        issues.append(("P1", "archive", "status=%r 取值异常" % last.get("status")))


def check_general(text, name, issues):
    for t in CONVO_TRACE:
        if t in text:
            issues.append(("P0", name, "含对话痕迹 %r" % t))
            break
    for p in CRED_PREFIX:
        if p in text:
            issues.append(("P0", name, "含疑似凭据前缀 %r" % p))
            break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True, help="发布产物目录")
    ap.add_argument("--enforce", action="store_true", help="存在 P0 时退出码 2")
    args = ap.parse_args()

    pkg = args.package
    issues = []
    files = {
        "wechat": os.path.join(pkg, "wechat_snippet.html"),
        "linkedin": os.path.join(pkg, "linkedin-post.md"),
        "standalone": os.path.join(pkg, "standalone.html"),
        "archive": os.path.join(pkg, "archive-ledger.json"),
    }
    present = {k: v for k, v in files.items() if os.path.exists(v)}
    if not present:
        print("[FAIL] 目录 %s 无任何渠道产物" % pkg, file=sys.stderr)
        return 2

    for name, path in present.items():
        text = read_text(path)
        if name == "wechat":
            check_wechat(text, issues)
        elif name == "linkedin":
            check_linkedin(text, issues)
        elif name == "standalone":
            check_standalone(text, issues)
        elif name == "archive":
            check_ledger(text, issues)
        check_general(text, name, issues)

    result = {"package": pkg, "issues": [{"severity": s, "channel": c, "detail": d} for s, c, d in issues]}
    out_path = os.path.join(pkg, "publish-gate.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    p0 = [i for i in issues if i[0] == "P0"]
    p1 = [i for i in issues if i[0] == "P1"]
    print("== 发布物料门禁 ==")
    print("检查渠道: %s" % ", ".join(sorted(present)))
    if not issues:
        print("结果: 通过（P0=0, P1=0）")
    else:
        for s, c, d in issues:
            print("  [%s] %s: %s" % (s, c, d))
        print("汇总: P0=%d, P1=%d" % (len(p0), len(p1)))
    print("报告: %s" % out_path)

    if args.enforce and p0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
