#!/usr/bin/env python3
"""Obsidian vault 結構驗證（literature skill 階段一 QA gate）

用法:
    python3 check_vault.py <vault路徑> [--source-dir <source路徑>]

檢查項目:
  1. 斷鏈 wikilink（連到不存在的筆記）
  2. 孤兒筆記（沒有任何入鏈的原子筆記）
  3. MOC 覆蓋率（atomic / source notes 是否全被 MOC 收錄）
  4. 原子筆記出鏈數（每則 >= 1）
  5. frontmatter 必填欄位（type / status；source note 另需 source_file）
  6. source_file 路徑是否指向實際檔案（提供 --source-dir 時檢查）

結束碼: 0 = 全數通過, 1 = 有問題（明細列印於 stdout）
"""
import os
import re
import sys
import argparse
import collections

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def load_dir(vault, sub):
    out = {}
    p = os.path.join(vault, sub)
    if not os.path.isdir(p):
        return out
    for f in os.listdir(p):
        if f.endswith(".md"):
            with open(os.path.join(p, f), encoding="utf-8") as fh:
                out[f[:-3]] = fh.read()
    return out


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    d = {}
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                d[k.strip()] = v.split("#")[0].strip().strip('"')
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--source-dir", default=None,
                    help="source/ 資料夾路徑；提供時檢查 source_file 是否存在")
    args = ap.parse_args()

    notes = load_dir(args.vault, "notes")
    sources = load_dir(args.vault, "sources")
    mocs = load_dir(args.vault, "MOCs")
    all_names = set(notes) | set(sources) | set(mocs)

    problems = []
    inbound = collections.Counter()
    status_count = collections.Counter()
    outlink_total = 0

    for group, coll in [("notes", notes), ("sources", sources), ("MOCs", mocs)]:
        for name, text in coll.items():
            links = [m.strip() for m in WIKILINK.findall(text)]
            valid = [l for l in links if l in all_names]
            for l in links:
                if l in all_names:
                    inbound[l] += 1
                else:
                    problems.append(f"[斷鏈] {group}/{name} -> [[{l}]]")
            if group == "notes":
                outlink_total += len(valid)
                if len(valid) < 1:
                    problems.append(f"[出鏈不足] notes/{name} 出鏈 0（標準 >=1）")
            fm = frontmatter(text)
            if group != "MOCs":   # MOC 依規定不需 status，不計入分佈以免顯示假性 MISSING
                status_count[fm.get("status", "MISSING")] += 1
            for key in (["type", "status"] if group != "MOCs" else ["type"]):
                if key not in fm:
                    problems.append(f"[frontmatter] {group}/{name} 缺 {key}")
            if group == "sources":
                sf = fm.get("source_file", "")
                if not sf:
                    problems.append(f"[frontmatter] sources/{name} 缺 source_file")
                elif args.source_dir:
                    base = os.path.basename(sf.replace("\\", "/"))
                    found = any(base in files for _, _, files in os.walk(args.source_dir))
                    if not found:
                        problems.append(f"[source_file] sources/{name}: 找不到 {base}")

    for name in notes:
        if inbound[name] == 0:
            problems.append(f"[孤兒] notes/{name} 無任何入鏈")

    moc_links = set()
    for text in mocs.values():
        moc_links |= {m.strip() for m in WIKILINK.findall(text)}
    for name in list(notes) + list(sources):
        if name not in moc_links:
            problems.append(f"[MOC未收錄] {name}")

    # 反向覆蓋：source/ 內存在、但沒有任何 source note 對應的文獻（未建檔偵測）
    if args.source_dir:
        IGNORE_EXT = {".js", ".css", ".png", ".jpg", ".svg", ".json", ".txt", ".md"}
        IGNORE_SUBSTR = ("_files", ".下載")
        referenced = set()
        for text in sources.values():
            fm_d = frontmatter(text)
            sf = fm_d.get("source_file", "")
            if sf:
                referenced.add(os.path.basename(sf.replace("\\", "/")))
        for dirpath, dirnames, files in os.walk(args.source_dir):
            dirnames[:] = [d for d in dirnames if not any(s in d for s in IGNORE_SUBSTR)]
            for f in files:
                if os.path.splitext(f)[1].lower() in IGNORE_EXT:
                    continue
                if any(s in f for s in IGNORE_SUBSTR):
                    continue
                if f not in referenced:
                    rel = os.path.relpath(os.path.join(dirpath, f), args.source_dir)
                    problems.append(f"[未建檔文獻] source/{rel} 尚無對應 source note")

    print("=== vault 統計 ===")
    print(f"notes: {len(notes)}  sources: {len(sources)}  MOCs: {len(mocs)}")
    print(f"status 分佈: {dict(status_count)}")
    if notes:
        print(f"原子筆記平均出鏈: {outlink_total / len(notes):.1f}")
    print()
    if problems:
        print(f"=== 發現 {len(problems)} 個問題 ===")
        for p in problems:
            print(" ", p)
        sys.exit(1)
    print("=== 全數通過 ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
