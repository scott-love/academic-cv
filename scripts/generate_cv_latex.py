#!/usr/bin/env python3
"""
Generate a ModernCV LaTeX CV from YAML data files and HAL publications.

This script:
1. Loads profile, employment, education, grants, teaching, supervision data
2. Loads publications from HAL (via publications.json)
3. Generates a professional ModernCV LaTeX document using the 'casual' style
4. Handles author abbreviation, sorting, and formatting
"""

import json
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

import yaml


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CV_DIR = ROOT / "cv"
OUTPUT_FILE = CV_DIR / "cv.tex"
PHOTO_FILE = CV_DIR / "pictures" / "scott.jpg"
PHOTO_LATEX_PATH = "pictures/scott"

# Ensure output directory exists
CV_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Load Data
# ---------------------------------------------------------------------------

def load_yaml(path):
    """Load and parse a YAML file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


profile = load_yaml(DATA / "profile.yml")
education = load_yaml(DATA / "education.yml") or []
employment = load_yaml(DATA / "employment.yml") or []
grants = load_yaml(DATA / "grants.yml") or []
teaching = load_yaml(DATA / "teaching.yml") or []
supervision = load_yaml(DATA / "supervision.yml") or []

with open(DATA / "publications.json", encoding="utf-8") as f:
    publications = json.load(f)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def escape_latex(text):
    """Escape special LaTeX characters."""
    if not text:
        return ""

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    # Handle backslash first
    result = text.replace("\\", r"\textbackslash{}")

    # Handle others
    for char, replacement in list(replacements.items())[1:]:
        result = result.replace(char, replacement)

    return result


def escape_latex_url(url):
    """Escape URL characters that can break LaTeX command arguments."""
    if not url:
        return ""

    normalized = str(url).replace(" ", "%20")
    return (
        normalized.replace("%", r"\%")
        .replace("#", r"\#")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def normalize_homepage_url(homepage):
    """Normalize homepage to an absolute URL."""
    if not homepage:
        return ""

    homepage = str(homepage).strip()
    if homepage.startswith(("http://", "https://")):
        return homepage
    return f"https://{homepage}"


def normalize_spaces(text):
    """Collapse repeated whitespace into single spaces."""
    return " ".join(str(text).split()).strip()


LATEX_MIDPOINT = r"\textperiodcentered{}"
LATEX_BOLD_MIDPOINT = rf"\textbf{{{LATEX_MIDPOINT}}}"


def join_latex_fragments(parts, separator=LATEX_MIDPOINT):
    """Join pre-escaped LaTeX fragments with a LaTeX-safe separator."""
    fragments = [part for part in parts if part]
    return f" {separator} ".join(fragments)


def format_research_interests(interests):
    """Format research interests as an escaped midpoint-separated line."""
    escaped_interests = [
        escape_latex(normalize_spaces(interest))
        for interest in (interests or [])
        if normalize_spaces(interest)
    ]
    return join_latex_fragments(escaped_interests)


def role_implies_coordinator(role):
    """Return True when role indicates the person is the coordinator."""
    normalized_role = normalize_spaces(str(role).replace("-", " ").replace("_", " ")).casefold()
    return normalized_role in {"coordinator", "local coordinator"}


def build_profile_links(profile_data):
    """Build clickable profile links for the ModernCV header."""
    links = []

    orcid = str(profile_data.get("orcid", "")).strip()
    if orcid:
        url = escape_latex_url(f"https://orcid.org/{quote(orcid, safe='')}")
        label = escape_latex(f"ORCID: {orcid}")
        links.append(f"\\href{{{url}}}{{{label}}}")

    hal = str(profile_data.get("hal", "")).strip()
    if hal:
        url = escape_latex_url(f"https://hal.science/{quote(hal, safe='')}")
        label = escape_latex(f"HAL: {hal}")
        links.append(f"\\href{{{url}}}{{{label}}}")

    github = str(profile_data.get("github", "")).strip()
    if github:
        url = escape_latex_url(f"https://github.com/{quote(github, safe='')}")
        label = escape_latex(f"GitHub: {github}")
        links.append(f"\\href{{{url}}}{{{label}}}")

    homepage_raw = str(profile_data.get("homepage", "")).strip()
    if homepage_raw:
        url = escape_latex_url(normalize_homepage_url(homepage_raw))
        label = escape_latex(homepage_raw)
        links.append(f"\\href{{{url}}}{{{label}}}")

    return links


def is_scott(author):
    """Check if author is Scott A. Love."""
    return author.strip().lower() in {
        "scott love",
        "scott a. love",
        "scott a love",
    }


def abbreviate_author(author):
    """
    Convert author name to surname + initials.

    Examples:
        Katherine L Bryant -> Bryant KL
        Arnaud Le Troter -> Le Troter A
        Scott A. Love -> Scott A. Love
    """
    author = author.strip()

    if is_scott(author):
        return author

    parts = author.split()

    if len(parts) < 2:
        return author

    # Multi-word surname particles
    surname_particles = {
        "de", "da", "del", "della", "di", "du", "des",
        "le", "la", "van", "von", "der", "den", "ter", "ten",
    }

    surname_start = len(parts) - 1
    while (
        surname_start > 0
        and parts[surname_start - 1].lower() in surname_particles
    ):
        surname_start -= 1

    surname = " ".join(parts[surname_start:])
    given_names = parts[:surname_start]

    initials = "".join(
        p[0].upper()
        for p in given_names
        if p and p[0].isalpha()
    )

    return f"{surname} {initials}"


def format_author_list(authors, max_authors=6):
    """
    Format author list with Scott highlighted.

    Abbreviates authors except Scott A. Love.
    Uses 'et al.' for long lists.
    """
    formatted = []

    for author in authors:
        if is_scott(author):
            formatted.append(f"\\textbf{{{author}}}")
        else:
            formatted.append(abbreviate_author(author))

    if len(formatted) > max_authors:
        visible = formatted[:max_authors]

        # Ensure Scott remains visible
        scott_found = any("\\textbf" in author for author in formatted)
        scott_visible = any("\\textbf" in author for author in visible)

        if scott_found and not scott_visible:
            visible[-1] = "\\textbf{Scott A. Love}"

        return ", ".join(visible) + ", \\textit{et al.}"

    return ", ".join(formatted)


def format_date(date_string):
    """Format YYYY-MM-DD as '19 November 2025'."""
    if not date_string:
        return None

    try:
        date = datetime.strptime(date_string, "%Y-%m-%d")
        return date.strftime("%-d %B %Y")
    except (ValueError, AttributeError):
        return str(date_string)


def format_conference_dates(pub):
    """Format conference start/end dates."""
    start = pub.get("conference_start")
    end = pub.get("conference_end")

    if not start:
        return None

    if not end or start == end:
        return format_date(start)

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        if start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return (
                    f"{start_date.day}–{end_date.day} "
                    f"{start_date.strftime('%B %Y')}"
                )
            else:
                return (
                    f"{start_date.day} {start_date.strftime('%B')}–"
                    f"{end_date.day} {end_date.strftime('%B %Y')}"
                )

        return f"{format_date(start)}–{format_date(end)}"

    except (ValueError, AttributeError):
        return f"{start}–{end}"


def format_country(code):
    """Convert HAL country codes to country names."""
    countries = {
        "fr": "France", "ca": "Canada", "gb": "United Kingdom",
        "uk": "United Kingdom", "us": "United States", "de": "Germany",
        "es": "Spain", "it": "Italy", "be": "Belgium", "nl": "Netherlands",
        "ch": "Switzerland", "gr": "Greece", "cy": "Cyprus", "au": "Australia",
        "jp": "Japan", "cn": "China", "se": "Sweden", "dk": "Denmark",
        "fi": "Finland", "no": "Norway", "pt": "Portugal",
    }

    if not code:
        return None

    return countries.get(code.lower(), code.upper())


def normalize_pages(value):
    """Return normalized pages or None for placeholders/missing values."""
    if value is None:
        return None

    pages = str(value).strip()
    if not pages:
        return None

    normalized = pages.lower().replace(" ", "")
    missing_tokens = {
        "np",
        "n.p.",
        "n.p",
        "na",
        "n/a",
        "none",
        "null",
        "-",
        "--",
        "?",
    }

    if normalized in missing_tokens:
        return None

    return pages


def sort_publications(items):
    """Sort publications by year (newest first), then by HAL ID."""
    return sorted(
        items,
        key=lambda p: (p.get("year") or 0, p.get("hal_id") or ""),
        reverse=True,
    )


def categorize_publications(publications):
    """Categorize publications by type."""
    journal_articles = [
        p for p in publications
        if p.get("category") == "Journal article"
    ]

    book_chapters = [
        p for p in publications
        if p.get("category") == "Book chapter"
    ]

    conference_presentations = [
        p for p in publications
        if p.get("category") == "Conference presentation"
    ]

    invited_talks = [
        p for p in conference_presentations
        if p.get("presentation_type") == "Invited talk"
    ]

    oral_presentations = [
        p for p in conference_presentations
        if p.get("presentation_type") == "Oral presentation"
    ]

    posters = [
        p for p in conference_presentations
        if p.get("presentation_type") == "Poster"
    ]

    reports = [
        p for p in publications
        if p.get("category") == "Report"
    ]

    other = [
        p for p in publications
        if p.get("category") == "Other scientific contribution"
    ]

    return {
        "journal_articles": sort_publications(journal_articles),
        "book_chapters": sort_publications(book_chapters),
        "invited_talks": sort_publications(invited_talks),
        "oral_presentations": sort_publications(oral_presentations),
        "posters": sort_publications(posters),
        "reports": sort_publications(reports),
        "other": sort_publications(other),
    }


def format_journal_reference(pub):
    """Format a journal article reference."""
    authors = format_author_list(pub.get("authors", []))
    title = escape_latex(pub.get("title", ""))
    journal = escape_latex(pub.get("journal", ""))
    year = pub.get("year", "")

    ref = f"{authors} ({year}). \\textit{{{title}}}."

    if journal:
        ref += f" \\textbf{{{journal}}}."

    if pub.get("doi"):
        doi_raw = pub["doi"]
        ref += f" \\href{{https://doi.org/{doi_raw}}}{{doi:\\nolinkurl{{{doi_raw}}}}}"

    return ref


def format_book_chapter_reference(pub):
    """Format a book chapter reference with container metadata."""
    authors = format_author_list(pub.get("authors", []))
    title = escape_latex(pub.get("title", ""))
    year = pub.get("year", "")

    ref = f"{authors} ({year}). \\textit{{{title}}}."

    editors = pub.get("editors") or []
    source = pub.get("source") or ""
    book_title = pub.get("book_title") or source

    in_parts = []

    if editors:
        editors_fmt = format_author_list(editors, max_authors=10)
        label = "Ed." if len(editors) == 1 else "Eds."
        in_parts.append(f"{editors_fmt} ({label})")

    if book_title:
        in_parts.append(f"\\textit{{{escape_latex(book_title)}}}")

    if in_parts:
        ref += f" In: {', '.join(in_parts)}."

    pages = normalize_pages(pub.get("pages"))
    if pages:
        ref += f" pp. {escape_latex(pages)}."

    if pub.get("publisher"):
        ref += f" {escape_latex(pub['publisher'])}."

    if pub.get("doi"):
        doi_raw = pub["doi"]
        ref += f" \\href{{https://doi.org/{doi_raw}}}{{doi:\\nolinkurl{{{doi_raw}}}}}"

    return ref


def format_conference_reference(pub):
    """Format a conference presentation reference."""
    authors = format_author_list(pub.get("authors", []))
    title = escape_latex(pub.get("title", ""))
    year = pub.get("year", "")

    ref = f"{authors} ({year}). \\textit{{{title}}}."

    if pub.get("conference"):
        conference = escape_latex(pub["conference"])
        ref += f" \\textit{{{conference}}}."

    dates = format_conference_dates(pub)
    if dates:
        ref += f" {dates}."

    location_parts = []
    if pub.get("city"):
        location_parts.append(escape_latex(pub["city"]))
    if pub.get("country"):
        country = format_country(pub["country"])
        if country:
            location_parts.append(country)

    if location_parts:
        ref += f" {', '.join(location_parts)}."

    return ref


# ---------------------------------------------------------------------------
# Generate LaTeX
# ---------------------------------------------------------------------------

latex_lines = []


def add_line(text=""):
    """Add a line to the LaTeX output."""
    latex_lines.append(text)


# Document preamble
add_line(r"\documentclass[10pt,a4paper,sans]{moderncv}")
add_line(r"\moderncvstyle{casual}")
add_line(r"\moderncvcolor{blue}")
add_line(r"\usepackage[utf8]{inputenc}")
add_line(r"\usepackage[T1]{fontenc}")
add_line(r"\usepackage[scale=.84]{geometry}")
add_line(r"\setlength{\hintscolumnwidth}{2.5cm}")
add_line()

# Personal information
name_parts = profile.get("name", "").split()
firstname = name_parts[0] if name_parts else ""
lastname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

add_line(f"\\firstname{{{escape_latex(firstname)}}}")
add_line(f"\\familyname{{{escape_latex(lastname)}}}")
profile_links = build_profile_links(profile)
if profile_links:
    add_line(f"\\extrainfo{{{r'\enspace\textbar\enspace'.join(profile_links)}}}")

# Optional: photo
if PHOTO_FILE.exists():
    add_line(f"\\photo[64pt][0.4pt]{{{PHOTO_LATEX_PATH}}}")
else:
    add_line(f"% \\photo[64pt][0.4pt]{{{PHOTO_LATEX_PATH}}}")

add_line()
add_line(r"\begin{document}")
add_line(r"\makecvtitle")
add_line()

# Combined summary and research interests (no heading)
summary = normalize_spaces(profile.get("summary", ""))
interests = format_research_interests(profile.get("research_interests"))

if summary and interests:
    add_line(f"{escape_latex(summary)}\\\\")
    add_line(f"{{\\small {interests}}}")
elif summary:
    add_line(escape_latex(summary))
elif interests:
    add_line(f"{{\\small {interests}}}")

if summary or interests:
    add_line()

# Education
if education:
    add_line(r"\section{Education}")

    for deg in education:
        if deg.get("start") and deg.get("end"):
            dates = f"{deg['start']} -- {deg['end']}"
        else:
            dates = str(deg.get("year", ""))

        degree = escape_latex(deg.get("degree", ""))
        institution = escape_latex(deg.get("institution", ""))

        if deg.get("country"):
            institution += f", {deg['country']}"

        add_line(f"\\cventry{{{dates}}}{{{degree}}}{{{institution}}}{{}}{{}}{{")

        # Order: Honors, Supervisor, Title (each with period)
        details = []

        if deg.get("honours"):
            details.append(f"\\textbf{{Honors:}} {escape_latex(deg['honours'])}")

        if deg.get("supervisor"):
            details.append(f"\\textbf{{Supervisor:}} {escape_latex(deg['supervisor'])}")

        if deg.get("thesis_title"):
            details.append(f"\\textbf{{Title:}} \\textit{{{escape_latex(deg['thesis_title'])}}}")

        if details:
            add_line(join_latex_fragments(details, LATEX_BOLD_MIDPOINT))

        add_line("}")

    add_line()

# Professional Experience / Employment
if employment:
    add_line(r"\section{Professional Experience}")

    # Group by category if available
    by_category = {}
    for pos in employment:
        cat = pos.get("category", "Research")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(pos)

    for category in sorted(by_category.keys()):
        if category != "Research":
            add_line(f"\\subsection{{{category}}}")

        for pos in by_category[category]:
            start = pos.get("start", "")
            end = pos.get("end", "")

            if start and end:
                dates = f"{start} -- {end}"
            else:
                dates = start or end

            position = escape_latex(pos.get("position", ""))
            institution = escape_latex(pos.get("institution", ""))

            if pos.get("country"):
                institution += f", {pos['country']}"

            add_line(f"\\cventry{{{dates}}}{{{position}}}{{{institution}}}{{}}{{}}{{")

            # Supervisor and Team on same line with bold labels and bullet separator
            details = []

            if pos.get("supervisor"):
                details.append(f"\\textbf{{Supervisor:}} {escape_latex(pos['supervisor'])}")

            if pos.get("team"):
                details.append(f"\\textbf{{Team:}} {escape_latex(pos['team'])}")

            if details:
                add_line(join_latex_fragments(details, LATEX_BOLD_MIDPOINT))

            add_line("}")

    add_line()

# Funding
if grants:
    add_line(r"\section{Funding}")

    for grant in grants:
        start = str(grant.get("start", ""))
        end = str(grant.get("end", ""))
        dates = f"{start} -- {end}" if start and end else start or end

        funder = escape_latex(grant.get("funder", ""))
        title = escape_latex(grant.get("title", ""))

        if grant.get("acronym"):
            title += f" ({escape_latex(grant['acronym'])})"

        add_line(f"\\cventry{{{dates}}}{{{title}}}{{{funder}}}{{}}{{}}{{")

        details = []

        role = normalize_spaces(grant.get("role", ""))
        coordinator = normalize_spaces(grant.get("coordinator", ""))
        amount = grant.get("amount", "")
        show_coordinator = bool(coordinator) and not role_implies_coordinator(role)

        if role:
            details.append(f"\\textbf{{Role:}} {escape_latex(role)}")
        if show_coordinator:
            details.append(f"\\textbf{{Coordinator:}} {escape_latex(coordinator)}")
        if amount:
            details.append(f"\\textbf{{Amount:}} {escape_latex(amount)}")

        if grant.get("partners"):
            partners_str = escape_latex(", ".join(grant["partners"]))
            details.append(f"\\textbf{{Partners:}} {partners_str}")

        if grant.get("description"):
            details.append(f"\\textbf{{Description:}} {escape_latex(grant['description'])}")

        if details:
            add_line(join_latex_fragments(details, LATEX_BOLD_MIDPOINT))

        add_line("}")

    add_line()

# Teaching
if teaching:
    add_line(r"\section{Teaching}")

    for course in teaching:
        start = str(course.get("start", ""))
        end = str(course.get("end", ""))

        if start and end:
            dates = start if start == end else f"{start} -- {end}"
        else:
            dates = start or end

        role = escape_latex(course.get("role", ""))
        course_name = escape_latex(course.get("course", ""))
        institution = escape_latex(course.get("institution", ""))

        if course.get("country"):
            institution += f", {course['country']}"

        add_line(f"\\cventry{{{dates}}}{{{role}}}{{{course_name}}}{{{institution}}}{{}}{{")

        if course.get("description"):
            add_line(escape_latex(course["description"]))

        classes = course.get("classes", [])
        if classes:
            add_line(r"\begin{itemize}")
            for cls in classes:
                cls_start = str(cls.get("start", ""))
                cls_end = str(cls.get("end", ""))
                if cls_start and cls_end:
                    cls_dates = cls_start if cls_start == cls_end else f"{cls_start} -- {cls_end}"
                else:
                    cls_dates = cls_start or cls_end
                cls_title = escape_latex(cls.get("title", ""))
                cls_type = escape_latex(cls.get("type", ""))
                detail = f"{cls_dates}: {cls_title}"
                if cls_type:
                    detail += f" ({cls_type})"
                add_line(f"\\item {detail}")
            add_line(r"\end{itemize}")

        add_line("}")

    add_line()

# Supervision
if supervision:
    add_line(r"\section{Supervision}")

    for student in supervision:
        name = escape_latex(student.get("name", ""))
        start = str(student.get("start", "")).strip()
        end = str(student.get("end", "")).strip()
        period = str(student.get("period", "")).strip()
        if start and end:
            period = start if start == end else f"{start} -- {end}"
        elif start or end:
            period = start or end

        level = escape_latex(student.get("level", "")) if student.get("level") else ""
        institution = escape_latex(student.get("institution", "")) if student.get("institution") else ""
        role = normalize_spaces(student.get("role", ""))
        topic = student.get("topic", "")

        add_line(f"\\cventry{{{period}}}{{{name}}}{{{level}}}{{{institution}}}{{}}{{")

        details = []
        if role:
            details.append(f"\\textbf{{Role:}} {escape_latex(role)}")
        if topic:
            details.append(f"\\textbf{{Topic:}} {escape_latex(topic)}")

        if details:
            add_line(join_latex_fragments(details, LATEX_BOLD_MIDPOINT))

        add_line("}")

    add_line()

# Publications - plain paragraphs at full text width (no ModernCV hint column, no bullet)
pubs = categorize_publications(publications)
total_pubs = sum(len(v) for v in pubs.values())

if total_pubs > 0:
    add_line(r"\section{Publications}")
    add_line()

    # Journal Articles
    if pubs["journal_articles"]:
        add_line(f"\\subsection{{Journal Articles ({len(pubs['journal_articles'])})}}")
        add_line()
        for pub in pubs["journal_articles"]:
            ref = format_journal_reference(pub)
            add_line(f"{ref}\\par\\medskip")
        add_line()

    # Book Chapters
    if pubs["book_chapters"]:
        add_line(f"\\subsection{{Book Chapters ({len(pubs['book_chapters'])})}}")
        add_line()
        for pub in pubs["book_chapters"]:
            ref = format_book_chapter_reference(pub)
            add_line(f"{ref}\\par\\medskip")
        add_line()

    # Conference Presentations
    conf_total = len(pubs['invited_talks']) + len(pubs['oral_presentations']) + len(pubs['posters'])
    if conf_total > 0:
        add_line(f"\\subsection{{Conference Presentations ({conf_total})}}")
        add_line()

        if pubs["invited_talks"]:
            add_line()
            add_line(f"\\textbf{{Invited Talks ({len(pubs['invited_talks'])})}}")
            add_line()
            for pub in pubs["invited_talks"]:
                ref = format_conference_reference(pub)
                add_line(f"{ref}\\par\\medskip")

        if pubs["oral_presentations"]:
            add_line()
            add_line(f"\\textbf{{Oral Presentations ({len(pubs['oral_presentations'])})}}")
            add_line()
            for pub in pubs["oral_presentations"]:
                ref = format_conference_reference(pub)
                add_line(f"{ref}\\par\\medskip")

        if pubs["posters"]:
            add_line()
            add_line(f"\\textbf{{Posters ({len(pubs['posters'])})}}")
            add_line()
            for pub in pubs["posters"]:
                ref = format_conference_reference(pub)
                add_line(f"{ref}\\par\\medskip")

        add_line()

    # Reports
    if pubs["reports"]:
        add_line()
        add_line(f"\\subsection{{Reports ({len(pubs['reports'])})}}")
        add_line()
        for pub in pubs["reports"]:
            authors = format_author_list(pub.get("authors", []))
            title = escape_latex(pub.get("title", ""))
            year = pub.get("year", "")
            ref = f"{authors} ({year}). \\textbf{{{title}}}."
            add_line(f"{ref}\\par\\medskip")
        add_line()

    # Other
    if pubs["other"]:
        add_line()
        add_line(f"\\subsection{{Other Scientific Contributions ({len(pubs['other'])})}}")
        add_line()
        for pub in pubs["other"]:
            authors = format_author_list(pub.get("authors", []))
            title = escape_latex(pub.get("title", ""))
            year = pub.get("year", "")
            ref = f"{authors} ({year}). \\textbf{{{title}}}."
            add_line(f"{ref}\\par\\medskip")
        add_line()

# Document end
add_line(r"\end{document}")

# Write to file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(latex_lines))

print(f"Generated {OUTPUT_FILE}")
print(f"  - Style: casual (blue)")
print(f"  - Profile: {profile.get('name')}")
print(f"  - Photo: {'Present' if PHOTO_FILE.exists() else 'Not found (placeholder commented out)'}")
print(f"  - Publications: {total_pubs} total")
print(f"    - Journal articles: {len(pubs['journal_articles'])}")
print(f"    - Book chapters: {len(pubs['book_chapters'])}")
print(f"    - Conference presentations: {len(pubs['invited_talks']) + len(pubs['oral_presentations']) + len(pubs['posters'])}")
print(f"    - Reports: {len(pubs['reports'])}")
print(f"    - Other: {len(pubs['other'])}")
