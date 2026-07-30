---
name: pxa-standards
description: PXA 技術報告標準體系的規則 SSoT——收錄 PXA-STD-SP-001（治理標準）與 PXA-STD-SP-002（結構與格式標準）正本、寫作範例集、合規檢查腳本 check_sp.py 與上位標準原文。凡涉及 PXA 技術報告的規則查詢、格式判定、STRN 編號、審查等級、文獻層級（L1/L2/L3）、信度標記（★）、[C-n] 結論格式、前頁模板、合規檢查、標準修訂——即使沒有明說 skill 名稱——都應使用本 skill。本 skill 只定義規則（What/Why），不定義執行流程（How）——撰寫流程屬 scribe skill、文獻建庫屬 literature skill。
---

# pxa-standards — PXA 技術報告標準體系（規則 SSoT）

> 📊 本 skill 套件內附 `pipeline-flowchart.html`——規則體系一頁式架構圖。第一次使用或向他人說明時，先開這張圖。

本 skill 為 PXA 標準體系的**規則單一真實來源（SSoT）與發佈載體**：`references/` 內的 STD 文件即正本（controlled documents，含版本紀錄，標準核准權責）。下游 skill（literature、scribe，未來 latexer）撰寫時**隨用隨讀本 skill 的 references/，不憑記憶**。

## 文件地圖（何時讀哪份）

| 文件 | 定位 | 何時讀 |
|------|------|--------|
| `references/PXA-STD-SP-001.md` v3.1 | **治理**——分級與信任鏈、STRN、審查/DAA、證據品質（L＋★＋vault 證據鏈）、數值規範、取捨研究、修訂紀律 | 遇治理疑義時查對應章節 |
| `references/PXA-STD-SP-002.md` v2.0 | **結構與格式**——Part 1–6 定義（各 Part 含 TM/TP 與 SP 分表）、語言與格式規則、表格 Schema、附錄結構、前頁模板（§7.2）、[S]/[H] 檢核清單（§8） | 立案時全讀 §3；各 Part 動筆前重讀該節；寫前頁時 §7 |
| `references/writing-examples.md` v1.0 | 範例——段落模式（N/F/T）、句型資料庫、黃金範例、SP 範例（few-shot 參考，**非合規條件**） | 各 Part 動筆前讀對應範例 |
| `scripts/check_sp.py` | 合規 gate——[S] 規則確定性檢查（條文對照 SP-002 §8.1） | 交付前必跑 |
| `raw/` | 上位標準原文 PDF（Z39.18/14/23、NASA SP-7602、AFRL Guide、NF-1676） | 裁剪疑義或修訂標準時回查原文 |

## 快速規則索引（最常查的條目）

| 主題 | 位置 |
|------|------|
| 分級判定樹、信任鏈 vault → SP → TM/TP/設計報告 | SP-001 §2.2–2.3 |
| STRN 三格式＋本地後綴＋版本規則 | SP-001 §3 |
| 審查等級、審查結果 A/B/C、DAA、安全分級 | SP-001 §4 |
| 文獻層級 L1/L2/L3（NASA TM/TP/CR＝L2；講義＝L3） | SP-001 §5.1 |
| 信度 ★ 判定樹＋vault status 對映（stable→上限★★） | SP-001 §5.2 |
| vault 證據鏈、L2 協調制、SSoT 迴寫 | SP-001 §5.5 |
| Quick/Update 裁剪 | SP-001 §2.5 |
| Part 1–6 不可變結構 [S] | SP-002 §3.0 |
| Part 4 敘事規則（2–3 段、禁子標題、局部 vs 全域結論） | SP-002 §3.4 |
| [C-n] 三要素（★＋適用條件＋限制；缺適用條件禁止發行）[S] | SP-002 §3.5 |
| 禁止用語 [S]、引用查核（禁記憶引用）、公式五元素 | SP-002 §4 |
| 前頁模板與 {STD_VERSIONS} 佔位符 | SP-002 §7 |
| [S] 腳本清單／[H] 人審清單 | SP-002 §8 |

## 合規 gate

```
python3 scripts/check_sp.py <Report.md>
```

檢查 SP-002 §8.1 全部 [S] 項；L2 計數僅回報（協調制）。結束碼 0＝全過。**凡 [S] 規則以腳本結果為準——不必逐條人工覆核；[H] 項（敘事品質、技術正確性）依 SP-002 §8.2 人審。**

## 已生效裁定（編號同 `documents/SP-series-map.md` 裁定紀錄；均已回寫正文，此表為索引）

| # | 裁定 | 回寫位置 |
|:-:|------|----------|
| 1 | L2 ≥ 5 改協調制（vault QA gate 保證品質；緊繃時回報裁量、不硬擋） | SP-001 §5.5 |
| 2 | 信任鏈改 vault → SP（NASA CR 風格）→ TM/TP/設計報告；TM 層證據角色由 vault 取代 | SP-001 §2.3 |
| 3 | 講義類（Okawa、MIT 16.001 等）定為 L3 | SP-001 §5.1 |
| 6 | NASA 正式出版品（TM/TP/CR）一律 L2 | SP-001 §5.1 |
| 7 | 規則體系 skill 化：STD 正本遷入本 skill；CLU-SP-001–004 退役歸檔 | SP-001 §1.6 |
| 8 | 二文件重構：SP-001 v3.0 純治理／SP-002 v2.0 結構與格式（併 SP-003）；E1–E4 與功能標籤廢除；[S]/[H] 標註 | SP-001 §1.6＋版本紀錄 |
| 9 | 正式交付格式定為 docx（scribe 確定性轉換管線）；MD 仍為 SSoT；latexer 取消，PDF 由 docx 另存 | SP-001 §2.6 |

（裁定 4、5 為 SP 系列專案層裁定——序號整批保留、產製優先序，見 series-map，不涉標準條文。）

新裁定流程：先記入 series-map 裁定紀錄（生效）→ 修訂對應 STD 文件（版本遞增＋版本紀錄行）→ 更新本表與下表（SP-001 §9）。

## 現行版本表（修訂時必同步；前頁 {STD_VERSIONS} 由此填入）

| 文件 | 版本 | 日期 |
|------|:----:|------|
| PXA-STD-SP-001 | v3.1 | 2026-07-19 |
| PXA-STD-SP-002 | v2.0 | 2026-07-18 |
| writing-examples.md | v1.0 | 2026-07-18 |

## 修訂紀律（細則見 SP-001 §9）

1. 規則變更 **必須** 落在 STD 正本（版本遞增＋版本紀錄行），**禁止** 只改 SKILL.md 或下游 skill。
2. [S] 規則變更 **必須** 同步修訂 `check_sp.py`；腳本與條文不一致時以條文為準並立即修腳本。
3. 修訂後同步：本檔裁定表與版本表、scribe skill 章節引用。
4. 涉上位標準解讀時回查 `raw/` 原文，不憑記憶。
5. 歷史版本與退役文件（CLU 系列、SP-003、舊版 SP-001/002）存 `documents/reference/archive/`。
