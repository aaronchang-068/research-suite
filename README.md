# Skills for Claude Code — 品翔航太 CTO 研究套件

Claude Code / Cowork **plugin marketplace**。內含文獻研究與標準寫作的團隊 skills，供團隊成員一鍵安裝。

## 安裝方式

**Claude Code（CLI）**

```
/plugin marketplace add aaronchang-068/Skills-for-Claude-Code
/plugin install research-suite@skills-for-claude-code
/reload-plugins
```

**桌面 App**：Settings → Plugins → Add → **Add from a repository**，輸入
`aaronchang-068/Skills-for-Claude-Code`，再安裝 `research-suite`。

## 內含 skills（1 個 plugin：`research-suite`）

| skill | 用途 |
|---|---|
| `pxa-scout` | 文獻缺口探勘（引用鏈滾雪球 snowballing） |
| `pxa-literature` | 文獻研究 SOP（source → atomic → MOC → 工程文件草稿） |
| `pxa-scribe` | 依 MOC 產出工程文件（.md → .docx/.pdf） |
| `pxa-obsidian-markdown` | Obsidian Markdown 規範（callouts / embeds / properties） |
| `pxa-standards` | 品翔 SP 標準寫作規範檢查 |

安裝後呼叫方式：`/research-suite:pxa-scout`、`/research-suite:pxa-literature` … 以此類推。

## 更新

```
/plugin marketplace update skills-for-claude-code
```

## Repo 結構

```
.claude-plugin/
  ├─ marketplace.json   ← marketplace 清單（列出 plugin 與其 skills 路徑）
  └─ plugin.json        ← plugin 身分檔
pxa-scout/  pxa-literature/  pxa-scribe/  pxa-obsidian-markdown/  pxa-standards/
                        ← 各 skill（SKILL.md 就地）
```
