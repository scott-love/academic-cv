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

import yaml


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CV_DIR = ROOT / "cv"
OUTPUT_FILE = CV_DIR / "cv.tex"
PHOTO_FILE = DATA / "photo.jpg"  # Placeholder path

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
        ref += f" \\href{{https://doi.org/{pub['doi']}}}{{doi:{pub['doi']}}}"
    
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
add_line(r"\documentclass[11pt,a4paper,sans]{moderncv}")
add_line(r"\moderncvstyle{casual}")
add_line(r"\moderncvcolor{blue}")
add_line(r"\usepackage[utf8]{inputenc}")
add_line(r"\usepackage[T1]{fontenc}")
add_line(r"\usepackage[scale=.84]{geometry}")
add_line(r"\setlength{\hintscolumnwidth}{2.5cm}")
add_line(r"\usepackage{hyperref}")
add_line()

# Personal information
name_parts = profile.get("name", "").split()
firstname = name_parts[0] if name_parts else ""
lastname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

add_line(f"\\firstname{{{escape_latex(firstname)}}}")
add_line(f"\\familyname{{{escape_latex(lastname)}}}")

# Optional: photo (placeholder)
if PHOTO_FILE.exists():
    add_line(f"\\photo[64pt][0.4pt]{{data/photo}}")
else:
    # Add placeholder comment
    add_line("% \\photo[64pt][0.4pt]{data/photo}  % Uncomment and add photo when available")

add_line()
add_line(r"\begin{document}")
add_line(r"\makecvtitle")
add_line()

# Profile/Summary
if profile.get("summary"):
    add_line(r"\section{Profile}")
    add_line(escape_latex(profile["summary"]))
    add_line()

# Research Interests
if profile.get("research_interests"):
    add_line(r"\section{Research Interests}")
    interests = ", ".join(profile["research_interests"])
    add_line(escape_latex(interests))
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
            add_line(" \\textbf{{·}} ".join(details))
        
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
                add_line(" \\textbf{{·}} ".join(details))
            
            add_line("}")
    
    add_line()

# Grants
if grants:
    add_line(r"\section{Grants}")
    
    for grant in grants:
        dates = f"{grant['start']} -- {grant['end']}"
        funder = escape_latex(grant.get("funder", ""))
        title = escape_latex(grant.get("title", ""))
        
        if grant.get("acronym"):
            title += f" ({grant['acronym']})"
        
        add_line(f"\\cventry{{{dates}}}{{{title}}}{{{funder}}}{{}}{{}}{{")
        
        if grant.get("amount"):
            add_line(f"Amount: {escape_latex(grant['amount'])}")
        
        if grant.get("description"):
            add_line(escape_latex(grant["description"]))
        
        if grant.get("partners"):
            partners = ", ".join(grant["partners"])
            add_line(f"Partners: {escape_latex(partners)}")
        
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
        
        add_line("}")
    
    add_line()

# Supervision
if supervision:
    add_line(r"\section{Supervision}")
    
    for student in supervision:
        name = escape_latex(student.get("name", ""))
        period = student.get("period", "")
        level = escape_latex(student.get("level", "")) if student.get("level") else ""
        
        add_line(f"\\cventry{{{period}}}{{{name}}}{{}}{{}}{{}}{{")
        
        if level:
            add_line(level)
        
        if student.get("role"):
            add_line(f"Role: {escape_latex(student['role'])}")
        
        if student.get("institution"):
            add_line(f"Institution: {escape_latex(student['institution'])}")
        
        if student.get("topic"):
            add_line(f"Topic: {escape_latex(student['topic'])}")
        
        add_line("}")
    
    add_line()

# Publications - NO TWO-COLUMN FORMAT, use simple list
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
            add_line(f"\\item {ref}")
        add_line()
    
    # Book Chapters
    if pubs["book_chapters"]:
        add_line(f"\\subsection{{Book Chapters ({len(pubs['book_chapters'])})}}")
        add_line()
        for pub in pubs["book_chapters"]:
            ref = format_journal_reference(pub)
            add_line(f"\\item {ref}")
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
                add_line(f"\\item {ref}")
        
        if pubs["oral_presentations"]:
            add_line()
            add_line(f"\\textbf{{Oral Presentations ({len(pubs['oral_presentations'])})}}")
            add_line()
            for pub in pubs["oral_presentations"]:
                ref = format_conference_reference(pub)
                add_line(f"\\item {ref}")
        
        if pubs["posters"]:
            add_line()
            add_line(f"\\textbf{{Posters ({len(pubs['posters'])})}}")
            add_line()
            for pub in pubs["posters"]:
                ref = format_conference_reference(pub)
                add_line(f"\\item {ref}")
        
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
            add_line(f"\\item {ref}")
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
            add_line(f"\\item {ref}")
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
