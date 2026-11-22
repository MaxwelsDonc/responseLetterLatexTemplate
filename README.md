# Response Letter LaTeX Template

默认生成一份 PDF，前面是回复信，后面附论文。回复信和正文页边使用同一套修订编号（`E1`、`E2` 等），点击即可在文件内跳到具体修订或对应回复。示例论文使用 ACM `acmart` 的 `manuscript` 版式。

## 快速开始

准备 Python 3.11 或更新版本，以及包含 `pdflatex`、`bibtex`、`biber` 和 `acmart.cls` 的 TeX Live 或 MacTeX。然后运行以下命令。

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build.py --strict-ids
```

打开 `output/pdf/responseLetter.pdf` 即可查看完整评审文件。书签中的 **Revised Manuscript** 通向附录正文。脚本把回跳按钮加在正文现有的页边空白处，保留原稿内容和分页。供单独投稿的原始论文 PDF 保存在配置的 `manuscript_pdf` 路径，示例中是 `demo/main.pdf`。

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
\elink{E2}
\elinks{E1,E4}
\elink[R2-C1]{E2}
```

正文修订 ID 在单篇论文里唯一。回复 ID 在每个回复块里唯一，同一块内可以用它关联多处修订。ID 以字母或数字开头，可以包含字母、数字、点、下划线和连字符。共享修订的回跳按钮保留相同的修订 ID，并附上回复页码。示例中的 `E2 p.4` 和 `E2 p.5` 分别回到第 4 和第 5 页的对应回复。

## 接入自己的论文

- 在 `project_config.yaml` 里指定 `manuscript_tex`、`manuscript_doc` 和 `manuscript_pdf`，同步更新回复信中的 `\setmainpaper`。`review_output_dir` 指定最终评审 PDF 的目录。
- 如果期刊有单独的构建流程，用原命令编译论文，并保留带修订锚点的 PDF 和 `.aux`。随后运行 `python3 scripts/build.py --letter-only --strict-ids`，复用该论文 PDF。`.aux` 提供回复信中显示的章节和页码。
- 保持期刊模板的页面尺寸和边距。构建会检查按钮位置的空白，空间不足时会报告对应的回复 ID、修订 ID 和页码。

## 构建与验收

```bash
python3 scripts/build.py --manuscript-only
python3 scripts/build.py --letter-only --strict-ids
python3 scripts/build.py --combined --strict-ids
python3 -m unittest discover -s tests
```

`--combined` 显式选择默认的合并模式。需要兼容先前的两份 PDF 工作流时可用 `--separate`，并将生成的 PDF 同目录保存。示例回归测试检查同一文件内的精确目标、共享修订的两个回跳入口和正文的像素级排版。
