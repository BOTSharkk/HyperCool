#!/usr/bin/env python3
"""Apply the Simplified Chinese dictionary to HyperCool's webroot/index.html.

The dictionary only rewrites display strings (HTML text, aria-label/placeholder/
title/alt, and JavaScript string literals). Paths, shell commands, config keys,
package names and status tokens are never touched.

Examples:
    # Rebuild the WebUI from the current upstream master
    python3 tools/zh_apply.py --from-git upstream/master --out webroot/index.html

    # Apply to a downloaded copy and write a translation report
    python3 tools/zh_apply.py --source /tmp/upstream-index.html --out /tmp/zh.html \
        --report /tmp/untranslated.txt

    # Only check which new strings still need a translation
    python3 tools/zh_apply.py --from-git upstream/master --out /tmp/zh.html --report -
"""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys

ATTRS = {"aria-label", "placeholder", "title", "alt"}
CJK = re.compile(r"[\u4e00-\u9fff]")
TECH = re.compile(
    r"(/sys|/proc|/data|/dev|https?:|\.sh\b|\.txt\b|\bcmd\b|\bdumpsys\b|"
    r"\bsettings\b|\bappops\b|\bpm\b|\bam\b|\bsvc\b|\bresetprop\b|"
    r"\blogcat\b|\becho\b|\bchmod\b|\bvar\(|rgba?\(|\dpx\b|\$\{|%[sd]|\\n)"
)
UNITS = re.compile(r"^\d+(?:\.\d+)?\s*(?:s|min|h|GB|MB|KB|MHz|Hz|mA|mV|°C|%)$")
MONTHS = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}
BRANDS = {
    "HyperCool", "KernelSU", "Magisk", "APatch", "Android", "Google", "GMS",
    "Qualcomm", "MediaTek", "Adreno", "Mali", "UFS", "F2FS", "ZRAM", "zram",
    "Doze", "WALT", "schedutil", "AMOLED", "BBR", "PPM", "GED", "EAS", "LMK",
    "JobScheduler", "Smart Pixels", "HyperOS", "MIUI", "Game Turbo", "Joyose",
    "MiGT", "Metis", "Telegram", "Ko-fi", "SociaBuzz", "QRIS", "PayPal",
    "Google Play", "Play Store", "WhatsApp", "batterystats.bin", "dex2oat",
}


def regex_start(line, i):
    """Heuristic: does the '/' at line[i] start a regex literal?"""
    j = i - 1
    while j >= 0 and line[j].isspace():
        j -= 1
    if j < 0:
        return True
    if line[j] in "(=:[,!&|?{};":
        return True
    word = re.search(r"(\w+)\s*$", line[:i])
    return bool(word and word.group(1) in ("return", "case", "typeof", "instanceof"))


def js_line_spans(line, base):
    """Tokenize display strings on one JS line, skipping comments and regexes."""
    out = []
    i, n = 0, len(line)
    while i < n:
        if line.startswith("//", i):
            break
        if line.startswith("/*", i):
            j = line.find("*/", i + 2)
            if j < 0:
                break
            i = j + 2
            continue
        c = line[i]
        if c in "'\"":
            j = i + 1
            buf = []
            while j < n:
                if line[j] == "\\":
                    buf.append(line[j:j + 2])
                    j += 2
                    continue
                if line[j] == c:
                    break
                buf.append(line[j])
                j += 1
            if j >= n:
                break
            out.append((base + i + 1, base + j, "".join(buf), "js"))
            i = j + 1
            continue
        if c == "`":
            j = i + 1
            buf = []
            while j < n:
                if line[j] == "\\":
                    buf.append(line[j:j + 2])
                    j += 2
                    continue
                if line[j] == "`":
                    break
                buf.append(line[j])
                j += 1
            if j >= n:
                break  # multi-line template: do not guess
            out.append((base + i + 1, base + j, "".join(buf), "tpl"))
            i = j + 1
            continue
        if c == "/" and not line.startswith("//", i) and not line.startswith("/*", i) and regex_start(line, i):
            j = i + 1
            in_class = False
            while j < n:
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == "[":
                    in_class = True
                elif line[j] == "]":
                    in_class = False
                elif line[j] == "/" and not in_class:
                    break
                j += 1
            i = j + 1
            continue
        i += 1
    return out


def js_spans(text, start, end):
    out = []
    pos = start
    while pos < end:
        line_end = text.find("\n", pos, end)
        if line_end < 0:
            line_end = end
        out += js_line_spans(text[pos:line_end], pos)
        pos = line_end + 1
    return out


