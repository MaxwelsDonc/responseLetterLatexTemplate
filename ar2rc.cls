\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ar2rc}[2026/11/02 Response Letter class — typography refresh]

\LoadClass[10pt,twoside]{article}

% ==============================
% Page geometry — compact academic letter
% ==============================
\RequirePackage{geometry}
\geometry{
  letterpaper,
  top=0.85in,
  bottom=0.85in,
  left=0.9in,
  right=0.9in,
  headheight=14pt,
  headsep=12pt,
  footskip=22pt,
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

\defbibheading{subbibliography}[\refname]{%
  \par\vspace{0.35em}%
  \noindent{\sffamily\scriptsize\bfseries\color{inkmuted}#1}\par\vspace{0.2em}%
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
% Comfortable but efficient leading for 10pt body
\setstretch{1.18}

\setlength{\parindent}{1em}
\setlength{\parskip}{0.05em}
\setlength{\abovecaptionskip}{0.7em}
\setlength{\belowcaptionskip}{0.5em}
\setlength{\footnotesep}{0.45em}

% ==============================
% Lists
% ==============================
\RequirePackage{enumitem}
\setlist{
  leftmargin=1.2em,
  itemsep=0.22em,
  topsep=0.3em,
  parsep=0.08em,
  partopsep=0pt,
  labelsep=0.45em
}
\setlist[itemize]{label=\textcolor{inkmuted}{\textbullet}}

% ==============================
% Section titles
% ==============================
\RequirePackage{titlesec}

\titleformat{\section}
  {\large\sffamily\bfseries\color{ink}\raggedright}
  {}{0em}{}
  [{\vspace{0.22em}\color{rulegray}\titlerule[0.35pt]}]

\titleformat{\subsection}
  {\normalsize\sffamily\bfseries\color{ink}\raggedright}
  {}{0em}{}

\titleformat{\subsubsection}
  {\normalsize\sffamily\itshape\color{inkmuted}\raggedright}
  {}{0em}{}

\titlespacing*{\section}
  {0pt}{1.55em plus 0.25em minus 0.15em}{0.7em}
\titlespacing*{\subsection}
  {0pt}{1.05em plus 0.15em}{0.45em}
\titlespacing*{\subsubsection}
  {0pt}{0.85em}{0.35em}

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
% Color & hyperlinks
% ==============================
\RequirePackage{xcolor}
\definecolor{ink}{RGB}{28,28,30}
\definecolor{inkmuted}{RGB}{110,110,115}
\definecolor{linkblue}{RGB}{20,78,150}
\definecolor{badgeblue}{RGB}{20,78,150}
\definecolor{rulegray}{RGB}{198,198,202}
\definecolor{commentwash}{RGB}{246,247,249}
\colorlet{ieeelinkblue}{linkblue}

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
