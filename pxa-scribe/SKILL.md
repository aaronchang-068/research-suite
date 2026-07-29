---
name: pxa-scribe
description: 從 obsidian 知識庫（Obsidian vault）產出合規的 PXA SP（研究）技術報告——NASA CR 風格完整研究報告，遵循 pxa-standards skill 收錄之 PXA-STD-SP-001/002/003 標準體系。凡使用者提到寫 SP、技術報告、研究報告、scribe、PXA-STRUCT-SP、Report.md、把 vault/筆記庫寫成報告、階段二工程文件——即使沒有明說 skill 名稱——都應使用本 skill。範圍到 Report.md 定稿＋docx 正式交付檔為止（含確定性 MD→docx 轉換）；審查簽核（DAA）不在本 skill 範圍。
---

# scribe — 從 vault 產出 PXA SP（研究）報告

> 📊 本 skill 套件內附 `pipeline-flowchart.html`——整條 pipeline 的一頁式流程圖。第一次使用或向他人說明時，先開這張圖。

把 obsidian vault 的已驗證知識轉寫為合規的 **PXA-{TOPIC}-SP-{YYYY}-{NNN}** 研究報告（NASA CR 風格）。核心原則：**規則不在本 skill 重複定義**——PXA 標準體系是唯一規則來源（SSoT），本 skill 只負責流程協調、vault 素材對應與合規驗證。

## 規則 SSoT（撰寫時隨用隨讀，不要憑記憶）

位置：`pxa-standards` skill（`<專案根>/.claude/skills/pxa-standards/`，staging 同步於 `skills-staging/pxa-standards/`）。CLU 系列已退役，規則一律以 pxa-standards 的 STD 正本為準。

| 文件 | 用途 | 何時讀 |
|------|------|--------|
| `references/PXA-STD-SP-002.md` **§3**（本文結構，各 Part 含 SP 分表；§3.4 Part 4 敘事規則；§3.5 [C-n] 三要素；§3.9 撰寫順序） | SP（研究）結構與內容定義 | 立案時全讀 §3；各 Part 動筆前重讀該節 |
| `references/PXA-STD-SP-002.md` §4（語言與格式）、§5（表格 Schema）、§7.2（前頁模板）、§8（檢核清單） | 引用/公式/禁止用語；Schema；前頁；交付檢核 | 撰寫中隨用隨讀 |
| `references/PXA-STD-SP-001.md` | 治理細則；§5.1 文獻層級、§5.2 信度判定（含 vault 對映）、§5.5 vault 證據鏈與 L2 協調制 | 遇疑義時查對應章節 |
| `references/writing-examples.md` **§4**（SP 範例）、§1（段落模式）、§2（句型庫）、§3（黃金範例） | few-shot 範例與句型 | 各 Part 動筆前讀對應範例 |
| `documents/SP-series-map.md` | SP 系列切分、素材筆記清單、裁定紀錄 | 立案時 |

**裁定狀態**：歷次裁定（L2 協調制；vault → SP → TM/TP/設計報告信任鏈；講義 L3；NASA TM/TP/CR＝L2；skill 化；二文件重構）已全數回寫 STD 正本（SP-001 v3.0／SP-002 v2.0），直接依標準條文執行即可；新裁定先查 SP-series-map 裁定紀錄。

## vault 素材對應（詳見 references/vault-mapping.md，動筆前必讀）

| SP 區段 | vault 取材 |
|---------|-----------|
| §2.3 文獻回顧 | 範圍內 source notes（L1/L2/L3 依 series-map） |
| Part 3 數學模型 | 原子筆記「數學形式」節（帶原文式號；`stable` 已逐式核驗） |
| Part 4 推導＋驗證比較 | 原子筆記「文獻回顧」「演算法程序」與文獻對比數據 |
| Part 5 [C-n] | 筆記「關鍵要點」→ 補適用條件＋限制＋★ |
| 附錄 E 逐字摘錄 | 筆記頁碼錨點 → 回 `source/` PDF 擷取 verbatim 原文 |

## 執行流程

### 0. 前置檢查

1. 讀 `documents/SP-series-map.md`：確認本次 SP 的議題、素材筆記清單、STRN、依賴。
2. 跑 literature skill 的 `check_vault.py`（vault 結構須全過）；列出素材筆記的 status 分佈——`reviewed` 筆記的內容在報告中須降信度處理（⚠/★），`stable` 才可標 ✓。
3. 統計範圍內 L2 文獻數；不足 5 時回報使用者裁量（協調制，STD-SP-001 §5.5），不得沉默帶過。NASA TM/TP/CR 計 L2、講義計 L3（STD-SP-001 §5.1）。

### 1. 立案確認（使用者核准後才動筆）

產出立案表交使用者確認：STRN＋後綴（`+v1-0+DRAFT`）、Quick（3,000–5,000 字）或 Update（8,000–15,000 字）模式、**§4.x 主題×素材筆記對應表**（Part 4 每個推導主題用哪幾則筆記）、預估 [C-n] 清單方向。

