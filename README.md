# Response Letter Template

这是一个用于论文回复信（Response Letter）的 LaTeX 工作流模板，支持：
- 回复信中点击 `\rlink{id}` 跳到正文对应修订位置
- 正文修订徽章点击回到回复信对应位置
- 配置化切换正文工程（例如从测试文档迁移到 `PSALM3/main.tex`）

---

## 核心文件
- `responseLetter.tex`：回复信主文档
- `commands.sty`：回复信侧命令（`\\rlink`、拼接正文等）
- `PSALM3/revision-marks.sty`：正文侧修订命令（`\\rlabel`、`\\revise`）
- `project_config.yaml`：构建与链接归一化配置
- `scripts/build.py`：一键构建入口
- `scripts/normalize_links.py`：PDF 链接归一化（修复“跳到外部 PDF”）

---

## 命令说明

### 回复信侧（`commands.sty`）
- `\setmainpaper{<path/to/manuscript-no-ext>}`
  - 指定正文主文档（不带 `.tex/.pdf`）
  - 例：`\setmainpaper{PSALM3/main}`
- `\rlink{id}`
  - 在当前位置创建回复锚点 `response.id`
  - 显示蓝底白字徽章（如 `r1c1a`）
  - 若正文存在 `\label{rev:id}`，点击徽章跳到正文对应页
  - 若正文不存在该标签，显示 `None`
- `\appendmainpaper`
  - 把正文 PDF 追加到回复信末尾

### 正文侧（`PSALM3/revision-marks.sty`）
- `\rlabel{id}`
  - 记录当前 ID
  - 写入 `\label{rev:id}`
  - 默认显示同款蓝底白字徽章（并可点击回到回复信锚点 `response.id`）
- `\revise{...}`
  - 只负责渲染蓝色修订文本
  - 不负责 ID 对齐

### 正文开关
- `\showrlabelmarkstrue / \showrlabelmarksfalse`
  - 控制 `\rlabel{id}` 的徽章显示开关
  - 不影响 `\label{rev:id}` 写入
- `\showrevmarkstrue / \showrevmarksfalse`
  - 控制 `\revise{...}` 是否渲染蓝色

---

## 推荐写法（一个评论对应多处修改）

回复信里：

```latex
The revised manuscript can be found in \rlink{r1c1a} and \rlink{r1c1b}.
```

正文里：

```latex
\rlabel{r1c1a}\revise{这是第一处修订文本。}
\rlabel{r1c1b}\revise{这是第二处修订文本。}
```

这样会实现严格一一对应：
- `r1c1a -> r1c1a`
- `r1c1b -> r1c1b`

---

## 编译方式

推荐一键构建：

```bash
python3 scripts/build.py
```

脚本流程：
1. 编译正文（`manuscript_tex`）
2. 编译回复信（`response_letter_tex`）
3. 对最终 PDF 做链接归一化（修复嵌入 PDF 的外链行为）
4. 输出 `responseLetter.pdf`

你会看到阶段日志：
- `[1/4] Building manuscript...`
- `[2/4] Building response letter...`
- `[3/4] Normalizing embedded PDF links...`
- `[4/4] Done...`

---

## 配置文件（`project_config.yaml`）

当前示例：

```yaml
response_letter_doc: responseLetter
response_letter_tex: responseLetter.tex
response_letter_pdf: responseLetter.pdf
manuscript_doc: main
manuscript_tex: PSALM3/main.tex
manuscript_pdf: PSALM3/main.pdf
anchor_prefix: response.
revision_prefix: rev:
enable_link_normalization: true
```

字段说明：
- `response_letter_*`：回复信工程
- `manuscript_*`：正文工程
- `anchor_prefix`：回复锚点前缀（建议 `response.`）
- `revision_prefix`：正文标签前缀（建议 `rev:`）
- `enable_link_normalization`：是否启用链接归一化（建议保持 `true`）

---

## 迁移到新期刊（如 TSE）

只需做三件事：
1. 在新正文工程里放入并加载 `revision-marks.sty`
2. 正文修订统一写成 `\rlabel{id}\revise{...}`
3. 在 `project_config.yaml` 里改正文路径（`manuscript_tex/pdf/doc`）

回复信侧命令和流程可以保持不变。

---

## 常见问题

- `\rlink{id}` 显示 `None`
  - 正文没有对应 `\rlabel{id}`，或正文尚未重新编译

- 点击正文徽章却打开外部 PDF
  - 确认 `enable_link_normalization: true`
  - 用 `python3 scripts/build.py` 完整跑一遍

- 看到 `Output written on main.pdf` 以为卡住
  - 这是正文阶段完成，不是整体结束
  - 等到出现 `[4/4] Done` 才是全流程完成

- macOS 预览跳转不稳定
  - 推荐 Acrobat / Skim / PDF-XChange
