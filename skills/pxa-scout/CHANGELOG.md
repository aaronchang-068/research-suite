# scout skill — CHANGELOG

## v1.1.1（2026-08-06）

腳本執行慣例：`snowball.py` 一律 `python3 <skill根>/scripts/…` 從 skill 自身目錄執行、禁止複製進使用者專案；工作檔（seeds.txt、raw.json）放 `documents/lit-scout/`。（修 literature 回報的「腳本滲入專案根」同型問題。）

## v1.1（2026-08-01）

兩項變更：修可靠度（OpenAlex lane）＋新增奠基者錨定（figures）。

### 可靠度：真正的 OpenAlex lane

起因：`snowball.py` docstring 宣稱「OpenAlex 補援」，但程式只打 Semantic Scholar（`OA` 常數定義了卻無任何函式使用）；S2 對共享出口 IP 狂 429、雲端沙箱常直接被擋，使用者體感「常連不上」。

| 變更 | 落點 |
|------|------|
| 新增 OpenAlex 實作：`oa_resolve_raw`／`oa_refs`／`oa_cites`／`oa_recs`／`oa_search`／`oa_fetch_many`（批次＋逐筆噴保）／`oa_dict`（統一輸出欄位） | scripts/snowball.py |
| `op_resolve`／`op_refs`／`op_cites`／`op_recs`／`op_search` 改**provider-ordered**：OpenAlex 優先 → S2 次之 → Crossref 噴保（僅 refs） | scripts/snowball.py |
| 資料通道表與 docstring 同步為「OpenAlex 優先」；WebFetch 通道亦改優先打 OpenAlex URL | SKILL.md §資料通道、docstring |

### 新增：figures 奠基者／代表人物錨定模式

| 項目 | 內容 |
|------|------|
| 方法 | 共被引（co-citation）：一份參考作被幾份種子的 reference list 共同引用＝奠基訊號；高門檻（預設 ≥ 半數種子，`max(2, ⌈N/2⌉)`）篩代表作 → 上捲到作者 |
| 腳本 | `snowball.py figures --seeds ... [--vault] [--top 8] [--min-seeds N]`；輸出 JSON＋奠基者候選表 md（人物／代表作／共引種子／被引／最早年／vault 狀態／OA） |
| 判定分層 | 數字（共引數、被引、年份）＝事實；「X 是奠基者」＝推估（附證據）；模型腦補無數據者＝假設，待查證 |
| 交付 | 缺 vault 的奠基者代表作列「建議納入引用」；取檔／建檔仍走既有流程（source note 屬 literature） |
| 紅線 | 新增「奠基者不得腦補」：人物排序必須來自 citation 數據 |
| 設計選擇 | 以「單一代表作被多種子共引」為主訊號（寧可漏、少而精），不跨作者不同著作做 breadth 聚合——精準優先 |

依賴：figures 需 OpenAlex `referenced_works`（完整參考清單）；種子全解析失敗（沙箱擋網）時腳本明確報錯，導引改本機 Cowork 或人工通道。
