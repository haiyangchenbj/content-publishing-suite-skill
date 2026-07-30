#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容发布套件 - 打包器。

将已审核定稿 Markdown 转换为多渠道发布物料：
  wechat_snippet.html / wechat_preview.html  (135 编辑器兼容内联 HTML)
  standalone.html                                (响应式单页)
  linkedin-post.md                              (起始稿，需人工润色)
  archive-ledger.json                           (本地入库台账)
  package-manifest.json                         (本次产物清单)

输入门禁：必须提供 --approved-gate（final-check.json 且 Gate B approved）
或 --approved 显式标志。本脚本只做本地生成，不执行任何外部发布动作。
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

INK = "#1a3a5c"
TEXT = "#333"
MUTED = "#999"
BAR = "#eee"


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r'<strong style="color:%s;">\1</strong>' % INK, text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def extract_frontmatter(md):
    fm = {}
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            block = md[3:end].strip()
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
            return fm, md[end + 4:]
    return fm, md


def first_heading(md):
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return ""


def parse_table_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def md_to_wechat(md, title, author, date):
    out = []
    out.append('<section style="text-align:center;padding:24px 16px 8px;">'
               '<h1 style="font-size:22px;font-weight:700;color:%s;margin:0;line-height:1.4;">%s</h1></section>' % (INK, inline(title)))
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            continue
        if s.startswith("## ") or s.startswith("### "):
            h = inline(s.lstrip("# ").strip())
            out.append('<section style="padding:18px 16px 6px;">'
                       '<span style="display:inline-block;width:4px;height:17px;background:%s;margin-right:8px;vertical-align:middle;"></span>'
                       '<strong style="font-size:17px;font-weight:700;color:%s;vertical-align:middle;">%s</strong></section>' % (INK, INK, h))
        elif s.startswith("> "):
            out.append('<section style="padding:10px 16px;">'
                       '<p style="font-size:15px;line-height:1.8;color:#555;background:#f5f7fa;padding:12px 14px;margin:0;border-radius:6px;">%s</p></section>' % inline(s[2:]))
        elif s.startswith("- "):
            out.append('<section style="padding:4px 16px;">'
                       '<p style="font-size:16px;line-height:1.8;color:%s;margin:0 0 8px;"><span style="color:%s;margin-right:6px;">•</span>%s</p></section>' % (TEXT, INK, inline(s[2:])))
        elif "|" in s and s.count("|") >= 2 and re.match(r"^\|", s):
            cells = parse_table_row(s)
            out.append('<section style="padding:8px 16px;overflow-x:auto;">'
                       '<table style="width:100%%;border-collapse:collapse;font-size:14px;line-height:1.6;">'
                       '<thead><tr style="background:%s;color:#fff;">%s</tr></thead></table></section>' % (INK, "".join('<th style="padding:8px 10px;text-align:left;border:1px solid %s;">%s</th>' % (INK, inline(c)) for c in cells)))
        else:
            out.append('<section style="padding:6px 16px;">'
                       '<p style="font-size:16px;line-height:1.8;color:%s;margin:0 0 12px;">%s</p></section>' % (TEXT, inline(s)))
    out.append('<section style="height:1px;background:%s;margin:12px 16px;"></section>' % BAR)
    out.append('<section style="padding:6px 16px;"><p style="font-size:14px;line-height:1.6;color:%s;margin:0;">%s · %s</p></section>' % (MUTED, author, date))
    out.append("<v2></v2>")
    return "".join(out)


def md_to_standalone(md, title, author, date, core):
    lines = md.splitlines()
    body = []
    toc = []
    idx = 0
    in_table = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            continue
        if s.startswith("## ") or s.startswith("### "):
            idx += 1
            h = inline(s.lstrip("# ").strip())
            sid = "s%d" % idx
            toc.append('<a href="#%s">%s</a>' % (sid, h))
            body.append('<h2 id="%s">%s</h2>' % (sid, h))
        elif s.startswith("> "):
            body.append('<blockquote>%s</blockquote>' % inline(s[2:]))
        elif s.startswith("- "):
            body.append('<p><span style="color:%s;margin-right:6px;">•</span>%s</p>' % (INK, inline(s[2:])))
        elif "|" in s and s.count("|") >= 2 and re.match(r"^\|", s):
            cells = parse_table_row(s)
            body.append('<table><thead><tr>%s</tr></thead></table>' % "".join("<th>%s</th>" % inline(c) for c in cells))
        else:
            body.append("<p>%s</p>" % inline(s))
    toc_html = '<nav class="toc" id="toc"><h2>目录</h2>%s</nav>' % "".join(toc) if toc else ""
    css = """:root{--ink:{INK};--text:{TEXT};--muted:#777;--line:#e6e9ef;}
*{box-sizing:border-box;}body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--text);background:#fafbfc;line-height:1.8;}
.wrap{max-width:760px;margin:0 auto;padding:48px 24px 80px;}header{border-bottom:2px solid var(--ink);padding-bottom:20px;margin-bottom:32px;}
h1{font-size:28px;color:var(--ink);margin:0 0 8px;} .meta{color:var(--muted);font-size:14px;}
nav.toc{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:24px 0;}
nav.toc h2{font-size:15px;color:var(--ink);margin:0 0 10px;} nav.toc a{color:var(--ink);text-decoration:none;display:block;padding:4px 0;font-size:14px;}
h2{font-size:21px;color:var(--ink);margin:36px 0 12px;} p{margin:0 0 16px;} strong{color:var(--ink);}
blockquote{background:#f5f7fa;border-left:4px solid var(--ink);margin:20px 0;padding:14px 18px;color:#555;border-radius:0 8px 8px 0;}
table{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;} th{background:var(--ink);color:#fff;text-align:left;padding:10px 12px;}
td{padding:10px 12px;border:1px solid var(--line);} tbody tr:nth-child(even){background:#f5f7fa;}
footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:13px;}""".replace("{INK}", INK).replace("{TEXT}", TEXT)
    doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<style>%s</style>
