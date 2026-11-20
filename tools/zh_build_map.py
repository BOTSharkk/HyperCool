#!/usr/bin/env python3
"""Rebuild tools/zh_map.json from an English upstream WebUI and a translated one.

Usage:
    python3 tools/zh_build_map.py --source /tmp/index-en.html --target webroot/index.html \
        --out tools/zh_map.json

The generated dictionary contains three parts:
  strings    exact English display string -> Chinese
  overrides  context-specific translations for ambiguous short strings
  raw_lines  whole-line replacements for sentences whose word order was rewritten

Only display strings are collected: paths, shell commands, config keys and
status tokens are not included.
"""

import argparse
import json
import re
from difflib import SequenceMatcher

CJK = re.compile(r"[\u4e00-\u9fff]")
CN_PUNCT = re.compile(r"[，。：；、]")
ATTRS = {"aria-label", "placeholder", "title", "alt"}
CHANGES_RE = re.compile(r"var CHANGES = \{(.*?)\n  \};", re.S)

# Lines whose word order cannot be rebuilt one-to-one. Each pair is
# (English marker, Chinese marker); the full lines are taken from the files.
RAW_MARKERS = [
    ("var bad = !!sticky", "var bad = !!sticky"),
    ("nx = check ?", "nx = check ?"),
    ("snack('System changes '", "snack('系统更改'"),
    ("$('dx-sum')", "$('dx-sum')"),
    ("$('dx-pick-txt')", "$('dx-pick-txt')"),
    ("var who = picked", "var who = picked"),
    ("? (picked ? 'The '", "将恢复系统默认编译方式"),
    (": who + (picked ? ' are'", "将在后台编译"),
    ("snack('Cleared '", "snack('已清理 '"),
    ("(freed > 0 ?", "释放 ' + freed"),
    ("snack('Open '", "snack('打开 '"),
    ("kpNote('Settings saved: '", "kpNote('设置已保存：'"),
    ("ch.slice(0, 8).join('; ')", "ch.slice(0, 8).join('；')"),
    ("kpNote('RAM cleaned (manual, ", "kpNote('内存已清理（手动，"),
    ("kpNote('Junk files cleaned (manual)'", "kpNote('垃圾文件已清理（手动）'"),
    ("a: 'Idle drain '", "a: '待机耗电 '"),
    ("r: a.t.slice(0, 11) + ' to '", "r: a.t.slice(0, 11) + ' 至 '"),
    ("Newest first: the last", "最新在前：最近"),
    ("and ' + kpIdle.length + ' days of idle drain", "，以及 Android 每日电池统计中的"),
    ("'.</p><div class=\"apseg kp-flt\">'", "'。</p><div class=\"apseg kp-flt\">'"),
    ("{ label: 'Clear', fn:", "{ label: '清空', fn:"),
    ("snack('Activity log cleared')", "snack('活动日志已清空')"),
    ("lbl = 'Running';", "lbl = '运行中';"),
    ("'失败' : 'Skipped';", "'失败' : '已跳过';"),
    ("lbl = 'Not running';", "lbl = '未运行';"),
    ("nRun + ' running'", "nRun + ' 个运行中'"),
    ("'No keeper is running'", "'没有守护进程在运行'"),
    ("'No CPU cap or prime-core parking was applied at the last boot.'", "'上次开机没有应用 CPU 上限或超大核停用。'"),
    ("next ? 'Turned on in the settings: starts at the next boot.'", "next ? '已在设置中开启：下次开机时启动。'"),
    ("$('dirty').textContent", "$('dirty').textContent"),
    ("modal(ch.length", "modal(ch.length"),
    ("txt + ': show the restart bar'", "txt + '：显示重启栏'"),
    ("var h = '<div class=\"wk-sum\">Counted since you pressed Mark start",
     "var h = '<div class=\"wk-sum\">自你按下“标记起点”以来"),
    ("var g = wkGroup(r.name), val =", "var g = wkGroup(r.name), val ="),
    ("var sub = byTime ?", "var sub = byTime ?"),
    ("'<div class=\"hint\">Nothing counted'", "'<div class=\"hint\">暂无统计'"),
    ("No app held a wake lock", "暂无应用持有唤醒锁"),
    ("var head = kv.base === 'mark' ?", "var head = kv.base === 'mark' ?"),
    ("var who = wlApp(a.uid, a.pkg), sub =", "var who = wlApp(a.uid, a.pkg), sub ="),
    ("else sumTxt = (sum > 30 ?", "else sumTxt = (sum > 30 ?"),
    ("(top && top.tot >= 5 ?", "(top && top.tot >= 5 ?"),
    ("var core = x.pct >= 95 ?", "var core = x.pct >= 95 ?"),
    ("x: 'Each time the screen was off for 30 minutes", "x: '熄屏 30 分钟以上"),
]


def script_flags(text):
    lines = text.splitlines()
    out = [False] * len(lines)
    for m in re.finditer(r"<script[^>]*>.*?</script>", text, re.S):
        a = text.count("\n", 0, m.start())
        b = text.count("\n", 0, m.end())
        for i in range(a, min(b + 1, len(out))):
            out[i] = True
    return lines, out


