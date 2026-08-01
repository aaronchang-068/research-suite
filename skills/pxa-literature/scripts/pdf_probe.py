#!/usr/bin/env python3
"""PDF ingestion 分流閘門 v1（literature skill 階段一 Pass 1 前置）

用途：在深讀之前，先**量測**每份 PDF 的文字層覆蓋率，確定性地判定它是
「文字型／掃描型／混合型」，並輸出強制路由——把「該用文字層擷取還是渲染
影像」這個高成本決策從模型的臨場判斷收回為可重複的機械判定，確保來源不論
本質為何，讀取路徑與 token 成本都一致。

用法:
    python3 pdf_probe.py <pdf檔或資料夾> [--source-dir <root>]
                         [--json <out.json>]
                         [--text-threshold 100] [--large-pages 200]

判定邏輯（每頁擷取文字層，計「有效字元數」）:
    有文字頁       = 該頁去空白後字元數 >= text-threshold（預設 100）
    text_coverage  = 有文字頁數 / 總頁數
    分類           text     coverage >= 0.85   → 文字層擷取，不渲染影像
                   hybrid   0.15 < cov < 0.85  → 文字頁走文字層；無文字頁交 OCR
                   scanned  coverage <= 0.15   → 整份委派 pdf skill OCR
    large 旗標     頁數 > large-pages（預設 200）→ 疊加「先章節定位、只深讀選中章節」

擷取後端：優先 poppler（pdftotext，SKILL.md 已列為環境需求；一次擷取全文、
以換頁符 \\x0c 切頁）；缺 poppler 時回退 pypdf。兩者皆缺則該檔標 unknown。

OCR 分支一律**委派官方 pdf skill**（本腳本不內建 OCR，維持零額外系統依賴）。

輸出：人類可讀摘要表 + JSON manifest（--json 落檔，供 Pass 1 triage 直接取用）。
結束碼: 0 = 全部判定成功; 1 = 有檔案無法判定（unknown）
"""
import os
import re
import sys
import json
import argparse
import subprocess

FORM_FEED = "\x0c"

ROUTE = {
    "text":    "文字層擷取（pdftotext/pdfplumber）；不得整份渲染影像。",
    "hybrid":  "有文字層頁走文字擷取；image_pages 清單交 pdf skill OCR 後併入。",
    "scanned": "整份委派 pdf skill 做 OCR → 產生文字層後再走文字擷取。",
    "unknown": "無法判定（擷取工具缺失或檔案異常）——人工檢視。",
}


def have(cmd):
    from shutil import which
    return which(cmd) is not None


def extract_pages_poppler(path):
    """回傳每頁文字 list；失敗回傳 None。一次 subprocess，以換頁符切頁。"""
    try:
        out = subprocess.run(
            ["pdftotext", "-q", path, "-"],
            capture_output=True, timeout=300,
        )
        if out.returncode != 0:
            return None
        text = out.stdout.decode("utf-8", "replace")
        pages = text.split(FORM_FEED)
        # pdftotext 尾端常多一個空頁（最後一個 \x0c 之後）
        if pages and pages[-1].strip() == "":
            pages = pages[:-1]
        return pages if pages else [text]
    except (OSError, subprocess.SubprocessError):
        return None


def extract_pages_pypdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # 舊名回退
        except ImportError:
            return None
    try:
        reader = PdfReader(path)
        return [(p.extract_text() or "") for p in reader.pages]
    except Exception:
        return None


def extract_pages(path):
    """回傳 (pages:list[str] 或 None, backend:str)。"""
    if have("pdftotext"):
        pages = extract_pages_poppler(path)
        if pages is not None:
            return pages, "poppler"
    pages = extract_pages_pypdf(path)
    if pages is not None:
        return pages, "pypdf"
    return None, "none"


def char_count(page_text):
    """去掉所有空白後的字元數——空白頁（掃描件）趨近 0。"""
    return len(re.sub(r"\s+", "", page_text or ""))


def classify(char_counts, text_threshold=100, hi=0.85, lo=0.15):
    """純函式（可單元測試）：回傳 (classification, coverage, image_pages)。
    image_pages 為 1-indexed、字元數低於門檻（需 OCR）的頁碼清單。"""
    n = len(char_counts)
    if n == 0:
        return "unknown", 0.0, []
    image_pages = [i for i, c in enumerate(char_counts, 1) if c < text_threshold]
    coverage = (n - len(image_pages)) / n
    if coverage >= hi:
        cls = "text"
    elif coverage <= lo:
        cls = "scanned"
    else:
        cls = "hybrid"
    return cls, coverage, image_pages


