# Response Letter LaTeX Template

双向可点击的论文回复信工作流：

- 回复信里的蓝徽章 `\rlink{id}` → 跳到附录正文的对应修订处
- 正文里的蓝徽章 → 跳回回复信对应回复
- 一键构建 + 修订 ID 校验 + PDF 链接归一化

---

## 快速开始

```bash
pip install -r requirements.txt
python3 scripts/build.py
```

打开 `responseLetter.pdf`，点击蓝徽章验证双向跳转。

仓库自带可编译的 `demo/` 正文，无需再挂自己的论文工程即可跑通全流程。

---

## 新 API（推荐）

### 正文（`revision-marks.sty`）

```latex
\usepackage{revision-marks}
\setresponseletter{responseLetter} % 回复信 PDF 文件名（无扩展名）

% 推荐：一个命令完成 id + 徽章 + 蓝色修订文本
\revise[r1c1a]{This sentence was revised.}

% 只标位置（图/表旁），不改写正文句子
\rpoint{r1c2}
```

兼容旧写法：

```latex
\rlabel{r1c1a}\revise{This sentence was revised.}
```

开关：

- `\showrevmarkstrue` / `\showrevmarksfalse`：同时控制徽章与蓝色高亮（`\label` 始终写入）

### 回复信（`commands.sty`）

```latex
\setmainpaper{demo/main}   % 正文路径，无 .tex/.pdf

See \rlink{r1c1a}.
See \rlinks{r1c1a,r1c1b}.  % 多个徽章

\revisionblock{quoted revised sentence...}
\appendmainpaper            % 将正文 PDF 拼到回复信末尾
```

ID 约定建议：`r<审稿人>c<评论><位点>`，例如 `r1c1a`、`r1c1b`。

---

## 核心文件

| 文件 | 作用 |
|------|------|
| `responseLetter.tex` | 回复信主文档（示例） |
| `commands.sty` | 回复信命令：`\rlink` / `\rlinks` / `\appendmainpaper` |
| `revision-marks.sty` | 正文命令：`\revise` / `\rpoint` / `\rlabel` |
| `demo/main.tex` | 可编译的最小正文示例 |
| `project_config.yaml` | 构建路径与链接配置 |
| `scripts/build.py` | 一键构建入口 |
| `scripts/check_ids.py` | 校验回复信与正文 ID 是否对齐 |
| `scripts/normalize_links.py` | 修复拼接 PDF 后的外链跳转 |

---

## 构建选项

```bash
python3 scripts/build.py                 # 全文构建
python3 scripts/build.py --manuscript-only
python3 scripts/build.py --letter-only
python3 scripts/build.py --skip-normalize
python3 scripts/build.py --strict-ids    # 正文有标记但回复信未引用也失败
```

流程：

1. 编译正文  
2. 编译回复信（并附录正文 PDF）  
3. 校验 `\rlink` ↔ `\revise`/`\rpoint`/`\rlabel` ID  
4. 归一化嵌入 PDF 链接  
5. 输出 `responseLetter.pdf`

---

## 配置（`project_config.yaml`）

```yaml
response_letter_doc: responseLetter
response_letter_tex: responseLetter.tex
response_letter_pdf: responseLetter.pdf
manuscript_doc: main
manuscript_tex: demo/main.tex
manuscript_pdf: demo/main.pdf
anchor_prefix: response.
revision_prefix: rev:
enable_link_normalization: true
```

换到自己的论文时，只需：

1. 把 `revision-marks.sty` 放进正文工程并 `\usepackage{revision-marks}`  
2. 用 `\revise[id]{...}` / `\rpoint{id}` 标记修订  
3. 改 `project_config.yaml` 与 `\setmainpaper{...}` 指向你的正文  

---

## 常见问题

- 徽章显示为灰色 `id?`  
  - 正文没有对应 id，或正文尚未重新编译  
  - 先跑 `python3 scripts/build.py`，看 ID check 输出  

- 点击正文徽章打开了外部 PDF  
  - 确认 `enable_link_normalization: true`  
  - 用完整 `build.py` 跑一遍，不要只编译 `.tex`  

- macOS 预览.app 跳转不稳定  
  - 推荐 Acrobat / Skim / PDF-XChange  

---

## 设计要点

1. **单一真相来源**：正文侧推荐只写 `\revise[id]{text}`，避免 `\rlabel` + `\revise` 拆开后顺序出错。  
2. **缺失可见**：回复信找不到正文标签时显示灰色 `id?`，不再静默变成 `None`。  
3. **构建期校验**：`check_ids.py` 在出 PDF 前暴露不对齐的 id。  
4. **模板可运行**：默认挂 `demo/`，克隆即可构建。  