### 2. 撰寫（依下列 SP 撰寫順序；每個 Part 完成即停下交使用者審——不要連寫多個 Part）

```
§2.3 文獻回顧 → Part 3 → Part 4（逐 §4.x）→ Part 5 → Part 6 §6.1
→ Part 2 其餘 → Part 1（最後）→ 前頁（STD-SP-002 §7.2）→ 附錄 A–F
```

各步要點（細則以 pxa-standards 的 STD 正本為準）：

- **§2.3**：依 L1/L2/L3 組織、結構＝現況→缺口→本 SP 定位；行文標 `[Author Year][L2]✓` 式標記。vault source notes 的「與主題關聯」段是現成素材。
- **Part 3**：每個方程標 `[Author Year, Eq.X]`——直接沿用筆記「數學形式」的原文式號；假設 A-n 格式附合理性。公式五元素：引入句／公式本體（`$$` 三行格式）／符號表（≥4 符號獨立表）／適用條件／應用句。
- **Part 4**：每 §4.x 為 2–3 段連續敘事（禁子標題、禁粗體步驟標記、禁段尾引用堆疊）；開場句「本節分析{主題}，目的為…，預期產出為…」；驗證比較小節必須（✓/⚠ 佐證）；推導完成即標 `[C-n-draft]`；Part 之間插入 page-break div＋`---`，Section 之間不插。
- **Part 5**：每條 `**[C-n]** ★ {結論}`＋適用條件＋限制——**缺適用條件即禁止發行**。★ 判定依 STD-SP-001 §5.2（含 vault 對映：stable→上限 ★★，實測多來源才有 ★★★；reviewed→★；筆記帶 ⚠ →⚠）。
- **Part 6 §6.1**：結論引用索引表（編號/摘要/所在節/適用條件摘要/引用格式）——**不是** TM 的 8 欄參數基線。
- **Part 1**：最後寫；禁公式、禁引用；[C-n] 清單各附適用條件。
- **附錄 E**：每筆正文引用附逐字原文摘錄（回 PDF 擷取，非英文附英譯）；引用位置/原文章節/摘錄/用途四欄。這是 vault 頁碼錨點的直接應用——禁止憑記憶或憑筆記轉述充當摘錄。

### 3. 合規 gate（交付前）

1. 執行 pxa-standards skill 的 `scripts/check_sp.py <Report.md>`：結構不可變、[C-n] 三要素、公式三行格式、page-break 位置、禁止用語、Part 1 淨空、metadata 一致性——全過才可交付。
2. 跑 STD-SP-002 §8.2 人審清單，逐項回報。
3. 抽驗：附錄 E 至少 20% 摘錄回 PDF 原文比對逐字一致。

### 4. docx 正式交付檔（依 STD-SP-001 §2.6）

```
python3 scripts/md2docx.py documents/report/{STRN}.md
```

- 範本：`templates/SP-reference.docx`（正黑＋Times New Roman、A4、頁首 STRN、頁尾頁碼、表格/標題/callout 樣式）。腳本自動處理：`$$` 公式→Word 原生方程式（OMML）、`\tag` 式號保留為式尾 `(X-Y)`、page-break div→分頁、`[!NOTE]` 等 callout→樣式區塊、附錄 E 巢狀表提升、MD 頭部 metadata 剝除（docx 自封面起始）。
- 轉出後以 `soffice --headless --convert-to pdf` 產預覽，**抽查封面、任一公式頁、附錄 E** 三頁版面無誤才交付。
- 版面問題改 `templates/SP-reference.docx` 或 `scripts/md2docx.py` 後重轉——**禁止手工改 docx 版面**。

### 5. 交付與停止

交付 `documents/report/{STRN}.md`＋`{STRN}.docx`（Draft 狀態）。內容修訂一律回 MD 端修改後重轉（MD 為 SSoT，STD-SP-001 §2.6）。審查簽核走 DAA 流程、PDF 由 docx 另存——皆不在本 skill 範圍，不要主動接續。

## 合規紅線（自動化最常踩的雷，時刻自查）

1. **禁止記憶引用**：任何數值/引文當下回 vault→PDF 查核；查不到→定性陳述＋`[來源待補]`。
2. P6 §6.1 與 P1 用 **SP 分表定義**（STD-SP-002 §3.1／§3.6），不是 TM 模板。
3. [C-n] 缺適用條件＝禁止發行。
4. Part 4 假敘事化（子標題/粗體小標/5–6 獨立段/堆疊引用）＝違規。
5. Typora 相容：`$$` 三行、page-break 只在 Part 間、標題 `## Part X:`／`### X.Y` 格式、MD 頭部 metadata 與工具版本表完整。
6. **docx 非 SSoT**：任何內容修訂回 MD 端重轉，禁止直接改 docx（版面問題改範本/腳本）。
