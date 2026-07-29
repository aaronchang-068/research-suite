#!/usr/bin/env python3
"""Obsidian vault 結構驗證 v3（literature skill 階段一 QA gate）

用法:
    python3 check_vault.py <vault路徑> [--source-dir <source路徑>]

檢查項目（E = error，違反即 exit 1；W = warning，列印供判讀，不影響結束碼）:
  E1  斷鏈 wikilink（連到不存在的筆記）
  E2  孤兒筆記（沒有任何入鏈的原子筆記）
  W1  僅被 MOC 連入的原子筆記（連結密度不足）
  E3  MOC 覆蓋率（atomic / source notes 是否全被 MOC 收錄）
  E4  原子筆記出鏈數（每則 >= 1）
  E5  frontmatter 必填欄位
        source: type / status / verified / authors / year / title / venue /
                bibkey / source_file / evidence_level
        atomic: type / status / verified / rq
        （W: source 缺 doi、stable 缺 verified_date）
  E6  source_file 指向實際檔案（相對路徑比對；同名檔必須給完整相對路徑）
  E7  重點摘錄／來源條目頁碼錨點（每條含 p./§/Eq./ch./式 等錨點）
  E8  必要章節（source: 批判評估、涵蓋自評；atomic: 爭議與歧異 等）
  E9  status ↔ verified 一致性（stable 必須 verified: content）
  E10 公式紀律（$$ display block 必帶 \\tag）
  W2  行內 $...$ 夾帶等號（疑似完整方程式塞進行文）
  E11 未建檔文獻（source/ 內存在但無任何 source note 指向）

結束碼: 0 = 無 error（warning 仍可能存在）, 1 = 有 error
"""
import os
import re
import sys
import argparse
import collections

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
ANCHOR = re.compile(
    r"(pp?\.?\s*\d|§\s*[\dIVX]|Eq[s]?\.?\s*\(?\d|[Cc]h(apter)?\.?\s*\d"
    r"|Sec\.?\s*[\dIVX]|Table\s*\d|Fig[s]?\.?\s*\d|第\s*\d+\s*頁|式\s*\(?\d"
    r"|[Aa]ppendix|attachment|slide\s*\d)")
DISPLAY_MATH = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_MATH = re.compile(r"(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)")

REQ_FM = {
    "sources": ["type", "status", "verified", "authors", "year", "title",
                "venue", "bibkey", "source_file", "evidence_level"],
    "notes": ["type", "status", "verified", "rq"],
    "MOCs": ["type"],
}
REQ_SECTIONS = {
    "sources": ["摘要", "重點摘錄", "批判評估", "涵蓋自評"],
    "notes": ["核心陳述", "文獻回顧", "爭議與歧異", "關鍵要點", "相關概念", "來源"],
}


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
            if ":" in line and not line.strip().startswith("#"):
                k, v = line.split(":", 1)
                v = re.sub(r"\s+#.*$", "", v)   # 只去掉「空白+#」起始的行尾註解
                d[k.strip()] = v.strip().strip('"')
    return d


