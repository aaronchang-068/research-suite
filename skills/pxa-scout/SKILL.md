---
name: pxa-scout
description: 文獻缺口探勘——當 vault（obsidian 知識庫）對某議題涵蓋不足時，以引用鏈滾雪球（seed 文獻的 backward references／forward citations／相似推薦／關鍵字搜尋）系統性尋找候選文獻，自動去重 vault 既有收錄，產出候選清單供使用者裁定收錄。取代人工「翻 reference list＋Google Scholar 來回搜尋」。凡使用者提到找文獻、補文獻、文獻缺口、相關文獻、引用鏈、cited by、snowball、找 paper、reference 追蹤、Google Scholar 搜尋——即使沒有明說 skill 名稱——都應使用本 skill。範圍到候選清單＋OA 取得協助為止；收錄建檔（source note）屬 literature skill。
---

# scout — 文獻缺口探勘（引用鏈滾雪球）

> 📊 本 skill 套件內附 `pipeline-flowchart.html`——整條 pipeline 的一頁式流程圖。第一次使用或向他人說明時，先開這張圖。

定位：literature skill 的**上游**。輸入＝議題缺口陳述；輸出＝去重後的候選文獻清單（`documents/lit-scout/{議題}-candidates.md`）＋OA 取得協助。方法學＝系統性文獻回顧的 snowballing：

```
vault 種子文獻 ──┬─ backward（種子引用了誰＝reference list）
                ├─ forward（誰引用了種子＝cited by）
                ├─ similar（語意相似推薦）
                └─ keyword（缺口關鍵字搜尋）
        → 合併去重（vault 既有＋批內）→ 相關性篩選 → 候選表 → 使用者裁定
```

## 資料通道（依序嘗試，每筆候選標註佐證通道）

| 順位 | 通道 | 條件 | 說明 |
|:----:|------|------|------|
| 1 | `scripts/snowball.py`（S2＋OpenAlex＋Crossref API 直連） | 執行環境可直連網路（**本機 Cowork 為主場景**；雲端沙箱通常被擋） | 確定性、可批次、自動去重排序。設 `S2_API_KEY` 環境變數可解除 Semantic Scholar 嚴格限流（免費申請） |
| 2 | WebFetch 打 API endpoint | 雲端 session | 同樣的 S2/Crossref URL；共享出口 IP 常 429——退避重試 ≥60s，仍失敗即換通道，**不要無限重試** |
| 3 | WebSearch | 任何有網路的 session | 關鍵字／標題／「"標題" cited」搜尋，找 arXiv、期刊頁、NTRS；逐筆人工組表 |
| 4 | claude-in-chrome 開 Google Scholar | 使用者桌面連線時 | 用使用者自己的瀏覽器開 seed 的 Scholar 頁 →「被引用次數」頁；最接近人工流程、不受共享 IP 限流 |

## 執行流程

### 0. 缺口確認（動筆前交使用者核准）

1. 讀該議題的 vault 素材：`obsidian/MOCs/` 對應章節＋範圍內 source notes；讀 `documents/SP-series-map.md` 該 SP 列（L2 計數與 ⚠ 註記就是現成的缺口線索）。
2. 產出**缺口陳述表**交使用者確認：缺口一句話（例：「002 薄壁截面缺 open-section shear lag 的實驗驗證文獻」）、種子文獻清單（預設＝該議題 vault 內全部 sources，可增刪）、搜尋深度（預設 1 輪滾雪球；窮盡模式＝滾到連續一輪無新增）、候選上限（預設 30）。

### 1. 種子解析

從 source notes 的 frontmatter／書目行取 title、year、DOI。無 DOI 者以 `snowball.py resolve "<title>"`（或通道 2–4）解析出 DOI／S2 paperId；解析不到的種子標註後仍可做 keyword 通道。

### 2. 滾雪球

```
python3 scripts/snowball.py sweep --seeds seeds.txt --vault obsidian/sources \
    --query "<缺口關鍵字>" --out documents/lit-scout/{議題}-raw.json
```

- `seeds.txt` 每行一筆：`DOI:10.xxx/...` 或標題。
- sweep＝每個種子跑 refs＋cites＋recs，加 `--query` 關鍵字搜尋，合併去重（vault 既有以標題正規化＋DOI 比對剔除），依**命中鏈數**（同一篇出現在幾條引用鏈）與引用數排序。
- 單項操作亦可：`resolve` / `refs <id>` / `cites <id>` / `recs <id>` / `search "<query>"`。
- 腳本不可用時：逐種子以通道 2–4 蒐集，人工維護同欄位表格（去重仍必做——對照 vault sources 標題）。

### 3. 相關性篩選

對 raw 結果逐筆判斷與缺口陳述的相關性（讀 title＋abstract；不確定的保留標 ?），砍到候選上限內。每筆預測文獻層級（期刊/專書/NASA TM-TP-CR → L2；講義/網頁 → L3——依 pxa-standards STD-SP-001 §5.1，**正式判定於 literature 建檔時**）。

### 4. 交付候選表

`documents/lit-scout/{議題}-candidates.md`，欄位：

| # | 書目（Author Year, Title, Venue） | DOI | 引用鏈關係 | 補缺口理由 | 引用數 | 預測層級 | OA 取得 | 佐證通道 |

- **引用鏈關係**寫明來源：`Grant 1992 的 ref`／`被 Kamal 2019 引用`／`S2 相似`／`keyword`。
- **OA 取得**：openAccessPdf／arXiv／NTRS 連結；無 OA 者標「需採購/館際」。
- 表末附：建議收錄 top-N＋理由、放棄項一句話理由。

### 5. 使用者裁定 → 取檔 → 停止

使用者勾選後：OA 者協助下載 PDF 至 `source/` 對應子資料夾（Paper/Textbooks/...，命名慣例同 literature skill）；非 OA 者輸出採購清單。**到此停止**——source note 建檔、vault 收錄走 literature skill，不要主動接續。

## 紅線

1. **禁止憑記憶造書目**——每筆候選必須有 API 回傳、網頁或 Scholar 頁佐證（佐證通道欄必填）；查無 DOI 標 `DOI:—`。
2. 去重是硬要求：交付表內不得出現 vault 已收錄文獻（同 DOI 或正規化標題相同）。
3. 相關性篩選寧可標 `?` 保留交使用者裁定，不得沉默丟棄整條引用鏈。
4. 雲端通道 429 時退避換通道，禁止高頻重試同一 endpoint。
5. 下載僅限合法 OA 來源（出版社 OA、arXiv、NTRS、機構 repository）；不碰盜版鏡像。
