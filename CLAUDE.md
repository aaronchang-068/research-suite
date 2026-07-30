# CLAUDE.md — research-suite 維護準則

本檔給任何在此 repo 工作的 Claude session／協作者。research-suite 是一個 Claude Code / Cowork **plugin marketplace**，內含文獻研究與標準寫作的 skill pipeline。

## 這是什麼

- 單一 plugin：`research-suite`（marketplace 名亦為 `research-suite`）。
- 4 個 skill：`pxa-scout`（文獻探勘）→ `pxa-literature`（研究整理 SOP）→ `pxa-scribe`（技術報告產出）；`pxa-standards` 為規則 SSoT（單一真實來源）。
- 扁平佈局：每個 skill 資料夾位於 repo 根目錄，`marketplace.json` 以 `skills` 欄位指向各資料夾（不使用 `skills/` 子目錄）。

## 不變量（每次變更後必須成立）

1. `marketplace.json` 的 `skills` == 實際存在的 skill 資料夾（無死引用、無遺漏）。
2. 每個 skill 的 `SKILL.md` frontmatter `name:` == 資料夾名（kebab-case、`pxa-` 前綴）。
3. plugin 名／marketplace 名／README 安裝字串一致（目前 `research-suite@research-suite`）。
4. `marketplace.json`、`plugin.json` 為合法 JSON。
5. skill 之間以**名稱**互相引用，不寫死檔案路徑。
6. README 的 skills 表與結構區塊與實際 skill 同步。
7. `pxa-standards` 為規則 SSoT；`pxa-literature`／`pxa-scribe` 只引用規則、不複製。

## 標準作業

- **新增／移除／改名 skill**：改資料夾 → 改 `SKILL.md` 的 `name:` → 更新 `marketplace.json` 的 `skills` → 更新 README（必要時寫 CHANGELOG）→ 驗證 JSON 與路徑 → 交由維護者 commit/push。
- **版本升級**：沿用 `pxa-literature` v3 的「審查 → 實作 → CHANGELOG」紀律（依審查發現逐項編號、落點可追溯）。
- **發佈前檢查**：JSON 合法、`skills` 路徑皆存在、名稱一致、（可行時）`claude plugin validate .`。
- **外部依賴**：以 plugin 層 `plugin.json` 的 `dependencies` 宣告（可鎖 semver、可跨 marketplace），不隨意 vendoring；vendoring 須遵守來源授權並保留出處。

## 環境限制（重要）

git 無法在裝置橋接的掛載點執行（`.git/index.lock` 無法 unlink）。因此固定分工：Claude 準備好檔案改動並寫回硬碟，**git add / commit / push 由維護者在自己的終端機執行**。資料夾改名走 `mv`／`sed`，不走 `git mv`。

## 安裝／更新（供使用者）

```
/plugin marketplace add aaronchang-068/research-suite
/plugin install research-suite@research-suite
/reload-plugins
# 更新：/plugin marketplace update research-suite
```
