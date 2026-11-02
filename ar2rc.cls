\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ar2rc}[2026/11/02 Response Letter class — typography refresh]

\LoadClass[10pt,twoside]{article}

\RequirePackage{xcolor}
\definecolor{ink}{RGB}{28,28,30}
\definecolor{inkmuted}{RGB}{110,110,115}
\definecolor{linkblue}{RGB}{20,78,150}
\definecolor{badgeblue}{RGB}{20,78,150}
\definecolor{rulegray}{RGB}{198,198,202}
\definecolor{commentwash}{RGB}{246,247,249}
\colorlet{ieeelinkblue}{linkblue}

% ==============================
% Page geometry — compact academic letter
% ==============================
\RequirePackage{geometry}
\geometry{
  letterpaper,
  top=0.72in,
  bottom=0.7in,
  left=0.75in,
  right=0.75in,
  headheight=13pt,
  headsep=14pt,
  footskip=18pt,
  heightrounded
}

% ==============================
% Bibliography (biblatex + biber)
% ==============================
\RequirePackage[
  backend=biber,
  style=numeric,
  sorting=none,
  giveninits=true,
  maxbibnames=8,
  minbibnames=1,
  doi=true,
  url=false,
  isbn=false,
  defernumbers=true
]{biblatex}
\urlstyle{same}

\DeclareFieldFormat{doi}{%
  \textnormal{DOI}\addcolon\space
  \ifhyperref{\href{https://doi.org/#1}{#1}}{#1}}

\renewcommand*{\bibfont}{\footnotesize\normalfont}
% Compact mini-bibliographies at the end of each reply block
\setlength{\bibhang}{1.1em}
\setlength{\biblabelsep}{0.5em}
\setlength{\bibitemsep}{0.2em}
\setlength{\bibnamesep}{0pt}
\setlength{\bibparsep}{0pt}

\defbibheading{subbibliography}[\refname]{%
  \par\vspace{0.35em}%
  \noindent{\sffamily\scriptsize\bfseries\color{inkmuted}#1}%
  \par\nobreak
  \nointerlineskip
  \vskip 3pt\relax
}

% ==============================
% Fonts & microtypography
% ==============================
\RequirePackage[T1]{fontenc}
\RequirePackage[tt=false, type1=true]{libertine}
\RequirePackage[varqu]{zi4}
\RequirePackage[libertine]{newtxmath}

\RequirePackage{microtype}
\microtypesetup{
  protrusion=true,
  expansion=true,
  tracking=true,
  kerning=true
}
\frenchspacing

% ==============================
% Leading & paragraph rhythm
% ==============================
\RequirePackage{setspace}
% Body leading: 1.20 × baselineskip (~12pt on 10pt)
\setstretch{1.20}

% Letter style: block paragraphs (no first-line indent).
% This removes the "mystery indent" on multi-paragraph responses.
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.45em}
\setlength{\abovecaptionskip}{0.45em}
\setlength{\belowcaptionskip}{0.45em}
\setlength{\footnotesep}{0.45em}

% ==============================
% Lists / tables / figures
% ==============================
\RequirePackage{enumitem}
\setlist{
  leftmargin=1.25em,
  itemsep=0.22em,
  topsep=0.35em,
  parsep=0.08em,
  partopsep=0pt,
  labelsep=0.45em,
  before={\vspace{0.1em}},
  after={\vspace{0.15em}}
}
\setlist[itemize]{
  label=\textcolor{linkblue}{\textbullet}
}
\setlist[enumerate]{
  label=\textcolor{linkblue}{\arabic*.},
  ref=\arabic*
}
\setlist[enumerate,2]{
  label=\textcolor{inkmuted}{\alph*.},
  ref=\theenumi.\alph*
}

\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{graphicx}
\RequirePackage{float}
\RequirePackage[font=small,labelfont={bf,sf},labelsep=period,skip=0.55em]{caption}
\captionsetup[table]{position=top}
\captionsetup[figure]{position=bottom}
\floatplacement{table}{H}
\floatplacement{figure}{H}

% ==============================
% Section titles
% ==============================
\RequirePackage{titlesec}

% No hairline under section — rules live between comment blocks instead.
\titleformat{\section}
  {\large\sffamily\bfseries\color{ink}\raggedright}
  {}{0em}{}

\titleformat{\subsection}
  {\normalsize\sffamily\bfseries\color{ink}\raggedright}
  {}{0em}{}

\titleformat{\subsubsection}
  {\normalsize\sffamily\itshape\color{inkmuted}\raggedright}
  {}{0em}{}

\titlespacing*{\section}
  {0pt}{1.35em plus 0.2em minus 0.1em}{0.7em}
\titlespacing*{\subsection}
  {0pt}{0.85em plus 0.1em}{0.35em}
\titlespacing*{\subsubsection}
  {0pt}{0.7em}{0.28em}

% ==============================
% Header / footer
% ==============================
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\footnotesize\sffamily\color{inkmuted} Manuscript ID: \printmanusid}
\fancyhead[RO]{\footnotesize\sffamily\color{inkmuted}\nouppercase{\printpapertitle}}
\fancyfoot[C]{\footnotesize\sffamily\color{inkmuted}\thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\footnotesize\sffamily\color{inkmuted}\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}

% ==============================
% Hyperlinks
% ==============================
\RequirePackage[
  bookmarks=true,
  bookmarksnumbered=false,
  bookmarksopen=true,
  colorlinks=true,
  linkcolor=linkblue,
  urlcolor=linkblue,
  citecolor=linkblue
]{hyperref}

\AtBeginDocument{\color{ink}}

\setcounter{secnumdepth}{-1}
\setcounter{tocdepth}{2}

\endinput
