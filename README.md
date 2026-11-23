# Response Letter LaTeX Template

默认生成一份 PDF，前面是回复信，后面附论文。回复信和正文页边使用同一套修订编号（`E1`、`E2` 等），点击即可在文件内跳到具体修订或对应回复。示例论文使用 ACM `acmart` 的 `manuscript` 版式。

## 快速开始

准备 Python 3.11 或更新版本，以及包含 `pdflatex`、`bibtex`、`biber` 和 `acmart.cls` 的 TeX Live 或 MacTeX。然后运行以下命令。

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build.py --strict-ids
```

打开 `output/pdf/responseLetter.pdf` 即可查看完整评审文件。书签中的 **Revised Manuscript** 通向附录正文。点击编号后，合并版会在目标上方保留一段上下文，并沿用阅读器当前的缩放比例。正文页边的回跳按钮复用回复信中的矢量徽章，保留徽章字体和大小以及原稿排版。供单独投稿的原始论文 PDF 保存在配置的 `manuscript_pdf` 路径，示例中是 `demo/main.pdf`。

## 标记修订和回复

在论文导言区加载 `revision-marks.sty` 并隐藏行内标记。在正文段落或图表内部、靠近目标的位置用 `\rpoint` 标记。把命令紧接在目标文字前，保持原有的空格和段落：

```latex
% Preamble
\usepackage{revision-marks}
\showrevmarksfalse

% Manuscript body
\rpoint[method-lambda]The regularization coefficient is strictly positive.
```

回复信中用 `\setmainpaper{path/to/main}` 指向正文主文件，路径省略扩展名。用 `\elink{修订ID}` 链接修订，回跳目标默认为当前回复块。也可以用 `\elink[回复ID]{修订ID}` 显式命名回跳目标。显示的徽章始终使用修订 ID。一条回复可以用 `\elinks` 引用多处修订。

```latex
\elinks{E3,E5}
\elink{E1}
\elink{E2}
```

每个修订标签对应一条回复。同一处修改回应多条意见时，在同一位置写入多个不可见标记，例如 `\rpoint[E1]\rpoint[E2]`。然后分别在两条回复里使用 `\elink{E1}` 和 `\elink{E2}`。两者跳到正文同一处，页边的 `E1` 和 `E2` 分别回到各自的回复。多个徽章优先在目标附近从上到下排成一列。竖向空间不足时可在附近分列，保留回复信中的字号和徽章大小。

修订 ID 在单篇论文里唯一。回复 ID 在每个回复块里唯一，同一块内可以用它关联多处修订。ID 以字母或数字开头，可以包含字母、数字、点、下划线和连字符。

## 接入自己的论文

- 在 `project_config.yaml` 里指定 `manuscript_tex`、`manuscript_doc` 和 `manuscript_pdf`，同步更新回复信中的 `\setmainpaper`。`review_output_dir` 指定最终评审 PDF 的目录。
- 如果期刊有单独的构建流程，用原命令编译论文，再运行 `python3 scripts/build.py --letter-only --strict-ids` 复用带修订锚点的论文 PDF。回复信使用 LaTeX 交叉引用时，也保留论文的 `.aux` 文件。
- 保持期刊模板的页面尺寸和边距。构建会检查按钮位置的空白，空间不足时会报告对应的回复 ID、修订 ID 和页码。

## 构建与验收

```bash
python3 scripts/build.py --manuscript-only
python3 scripts/build.py --letter-only --strict-ids
python3 scripts/build.py --combined --strict-ids
python3 -m unittest discover -s tests
```

`--combined` 显式选择默认的合并模式。需要兼容先前的两份 PDF 工作流时可用 `--separate`，并将生成的 PDF 同目录保存。

另有一个两页双栏的 ACM `sigconf` 示例，合并 PDF 输出到 `output/pdf/two-column/responseLetter.pdf`。

```bash
python3 scripts/build.py --config demo/two-column/project_config.yaml --strict-ids
```

提交到 `main` 的 PR 会自动编译这两个示例。测试用 PDFium 在徽章位置查找可点击链接，验证跨页双向跳转的精确位置，以及同一处的 E1、E2 是否分别回到各自的回复。测试逐页比对去掉修订标记的 ACM 原稿，并检查合并版正文的渲染差异是否仅出现在原本空白的徽章区域。