def line_tokens(line, is_script):
    toks = []
    if is_script:
        for m in re.finditer(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"", line):
            idx = 1 if m.group(1) is not None else 2
            toks.append((m.start(idx), m.end(idx), m.group(idx)))
        return toks
    i, n = 0, len(line)
    while i < n:
        if line.startswith("<!--", i):
            j = line.find("-->", i)
            i = n if j < 0 else j + 3
            continue
        if line[i] == "<":
            j = line.find(">", i)
            if j < 0:
                break
            for m in re.finditer(r'([\w-]+)="([^"]*)"', line[i:j + 1]):
                if m.group(1) in ATTRS:
                    toks.append((i + m.start(2), i + m.end(2), m.group(2)))
            i = j + 1
            continue
        j = line.find("<", i)
        if j < 0:
            j = n
        seg = line[i:j]
        lead = len(seg) - len(seg.lstrip())
        trail = len(seg) - len(seg.rstrip())
        s, e = i + lead, j - trail
        if e > s:
            toks.append((s, e, line[s:e]))
        i = j
    return toks


def skeleton(line, toks):
    out = []
    last = 0
    for s, e, _ in sorted(toks):
        out.append(line[last:s])
        out.append("\u00a7")
        last = e
    out.append(line[last:])
    return "".join(out)


def changes(text):
    m = CHANGES_RE.search(text)
    if not m:
        return {}
    return dict(re.findall(r'"([a-z0-9_]+)":\s*"((?:[^"\\]|\\.)*)"', m.group(1)))


def line_with(text, needle):
    for line in text.splitlines():
        if needle in line:
            return line
    return None


def build(base, new):
    bl, bs = script_flags(base)
    nl, ns = script_flags(new)
    sm = SequenceMatcher(None, bl, nl, autojunk=False)
    pairs = {}
    bad = {}
    stats = {"paired": 0, "skipped": 0}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        for k in range(min(i2 - i1, j2 - j1)):
            a, b = bl[i1 + k], nl[j1 + k]
            ta = line_tokens(a, bs[i1 + k])
            tb = line_tokens(b, ns[j1 + k])
            if len(ta) != len(tb) or skeleton(a, ta) != skeleton(b, tb):
                stats["skipped"] += 1
                continue
            stats["paired"] += 1
            for (_, _, old), (_, _, val) in zip(ta, tb):
                if old == val:
                    continue
                if not (CJK.search(val) or CN_PUNCT.search(val)):
                    continue
                if not re.search(r"[A-Za-z0-9]", old):
                    continue
                if old in pairs and pairs[old] != val:
                    bad.setdefault(old, set()).add(pairs[old])
                    bad[old].add(val)
                pairs[old] = val

    pairs = {
        k: v for k, v in pairs.items()
        if k != v
        and len(k) > 1
        and (CJK.search(v) or CN_PUNCT.search(v))
        and not re.search(r"[\n{}]", k)
        and len(k) < 500
        and not (k != k.strip() and len(k.strip()) <= 4)
        and not (" " not in k and k[0].islower())
        and k not in {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}
    }

    ch_b, ch_n = changes(base), changes(new)
    for k, old in ch_b.items():
        val = ch_n.get(k)
        if val is not None and val != old:
            pairs[old] = val

    for k in ("Health", "Level", "Cancel"):
        pairs.pop(k, None)
    pairs["Health"] = "健康度"
    pairs["Level"] = "电量"
    pairs["Cancel"] = "取消"
    overrides = [
        {"en": "Health", "zh": "健康状态", "when": "rows.push(['Health'"},
        {"en": "Health", "zh": "健康度", "when": "bstat"},
        {"en": "Level", "zh": "电量", "when": "rows.push(['Level'"},
        {"en": "Level", "zh": "等级", "when": "x_ram_level"},
    ]

    raw_lines = {}
    for en_marker, zh_marker in RAW_MARKERS:
        a = line_with(base, en_marker)
        b = line_with(new, zh_marker)
        if a and b and a != b:
            raw_lines[a] = b
    return pairs, raw_lines, bad, stats, overrides


def main():
    ap = argparse.ArgumentParser(description="Rebuild the HyperCool zh-CN dictionary")
    ap.add_argument("--source", required=True, help="English webroot/index.html")
    ap.add_argument("--target", required=True, help="translated webroot/index.html")
    ap.add_argument("--out", default="tools/zh_map.json")
    args = ap.parse_args()

    with open(args.source, encoding="utf-8") as f:
        base = f.read()
    with open(args.target, encoding="utf-8") as f:
        new = f.read()

    pairs, raw_lines, bad, stats, overrides = build(base, new)
    print(f"strings {len(pairs)}, raw_lines {len(raw_lines)}, conflicts {len(bad)}, {stats}")
    for k, v in list(bad.items())[:8]:
        print("CONFLICT", repr(k), v)

    data = {
        "version": 4,
        "note": "Exact-string dictionary for webroot/index.html. Keys are English display strings; values are Simplified Chinese. raw_lines are whole-line replacements for strings whose word order was rewritten. Technical tokens, paths, commands and config keys are intentionally not included.",
        "raw": [{"from": '<html lang="en">', "to": '<html lang="zh-CN">'}],
        "overrides": overrides,
        "raw_lines": dict(sorted(raw_lines.items())),
        "strings": dict(sorted(pairs.items())),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("written", args.out)


if __name__ == "__main__":
    main()
