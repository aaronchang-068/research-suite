#!/usr/bin/env python3
"""scout skill — 引用鏈滾雪球 + 奠基者錨定（OpenAlex 主、Semantic Scholar 次、Crossref 噴保）

用法:
    snowball.py resolve "<title 或 DOI:10.x/...>"
    snowball.py refs  <id>          # backward：此文獻引用了誰
    snowball.py cites <id>          # forward：誰引用了此文獻
    snowball.py recs  <id>          # 語意相似推薦
    snowball.py search "<query>" [--limit 20]
    snowball.py sweep --seeds seeds.txt [--vault obsidian/sources]
                      [--query "<關鍵字>"] [--limit-per-op 40] [--out raw.json]
    snowball.py figures --seeds seeds.txt [--vault obsidian/sources]
                      [--top 8] [--min-seeds N] [--limit-per-op 60] [--out figures.json]

<id>: DOI:10.xxx/... 或 S2 paperId 或 標題（自動 resolve）。

資料來源順位（refs/cites 皆同）：**OpenAlex 優先**（免金鑰、額度大、少斷）→ S2 次之
（帶 S2_API_KEY 可解嚴格限流）→ Crossref 噴保（僅 refs）。OpenAlex 用 mailto polite pool。
需可直連網路之環境（本機 Cowork）；雲端沙箱被擋時請改用 SKILL.md 通道 2–4。
輸出：JSON（stdout 或 --out）；sweep／figures 另存同名 .md 表格草稿。

figures＝奠基者／代表人物錨定：以「共被引」（一份參考作被幾份種子的 reference list 共同
引用）為奠基訊號，高門檻（預設 ≥ 半數種子）篩出領域反覆奠基引用的代表作，上捲到作者。
"""
import argparse, json, os, re, sys, time, unicodedata
import urllib.request, urllib.parse, urllib.error

S2 = "https://api.semanticscholar.org/graph/v1"
S2R = "https://api.semanticscholar.org/recommendations/v1"
OA = "https://api.openalex.org"
CR = "https://api.crossref.org"
FIELDS = "title,year,externalIds,venue,citationCount,openAccessPdf,authors"
MAILTO = "research-suite@example.com"
SLEEP = 1.2 if os.environ.get("S2_API_KEY") else 3.2
OA_SLEEP = 0.2   # OpenAlex polite pool 寬鬆，短 sleep 即可


def http_json(url, tries=4):
    req = urllib.request.Request(url, headers={
        "User-Agent": f"pxa-scout/1.0 (mailto:{MAILTO})",
        **({"x-api-key": os.environ["S2_API_KEY"]} if "api.semanticscholar" in url and os.environ.get("S2_API_KEY") else {}),
    })
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                wait = 10 * (i + 1)
                print(f"  [429] backoff {wait}s: {url[:80]}", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if i < tries - 1:
                time.sleep(5)
                continue
            raise


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").lower()
    return re.sub(r"[^a-z0-9一-鿿]+", "", t)


def paper_dict(p):
    """統一 S2 paper 物件為輸出欄位"""
    if not p or not p.get("title"):
        return None
    ext = p.get("externalIds") or {}
    oa = (p.get("openAccessPdf") or {}).get("url")
    authors = ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:4])
    return {
        "title": p["title"], "year": p.get("year"), "authors": authors,
        "venue": p.get("venue") or "", "doi": ext.get("DOI"),
        "arxiv": ext.get("ArXiv"), "s2id": p.get("paperId"),
        "citations": p.get("citationCount"), "oa_pdf": oa,
    }


# ── OpenAlex lane（主通道：免金鑰、referenced_works 完整、少斷）──────────────

def oa_short_id(oaid):
    """https://openalex.org/W123 → W123"""
    return (oaid or "").rsplit("/", 1)[-1]


def norm_author(name):
    """作者名正規化為 姓_首字母（heuristic，供 figures 上捲；縮寫/全名會被合併）。"""
    name = (name or "").strip()
    if not name:
        return None
    parts = name.replace(".", "").split()
    if not parts:
        return None
    return f"{parts[-1].lower()}_{parts[0][0].lower()}" if parts[0] else parts[-1].lower()


