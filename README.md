# Response Letter LaTeX Template

简洁美观的论文回复信模板。核心能力：

- 正文自动标记改动 `E1 / E2 / E3…`（蓝底白字徽章）
- 回复信用 `\elink` 声明「意见 ↔ 改动」的多对多关系
- 将**独立编译的正文 PDF 原样**附在信后，并保持双向可点跳转

不区分 IEEE/ACM 版式——回复信通常无强制格式；精力放在可读性与跳转可靠性上。

---

## 快速开始

```bash
pip install -r requirements.txt
python3 scripts/build.py
```

打开 `responseLetter.pdf`，点击蓝徽章验证双向跳转。

---

## 工作方式（正文如何接在后面）

1. **先单独编译论文** → `demo/main.pdf`（或你自己的论文 PDF）  
2. **再编译回复信**；信末 `\appendmainpaper` 用 `pdfpages` 把论文 PDF **原样拼在后面**（不盖回复信页眉）  
3. **链接归一化**：`normalize_links.py` 把拼接后的外链改成同一 PDF 内跳转  

仅把两个 PDF 用系统工具硬合并，跳转通常会坏；请走 `scripts/build.py`。

```text
回复信  --\elink{E2}-->  附录中的论文页（mainpaper.N）
   ^                         |
   └──── 正文徽章回跳 ────────┘
```

---

## API

### 正文（`revision-marks.sty`）

```latex
\usepackage{revision-marks}
\setresponseletter{responseLetter}

\revise{Architecture-agnostic pipeline...}   % 自动 -> E1
\revise{Define $\lambda$ clearly...}         % 自动 -> E2
\rpoint                                      % 自动 -> E3（只标位置）

\revise[lambda]{...}                         % 可选：稳定起名
```

- `\showrevmarkstrue` / `\showrevmarksfalse`：开关徽章与蓝字  

### 回复信（`commands.sty`）

```latex
\setmainpaper{demo/main}    % 无 .tex/.pdf

See \elink{E2}.
See \elinks{E1,E4}.         % 一个意见对应多处改动

% 多处意见可共享同一改动：两边都 \elink{E2}
\appendmainpaper            % 原样附录正文 PDF
```

`\rlink` / `\rlinks` 仍可用（等同 `\elink` / `\elinks`）。

同一个 edit 被多次 `\elink` 时，**回跳锚点只创建一次**（第一次出现处）。

---

## 接上你自己的论文

1. 把 `revision-marks.sty` 放进论文工程并 `\usepackage{revision-marks}`  
2. 用 `\revise{...}` / `\rpoint` 标记改动  
3. 改 `project_config.yaml` 的 `manuscript_*` 路径  
4. 回复信里 `\setmainpaper{你的路径/main}`  

论文与回复信始终是两套工程；模板只引用编译好的 PDF 并建立跳转。

---

## 构建

```bash
python3 scripts/build.py
python3 scripts/build.py --letter-only
python3 scripts/build.py --manuscript-only
python3 scripts/build.py --strict-ids
```

`check_ids.py` 用正文 `.aux` 里的 `rev:E*` 与回复信 `\elink` 对齐（支持自动编号）。

---

## 配置

```yaml
manuscript_tex: demo/main.tex
manuscript_pdf: demo/main.pdf
manuscript_doc: main
response_letter_tex: responseLetter.tex
response_letter_pdf: responseLetter.pdf
enable_link_normalization: true
```

---

## Demo 里的多对多

| 关系 | 例子 |
|------|------|
| 一对多 | Reviewer 1 Comment 1 → `E1` + `E4` |
| 多对一 | Reviewer 2 Comment 1 与 Reviewer 3 Comment 2 → 共用 `E2` |
