\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ar2rc}[2025/04/26 Custom class for Response Letter]

% 基础类：9 pt article（保留你原来的字号和 twoside）
\LoadClass[9pt,twoside]{article}

% ==============================
% 页面布局 —— 参考 acmart manuscript
% ==============================
\RequirePackage{geometry}
\geometry{
  letterpaper,
  margin=1in,
  head=8pt,
  marginparwidth=6pc,
  heightrounded
}

% ==============================
% Reference formatting (biblatex + biber)
% ==============================
\RequirePackage[
  backend=biber,
  style=numeric,     % 数字引用
  sorting=none,      % 按引用顺序
  giveninits=true,   % 名字缩写
  maxbibnames=8,
  minbibnames=1,
  doi=true,
  url=false,
  isbn=false,
  defernumbers=true
]{biblatex}
\urlstyle{same}

% --- 编号格式：[1], [2], ... ---
% \DeclareFieldFormat{labelnumber}{\mkbibbrackets{#1}}

% --- DOI 格式：正常字体，不用等宽，不乱跳 ---
\DeclareFieldFormat{doi}{%
  \textnormal{DOI}\addcolon\space
  \ifhyperref{\href{https://doi.org/#1}{#1}}{#1}}


% --- 全局参考文献字体（小号，正文字体） ---
\renewcommand*{\bibfont}{\small\normalfont}

% --- 子参考文献 heading（for reviewerblock） ---
\defbibheading{subbibliography}[\refname]{%
  \par\vspace{0.5em}%
  \noindent\textit{#1}\par\vspace{0.3em}%
}

% ==============================
% 字体与微排版 —— 参考 acmart
% ==============================
\RequirePackage[T1]{fontenc}
% acmart 使用的组合：Libertine + newtxmath + zi4
\RequirePackage[tt=false, type1=true]{libertine}
\RequirePackage[varqu]{zi4}
\RequirePackage[libertine]{newtxmath}

\RequirePackage{microtype}
\microtypesetup{protrusion=true,expansion=true}
\frenchspacing % 和 acmart 一致：句号后不额外加空格

% ==============================
% 行距设置 —— 参考 acmart manuscript
% ==============================
\RequirePackage{setspace}
\onehalfspacing  % 等价于 acmart manuscript 中的 onehalfspacing

% ==============================
% 段落样式 —— 有缩进、无额外段间距
% ==============================
% 不再使用 parskip 包（ACM manuscript 是首行缩进 + 无段间距）
\setlength{\parindent}{12pt}
\setlength{\parskip}{0pt}
\setlength{\abovecaptionskip}{1em}
\setlength{\belowcaptionskip}{0.8em}

% ==============================
% 列表样式（保留你原来的，只调整在 ACM 风格基础上）
% ==============================
\RequirePackage{enumitem}
\setlist{
  leftmargin=*,
  labelsep=0.4em
}
\setlist[itemize]{
  itemsep=0.25em,
  topsep=0.2em,
  parsep=0.25em
}
\setlist[enumerate]{
  itemsep=0.25em,
  topsep=0.2em,
  parsep=0.5em
}

% ==============================
% Section 标题样式 —— 仿 ACM（无衬线粗体，稍宽松间距）
% ==============================
\RequirePackage{titlesec}

% section
\titleformat{\section}
  {\large\sffamily\bfseries\raggedright} % 直接写样式
  {\thesection}{0.75em}{}

% subsection
\titleformat{\subsection}
  {\normalsize\sffamily\bfseries\raggedright}
  {\thesubsection}{0.75em}{}

% subsubsection
\titleformat{\subsubsection}
  {\normalsize\sffamily\itshape}
  {\thesubsubsection}{0.75em}{}

% 间距
\titlespacing*{\section}
  {0pt}
  {2.5ex plus 1ex minus .2ex}
  {1.5ex plus .2ex}

\titlespacing*{\subsection}
  {0pt}
  {2.2ex plus 1ex minus .2ex}
  {1.2ex plus .2ex}

\titlespacing*{\subsubsection}
  {0pt}
  {2.0ex plus 0.8ex minus .2ex}
  {1.0ex plus .2ex}


% ==============================
% 页眉与页脚设计（保留你的逻辑）
% ==============================
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}

% 偶数页（左页）显示 Manuscript ID
\fancyhead[LE]{\itshape Manuscript ID: \printmanusid}

% 奇数页（右页）显示论文标题
\fancyhead[RO]{\itshape \printpapertitle}

% 其余位置留空
\fancyhead[LO]{}
\fancyhead[RE]{}

% 页脚：页码居中
\fancyfoot[C]{\thepage}

% 去掉页眉页脚横线
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% ==============================
% 颜色与超链接设置
% ==============================
\RequirePackage{xcolor}
\definecolor{ieeelinkblue}{RGB}{0,70,160}

\RequirePackage[
  bookmarks=true,
  bookmarksnumbered=false, % 因为我们禁用了章节编号
  bookmarksopen=true,
  colorlinks=true,
  linkcolor=ieeelinkblue,
  urlcolor=ieeelinkblue,
  citecolor=ieeelinkblue
]{hyperref}

% 不显示章节编号，但允许 section 进书签
\setcounter{secnumdepth}{-1}
% 允许 subsection (comments) 进书签
\setcounter{tocdepth}{2}

% ==============================
% 结束
% ==============================
\endinput
