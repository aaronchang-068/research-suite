# literature skill — CHANGELOG

## v3（2026-07-28）

依審查發現逐步更新（編號對應審查報告；v2 原版保留於 `.claude/skills/literature/`，本版位於專案根 `literature-v3/`，經審閱後手動取代原版即可生效）。

### 步驟 1 — 研究能力層（A1–A6）

| 審查項 | 變更 | 落點 |
|--------|------|------|
| A1 缺批判性評估 | source note 新增必要章節「批判評估」（evidence_level L1–L4、方法有效性、適用邊界、可信度評語）；frontmatter 加 `evidence_level`；階段二引用弱證據結論須如實限定效力 | SKILL.md §階段一-3、templates/source-note.md、check_vault E5/E8 |
| A2 文獻衝突無處理機制 | atomic note 新增**必要**章節「爭議與歧異」：歧異一律並陳＋錨點＋裁定（已裁定/未裁定），禁止默默擇一；未裁定項同步登錄 MOC 待釐清；無歧異須寫「無（已核對 N 份）」 | SKILL.md §階段一-4、templates/atomic-note.md、check_vault E8 |
| A3 非研究問題驅動 | 新增「階段〇：研究框架確認」（RQ、工程決策需求、萃取判準三判準）；atomic note frontmatter 加 `rq` | SKILL.md §階段〇、templates、check_vault E5 |
| A4 缺綜合層 | MOC 升級為「索引＋綜合層」：方法比較矩陣（欄位依決策需求）、SOTA 評述（逐 RQ）、待釐清升格必填且條目寫成 scout 缺口語句 | SKILL.md §階段一-5、templates/MOC.md、check_vault W(MOC) |
| A5 閱讀策略太薄 | 新增 Pass 1 全批略讀 → triage 表（seminal/derivative/survey、關聯 RQ、分群、優先序、深讀範圍）；深讀順序依 triage：survey 先、同群 seminal → derivative | SKILL.md §階段一-2 |
| A6 符號統一政策缺席 | 每主題建 `notes/{主題}-符號慣例.md`（軸系、正負號、無因次化）；原子筆記符號表改三欄：本筆記符號｜原文符號（各文獻）｜意義，不一致須寫轉換說明 | SKILL.md §階段一-4、templates/atomic-note.md |

### 步驟 2 — 品質保證層（B7–B10）

| 審查項 | 變更 | 落點 |
|--------|------|------|
| B7 萃取完整性無法驗證 | source note 新增「涵蓋自評」（章節/貢獻逐項標記已萃取/未萃取＋原因）；QA 內容抽驗加第三軌「完整性抽驗」（以涵蓋自評對照原文查 recall） | SKILL.md §階段一-3/-6、templates/source-note.md、check_vault E8 |
| B8 原子筆記無強制內容抽驗 | 含「數學形式」的原子筆記升 `stable` 前公式**全驗**（逐條對照頁面渲染影像），不適用抽驗率 | SKILL.md §階段一-6 |
| B9 status 純榮譽制 | frontmatter 加 `verified: none/structure/content`（＋`verified_date`）並與 status 機械綁定：`stable` 必須 `verified: content`（腳本強制）；stable 後實質修改 → 降回 draft 重驗 | SKILL.md §階段一-6、templates、check_vault E9 |
| B10 頁碼錨點無機械檢查 | check_vault 新增 E7：source note 重點摘錄與 atomic note 來源段每條 bullet 須含 p./§/Eq./ch./式 等錨點 | scripts/check_vault.py |

### 步驟 3 — 工程與腳本層（C11–C14）

| 審查項 | 變更 | 落點 |
|--------|------|------|
| C11 書目 metadata 太弱 | source note frontmatter 加 `venue`、`bibkey`（必填）與 `doi`、`volume_pages`（建議）；階段二參考文獻改由 frontmatter 機械生成，不憑記憶補書目 | templates/source-note.md、SKILL.md §階段二-1、check_vault E5/W |
| C12 check_vault.py 弱點 | (a) `source_file` 改相對路徑比對，同名檔強制完整路徑（E6）；(b) frontmatter 行尾註解只在「空白＋#」時剝除，含 `#` 的 title 不再截斷；(c) 孤兒檢查拆分：全無入鏈＝error、僅 MOC 入鏈＝warning（W1）；另新增 E8/E9/E10/W2 檢查與 error/warning 分級（warning 不擋 gate） | scripts/check_vault.py |
| C13 公式轉寫方法與風險不匹配 | 新增公式轉寫規則：文字層擷取僅作初稿，含數學式頁面須以頁面渲染影像視覺核對後才可寫入 | SKILL.md §階段一-3、環境需求表 |
| C14 增量更新無程序 | 新增「增量更新程序」：新文獻併入 triage → 整合進既有筆記（status 降級＋變更紀錄節）→ 連動 MOC/矩陣/開放問題 → 已交付文件列「受影響段落清單」交使用者決定 → 重跑 QA | SKILL.md §增量更新、templates/atomic-note.md |

### 步驟 4 — 其他（D15–D16）

| 審查項 | 變更 | 落點 |
|--------|------|------|
| D15 evals 覆蓋不足 | 新增 eval 2（衝突整合＋符號對映＋增量降級）、eval 3（QA 失敗修復，含「不可捏造頁碼」紅線）；原有 eval 0/1 的 expected_output 對齊 v3 產物 | evals/evals.json |
| D16 無人值守與大批量 | 新增專節：無人值守＝假設＋記錄＋待裁定清單（衝突一律不代裁）；>10 篇時 Pass 2 可分群平行，但整合/MOC/QA 必須單一主流程 | SKILL.md §無人值守與大批量模式 |

### 同步更新

- `pipeline-flowchart.html`：加入階段〇研究框架帶、triage 節點、批判評估＋涵蓋自評節點、MOC 綜合層節點、QA 三軌抽驗、status↔verified 綁定、增量更新帶、下游「MOC 開放問題 → scout」節點；v3 新增項以紫色 ◆v3 標示。
- `references/example-atomic-note.md`：對齊 v3 格式（`rq`/`verified` frontmatter、爭議與歧異節示範「無歧異」寫法、三欄符號表、證據層級限定語）。

### 未變更（刻意保留）

- `obsidian/` 資料夾命名慣例、三類筆記架構、公式與文本分離規則、階段推進確認、停止點、語言慣例——v2 的骨架全數保留，v3 只疊加研究判斷層與驗證強度。
