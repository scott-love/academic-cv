#!/usr/bin/env python3
"""
Generate a LaTeX CV file from YAML/JSON data using ModernCV template.

This script reads structured CV data and outputs a complete .tex file
that can be compiled with pdflatex using the ModernCV document class.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from textwrap import dedent


class CVGenerator:
    """Generate LaTeX CV from structured data."""

    def __init__(self, data_dir: Path, output_file: Path):
        """Initialize CV generator."""
        self.data_dir = data_dir
        self.output_file = output_file
        self.load_data()

    def load_data(self):
        """Load all CV data from YAML and JSON files."""
        with open(self.data_dir / "profile.yml", encoding="utf-8") as f:
            self.profile = yaml.safe_load(f)

        with open(self.data_dir / "education.yml", encoding="utf-8") as f:
            self.education = yaml.safe_load(f) or []

        with open(self.data_dir / "employment.yml", encoding="utf-8") as f:
            self.employment = yaml.safe_load(f) or []

        with open(self.data_dir / "teaching.yml", encoding="utf-8") as f:
            self.teaching = yaml.safe_load(f) or []

        with open(self.data_dir / "grants.yml", encoding="utf-8") as f:
            self.grants = yaml.safe_load(f) or []

        with open(self.data_dir / "supervision.yml", encoding="utf-8") as f:
            self.supervision = yaml.safe_load(f) or []

        with open(self.data_dir / "languages.yml", encoding="utf-8") as f:
            self.languages = yaml.safe_load(f) or []

        with open(self.data_dir / "honors_awards.yml", encoding="utf-8") as f:
            self.honors_awards = yaml.safe_load(f) or []

        with open(self.data_dir / "publications.json", encoding="utf-8") as f:
            self.publications = json.load(f)

        self.categorize_publications()

    def categorize_publications(self):
        """Categorize publications by type."""
        self.journal_articles = [
            p for p in self.publications
            if p.get("category") == "Journal article"
        ]

        self.book_chapters = [
            p for p in self.publications
            if p.get("category") == "Book chapter"
        ]

        self.conference_presentations = [
            p for p in self.publications
            if p.get("category") == "Conference presentation"
        ]

        self.invited_talks = [
            p for p in self.conference_presentations
            if p.get("presentation_type") == "Invited talk"
        ]

        self.oral_presentations = [
            p for p in self.conference_presentations
            if p.get("presentation_type") == "Oral presentation"
        ]

        self.posters = [
            p for p in self.conference_presentations
            if p.get("presentation_type") == "Poster"
        ]

        self.reports = [
            p for p in self.publications
            if p.get("category") == "Report"
        ]

        self.other_contributions = [
            p for p in self.publications
            if p.get("category") == "Other scientific contribution"
        ]

    def escape_latex(self, text: str) -> str:
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
        
        result = text
        # Handle backslash first
        result = result.replace("\\", r"\textbackslash{}")
        # Then handle other characters
        for char, replacement in replacements.items():
            if char != "\\":  # Already handled
                result = result.replace(char, replacement)
        
        return result

    def format_employment_date(self, value) -> str:
        """Format employment dates."""
        if not value:
            return ""

        value = str(value).strip()

        if value.lower() == "present":
            return "present"

        # Handle YYYY-MM format
        if len(value) == 7 and value[4] == "-":
            year, month = value.split("-")
            months = {
                "01": "January", "02": "February", "03": "March",
                "04": "April", "05": "May", "06": "June",
                "07": "July", "08": "August", "09": "September",
                "10": "October", "11": "November", "12": "December",
            }
            return f"{months.get(month, month)} {year}"

        return value

    def format_date(self, date_string: str) -> str:
        """Format YYYY-MM-DD as readable date."""
        if not date_string:
            return None

        try:
            date = datetime.strptime(date_string, "%Y-%m-%d")
            return date.strftime("%-d %B %Y")
        except (ValueError, AttributeError):
            return date_string

    def is_scott(self, author: str) -> bool:
        """Check if author is Scott A. Love."""
        return author.strip().lower() in {
            "scott love",
            "scott a. love",
            "scott a love",
        }

    def abbreviate_author(self, author: str) -> str:
        """Abbreviate author name to surname + initials."""
        author = author.strip()

        if self.is_scott(author):
            return author

        parts = author.split()

        if len(parts) < 2:
            return author

        surname_particles = {
            "de", "da", "del", "della", "di", "du", "des",
            "le", "la", "van", "von", "der", "den", "ter", "ten",
        }

        surname_start = len(parts) - 1

        while (surname_start > 0 and
               parts[surname_start - 1].lower() in surname_particles):
            surname_start -= 1

        surname = " ".join(parts[surname_start:])
        given_names = parts[:surname_start]

        initials = "".join(
            p[0].upper()
            for p in given_names
            if p and p[0].isalpha()
        )

        return f"{surname} {initials}"

    def format_author_list(self, authors: list, max_authors: int = 6) -> str:
        """Format authors with Scott highlighted."""
        formatted = []

        for author in authors:
            if self.is_scott(author):
                formatted.append(f"\\textbf{{{author}}}")
            else:
                formatted.append(self.abbreviate_author(author))

        if len(formatted) > max_authors:
            visible = formatted[:max_authors]

            # Ensure Scott remains visible
            if any("\\textbf" in author for author in formatted):
                if not any("\\textbf" in author for author in visible):
                    visible[-1] = "\\textbf{Scott A. Love}"

            return ", ".join(visible) + ", et al."

        return ", ".join(formatted)

    def sort_publications(self, items: list) -> list:
        """Sort publications from newest to oldest."""
        return sorted(
            items,
            key=lambda p: p.get("year") or 0,
            reverse=True
        )

    def format_reference(self, pub: dict) -> str:
        """Format journal/book reference."""
        authors = self.format_author_list(pub["authors"])

        reference = (
            f"{authors} "
            f"({pub['year']}). "
            f"\\textit{{{self.escape_latex(pub['title'])}}}."
        )

        if pub.get("journal"):
            reference += f" \\textbf{{{self.escape_latex(pub['journal'])}}}."

        if pub.get("publisher"):
            reference += f" {self.escape_latex(pub['publisher'])}."

        if pub.get("doi"):
            reference += f" \\href{{https://doi.org/{pub['doi']}}}{{doi:{pub['doi']}}}"

        return reference

    def generate_preamble(self) -> str:
        """Generate LaTeX preamble."""
        return dedent(r"""
            \documentclass[11pt,a4paper,sans]{moderncv}
            
            \moderncvstyle{casual}
            \moderncvcolor{blue}
            
            \usepackage[utf8]{inputenc}
            \usepackage[T1]{fontenc}
            \usepackage[scale=.84]{geometry}
            \setlength{\hintscolumnwidth}{2.5cm}
            
            \usepackage{hyperref}
        """).strip()

    def generate_header(self) -> str:
        """Generate personal information section."""
        lines = []

        # Name and title
        lines.append(f"\\firstname{{{self.profile['name'].split()[0]}}}")
        lines.append(f"\\familyname{{{', '.join(self.profile['name'].split()[1:])}}}")

        if self.profile.get("title"):
            lines.append(f"\\title{{{self.escape_latex(self.profile['title'])}}}")

        # Contact info
        if self.profile.get("email"):
            lines.append(f"\\email{{{self.profile['email']}}}")

        if self.profile.get("homepage"):
            lines.append(
                f"\\homepage{{{self.profile['homepage']}}}"
                f"{{{self.profile['homepage']}}}"
            )

        return "\n".join(lines)

    def generate_education_section(self) -> str:
        """Generate education section."""
        if not self.education:
            return ""

        lines = ["\n\\section{Education}"]

        for degree in self.education:
            # Date range
            if degree.get("start") and degree.get("end"):
                dates = f"{degree['start']}--{degree['end']}"
            else:
                dates = str(degree.get("year", ""))

            institution = self.escape_latex(degree["institution"])

            lines.append(
                f"\\cventry{{{dates}}}"
                f"{{{self.escape_latex(degree['degree'])}}}"
                f"{{{institution}}}"
                f"{{}}{{}}{{}}"
            )

            if degree.get("honours"):
                lines.append(
                    f"\\cvitem{{Honors}}{{{self.escape_latex(degree['honours'])}}}"
                )

            if degree.get("supervisor"):
                lines.append(
                    f"\\cvitem{{Supervisor}}{{{self.escape_latex(degree['supervisor'])}}}"
                )

            if degree.get("thesis_title"):
                lines.append(
                    f"\\cvitem{{Thesis}}{{{self.escape_latex(degree['thesis_title'])}}}"
                )

        return "\n".join(lines)

    def generate_employment_section(self) -> str:
        """Generate employment section."""
        if not self.employment:
            return ""

        lines = ["\n\\section{Professional Experience}"]

        # Group by category if available
        by_category = {}
        for pos in self.employment:
            cat = pos.get("category", "Other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(pos)

        for category, positions in by_category.items():
            if category != "Other":
                lines.append(f"\n\\subsection{{{category}}}")

            for position in positions:
                start = self.format_employment_date(position.get("start"))
                end = self.format_employment_date(position.get("end"))

                if start and end:
                    dates = f"{start}--{end}"
                else:
                    dates = start or end

                institution = self.escape_latex(position["institution"])
                if position.get("country"):
                    institution += f", {position['country']}"

                lines.append(
                    f"\\cventry{{{dates}}}"
                    f"{{{self.escape_latex(position['position'])}}}"
                    f"{{{institution}}}"
                    f"{{}}{{}}{{}}"
                )

                if position.get("supervisor"):
                    lines.append(
                        f"\\cvitem{{Supervisor}}{{{self.escape_latex(position['supervisor'])}}}"
                    )

                if position.get("team"):
                    lines.append(
                        f"\\cvitem{{Team}}{{{self.escape_latex(position['team'])}}}"
                    )

        return "\n".join(lines)

    def generate_publications_section(self) -> str:
        """Generate publications section."""
        lines = ["\n\\section{Publications}"]

        # Journal articles
        lines.append(
            f"\n\\subsection{{Journal Articles ({len(self.journal_articles)})}}"
        )
        for pub in self.sort_publications(self.journal_articles):
            lines.append(f"\\cvitem{{}}{{{self.format_reference(pub)}}}")

        # Book chapters
        if self.book_chapters:
            lines.append(
                f"\n\\subsection{{Book Chapters ({len(self.book_chapters)})}}"
            )
            for pub in self.sort_publications(self.book_chapters):
                lines.append(f"\\cvitem{{}}{{{self.format_reference(pub)}}}")

        # Conference presentations
        if self.conference_presentations:
            lines.append(
                f"\n\\subsection{{Conference Presentations"
                f" ({len(self.conference_presentations)})}}"
            )

            if self.invited_talks:
                lines.append(
                    f"\\subsubsection{{Invited Talks ({len(self.invited_talks)})}}"
                )
                for pub in self.sort_publications(self.invited_talks):
                    lines.append(
                        f"\\cvitem{{}}{{{self.format_conference_reference(pub)}}}"
                    )

            if self.oral_presentations:
                lines.append(
                    f"\\subsubsection{{Oral Presentations"
                    f" ({len(self.oral_presentations)})}}"
                )
                for pub in self.sort_publications(self.oral_presentations):
                    lines.append(
                        f"\\cvitem{{}}{{{self.format_conference_reference(pub)}}}"
                    )

            if self.posters:
                lines.append(f"\\subsubsection{{Posters ({len(self.posters)})}}")
                for pub in self.sort_publications(self.posters):
                    lines.append(
                        f"\\cvitem{{}}{{{self.format_conference_reference(pub)}}}"
                    )

        # Reports
        if self.reports:
            lines.append(f"\n\\subsection{{Reports ({len(self.reports)})}}")
            for pub in self.sort_publications(self.reports):
                lines.append(f"\\cvitem{{}}{{{self.format_reference(pub)}}}")

        # Other contributions
        if self.other_contributions:
            lines.append(
                f"\n\\subsection{{Other Scientific Contributions"
                f" ({len(self.other_contributions)})}}"
            )
            for pub in self.sort_publications(self.other_contributions):
                lines.append(f"\\cvitem{{}}{{{self.format_reference(pub)}}}")

        return "\n".join(lines)

    def format_conference_reference(self, pub: dict) -> str:
        """Format conference presentation."""
        authors = self.format_author_list(pub["authors"])
        
        text = (
            f"{authors} ({pub['year']}). "
            f"\\textit{{{self.escape_latex(pub['title'])}}}. "
        )

        if pub.get("conference"):
            text += f"{self.escape_latex(pub['conference'])}"

        if pub.get("conference_start"):
            text += f", {self.format_date(pub['conference_start'])}"

        if pub.get("city"):
            text += f", {self.escape_latex(pub['city'])}"

        if pub.get("country"):
            text += f", {self.escape_latex(pub['country'])}"

        return text + "."

    def generate_latex(self) -> str:
        """Generate complete LaTeX document."""
        content = [
            self.generate_preamble(),
            "\n\\begin{document}\n",
            self.generate_header(),
            "\n\\makecvtitle\n",
            self.generate_education_section(),
            self.generate_employment_section(),
            self.generate_publications_section(),
            "\n\\end{document}\n",
        ]

        return "\n".join(content)

    def write(self):
        """Write LaTeX to file."""
        latex_content = self.generate_latex()
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        print(f"Generated CV LaTeX file: {self.output_file}")


def main():
    """Main entry point."""
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    output_file = root / "cv" / "cv_generated.tex"

    generator = CVGenerator(data_dir, output_file)
    generator.write()


if __name__ == "__main__":
    main()
