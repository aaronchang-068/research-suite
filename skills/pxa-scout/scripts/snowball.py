#!/usr/bin/env python3
"""scout skill — 引用鏈滾雪球（Semantic Scholar 主、OpenAlex/Crossref 補援）

用法:
    snowball.py resolve "<title 或 DOI:10.x/...>"
    snowball.py refs  <id>          # backward：此文獻引用了誰
    snowball.py cites <id>          # forward：誰引用了此文獻
    snowball.py recs  <id>          # 語意相似推薦（S2）
    snowball.py search "<query>" [--limit 20]
    snowball.py sweep --seeds seeds.txt [--vault obsidian/sources]
                      [--query "<關鍵字>"] [--limit-per-op 40] [--out raw.json]

<id>: DOI:10.xxx/... 或 S2 paperId 或 標題（自動 resolve）。
環境變數 S2_API_KEY（免費申請）可解除 S2 嚴格限流。
需可直連網路之環境（本機 Cowork）；雲端沙箱被擋時請改用 SKILL.md 通道 2–4。
輸出：JSON（stdout 或 --out）；sweep 另存同名 .md 候選表草稿。
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
    pid = s2_id(ident)
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
    pid = s2_id(ident)
    return _listing(f"{S2}/paper/{pid}/references?limit={limit}&fields={FIELDS}", "citedPaper") if pid else []


def op_cites(ident, limit):
    pid = s2_id(ident)
    return _listing(f"{S2}/paper/{pid}/citations?limit={limit}&fields={FIELDS}", "citingPaper") if pid else []


def op_recs(ident, limit):
    pid = s2_id(ident)
    if not pid:
        return []
    if pid.startswith("DOI:"):
        pid = (op_resolve(pid) or {}).get("s2id") or pid
    r = http_json(f"{S2R}/papers/forpaper/{pid}?limit={limit}&fields={FIELDS}")
    time.sleep(SLEEP)
    return [d for d in (paper_dict(p) for p in r.get("recommendedPapers") or []) if d]


def op_search(query, limit):
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
    a = ap.parse_args()

    if a.cmd == "sweep":
        sweep(a)
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
