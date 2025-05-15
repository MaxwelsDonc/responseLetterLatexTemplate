
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ar2rc}[2025/04/26 Custom class for Response Letter]

\LoadClass[11pt]{article}

% Page layout
\RequirePackage{geometry}
\geometry{margin=1in}

% Line spacing
\RequirePackage{setspace}
\setstretch{1.2}

% No paragraph indentation
\RequirePackage{parskip}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}

% Add spacing between list items
\usepackage{enumitem}
% \setlist[itemize]{itemsep=0.5em, topsep=0.5em,parsep=0.5em}
% \setlist[enumerate]{itemsep=0.5em, topsep=0.5em,parsep=0.5em}
\setlist[itemize]{parsep=0.5em}
\setlist[enumerate]{parsep=0.5em}

% Section title style
\RequirePackage{titlesec}
\titleformat*{\section}{\large\bfseries}

% Optional font
\usepackage{times}

\endinput
