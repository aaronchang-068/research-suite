# research-suite — 文獻研究與技術報告 skill 套件

Claude Code / Cowork **plugin marketplace**。內含文獻研究與標準寫作的團隊 skills，供團隊成員一鍵安裝。

## 安裝方式

**Claude Code（CLI）**

```
/plugin marketplace add aaronchang-068/research-suite
/plugin install research-suite@research-suite
/reload-plugins
```

**桌面 App**：Settings → Plugins → Add → **Add from a repository**，輸入
`aaronchang-068/research-suite`，再安裝 `research-suite`。

## 內含 skills（1 個 plugin：`research-suite`）

| skill | 用途 |
|---|---|
| `pxa-scout` | 文獻缺口探勘（引用鏈滾雪球 snowballing） |
| `pxa-literature` | 文獻研究 SOP（source → atomic → MOC → 工程文件草稿） |
| `pxa-scribe` | 依 MOC 產出工程文件（.md → .docx/.pdf） |
| `pxa-standards` | SP 技術報告標準寫作規範檢查 |

安裝後呼叫方式：`/research-suite:pxa-scout`、`/research-suite:pxa-literature` … 以此類推。

## 更新

```
/plugin marketplace update research-suite
```

## Repo 結構

```
.claude-plugin/
  ├─ marketplace.json   ← marketplace 清單（列出 plugin 與其 skills 路徑）
  └─ plugin.json        ← plugin 身分檔
pxa-scout/  pxa-literature/  pxa-scribe/  pxa-standards/
                        ← 各 skill（SKILL.md 就地）
```