def oa_dict(w):
    """統一 OpenAlex work 物件為與 paper_dict 相同的輸出欄位（多帶 oaid／_refs）。"""
    if not w or not (w.get("display_name") or w.get("title")):
        return None
    doi = re.sub(r"^https?://doi\.org/", "", w.get("doi") or "", flags=re.I) or None
    authors = ", ".join((a.get("author") or {}).get("display_name", "")
                        for a in (w.get("authorships") or [])[:4])
    oa = (w.get("open_access") or {}).get("oa_url") \
        or ((w.get("best_oa_location") or {}) or {}).get("pdf_url")
    venue = (((w.get("primary_location") or {}).get("source") or {}) or {}).get("display_name") or ""
    return {
        "title": w.get("display_name") or w.get("title"),
        "year": w.get("publication_year"), "authors": authors, "venue": venue,
        "doi": doi, "arxiv": None, "s2id": None, "oaid": oa_short_id(w.get("id")),
        "citations": w.get("cited_by_count"), "oa_pdf": oa,
        "_refs": w.get("referenced_works") or [],
    }


def oa_resolve_raw(ident):
    """回傳 OpenAlex 原始 work 物件（含 authorships／referenced_works）。"""
    ident = ident.strip()
    if ident.upper().startswith("DOI:"):
        ident = ident[4:]
    if re.match(r"^10\.\d{4,}/", ident):
        return http_json(f"{OA}/works/https://doi.org/{urllib.parse.quote(ident)}?mailto={MAILTO}")
    if re.fullmatch(r"W\d+", ident):
        return http_json(f"{OA}/works/{ident}?mailto={MAILTO}")
    r = http_json(f"{OA}/works?search={urllib.parse.quote(ident)}&per-page=1&mailto={MAILTO}")
    res = r.get("results") or []
    return res[0] if res else None


def oa_fetch_many(ids, limit=None):
    """批次抓多個 OpenAlex work（先試 pipe-OR 批次，失敗退回逐筆 /works/{id}，確保正確）。"""
    short = [oa_short_id(i) for i in ids if i]
    if limit:
        short = short[:limit]
    out = []
    for i in range(0, len(short), 50):
        chunk = short[i:i + 50]
        try:
            u = f"{OA}/works?filter=openalex_id:{'|'.join(chunk)}&per-page=50&mailto={MAILTO}"
            res = (http_json(u).get("results") or [])
            if res:
                out.extend(d for d in (oa_dict(x) for x in res) if d)
                time.sleep(OA_SLEEP)
                continue
        except Exception:
            pass
        for sid in chunk:                       # 逐筆噴保（語法保證正確）
            try:
                d = oa_dict(http_json(f"{OA}/works/{sid}?mailto={MAILTO}"))
                if d:
                    out.append(d)
            except Exception:
                pass
            time.sleep(OA_SLEEP)
    return out


def oa_refs(ident, limit):
    w = oa_resolve_raw(ident)
    if not w:
        return []
    return oa_fetch_many(w.get("referenced_works") or [], limit=limit)


def oa_cites(ident, limit):
    w = oa_resolve_raw(ident)
    if not w:
        return []
    oaid = oa_short_id(w.get("id"))
    u = f"{OA}/works?filter=cites:{oaid}&per-page={min(limit, 50)}&sort=cited_by_count:desc&mailto={MAILTO}"
    return [d for d in (oa_dict(x) for x in (http_json(u).get("results") or [])) if d]


def oa_recs(ident, limit):
    w = oa_resolve_raw(ident)
    if not w:
        return []
    return oa_fetch_many(w.get("related_works") or [], limit=limit)


def oa_search(query, limit):
    u = f"{OA}/works?search={urllib.parse.quote(query)}&per-page={limit}&mailto={MAILTO}"
    return [d for d in (oa_dict(x) for x in (http_json(u).get("results") or [])) if d]


# ── Semantic Scholar lane（次通道）──────────────────────────────────────────

def s2_id(ident):
    ident = ident.strip()
    if ident.upper().startswith("DOI:"):
        return "DOI:" + ident[4:]
    if re.fullmatch(r"[0-9a-f]{40}", ident):
        return ident
    if re.match(r"^10\.\d{4,}/", ident):
        return "DOI:" + ident
    # 標題 → search resolve
    r = http_json(f"{S2}/paper/search?query={urllib.parse.quote(ident)}&limit=1&fields={FIELDS}")
    time.sleep(SLEEP)
    data = (r.get("data") or [])
    if not data:
        return None
    return data[0]["paperId"]


def op_resolve(ident):
    try:                                    # OpenAlex 優先
        d = oa_dict(oa_resolve_raw(ident))
        if d:
            time.sleep(OA_SLEEP)
            return d
    except Exception as e:
        print(f"  [OA resolve 失敗] {e}", file=sys.stderr)
    pid = s2_id(ident)                       # S2 次之
    if not pid:
        return {"error": f"resolve 失敗: {ident}"}
    r = http_json(f"{S2}/paper/{pid}?fields={FIELDS}")
    time.sleep(SLEEP)
    return paper_dict(r)


