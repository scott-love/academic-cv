%% start of file `moderncv.cls'.
%% Copyright 2006-2012 Xavier Danaux (xdanaux@gmail.com).
%
% This work may be distributed and/or modified under the
% conditions of the LaTeX Project Public License version 1.3c,
% available at http://www.latex-project.org/lppl/.


%-------------------------------------------------------------------------------
%                identification
%-------------------------------------------------------------------------------
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{moderncv}[2012/10/31 v1.2.0 modern curriculum vitae and letter document class]


%-------------------------------------------------------------------------------
%                class options
%
% (need to be done before the external package loading, for example because
% we need \paperwidth, \paperheight and \@ptsize to be defined before loading
% geometry and fancyhdr)
%-------------------------------------------------------------------------------
% paper size option
\DeclareOption{a4paper}{
  \setlength\paperheight{297mm}
  \setlength\paperwidth{210mm}}
\DeclareOption{a5paper}{
  \setlength\paperheight{210mm}
  \setlength\paperwidth{148mm}}
\DeclareOption{b5paper}{
  \setlength\paperheight{250mm}
  \setlength\paperwidth{176mm}}
\DeclareOption{letterpaper}{
  \setlength\paperheight{11in}
  \setlength\paperwidth{8.5in}}
\DeclareOption{legalpaper}{
  \setlength\paperheight{14in}
  \setlength\paperwidth{8.5in}}
\DeclareOption{executivepaper}{
  \setlength\paperheight{10.5in}
  \setlength\paperwidth{7.25in}}
\DeclareOption{landscape}{
  \setlength\@tempdima{\paperheight}
  \setlength\paperheight{\paperwidth}
  \setlength\paperwidth{\@tempdima}}

% font size options
\newcommand\@ptsize{}
\DeclareOption{10pt}{\renewcommand\@ptsize{0}}
\DeclareOption{11pt}{\renewcommand\@ptsize{1}}
\DeclareOption{12pt}{\renewcommand\@ptsize{2}}

% font type options
\DeclareOption{sans}{\AtBeginDocument{\renewcommand{\familydefault}{\sfdefault}}}
\DeclareOption{roman}{\AtBeginDocument{\renewcommand{\familydefault}{\rmdefault}}}

% draft/final option
\DeclareOption{draft}{\setlength\overfullrule{5pt}}
\DeclareOption{final}{\setlength\overfullrule{0pt}}

% execute default options
\ExecuteOptions{a4paper,11pt,final}

% process given options
\ProcessOptions\relax
\input{size1\@ptsize.clo}


%-------------------------------------------------------------------------------
%                required packages
%-------------------------------------------------------------------------------
\RequirePackage{etoolbox}
\RequirePackage{ifthen}
\RequirePackage{xcolor}
\RequirePackage[T1]{fontenc}
\IfFileExists{lmodern.sty}%
  {\RequirePackage{lmodern}}%
  {}

\renewcommand*{\marvosymbol}[1]{{\fontfamily{mvs}\fontencoding{U}\fontseries{m}\fontshape{n}\selectfont\char#1}}

\RequirePackage{url}
\urlstyle{tt}
\AtEndPreamble{
  \pagenumbering{arabic}
  \RequirePackage[unicode]{hyperref}
  \hypersetup{
    breaklinks,
    baseurl       = http://,
    pdfborder     = 0 0 0,
    pdfpagemode   = UseNone,
    pdfstartpage  = 1,
    pdfcreator    = {\LaTeX{} with 'moderncv' package},
    bookmarksopen = true,
    bookmarksdepth= 2,
    pdfauthor     = {\@firstname{}~\@familyname{}},
    pdftitle      = {\@firstname{}~\@familyname{} -- \@title{}},
    pdfsubject    = {Resum\'e of \@firstname{}~\@familyname{}},
    pdfkeywords   = {\@firstname{}~\@familyname{}, curriculum vit\ae{}, resum\'e}}}

\RequirePackage{graphicx}
\RequirePackage{fancyhdr}
\fancypagestyle{plain}{
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
  \fancyhf{}}

\newif\if@displaypagenumbers\@displaypagenumberstrue
\newcommand*{\nopagenumbers}{\@displaypagenumbersfalse}
\AtEndPreamble{%
  \AtBeginDocument{%
    \if@displaypagenumbers%
      \@ifundefined{r@lastpage}{}{%
        \ifthenelse{\pageref{lastpage}>1}{%
          \newlength{\pagenumberwidth}%
          \settowidth{\pagenumberwidth}{\color{color2}\addressfont\itshape\strut\thepage/\pageref{lastpage}}%
          \fancypagestyle{plain}{%
            \fancyfoot[r]{\parbox[b]{\pagenumberwidth}{\color{color2}\addressfont\itshape\strut\thepage/\pageref{lastpage}}}}
          \pagestyle{plain}}{}}%
      \AtEndDocument{\label{lastpage}}\else\fi}}
\pagestyle{plain}

\RequirePackage{calc}
\RequirePackage{xargs}
\RequirePackage{microtype}
\RequirePackageWithOptions{moderncvcompatibility}


%-------------------------------------------------------------------------------
%                class definition
%-------------------------------------------------------------------------------
\setlength\lineskip{1\p@}
\setlength\normallineskip{1\p@}
\renewcommand\baselinestretch{}
\setlength{\parindent}{0\p@}
\setlength{\parskip}{0\p@}
\setlength\columnsep{10\p@}
\setlength\columnseprule{0\p@}
\setlength\fboxsep{3\p@}
\setlength\fboxrule{.4\p@}
\setlength\arrayrulewidth{.4\p@}
\setlength\doublerulesep{2\p@}

\raggedbottom
\onecolumn


%-------------------------------------------------------------------------------
%                overall design commands definitions
%-------------------------------------------------------------------------------
\newcommand*{\firstname}[1]{\def\@firstname{#1}}
\newcommand*{\familyname}[1]{\def\@familyname{#1}}
\renewcommand*{\title}[1]{\def\@title{#1}}
\newcommand*{\address}[2]{\def\@addressstreet{#1}\def\@addresscity{#2}}
\newcommand*{\mobile}[1]{\def\@mobile{#1}}
\newcommand*{\phone}[1]{\def\@phone{#1}}
\newcommand*{\fax}[1]{\def\@fax{#1}}
\newcommand*{\email}[1]{\def\@email{#1}}
\newcommand*{\homepage}[2]{\def\@homepage{#1}\def\@homepagetitle{#2}}

\definecolor{color0}{rgb}{0,0,0}
\definecolor{color1}{rgb}{0,0,0}
\definecolor{color2}{rgb}{0,0,0}
\definecolor{color3}{rgb}{0,0,0}

\newcommand*{\labelitemi}{\strut\textcolor{color1}{\marvosymbol{123}}}
\newcommand*{\labelitemii}{\strut\textcolor{color1}{\large\bfseries-}}
\newcommand*{\labelitemiii}{\strut\textcolor{color1}{\rmfamily\textperiodcentered}}
\newcommand*{\labelitemiv}{\labelitemiii}

\renewcommand{\theenumi}{\@arabic\c@enumi}
\renewcommand{\theenumii}{\@alph\c@enumii}
\renewcommand{\theenumiii}{\@roman\c@enumiii}
\renewcommand{\theenumiv}{\@Alph\c@enumiv}

\newcommand*{\listitemsymbol}{\labelitemi~}
\newcommand*{\addresssymbol}{}
\newcommand*{\mobilesymbol}{}
\newcommand*{\phonesymbol}{}
\newcommand*{\faxsymbol}{}
\newcommand*{\emailsymbol}{}
\newcommand*{\homepagesymbol}{}

\AtBeginDocument{\normalfont\color{color0}}

\newcommand*{\refname}{Publications}
\newcommand*{\enclname}{Enclosure}

\newcommand*{\makefooter}{}

\newcommand*{\moderncvstyle}[1]{
  \RequirePackage{moderncvstyle#1}}

\newcommand*{\moderncvcolor}[1]{
  \RequirePackage{moderncvcolor#1}}

\newcommand*{\recomputelengths}{\recomputecvlengths}
\AtBeginDocument{\recomputelengths{}}

\newcommand*{\@initializelength}[1]{%
  \ifdefined#1\else\newlength{#1}\fi}


%-------------------------------------------------------------------------------
%                resume design commands definitions
%-------------------------------------------------------------------------------
\newcommand*{\extrainfo}[1]{\def\@extrainfo{#1}}
\newcommandx*{\photo}[3][1=64pt,2=0.4pt,usedefault]{\def\@photowidth{#1}\def\@photoframewidth{#2}\def\@photo{#3}}
\newcommand*{\quote}[1]{\def\@quote{#1}}

\newcommand*{\namefont}{}
\newcommand*{\titlefont}{}
\newcommand*{\addressfont}{}
\newcommand*{\quotefont}{}
\newcommand*{\sectionfont}{}
\newcommand*{\subsectionfont}{}
\newcommand*{\hintfont}{}

\newcommand*{\namestyle}[1]{{\namefont#1}}
\newcommand*{\titlestyle}[1]{{\titlefont#1}}
\newcommand*{\addressstyle}[1]{{\addressfont#1}}
\newcommand*{\quotestyle}[1]{{\quotefont#1}}
\newcommand*{\sectionstyle}[1]{{\sectionfont#1}}
\newcommand*{\subsectionstyle}[1]{{\subsectionfont#1}}
\newcommand*{\hintstyle}[1]{{\hintfont#1}}

\newcommand*{\recomputecvlengths}{}

\newif\if@firstdetailselement\@firstdetailselementtrue
\newcommand*{\makenewline}{
  \if@firstdetailselement%
    \strut
  \else%
    \\\fi%
  \@firstdetailselementfalse}

\newcommand*{\makecvtitle}{}
\newcommand*{\makecvfooter}{\makefooter}
\newcommand*{\section}[1]{}
\RequirePackage{suffix}
\AtBeginDocument{\WithSuffix\newcommand\section*{\section}}

\newcommand*{\cvitem}[3][.25em]{}
\newcommand*{\cvdoubleitem}[5][.25em]{}
\newcommand*{\cvlistitem}[2][.25em]{}
\newcommand*{\cvlistdoubleitem}[3][.25em]{}
\newcommand*{\cventry}[7][.25em]{}
\newcommand*{\cvitemwithcomment}[4][.25em]{}

\newcommand*{\link}[2][]{
  \ifthenelse{\equal{#1}{}}
    {\href{#2}{#2}}
    {\href{#2}{#1}}}

\newcommand*{\httplink}[2][]{
  \ifthenelse{\equal{#1}{}}
    {\href{http://#2}{#2}}
    {\href{http://#2}{#1}}}

\newcommand*{\emaillink}[2][]{
  \ifthenelse{\equal{#1}{}}
    {\href{mailto:#2}{#2}}
    {\href{mailto:#2}{#1}}}

\newlength{\bibindent}
\setlength{\bibindent}{1.5em}
\newcommand*{\bibliographyitemlabel}{}
\newcommand*{\bibliographyhead}[1]{\section{#1}}
\AtEndPreamble{\@ifpackageloaded{multibib}{\renewcommand*{\bibliographyhead}[1]{\subsection{#1}}}{}}
\newenvironment{thebibliography}[1]{}{}
\newcommand*{\newblock}{\hskip .11em\@plus.33em\@minus.07em}
\let\@openbib@code\@empty

\setlength{\leftmargini}   {1em}
\leftmargin\leftmargini
\setlength{\leftmarginii}  {\leftmargini}
\setlength{\leftmarginiii} {\leftmargini}
\setlength{\leftmarginiv}  {\leftmargini}
\setlength{\leftmarginv}   {\leftmargini}
\setlength{\leftmarginvi}  {\leftmargini}
\setlength{\labelsep}      {.5em}
\setlength{\labelwidth}    {\leftmargini}
\addtolength{\labelwidth}  {-\labelsep}
\@beginparpenalty -\@lowpenalty
\@endparpenalty   -\@lowpenalty
\@itempenalty     -\@lowpenalty
\newcommand\labelenumi{\theenumi.}
\newcommand\labelenumii{(\theenumii)}
\newcommand\labelenumiii{\theenumiii.}
\newcommand\labelenumiv{\theenumiv.}
\renewcommand\p@enumii{\theenumi}
\renewcommand\p@enumiii{\p@enumii(\theenumii)}
\renewcommand\p@enumiv{\p@enumiii\theenumiii}
\newcommand*\descriptionlabel[1]{\hspace\labelsep\normalfont\bfseries#1}
\RequirePackage{tweaklist}
\renewcommand*{\itemhook}{
  \setlength{\topsep}{0pt}
  \setlength{\parsep}{0pt}
  \setlength{\parskip}{0pt}
  \setlength{\itemsep}{0pt}}
\renewcommand*{\enumhook}{\itemhook{}}
\renewcommand*{\deschook}{\itemhook{}}

\def\today{\ifcase\month\or
  January\or February\or March\or April\or May\or June\or
  July\or August\or September\or October\or November\or December\fi
  \space\number\day, \number\year}


%-------------------------------------------------------------------------------
%                letter design commands definitions
%-------------------------------------------------------------------------------
\newcommand*{\recipient}[2]{\def\@recipientname{#1}\def\@recipientaddress{#2}}
\renewcommand*{\date}[1]{\def\@date{#1}}\date{\today}
\newcommand*{\opening}[1]{\def\@opening{#1}}
\newcommand*{\closing}[1]{\def\@closing{#1}}
\newcommand*{\enclosure}[2][]{
  \ifthenelse{\equal{#1}{}}{}{\renewcommand*{\enclname}{#1}}
  \def\@enclosure{#2}}

\newcommand*{\recomputeletterlengths}{}
\newcommand*{\makelettertitle}{}
\newcommand*{\makeletterfooter}{\makefooter}
\newcommand*{\makeletterclosing}{}

\endinput

%% end of file `moderncv.cls'.