def spans(text):
    """Return (start, end, value, kind) for display strings only."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("<!--", i):
            j = text.find("-->", i)
            i = n if j < 0 else j + 3
            continue
        if text.startswith("<script", i):
            j = text.find(">", i)
            k = text.find("</script>", j)
            if k < 0:
                break
            out += js_spans(text, j + 1, k)
            i = k + 9
            continue
        if text.startswith("<style", i):
            j = text.find(">", i)
            k = text.find("</style>", j)
            if k < 0:
                break
            i = k + 8
            continue
        if text[i] == "<":
            j = text.find(">", i)
            if j < 0:
                break
            tag = text[i:j + 1]
            for m in re.finditer(r'([\w-]+)="([^"]*)"', tag):
                if m.group(1) in ATTRS:
                    v = m.group(2)
                    out.append((i + m.start(2), i + m.end(2), v, "attr"))
            i = j + 1
            continue
        j = text.find("<", i)
        if j < 0:
            j = n
        seg = text[i:j]
        lead = len(seg) - len(seg.lstrip())
        trail = len(seg) - len(seg.rstrip())
        s, e = i + lead, j - trail
        if e > s:
            out.append((s, e, text[s:e], "txt"))
        i = j
    return out


def line_at(text, pos):
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    if b < 0:
        b = len(text)
    return text[a:b]


def looks_like_ui(value):
    v = value.strip()
    if not v or not re.search(r"[A-Za-z]", v) or CJK.search(v):
        return False
    if v in BRANDS or v in MONTHS or UNITS.match(v):
        return False
    if v.isupper() and len(v) <= 12:
        return False
    if len(v) > 300 or "\n" in v or TECH.search(v):
        return False
    if re.search(r"[{};()=<>]", v):
        return False
    if " " in v:
        words = re.findall(r"[A-Za-z]{2,}", v)
        return len(words) >= 2
    if not v[0].isupper() or len(v) < 3:
        return False
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", v))


def apply_map(text, data):
    raw_lines = data.get("raw_lines", {})
    if raw_lines:
        text = "\n".join(raw_lines.get(line, line) for line in text.split("\n"))
    for rule in data.get("raw", []):
        text = text.replace(rule["from"], rule["to"])
    strings = data.get("strings", {})
    overrides = data.get("overrides", [])
    repls = []
    for s, e, v, _kind in spans(text):
        repl = None
        line = line_at(text, s) if overrides else ""
        for ov in overrides:
            if v == ov["en"] and ov["when"] in line:
                repl = ov["zh"]
                break
        if repl is None:
            repl = strings.get(v)
        if repl is not None and repl != v:
            repls.append((s, e, repl))
    out, last = [], 0
    for s, e, repl in repls:
        out.append(text[last:s])
        out.append(repl)
        last = e
    out.append(text[last:])
    return "".join(out), len(repls)


def report_untranslated(text, data, limit):
    known_en = set(data.get("strings", {}))
    known_en |= {o["en"] for o in data.get("overrides", [])}
    seen = set()
    rows = []
    for s, _e, v, _kind in spans(text):
        if v in known_en or v in seen:
            continue
        if not looks_like_ui(v):
            continue
        seen.add(v)
        rows.append((text.count("\n", 0, s) + 1, v))
    rows.sort()
    print(f"\n待翻译的新文案：{len(rows)} 条")
    for line, value in rows[:limit]:
        print(f"  L{line}: {value[:160]}")
    if len(rows) > limit:
        print(f"  ... 另外 {len(rows) - limit} 条，使用 --report 查看全部")
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Apply the zh-CN dictionary to HyperCool's WebUI")
    ap.add_argument("--source", help="English index.html to translate")
    ap.add_argument("--from-git", metavar="REV", help="read webroot/index.html from a git revision")
    ap.add_argument("--out", default="webroot/index.html", help="output file (default: webroot/index.html)")
    ap.add_argument("--map", default=os.path.join(here, "zh_map.json"), help="dictionary JSON")
    ap.add_argument("--report", help="write untranslated lines to this file ('-' for stdout)")
    ap.add_argument("--limit", type=int, default=40, help="max untranslated entries printed")
    ap.add_argument("--diff", metavar="FILE", help="compare the result with FILE after writing")
    args = ap.parse_args()

    if args.source and args.from_git:
        ap.error("use either --source or --from-git")
    if args.from_git:
        source = subprocess.check_output(
            ["git", "show", f"{args.from_git}:webroot/index.html"], text=True
        )
        label = f"{args.from_git}:webroot/index.html"
    else:
        path = args.source or args.out
        with open(path, encoding="utf-8") as f:
            source = f.read()
        label = path

    with open(args.map, encoding="utf-8") as f:
        data = json.load(f)
    result, applied = apply_map(source, data)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"source: {label}")
    print(f"dictionary: {args.map} ({len(data.get('strings', {}))} strings)")
    print(f"replaced: {applied} strings -> {args.out}")

    rows = report_untranslated(result, data, args.limit)
    if args.report:
        if args.report == "-":
            print("\n--- untranslated ---")
            for line, value in rows:
                print(f"L{line}: {value}")
        else:
            with open(args.report, "w", encoding="utf-8") as f:
                for line, value in rows:
                    f.write(f"L{line}: {value}\n")
            print(f"report: {args.report} ({len(rows)} lines)")

    if args.diff:
        with open(args.diff, encoding="utf-8") as f:
            expected = f.read().splitlines()
        got = result.splitlines()
        diff = list(difflib.unified_diff(expected, got, fromfile=args.diff, tofile=args.out, lineterm="", n=1))
        print(f"diff: {len(diff)} lines (0 means an exact reproduction)")
        return 0 if not diff else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
