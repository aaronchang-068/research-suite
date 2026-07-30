#!/usr/bin/env python3
"""SP（研究）Report.md 合規檢查（scribe skill 合規 gate）

用法:
    python3 check_sp.py <Report.md>

檢查項（依 PXA-STD-SP-001 v3.0／PXA-STD-SP-002 v2.0，條文對照見 SP-002 §8.1；L2 門檻為協調制，僅回報）:
  1. Part 1–6 不可變結構：六個 Part 齊全、順序正確、無 Part 7、標題格式 `## Part N:`
  2. Part 之間有 page-break div；`### X.Y` 節之間不得有
  3. $$ 三行格式（$$ 必須獨立成行）
  4. [C-n] 三要素：結論行含 ★/⚠ 信度標記，其後含「適用條件」與「限制」
  5. 禁止用語掃描（大約/應該可以/眾所周知/顯然/等等/顯著影響/大幅提升）
  6. Part 1 淨空：無 $$ 公式、無 [Author Year] 外部引用
  7. Part 4 假敘事化：§4.x 內無 ####/##### 子標題、無粗體步驟標記（**Step**、**xx**: 開頭）
  8. 附錄 E 存在且每個引用代碼有「引用摘錄」表
  9. MD 頭部 metadata：文件編號/版本/日期/狀態 齊全
 10. [回報不擋件] [L2] 標記計數（協調制門檻 5）

結束碼: 0 = 全過（第 10 項僅回報）, 1 = 有違規
"""
import re
import sys

REQUIRED_PARTS = ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6"]
BANNED = ["大約", "應該可以", "眾所周知", "顯然", "等等", "顯著影響", "大幅提升"]
PAGEBREAK = 'page-break-after: always'


def main(path):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    problems, notices = [], []

    # 1. Part structure
    part_heads = [(i, l) for i, l in enumerate(lines) if re.match(r"^##\s*Part\s+\d", l)]
    found = [re.match(r"^##\s*Part\s+(\d+)", l).group(1) for _, l in part_heads]
    if found != ["1", "2", "3", "4", "5", "6"]:
        problems.append(f"[結構] Part 順序/數量異常: {found}（要求 1–6 各一、順序固定、無 Part 7）")
    for _, l in part_heads:
        if not re.match(r"^##\s*Part\s+\d+[:：]", l):
            problems.append(f"[結構] Part 標題缺冒號格式: {l.strip()}")

    # 2. page-break between Parts only
    for idx in range(1, len(part_heads)):
        prev_end = part_heads[idx][0]
        seg = "\n".join(lines[part_heads[idx - 1][0]:prev_end])
        if PAGEBREAK not in seg:
            problems.append(f"[分頁] {lines[part_heads[idx-1][0]].strip()} 與下一 Part 之間缺 page-break div")
    # no pagebreak between ### sections (within a part, more than needed)
    for i, l in enumerate(lines):
        if PAGEBREAK in l:
            nxt = next((x for x in lines[i + 1:i + 4] if x.strip()), "")
            if re.match(r"^###\s", nxt):
                problems.append(f"[分頁] 第 {i+1} 行 page-break 出現在 Section 之間（僅允許 Part 間）")

    # 3. $$ three-line format
    for i, l in enumerate(lines):
        s = l.strip()
        if "$$" in s and s != "$$":
            problems.append(f"[公式] 第 {i+1} 行 $$ 未獨立成行: {s[:60]}")

    # 4. [C-n] triples
    cns = [(i, l) for i, l in enumerate(lines) if re.match(r"^\*\*\[C-\d+\]\*\*", l.strip())]
    for i, l in cns:
        if not re.search(r"[★⚠]", l):
            problems.append(f"[C-n] 第 {i+1} 行缺信度標記（★/⚠）: {l.strip()[:50]}")
        block = "\n".join(lines[i:i + 6])
        if "適用條件" not in block:
            problems.append(f"[C-n] 第 {i+1} 行 {l.strip()[:20]} 缺「適用條件」（缺適用條件禁止發行）")
        if "限制" not in block:
            problems.append(f"[C-n] 第 {i+1} 行 {l.strip()[:20]} 缺「限制」")
    if not cns:
        problems.append("[C-n] 全文未找到任何 **[C-n]** 結論")

    # locate part ranges
    def part_range(n):
        starts = [i for i, l in part_heads if re.match(rf"^##\s*Part\s+{n}", l)]
        if not starts:
            return None
        s = starts[0]
        later = [i for i, _ in part_heads if i > s]
        e = later[0] if later else len(lines)
        return "\n".join(lines[s:e])

    # 5. banned phrases
    for w in BANNED:
        for i, l in enumerate(lines):
            if w in l and not l.strip().startswith(">"):
                problems.append(f"[用語] 第 {i+1} 行含禁止用語「{w}」")
                break  # 每詞回報一次即可

    # 6. Part 1 clean
    p1 = part_range(1)
    if p1:
        if "$$" in p1:
            problems.append("[Part1] 含公式（禁止）")
        if re.search(r"\[[A-Z][a-zA-Z]+ (19|20)\d\d", p1):
            problems.append("[Part1] 含外部文獻引用（禁止）")

    # 7. Part 4 pseudo-narrative
    p4 = part_range(4)
    if p4:
        for m in re.finditer(r"^####+\s.*$", p4, re.M):
            problems.append(f"[Part4] 含子標題（禁止）: {m.group(0)[:40]}")
        for m in re.finditer(r"^\*\*(Step\s*\d|步驟\s*\d|[^*]{2,12})[:：]\*\*", p4, re.M):
            problems.append(f"[Part4] 含粗體步驟/小標標記（禁止）: {m.group(0)[:40]}")

    # 8. Appendix E
    if not re.search(r"^#+\s*附錄\s*E", text, re.M):
        problems.append("[附錄E] 缺附錄 E 參考文獻與證據鏈")
    else:
        appe = text.split("附錄 E", 1)[1]
        codes = re.findall(r"^####\s*\[(.+?)\]", appe, re.M)
        for c in codes:
            seg = appe.split(f"[{c}]", 1)[1][:1500]
            if "引用摘錄" not in seg:
                problems.append(f"[附錄E] [{c}] 缺引用摘錄表")

    # 9. metadata header
    head = "\n".join(lines[:30])
    for field in ["文件編號", "版本", "日期", "狀態"]:
        if field not in head:
            problems.append(f"[metadata] 頭部缺「{field}」")

    # 10. L2 count (report only)
    l2 = len(re.findall(r"\[L2\]", text))
    notices.append(f"[L2] 標記出現 {l2} 次（協調制參考門檻 5；不足時須經使用者裁量）")

    print(f"=== check_sp: {path} ===")
    for n in notices:
        print("ℹ", n)
    if problems:
        print(f"\n=== 發現 {len(problems)} 項違規 ===")
        for p in problems:
            print(" ✗", p)
        sys.exit(1)
    print("\n=== 全數通過 ===")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
