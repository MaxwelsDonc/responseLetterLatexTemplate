\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ar2rc}[2026/11/02 Response Letter class — typography refresh]

\LoadClass[10pt,twoside]{article}

% ==============================
% Page geometry — roomier letter margins
% ==============================
\RequirePackage{geometry}
\geometry{
  letterpaper,
  top=1.05in,
  bottom=1.05in,
  left=1.1in,
  right=1.1in,
  headheight=15pt,
  headsep=18pt,
  footskip=28pt,
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
  \par\vspace{0.65em}%
  \noindent{\sffamily\scriptsize\bfseries\color{inkmuted}#1}\par\vspace{0.35em}%
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
% Slightly open leading; denser than classic 1.5, airier than single
\setstretch{1.28}

\setlength{\parindent}{1.15em}
\setlength{\parskip}{0.15em}
\setlength{\abovecaptionskip}{0.9em}
\setlength{\belowcaptionskip}{0.7em}
\setlength{\footnotesep}{0.6em}

% ==============================
% Lists
% ==============================
\RequirePackage{enumitem}
\setlist{
  leftmargin=1.35em,
  itemsep=0.38em,
  topsep=0.55em,
  parsep=0.15em,
  partopsep=0pt,
  labelsep=0.55em
}
\setlist[itemize]{label=\textcolor{inkmuted}{\textbullet}}

% ==============================
% Section titles
% ==============================
\RequirePackage{titlesec}

\titleformat{\section}
  {\Large\sffamily\bfseries\color{ink}\raggedright}
  {}{0em}{}
  [{\vspace{0.35em}\color{rulegray}\titlerule[0.4pt]}]

\titleformat{\subsection}
  {\normalsize\sffamily\bfseries\color{ink}\raggedright}
  {}{0em}{}

\titleformat{\subsubsection}
  {\normalsize\sffamily\itshape\color{inkmuted}\raggedright}
  {}{0em}{}

\titlespacing*{\section}
  {0pt}{2.8em plus 0.4em minus 0.2em}{1.15em}
\titlespacing*{\subsection}
  {0pt}{1.6em plus 0.2em}{0.7em}
\titlespacing*{\subsubsection}
  {0pt}{1.2em}{0.5em}

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
