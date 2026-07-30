# CLAUDE.md — research-suite 維護準則

本檔給任何在此 repo 工作的 Claude session／協作者。research-suite 是一個 Claude Code / Cowork **plugin marketplace**，內含文獻研究與標準寫作的 skill pipeline。

## 這是什麼

- 單一 plugin：`research-suite`（marketplace 名亦為 `research-suite`）。
- 4 個 skill：`pxa-scout`（文獻探勘）→ `pxa-literature`（研究整理 SOP）→ `pxa-scribe`（技術報告產出）；`pxa-standards` 為規則 SSoT（單一真實來源）。
- **佈局**：每個 skill 位於 `skills/<name>/SKILL.md`，plugin 安裝時自動探索。這是官方唯一保證會被載入的佈局。

## ⚠️ 載入／sync 的鐵則（踩過的雷）

- skill **必須**放在 `skills/` 目錄下（`skills/<name>/SKILL.md`）才會被自動載入。
- **不要**把 skill 資料夾放在 repo 根目錄再用 `marketplace.json` 的 `skills` 欄位去指——當 `source` 指向 marketplace 根（`.` / `./`）時，該欄位會**取代**預設掃描，實測結果是安裝後 skill 不載入（plugin 看起來是空的）。因此 `marketplace.json` 與 `plugin.json` 都**不宣告** `skills` 欄位，一律靠 `skills/` 自動探索。
- plugin 的 `source` 用 **`./`**（相對路徑**必須以 `./` 開頭**）。裸 `.` 會被 CLI `plugin validate` 放行，但 desktop／claude.ai 的 **sync 後端更嚴會拒絕**，回報籠統的「Marketplace sync failed」。單一 plugin repo 固定寫 `"source": "./"`。

## 不變量（每次變更後必須成立）

1. `skills/` 底下每個資料夾 == 一個 skill；`marketplace.json`／`plugin.json` 都不宣告 `skills` 欄位。
2. 每個 skill 的 `SKILL.md` frontmatter `name:` == 資料夾名（kebab-case、`pxa-` 前綴）。
3. plugin 名／marketplace 名／README 安裝字串一致（目前 `research-suite@research-suite`）。
4. `marketplace.json`、`plugin.json` 為合法 JSON。
5. plugin `source` 以 `./` 開頭（不可用裸 `.`）。
6. skill 之間以**名稱**互相引用，不寫死檔案路徑。
7. README 的 skills 表與結構區塊與實際 skill 同步。
8. `pxa-standards` 為規則 SSoT；`pxa-literature`／`pxa-scribe` 只引用規則、不複製。

## 標準作業

- **新增／移除／改名 skill**：在 `skills/` 下增／刪／改資料夾 → 改 `SKILL.md` 的 `name:` → 更新 README（必要時寫 CHANGELOG）→ 驗證 JSON 與 `skills/` 結構 → 交由維護者 commit/push。（不需動 `marketplace.json` 的 skills，因為沒有該欄位。）
- **版本升級**：沿用 `pxa-literature` v3 的「審查 → 實作 → CHANGELOG」紀律（依審查發現逐項編號、落點可追溯）。
- **發佈前檢查**：JSON 合法、`skills/<name>/SKILL.md` 皆存在、名稱一致、`source` 以 `./` 開頭。`claude plugin validate .` 可跑但**較寬鬆**（會放行裸 `.`）；最終以 desktop/claude.ai 實際 `add`＋`install` 跑一次、確認 skill 有載入為準。
- **外部依賴**：以 plugin 層 `plugin.json` 的 `dependencies` 宣告（可鎖 semver、可跨 marketplace），不隨意 vendoring；vendoring 須遵守來源授權並保留出處。

## 環境限制（重要）

git 無法在裝置橋接的掛載點執行（`.git/index.lock` 無法 unlink）。因此固定分工：Claude 準備好檔案改動並寫回硬碟，**git add / commit / push 由維護者在自己的終端機執行**。資料夾搬移／改名走 `mv`／`sed`，不走 `git mv`。

## 安裝／更新（供使用者）

```
/plugin marketplace add aaronchang-068/research-suite
/plugin install research-suite@research-suite
/reload-plugins
# 更新：/plugin marketplace update research-suite
```