def probe_file(path, rel, text_threshold, large_pages):
    pages, backend = extract_pages(path)
    if pages is None:
        return {
            "file": rel, "pages": None, "classification": "unknown",
            "text_coverage": None, "large": None, "image_pages": [],
            "backend": backend, "route": ROUTE["unknown"],
            "notes": ["擷取失敗：poppler 與 pypdf 皆不可用或檔案異常"],
        }
    counts = [char_count(p) for p in pages]
    cls, coverage, image_pages = classify(counts, text_threshold)
    n = len(pages)
    large = n > large_pages
    notes = []
    if large:
        notes.append(f"大檔（{n} 頁 > {large_pages}）：先以目錄／章節定位，"
                     "只深讀 triage 選中章節，勿整份深讀。")
    if cls == "scanned":
        notes.append("掃描型：文字層近乎空白，直接文字擷取會得亂碼——須先 OCR。")
    if cls == "hybrid":
        notes.append(f"混合型：{len(image_pages)} 頁無文字層，僅這些頁需 OCR。")
    return {
        "file": rel, "pages": n, "classification": cls,
        "text_coverage": round(coverage, 3), "large": large,
        "image_pages": image_pages, "backend": backend,
        "route": ROUTE[cls], "notes": notes,
    }


def iter_pdfs(target):
    if os.path.isfile(target):
        yield target, os.path.basename(target)
        return
    for dirpath, dirnames, files in os.walk(target):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in sorted(files):
            if f.lower().endswith(".pdf"):
                full = os.path.join(dirpath, f)
                yield full, os.path.relpath(full, target).replace("\\", "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="單一 PDF 或含 PDF 的資料夾（如 source/）")
    ap.add_argument("--source-dir", default=None,
                    help="相對路徑基準；提供時 file 欄改為相對此目錄")
    ap.add_argument("--json", default=None, help="JSON manifest 落檔路徑")
    ap.add_argument("--text-threshold", type=int, default=100,
                    help="每頁『有文字』的最低字元數（預設 100）")
    ap.add_argument("--large-pages", type=int, default=200,
                    help="大檔頁數門檻（預設 200）")
    args = ap.parse_args()

    if not os.path.exists(args.target):
        print(f"找不到路徑：{args.target}", file=sys.stderr)
        sys.exit(2)

    base = args.source_dir or (args.target if os.path.isdir(args.target) else None)
    results = []
    for full, rel in iter_pdfs(args.target):
        if base:
            rel = os.path.relpath(full, base).replace("\\", "/")
        results.append(probe_file(full, rel, args.text_threshold, args.large_pages))

    manifest = {
        "generated_by": "pdf_probe v1",
        "text_threshold_chars": args.text_threshold,
        "large_pages_threshold": args.large_pages,
        "route_legend": ROUTE,
        "files": results,
    }

    # --- 人類可讀摘要 ---
    print("=== PDF ingestion 分流 ===")
    if not results:
        print("（未找到任何 .pdf）")
    hdr = f"{'檔案':<40} {'頁數':>5} {'分類':<8} {'覆蓋':>5} {'大檔':>4} {'需OCR頁':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        cov = "-" if r["text_coverage"] is None else f"{r['text_coverage']:.2f}"
        pages = "-" if r["pages"] is None else str(r["pages"])
        large = "是" if r["large"] else ("-" if r["large"] is None else "否")
        ocr_n = len(r["image_pages"]) if r["classification"] in ("hybrid", "scanned") else 0
        name = r["file"] if len(r["file"]) <= 40 else "…" + r["file"][-39:]
        print(f"{name:<40} {pages:>5} {r['classification']:<8} {cov:>5} {large:>4} {ocr_n:>7}")
    print()
    print("路由與備註：")
    for r in results:
        print(f"  ▸ {r['file']}")
        print(f"      → {r['route']}")
        for note in r["notes"]:
            print(f"      · {note}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        print(f"\nmanifest 已寫入：{args.json}")

    unknown = [r for r in results if r["classification"] == "unknown"]
    sys.exit(1 if unknown else 0)


if __name__ == "__main__":
    main()