def _listing(url, key):
    r = http_json(url)
    time.sleep(SLEEP)
    out = []
    for item in r.get("data") or []:
        p = paper_dict(item.get(key) if key else item)
        if p:
            out.append(p)
    return out


def op_refs(ident, limit):
    try:                                    # OpenAlex 優先
        r = oa_refs(ident, limit)
        if r:
            return r
    except Exception as e:
        print(f"  [OA refs 失敗，改 S2] {e}", file=sys.stderr)
    pid = s2_id(ident)                       # S2 次之
    if pid:
        try:
            r = _listing(f"{S2}/paper/{pid}/references?limit={limit}&fields={FIELDS}", "citedPaper")
            if r:
                return r
        except Exception as e:
            print(f"  [S2 refs 失敗，改 Crossref] {e}", file=sys.stderr)
    if ident.strip().upper().startswith("DOI:"):   # Crossref 噴保
        return crossref_refs(ident.strip()[4:])
    return []


def op_cites(ident, limit):
    try:                                    # OpenAlex 優先
        r = oa_cites(ident, limit)
        if r:
            return r
    except Exception as e:
        print(f"  [OA cites 失敗，改 S2] {e}", file=sys.stderr)
    pid = s2_id(ident)                       # S2 次之
    return _listing(f"{S2}/paper/{pid}/citations?limit={limit}&fields={FIELDS}", "citingPaper") if pid else []


def op_recs(ident, limit):
    try:                                    # OpenAlex related_works 優先
        r = oa_recs(ident, limit)
        if r:
            return r
    except Exception as e:
        print(f"  [OA recs 失敗，改 S2] {e}", file=sys.stderr)
    pid = s2_id(ident)                       # S2 次之
    if not pid:
        return []
    if pid.startswith("DOI:"):
        pid = (op_resolve(pid) or {}).get("s2id") or pid
    r = http_json(f"{S2R}/papers/forpaper/{pid}?limit={limit}&fields={FIELDS}")
    time.sleep(SLEEP)
    return [d for d in (paper_dict(p) for p in r.get("recommendedPapers") or []) if d]


def op_search(query, limit):
    try:                                    # OpenAlex 優先
        r = oa_search(query, limit)
        if r:
            return r
    except Exception as e:
        print(f"  [OA search 失敗，改 S2] {e}", file=sys.stderr)
    return _listing(f"{S2}/paper/search?query={urllib.parse.quote(query)}&limit={limit}&fields={FIELDS}", None)


def crossref_refs(doi):
    """Crossref 備援：由 DOI 取 reference list（S2 失敗時）"""
    try:
        r = http_json(f"{CR}/works/{urllib.parse.quote(doi)}?mailto={MAILTO}")
        refs = (r.get("message") or {}).get("reference") or []
        out = []
        for x in refs:
            t = x.get("article-title") or x.get("volume-title") or x.get("unstructured")
            if t:
                out.append({"title": t, "year": x.get("year"), "authors": x.get("author") or "",
                            "venue": x.get("journal-title") or "", "doi": x.get("DOI"),
                            "arxiv": None, "s2id": None, "citations": None, "oa_pdf": None})
        return out
    except Exception:
        return []


def vault_known(vault_dir):
    """掃 vault sources：回傳 (正規化標題集合, DOI 集合)"""
    titles, dois = set(), set()
    if not vault_dir or not os.path.isdir(vault_dir):
        return titles, dois
    for fn in os.listdir(vault_dir):
        if not fn.endswith(".md"):
            continue
        txt = open(os.path.join(vault_dir, fn), encoding="utf-8", errors="ignore").read()
        m = re.search(r"^title:\s*(.+)$", txt, re.M)
        if m:
            titles.add(norm_title(m.group(1).strip().strip('"')))
        titles.add(norm_title(re.sub(r"^\d{4}\s+\S+\s+-\s+", "", fn[:-3])))
        for d in re.findall(r"10\.\d{4,}/[^\s\)\]\"']+", txt):
            dois.add(d.rstrip(".,;").lower())
    return titles, dois


