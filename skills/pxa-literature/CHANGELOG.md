# literature skill — CHANGELOG

## v3.2.1（2026-08-06）

修 bug：執行本 skill 時，`check_vault.py` 會被複製到使用者專案根（含 QA 輸出落地 vault_report.txt）。根因＝SKILL.md 指令用相對路徑 `scripts/…`，session cwd 在專案根、路徑不存在，模型遂「重建」腳本進專案。修法：新增「腳本執行慣例」——腳本一律 `python3 <skill根>/scripts/…` 從 skill 自身目錄執行、禁止複製進專案；QA 結果以對話回報、不落地專案根。全部指令範例同步改 `<skill根>` 前綴。（scout／scribe／standards 同型問題同批修正。）

## v3.2（2026-08-01）

導入 **PDF 分流閘門**——解決「來源 PDF 本質（文字型／掃描型）不可控，導致讀取路徑與 token 成本不一致」的問題。起因：一次對 600 頁 PDF 跑 literature，token 快速見底；根因是「文字層擷取 vs 影像渲染」交由模型臨場判斷，缺大檔章節鎖定，且公式視覺核對規則可能觸發全文渲染。

| 項目 | 變更 | 落點 |
|------|------|------|
| PDF 分流閘門 | 新增 `scripts/pdf_probe.py`：量測每頁文字層覆蓋率，確定性判定 `text`／`hybrid`／`scanned`＋`large`（>200 頁）旗標，輸出強制路由 manifest。優先 poppler、回退 pypdf；OCR 分支**委派官方 `pdf` skill**，不內建 OCR | scripts/pdf_probe.py（新增） |
| 前置閘門 | 盤點階段於 `check_vault` 之外加跑 `pdf_probe`，Pass 1／Pass 2 一律依 manifest 路由讀取，不自行改路 | SKILL.md §階段一-1、總流程、最小起步 |
| 公式渲染限縮 | 公式視覺核對從「凡含數學式頁面」限縮為「選定深讀章節內、當下要轉寫公式的那幾頁」，禁止為找公式而整份／整章渲染影像 | SKILL.md §階段一-3、環境需求表 |
| 大檔章節鎖定推廣 | triage「預估深讀範圍」的 >200 頁章節鎖定，從「教科書」推廣到 paper/thesis/report 等所有 `large` 檔 | SKILL.md §階段一-2/-3 |
| 成本控制原則 | 品質原則新增第 6 條：分流路由、文字層優先、影像最小化、大檔絕不整份深讀／渲染 | SKILL.md §品質原則 |
| 增量更新連動 | scout 回流新檔亦先過 `pdf_probe` 再走 Pass 1 | SKILL.md §增量更新 |

設計原則：把高成本決策（文字 vs 影像）從模型裁量收回為機械判定——來源本質不論為何，讀取路徑固定、成本可預期；同時保品質（掃描件不再被當文字層擷取產出亂碼）。

## v3.1（2026-07-30）

新增「工程實踐」章節（source note）——銜接文獻研究與工程實作（coding／Simulink modeling）。

| 項目 | 變更 | 落點 |
|------|------|------|
| 工程實踐章節 | source note 於「我的評註」後新增**必要**章節：實作標的／介面定義（維度、單位、來源式號）／逐步實驗步驟（帶錨點＋驗證點）；純文字描述、不畫圖；無可實作內容寫「不適用（原因）」（比照「爭議與歧異」的「無」模式） | SKILL.md §階段一-3、templates/source-note.md |
| 機械檢查 | E8 必要章節（sources）加入「工程實踐」 | scripts/check_vault.py |
| 階段二連動 | 「工程實踐」節彙整為工程文件「實作/驗證」章的素材 | SKILL.md §階段二-1 |
| evals | eval 0 expected_output 納入工程實踐；新增 eval 4（可實作文獻寫實作藍圖、survey 寫不適用） | evals/evals.json |
| 流程圖同步 | 階段一插入「工程實踐」節點（◆v3.1 標記）；階段二 MOC 節點加「工程實踐 → 實作/驗證章素材」；下游節點改「Python／Simulink／EXE」並列工程實踐為依據 | pipeline-flowchart.html |

設計原則：概念層演算法細節仍住原子筆記「演算法程序」，工程實踐是**文獻層級**的端到端實作藍圖，只引用不重複（一個概念一個家）。

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
