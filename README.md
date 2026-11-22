# Response Letter LaTeX Template

论文回复信与正文各输出一份独立 PDF。回复信徽章跳到正文中的具体修订，正文页边的按钮回到对应回复。示例论文使用 ACM `acmart` 的 `manuscript` 版式。

## 快速开始

安装 TeX Live 或 MacTeX，并确认 `pdflatex`、`bibtex`、`biber` 和 `acmart.cls` 可用。然后运行：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build.py --strict-ids
```

构建输出在 `output/pdf/`：

| 文件 | 内容 |
| --- | --- |
| `responseLetter.pdf` | 回复信。修订徽章附有正文页码和章节，点击徽章可跳到具体位置。 |
| `manuscript.pdf` | 带回跳入口的论文。脚本把按钮加在现有页边空白处，保留原稿内容和分页。 |

把两份 PDF 放在同一目录并保留文件名，用支持跨文件跳转的 PDF 阅读器打开。独立预览时也可以按回复信中显示的页码和章节查找。原始论文 PDF 保存在配置的 `manuscript_pdf` 路径，示例中是 `demo/main.pdf`。

## 标记修订和回复

在论文导言区加载 `revision-marks.sty` 并隐藏行内标记。在正文段落或图表内部、靠近目标的位置用 `\rpoint` 标记。把命令紧接在目标文字前，保持原有的空格和段落：

```latex
% Preamble
\usepackage{revision-marks}
\showrevmarksfalse

% Manuscript body
\rpoint[method-lambda]The regularization coefficient is strictly positive.
```

回复信中用 `\setmainpaper{path/to/main}` 指向正文主文件，路径省略扩展名。用 `\elink[回复ID]{修订ID}` 声明对应关系。一条回复可以用 `\elinks` 引用多处修订：

```latex
\elink[R2-C1]{method-lambda}
\elink[R3-C2]{method-lambda}
\elinks[R1-C1]{introduction,experiments}
```

正文修订 ID 在单篇论文里唯一。回复 ID 在每个回复块里唯一，同一块内可以用它关联多处修订。ID 以字母或数字开头，可以包含字母、数字、点、下划线和连字符。共享修订会在正文同一处附近生成多个回跳按钮。示例里的 `E2` 分别回到 `R2-C1` 和 `R3-C2`。

## 接入自己的论文

- 在 `project_config.yaml` 里指定 `manuscript_tex`、`manuscript_doc` 和 `manuscript_pdf`，同步更新回复信中的 `\setmainpaper`。`review_output_dir` 指定两份最终 PDF 的目录。
- 如果期刊有单独的构建流程，用原命令编译论文，并保留带修订锚点的 PDF 和 `.aux`。随后运行 `python3 scripts/build.py --letter-only --strict-ids`，复用该论文 PDF。`.aux` 提供回复信中显示的章节和页码。
- 保持期刊模板的页面尺寸和边距。构建会检查按钮位置的空白，空间不足时会报告对应的回复 ID、修订 ID 和页码。

## 构建与验收

```bash
python3 scripts/build.py --manuscript-only
python3 scripts/build.py --letter-only --strict-ids
python3 scripts/build.py --combined --strict-ids
python3 -m unittest discover -s tests
```

`--combined` 保留旧的附录构建，输出仓库根目录的 `responseLetter.pdf`。独立模式默认使用显式回复 ID。示例回归测试检查两个 PDF 的跨文件目标、共享修订的两条回跳和正文的像素级排版。