</head>
<body>
<div class="wrap">
<header><h1>%s</h1><div class="meta">%s · %s · %s</div></header>
%s
%s
<footer><p>本页由内容发布套件自动生成。</p></footer>
</div>
</body>
</html>""" % (inline(title), css, inline(title), author, date, inline(core), toc_html, "\n".join(body))
    return doc


def clean_md(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^-\s+", "", text)
    return text.strip()


def derive_linkedin(md, title):
    paras = [clean_md(l) for l in md.splitlines()
             if l.strip() and not l.strip().startswith("#") and not l.strip().startswith(">")]
    paras = [p for p in paras if p]
    lead = paras[0] if paras else title
    body = "\n\n".join(paras[1:4]) if len(paras) > 1 else lead
    return "%s\n\n%s\n\n#人工智能 #数据智能 #技术洞察 #产业研究 #%s" % (title, body[:600], title[:4])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True)
    ap.add_argument("--approved-gate", default=None, help="final-check.json 路径")
    ap.add_argument("--approved", action="store_true", help="显式声明定稿已审核")
    ap.add_argument("--channels", default="wechat,linkedin,html,archive")
    ap.add_argument("--output", default="./publish-output")
    args = ap.parse_args()

    if not args.approved_gate and not args.approved:
        print("[FAIL] 必须通过 --approved-gate <final-check.json> 或 --approved 证明定稿已审核", file=sys.stderr)
        return 2
    if args.approved_gate:
        try:
            gate = json.load(open(args.approved_gate, encoding="utf-8"))
        except Exception as e:
            print("[FAIL] 读取审核门禁文件失败: %s" % e, file=sys.stderr)
            return 2
        ok = (str(gate.get("Gate B", "")).lower().startswith("approved")
              and str(gate.get("red-line hits", gate.get("red_line_hits", "0"))) == "0"
              and str(gate.get("credential/privacy P0", gate.get("credential_privacy_p0", "0"))) == "0")
        if not ok:
            print("[FAIL] 审核门禁未通过（需 Gate B approved、red-line hits=0、credential/privacy P0=0）", file=sys.stderr)
            return 2

    if not os.path.exists(args.draft):
        print("[FAIL] 定稿文件不存在: %s" % args.draft, file=sys.stderr)
        return 2

    raw = open(args.draft, encoding="utf-8").read()
    fm, body = extract_frontmatter(raw)
    title = fm.get("title") or first_heading(body) or "未命名文章"
    author = fm.get("author") or ""
    date = datetime.date.today().isoformat()
    core = fm.get("core_judgment") or fm.get("核心判断") or ""
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    os.makedirs(args.output, exist_ok=True)
    manifest = {"draft": args.draft, "title": title, "generated_at": datetime.datetime.now().isoformat(), "channels": channels, "files": {}}

    if "wechat" in channels:
        wc = md_to_wechat(body, title, author, date)
        sp = os.path.join(args.output, "wechat_snippet.html")
        pv = os.path.join(args.output, "wechat_preview.html")
        open(sp, "w", encoding="utf-8").write(wc)
        preview = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>预览 %s</title><style>body{margin:0;background:#e9edf2;display:flex;justify-content:center;padding:24px;} .phone{width:375px;background:#fff;border-radius:18px;box-shadow:0 8px 30px rgba(0,0,0,.12);overflow:hidden;}</style></head><body><div class='phone'>%s</div></body></html>" % (title, wc)
        open(pv, "w", encoding="utf-8").write(preview)
        manifest["files"]["wechat"] = [sp, pv]

    if "html" in channels:
        st = md_to_standalone(body, title, author, date, core)
        p = os.path.join(args.output, "standalone.html")
        open(p, "w", encoding="utf-8").write(st)
        manifest["files"]["html"] = [p]

    if "linkedin" in channels:
        li = derive_linkedin(body, title)
        p = os.path.join(args.output, "linkedin-post.md")
        open(p, "w", encoding="utf-8").write(li)
        manifest["files"]["linkedin"] = [p]

    if "archive" in channels:
        ledger_path = os.path.join(args.output, "archive-ledger.json")
        entries = []
        if os.path.exists(ledger_path):
            try:
                entries = json.load(open(ledger_path, encoding="utf-8"))
                if not isinstance(entries, list):
                    entries = entries.get("entries", [])
            except Exception:
                entries = []
        entries.append({
            "title": title, "author": author, "date": date,
            "source_draft": args.draft, "channels": channels,
            "generated_at": datetime.datetime.now().isoformat(), "status": "draft",
            "notion_page_id": None, "notes": ""
        })
        open(ledger_path, "w", encoding="utf-8").write(json.dumps(entries, ensure_ascii=False, indent=2))
        manifest["files"]["archive"] = [ledger_path]

    mp = os.path.join(args.output, "package-manifest.json")
    open(mp, "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))

    print("== 发布套件打包完成 ==")
    print("标题: %s" % title)
    print("渠道: %s" % ", ".join(channels))
    print("产物目录: %s" % os.path.abspath(args.output))
    print("清单: %s" % mp)
    print("提示: 外部发布（推送/建草稿/写 Notion）需单独确认，本脚本不执行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
