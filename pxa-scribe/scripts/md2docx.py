#!/usr/bin/env python3
"""PXA SP Report.md → docx 轉換（scribe 交付管線）

用法:
    python3 md2docx.py <Report.md> [-o out.docx] [--refdoc SP-reference.docx]

流程（確定性，同一輸入產出同一版面）:
  1. 前處理 MD：
     - 剝除 MD 頭部 metadata 區塊（docx 自「封面」起始；MD 頭部僅為檔案自身 metadata）
     - page-break div → OOXML 原生分頁（其後緊鄰之 `---` 一併移除，避免多餘水平線）
     - 提示區塊 `> [!NOTE]` / `[!IMPORTANT]` / `[!TIP]` → 樣式化引用區塊（BlockText）
  2. pandoc -t docx --reference-doc（LaTeX 數學 → Word 原生 OMML 方程式）
  3. 後處理 docx：頁首 {STRN} 佔位替換、表格版面（自動適寬）
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, zipfile

PAGEBREAK_MD = '\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n'
CALLOUT = {"NOTE": "NOTE", "IMPORTANT": "IMPORTANT", "TIP": "TIP"}


def fix_tags(text: str) -> str:
    r"""$$ 區塊內 \tag{X} → 式尾 \qquad(\text{X})——texmath 會丟棄 \tag，式號需保留供內文「式 (X)」引用"""
    def repl(m):
        body = m.group(1)
        tm = re.search(r"\\tag\{([^}]*)\}", body)
        if not tm:
            return m.group(0)
        num = tm.group(1)
        body = re.sub(r"\s*\\tag\{[^}]*\}\s*", "\n", body).strip()
        return "$$\n" + body + "\\qquad(\\text{" + num + "})\n$$"
    return re.sub(r"\$\$\n(.*?)\$\$", repl, text, flags=re.S)


def preprocess(text: str) -> tuple[str, str]:
    # STRN：取 MD 頭部「文件編號」行
    m = re.search(r"文件編號[:：]\*{0,2}\s*([A-Za-z0-9+\-]+)", text)
    strn = m.group(1) if m else ""

    # 1) 剝除頭部 metadata：自檔首至第一個「## 封面」前
    i = text.find("## 封面")
    if i > 0:
        text = text[i:]

    text = fix_tags(text)

    lines = text.split("\n")
    out = []
    skip_next_hr = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("<div") and "page-break-after" in s:
            out.append(PAGEBREAK_MD)
            skip_next_hr = True
            continue
        if skip_next_hr:
            if s == "":
                continue
            if s == "---":
                skip_next_hr = False
                continue
            skip_next_hr = False
        # 清單項內縮排表格（如附錄 E 引用摘錄）→ 提出為頂層表格（pandoc 不解析巢狀縮排表）
        if re.match(r"^ {2,3}\|", ln):
            if out and out[-1].strip() != "" and not out[-1].lstrip().startswith("|"):
                out.append("")
            out.append(ln.lstrip())
            continue
        # callout 首行：> [!NOTE] **標題** → > **NOTE｜標題**
        mm = re.match(r">\s*\[!(NOTE|IMPORTANT|TIP)\]\s*(.*)", s)
        if mm:
            tag, rest = mm.group(1), mm.group(2).strip()
            rest = rest.strip("*").strip()
            label = f"**{CALLOUT[tag]}**" if not rest else f"**{CALLOUT[tag]}｜{rest}**"
            out.append("> " + label)
            continue
        out.append(ln)
    return "\n".join(out), strn


def postprocess(docx_path: str, strn: str) -> None:
    tmp = tempfile.mkdtemp()
    subprocess.run(["unzip", "-oq", docx_path, "-d", tmp], check=True)
    # 頁首 STRN
    hp = os.path.join(tmp, "word", "header1.xml")
    if os.path.exists(hp):
        h = open(hp, encoding="utf-8").read().replace("{STRN}", strn)
        open(hp, "w", encoding="utf-8").write(h)
    # 表格：固定寬 → 自動適寬（滿版），避免窄欄擠壓中文
    dp = os.path.join(tmp, "word", "document.xml")
    d = open(dp, encoding="utf-8").read()
    d = re.sub(r'<w:tblW w:w="\d+" w:type="dxa"/>', '<w:tblW w:w="5000" w:type="pct"/>', d)
    d = d.replace('<w:tblLayout w:type="fixed"/>', '<w:tblLayout w:type="autofit"/>')
    open(dp, "w", encoding="utf-8").write(d)
    dest = os.path.abspath(docx_path)
    os.remove(docx_path)
    cwd = os.getcwd()
    os.chdir(tmp)
    subprocess.run(["zip", "-Xqr", dest, "."], check=True)
    os.chdir(cwd)
    shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--refdoc", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "SP-reference.docx"))
    a = ap.parse_args()
    out = a.output or os.path.splitext(a.input)[0] + ".docx"

    text = open(a.input, encoding="utf-8").read()
    pre, strn = preprocess(text)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(pre)
        premd = f.name
    subprocess.run([
        "pandoc", premd, "-f", "markdown", "-t", "docx",
        "--reference-doc", a.refdoc, "-o", out,
    ], check=True)
    os.unlink(premd)
    postprocess(out, strn)
    print(f"OK {out}  (STRN: {strn or 'n/a'})")


if __name__ == "__main__":
    main()
