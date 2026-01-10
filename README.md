# Response Letter LaTeX Template

这是一个用于撰写学术论文 Response Letter 的 LaTeX 模板。它旨在帮助作者清晰、专业地回复编辑和审稿人的意见。该模板具有自动编号、书签导航、独立参考文献列表等功能。

## 核心命令与环境

### 1. 论文元数据配置
在 `main.tex` 导言区设置，用于自动生成信头和正文中的引用。

- `\papertitle{...}`: 论文标题
- `\manusid{...}`: 稿件编号 (Manuscript ID)
- `\authors{...}`: 作者列表
- `\affiliations{...}`: 作者单位
- `\contactemails{...}`: 联系邮箱
- `\journalname{...}`: 期刊名称
- `\editorname{...}`: 编辑姓名
- `\resubmissiondate{...}`: 重投日期
- `\decisiondate{...}`: 决定信日期

**输出命令**（在正文中使用）：
`\printpapertitle`, `\printmanusid`, `\printjournalname` 等。

### 2. 结构化回复环境

#### 编辑/总体意见
用于回复 Editor 的信或 Reviewers 的 General Comments。
- **环境**: `generalblock` (最外层，处理参考文献)
- **子环境**: 
  - `generalcomment`: 包裹评论内容，自动生成“General Comment”标题并加入书签。
  - `generalresponse`: 包裹回复内容。

#### 审稿人具体意见
用于回复具体的编号意见（如 Comment 1.1, 1.2）。
- **环境**: `reviewerblock` (最外层，处理参考文献)
- **子环境**:
  - `reviewercomment`: 自动编号（如 Comment 1.1），斜体显示，加入书签。
  - `reviewerresponse`: 正体显示回复内容。
- **计数重置**: `\resetcommentcounter` (在开始新的 Reviewer 章节时使用，重置编号)。

### 3. 辅助功能命令

- `\revisionblock{...}`: 用于在回复中引用修改后的论文原文。显示为蓝色引用块。
- `\cite{...}`: 支持在每个 `generalblock` 或 `reviewerblock` 内独立引用文献，互不干扰。
- `\responseletterheader`: 生成标准的 Response Letter 标题区。
- `\responselettersignature`: 生成落款签名区。
- `\zzh{...}`, `\pl{...}` 等: 预定义的彩色标注命令，用于作者间协作注释。

## 用法示例

### 基础结构
```latex
\documentclass{ar2rc}
% ... 宏包加载 ...
\begin{document}

% 1. 信头
\responseletterheader
Dear \printeditorname, ...

% 2. 编辑意见
\section{Responses to the Comments from Editor}
\begin{generalblock}
  \begin{generalcomment}
    Please fix the typos.
  \end{generalcomment}
  \begin{generalresponse}
    Fixed.
  \end{generalresponse}
\end{generalblock}

% 3. 审稿人 1 意见
\section{Responses to the Comments from Reviewer 1}
\resetcommentcounter % 务必重置计数器

\begin{reviewerblock}
  \begin{reviewercomment}
    Equation (5) is unclear.
  \end{reviewercomment}
  \begin{reviewerresponse}
    We have revised it as follows:
    \revisionblock{
       E = mc^2 ...
    }
  \end{reviewerresponse}
\end{reviewerblock}

\end{document}
```

### 编译方式
由于使用了 `biber` 进行独立的参考文献管理，请按以下顺序编译：

1. `pdflatex main`
2. `biber main`
3. `pdflatex main`
4. `pdflatex main`

或者使用 `latexmk`：
```bash
latexmk -pdf main.tex
```