def sections(text):
    """回傳 {章節名: 章節內文}（## 層級）。"""
    out = {}
    parts = re.split(r"^##\s+(.+)$", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        out[parts[i].strip()] = parts[i + 1]
    if len(parts) % 2 == 0:                     # 最末章節
        out[parts[-1].strip() if len(parts) > 1 else ""] = ""
    return out


def find_section(secs, name):
    for k, v in secs.items():
        if name in k:
            return v
    return None


def bullet_lines(body):
    return [ln.strip() for ln in body.split("\n") if ln.strip().startswith("- ")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--source-dir", default=None,
                    help="source/ 資料夾路徑；提供時檢查 source_file 與未建檔文獻")
    args = ap.parse_args()

    notes = load_dir(args.vault, "notes")
    sources = load_dir(args.vault, "sources")
    mocs = load_dir(args.vault, "MOCs")
    all_names = set(notes) | set(sources) | set(mocs)

    errors, warnings = [], []
    inbound = collections.Counter()          # 全部入鏈
    inbound_nonmoc = collections.Counter()   # 排除 MOC 的入鏈
    status_count = collections.Counter()
    outlink_total = 0

    # source/ 檔案索引（E6 / E11 用）
    src_index = {}   # basename -> [relpath, ...]
    if args.source_dir:
        IGNORE_EXT = {".js", ".css", ".png", ".jpg", ".svg", ".json", ".txt", ".md"}
        IGNORE_SUBSTR = ("_files", ".下載")
        for dirpath, dirnames, files in os.walk(args.source_dir):
            dirnames[:] = [d for d in dirnames if not any(s in d for s in IGNORE_SUBSTR)]
            for f in files:
                if os.path.splitext(f)[1].lower() in IGNORE_EXT:
                    continue
                if any(s in f for s in IGNORE_SUBSTR):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, f), args.source_dir).replace("\\", "/")
                src_index.setdefault(f, []).append(rel)

    referenced_rel = set()   # 已被 source note 指向的 relpath

    for group, coll in [("notes", notes), ("sources", sources), ("MOCs", mocs)]:
        for name, text in coll.items():
            fm = frontmatter(text)
            secs = sections(text)
            links = [m.strip() for m in WIKILINK.findall(text)]
            valid = [l for l in links if l in all_names]
            for l in links:
                if l in all_names:
                    inbound[l] += 1
                    if group != "MOCs":
                        inbound_nonmoc[l] += 1
                else:
                    errors.append(f"[E1 斷鏈] {group}/{name} -> [[{l}]]")

            # --- E4 出鏈 ---
            if group == "notes":
                outlink_total += len(valid)
                if len(valid) < 1:
                    errors.append(f"[E4 出鏈不足] notes/{name} 出鏈 0（標準 >=1）")

            # --- E5 frontmatter ---
            if group != "MOCs":
                status_count[fm.get("status", "MISSING")] += 1
            for key in REQ_FM[group]:
                if key not in fm or fm[key] in ("", "[]"):
                    errors.append(f"[E5 frontmatter] {group}/{name} 缺 {key}")
            if group == "sources" and not fm.get("doi"):
                warnings.append(f"[W doi] sources/{name} 未填 doi（無 DOI 者請於書目節註明）")

            # --- E9 status ↔ verified ---
            st, vf = fm.get("status", ""), fm.get("verified", "")
            if st == "stable":
                if vf != "content":
                    errors.append(f"[E9 status] {group}/{name} status=stable 但 verified={vf or 'none'}（須 content）")
                if group != "MOCs" and not fm.get("verified_date"):
                    warnings.append(f"[W verified_date] {group}/{name} stable 未填 verified_date")
            elif st == "reviewed" and vf not in ("structure", "content"):
                warnings.append(f"[W status] {group}/{name} status=reviewed 但 verified={vf or 'none'}")

            # --- E8 必要章節 ---
            for sec in REQ_SECTIONS.get(group, []):
                if find_section(secs, sec) is None:
                    errors.append(f"[E8 缺章節] {group}/{name} 缺「{sec}」")

            # --- E7 錨點 ---
            if group == "sources":
                body = find_section(secs, "重點摘錄")
                if body:
                    for ln in bullet_lines(body):
                        if not ANCHOR.search(ln):
                            errors.append(f"[E7 無錨點] sources/{name} 重點摘錄：{ln[:40]}…")
            if group == "notes":
                body = find_section(secs, "來源")
                if body:
                    for ln in bullet_lines(body):
                        if not ANCHOR.search(ln):
                            errors.append(f"[E7 無錨點] notes/{name} 來源：{ln[:40]}…")

            # --- E10 / W2 公式紀律（原子筆記） ---
            if group == "notes":
                stripped = text
                for i, blk in enumerate(DISPLAY_MATH.findall(text), 1):
                    if "\\tag" not in blk:
                        errors.append(f"[E10 公式無tag] notes/{name} 第 {i} 個 $$ block 缺 \\tag")
                stripped = DISPLAY_MATH.sub("", stripped)
                for im in INLINE_MATH.findall(stripped):
                    if "=" in im:
                        warnings.append(f"[W2 行內方程] notes/{name}：${im[:30]}$（完整方程式應入數學形式）")

            # --- E6 source_file ---
            if group == "sources":
                sf = fm.get("source_file", "").replace("\\", "/")
                if sf and args.source_dir:
                    rel = re.sub(r"^source/", "", sf)
                    base = os.path.basename(rel)
                    cands = src_index.get(base, [])
                    if rel in cands:
                        referenced_rel.add(rel)
                    elif len(cands) == 1 and "/" not in rel:
                        referenced_rel.add(cands[0])
                        warnings.append(f"[W source_file] sources/{name}: 建議寫完整相對路徑 source/{cands[0]}")
                    elif len(cands) > 1:
                        errors.append(f"[E6 同名檔] sources/{name}: {base} 在 source/ 有多份（{', '.join(cands)}），須寫完整相對路徑")
                    else:
                        errors.append(f"[E6 source_file] sources/{name}: 找不到 {sf}")

    # --- E2 / W1 孤兒與弱連結 ---
    for name in notes:
        if inbound[name] == 0:
            errors.append(f"[E2 孤兒] notes/{name} 無任何入鏈")
        elif inbound_nonmoc[name] == 0:
            warnings.append(f"[W1 弱連結] notes/{name} 僅被 MOC 連入（無其他筆記的「相關概念」指向它）")

    # --- E3 MOC 覆蓋 ---
    moc_links = set()
    for text in mocs.values():
        moc_links |= {m.strip() for m in WIKILINK.findall(text)}
    for name in list(notes) + list(sources):
        if name not in moc_links:
            errors.append(f"[E3 MOC未收錄] {name}")

    # --- W MOC 綜合層 ---
    for name, text in mocs.items():
        secs = sections(text)
        for sec in ("研究框架", "待釐清"):
            if find_section(secs, sec) is None:
                warnings.append(f"[W MOC] MOCs/{name} 缺「{sec}」節（v3 綜合層要求）")

    # --- E11 未建檔文獻 ---
    if args.source_dir:
        for base, rels in src_index.items():
            for rel in rels:
                if rel not in referenced_rel:
                    errors.append(f"[E11 未建檔文獻] source/{rel} 尚無對應 source note")

    # --- 報告 ---
    print("=== vault 統計 ===")
    print(f"notes: {len(notes)}  sources: {len(sources)}  MOCs: {len(mocs)}")
    print(f"status 分佈: {dict(status_count)}")
    if notes:
        print(f"原子筆記平均出鏈: {outlink_total / len(notes):.1f}")
    print()
    if warnings:
        print(f"=== {len(warnings)} 個 warning（判讀後回報，不擋 gate）===")
        for w in warnings:
            print(" ", w)
        print()
    if errors:
        print(f"=== 發現 {len(errors)} 個 error ===")
        for e in errors:
            print(" ", e)
        sys.exit(1)
    print("=== error 全數通過 ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