def sweep(args):
    seeds = [ln.strip() for ln in open(args.seeds, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
    kt, kd = vault_known(args.vault)
    agg = {}   # key -> {paper, chains:[...]}

    def add(p, chain):
        if not p:
            return
        key = (p.get("doi") or "").lower() or norm_title(p["title"])
        if not key:
            return
        if (p.get("doi") or "").lower() in kd or norm_title(p["title"]) in kt:
            return  # vault 已收錄
        e = agg.setdefault(key, {**p, "chains": []})
        if chain not in e["chains"]:
            e["chains"].append(chain)

    for s in seeds:
        label = s[:50]
        print(f"== seed: {label}", file=sys.stderr)
        try:
            for p in op_refs(s, args.limit_per_op):
                add(p, f"ref of [{label}]")
        except Exception as e:
            print(f"  refs 失敗（{e}），試 Crossref", file=sys.stderr)
            if s.upper().startswith("DOI:"):
                for p in crossref_refs(s[4:]):
                    add(p, f"ref of [{label}] (crossref)")
        for op, tag in ((op_cites, "cites"), (op_recs, "similar")):
            try:
                for p in op(s, args.limit_per_op):
                    add(p, f"{tag} [{label}]")
            except Exception as e:
                print(f"  {tag} 失敗: {e}", file=sys.stderr)
    if args.query:
        try:
            for p in op_search(args.query, args.limit_per_op):
                add(p, f"keyword [{args.query}]")
        except Exception as e:
            print(f"  search 失敗: {e}", file=sys.stderr)

    ranked = sorted(agg.values(), key=lambda x: (-len(x["chains"]), -(x.get("citations") or 0)))
    out = args.out or "sweep-raw.json"
    json.dump(ranked, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 候選表草稿
    md = out.rsplit(".", 1)[0] + ".md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("| # | 書目 | DOI | 引用鏈關係 | 引用數 | OA |\n|--|------|-----|-----------|:----:|----|\n")
        for i, p in enumerate(ranked, 1):
            bib = f"{p.get('authors','')} ({p.get('year','?')}). {p['title']}. {p.get('venue','')}"
            f.write(f"| {i} | {bib} | {p.get('doi') or '—'} | {'；'.join(p['chains'])} | {p.get('citations') or '—'} | {p.get('oa_pdf') or ('arXiv:'+p['arxiv'] if p.get('arxiv') else '—')} |\n")
    print(f"OK {len(ranked)} 筆候選（去重後）→ {out} / {md}")


def figures(args):
    """奠基者／代表人物錨定：以『共被引』為奠基訊號，高門檻篩代表作 → 上捲作者。

    訊號＝一份參考作被幾份種子的 reference list 共同引用（co-citation breadth）。
    只有被 ≥ min_seeds 份種子共引的參考作才進入（高門檻＝寧可漏），再依作者上捲。
    需 OpenAlex 的 referenced_works（此模式不走 S2，因 co-citation 需完整 ref list）。
    """
    seeds = [ln.strip() for ln in open(args.seeds, encoding="utf-8")
             if ln.strip() and not ln.startswith("#")]
    n = len(seeds)
    min_seeds = args.min_seeds or (1 if n < 2 else max(2, (n + 1) // 2))
    kt, kd = vault_known(args.vault)

    # 1) 逐種子取 OpenAlex reference list，累計每份參考作被幾份種子共引
    cocite = {}   # oaid -> set(seed label)
    resolved = 0
    for s in seeds:
        label = s[:50]
        print(f"== seed refs: {label}", file=sys.stderr)
        try:
            w = oa_resolve_raw(s)
        except Exception as e:
            print(f"  [OA resolve 失敗] {e}", file=sys.stderr)
            w = None
        if not w:
            print("  種子解析失敗，跳過（co-citation 需 OpenAlex ref list）", file=sys.stderr)
            continue
        resolved += 1
        for rid in (w.get("referenced_works") or []):
            cocite.setdefault(oa_short_id(rid), set()).add(label)
        time.sleep(OA_SLEEP)

    if resolved == 0:
        print("！OpenAlex 無法解析任何種子（可能沙箱擋網）——請改在本機 Cowork 執行，"
              "或依 SKILL.md 通道 3–4 人工找奠基者。", file=sys.stderr)
        print(json.dumps({"error": "no_openalex_access", "seeds_resolved": 0}, ensure_ascii=False))
        sys.exit(2)

    # 2) 高門檻：只留被 >= min_seeds 份種子共引的參考作
    survivors = {sid: seedset for sid, seedset in cocite.items() if len(seedset) >= min_seeds}
    print(f"共引存活 {len(survivors)}/{len(cocite)} 份參考作"
          f"（門檻 {min_seeds}/{n} 種子；解析成功 {resolved}/{n}）", file=sys.stderr)

    # 3) 取存活作 metadata → 依作者上捲（作者 breadth＝其代表作被共引的種子聯集）
    metas = oa_fetch_many(list(survivors.keys()))
    by_oaid = {m["oaid"]: m for m in metas if m.get("oaid")}
    people = {}   # akey -> {display, seeds:set, works:{oaid:work}}
    for sid, seedset in survivors.items():
        d = by_oaid.get(sid)
        if not d:
            continue
        # 逐作者：需完整 authorships，重抓原始物件
        try:
            raw = oa_resolve_raw("DOI:" + d["doi"]) if d.get("doi") else http_json(f"{OA}/works/{sid}?mailto={MAILTO}")
        except Exception:
            raw = None
        names = [(a.get("author") or {}).get("display_name", "")
                 for a in ((raw or {}).get("authorships") or [])] or d.get("authors", "").split(", ")
        for name in names:
            k = norm_author(name)
            if not k:
                continue
            e = people.setdefault(k, {"display": name, "seeds": set(), "works": {}})
            if len(name) > len(e["display"]):
                e["display"] = name
            e["seeds"] |= seedset
            e["works"][sid] = d
        time.sleep(OA_SLEEP)

    # 4) 排序：作者共引 breadth → 代表作被引 → 奠基年代（越早越前）
    def landmark(e):
        return max(e["works"].values(), key=lambda w: (w.get("citations") or 0))

    def score(e):
        breadth = len(e["seeds"])
        cits = max((w.get("citations") or 0) for w in e["works"].values())
        earliest = min((w.get("year") or 9999) for w in e["works"].values())
        return (breadth, cits, -earliest)

    ranked = sorted(people.values(), key=score, reverse=True)[:args.top]

    rows = []
    for e in ranked:
        lm = landmark(e)
        in_vault = ((lm.get("doi") or "").lower() in kd) or (norm_title(lm.get("title", "")) in kt)
        rows.append({
            "person": e["display"], "cocited_seeds": len(e["seeds"]), "seeds_total": n,
            "landmark": lm, "earliest_year": min((w.get("year") or 9999) for w in e["works"].values()),
            "max_citations": max((w.get("citations") or 0) for w in e["works"].values()),
            "works_count": len(e["works"]), "in_vault": in_vault,
        })

    out = args.out or "figures.json"
    json.dump({"min_seeds": min_seeds, "seeds_total": n, "seeds_resolved": resolved,
               "figures": rows}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = out.rsplit(".", 1)[0] + ".md"
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# 奠基者／代表人物錨定（共引門檻 ≥ {min_seeds}/{n} 種子）\n\n")
        f.write("> 表內數字（共引種子數、被引、年份）為 OpenAlex 事實；"
                "「奠基者」判定屬**推估**，請於交付時標注並交使用者裁定。\n\n")
        f.write("| # | 人物 | 代表作 | 共引種子 | 代表作被引 | 最早年 | vault | OA 取得 |\n")
        f.write("|--|------|--------|:-------:|:--------:|:----:|:----:|--------|\n")
        for i, r in enumerate(rows, 1):
            lm = r["landmark"]
            bib = f"{lm.get('authors','')} ({lm.get('year','?')}). {lm.get('title','')}. {lm.get('venue','')}"
            oa = lm.get("oa_pdf") or (f"arXiv:{lm['arxiv']}" if lm.get("arxiv") else "—")
            vault = "✓已收錄" if r["in_vault"] else "缺"
            f.write(f"| {i} | {r['person']} | {bib} | {r['cocited_seeds']}/{n} | "
                    f"{lm.get('citations') or '—'} | {r['earliest_year']} | {vault} | {oa} |\n")
    print(f"OK {len(rows)} 位奠基者候選（門檻 {min_seeds}/{n}）→ {out} / {md}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("resolve", "refs", "cites", "recs"):
        p = sub.add_parser(c)
        p.add_argument("ident")
        p.add_argument("--limit", type=int, default=40)
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("sweep")
    p.add_argument("--seeds", required=True)
    p.add_argument("--vault", default=None)
    p.add_argument("--query", default=None)
    p.add_argument("--limit-per-op", type=int, default=40)
    p.add_argument("--out", default=None)
    p = sub.add_parser("figures")
    p.add_argument("--seeds", required=True)
    p.add_argument("--vault", default=None)
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--min-seeds", type=int, default=0, help="共引門檻；0＝自動（max(2, 半數種子)）")
    p.add_argument("--limit-per-op", type=int, default=60)
    p.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.cmd == "sweep":
        sweep(a)
        return
    if a.cmd == "figures":
        figures(a)
        return
    if a.cmd == "resolve":
        r = op_resolve(a.ident)
    elif a.cmd == "refs":
        r = op_refs(a.ident, a.limit)
    elif a.cmd == "cites":
        r = op_cites(a.ident, a.limit)
    elif a.cmd == "recs":
        r = op_recs(a.ident, a.limit)
    else:
        r = op_search(a.query, a.limit)
    json.dump(r, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
