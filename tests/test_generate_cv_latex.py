import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parents[1]
HAL_PROFILE_BASE_URL = "https://cv.hal.science/"


def escape_latex(text):
    replacements = {
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

    result = str(text).replace("\\", r"\textbackslash{}")
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    return result


def escape_latex_url(url):
    return (
        str(url)
        .replace(" ", "%20")
        .replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def test_generator_emits_expected_header_profile_links():
    output_file = ROOT / "cv" / "cv.tex"
    original_content = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")
        profile = yaml.safe_load((ROOT / "data" / "profile.yml").read_text(encoding="utf-8")) or {}

        expected_parts = []

        orcid = str(profile.get("orcid", "")).strip()
        if orcid:
            url = escape_latex_url(f"https://orcid.org/{quote(orcid, safe='')}")
            expected_parts.append(f"\\href{{{url}}}{{\\aiOrcid\\enspace {escape_latex(orcid)}}}")

        hal = str(profile.get("hal", "")).strip()
        if hal:
            url = escape_latex_url(f"{HAL_PROFILE_BASE_URL}{quote(hal, safe='')}")
            expected_parts.append(f"\\href{{{url}}}{{\\aiHAL\\enspace {escape_latex(hal)}}}")

        homepage = str(profile.get("homepage", "")).strip()
        if homepage:
            homepage_url = (
                homepage if homepage.startswith(("http://", "https://")) else f"https://{homepage}"
            )
            expected_parts.append(f"\\href{{{escape_latex_url(homepage_url)}}}{{\\faGlobe\\enspace {escape_latex(homepage)}}}")

        if expected_parts:
            expected_extrainfo = r"\enspace\textbar\enspace".join(expected_parts)
            assert f"\\newcommand*{{\\cvheaderlinks}}{{{expected_extrainfo}}}" in latex
            makecvhead_start = latex.index(r"\renewcommand*{\makecvhead}{%")
            rule_index = latex.index(r"  {\color{color2!50}\rule{\textwidth}{.25ex}}%", makecvhead_start)
            header_links_index = latex.index(r"      {\addressfont\color{color2}\cvheaderlinks}}}%", makecvhead_start)
            assert r"      \\[1em]%" in latex[makecvhead_start:rule_index]
            assert header_links_index < rule_index
            assert r"{\raggedleft\addressfont\color{color2}\cvheaderlinks\par}" not in latex
            assert "\\extrainfo{" not in latex
            assert "github.com" not in expected_extrainfo
            assert r"\aiGoogleScholar" not in expected_extrainfo
        else:
            assert r"\newcommand*{\cvheaderlinks}{" not in latex
    finally:
        if original_content is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_content, encoding="utf-8")


def test_generator_emits_icon_only_footer_profile_links():
    output_file = ROOT / "cv" / "cv.tex"
    original_content = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")
        profile = yaml.safe_load((ROOT / "data" / "profile.yml").read_text(encoding="utf-8")) or {}
        footer_links_line = next(
            line for line in latex.splitlines() if line.startswith(r"\newcommand*{\cvfooterlinks}{")
        )

        expected_parts = []

        orcid = str(profile.get("orcid", "")).strip()
        if orcid:
            orcid_url = escape_latex_url(f"https://orcid.org/{quote(orcid, safe='')}")
            expected_parts.append(f"\\href{{{orcid_url}}}{{\\aiOrcid}}")

        hal = str(profile.get("hal", "")).strip()
        if hal:
            hal_url = escape_latex_url(f"{HAL_PROFILE_BASE_URL}{quote(hal, safe='')}")
            expected_parts.append(f"\\href{{{hal_url}}}{{\\aiHAL}}")

        google_scholar = str(profile.get("google_scholar", "")).strip()
        if google_scholar:
            expected_parts.append(
                f"\\href{{{escape_latex_url(google_scholar)}}}{{\\aiGoogleScholar}}"
            )

        github = str(profile.get("github", "")).strip()
        if github:
            github_url = escape_latex_url(f"https://github.com/{quote(github, safe='')}")
            expected_parts.append(f"\\href{{{github_url}}}{{\\faGithub}}")

        homepage = str(profile.get("homepage", "")).strip()
        if homepage:
            homepage_url = (
                homepage if homepage.startswith(("http://", "https://")) else f"https://{homepage}"
            )
            expected_parts.append(f"\\href{{{escape_latex_url(homepage_url)}}}{{\\faGlobe}}")

        assert r"\usepackage{academicons}" in latex
        assert r"\usepackage{fontawesome5}" in latex
        expected_footer_links = r" \enspace ".join(expected_parts)
        assert footer_links_line == f"\\newcommand*{{\\cvfooterlinks}}{{{expected_footer_links}}}"
    finally:
        if original_content is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_content, encoding="utf-8")


def test_profile_and_research_interests_render_as_single_heading_free_block():
    output_file = ROOT / "cv" / "cv.tex"
    profile_file = ROOT / "data" / "profile.yml"

    original_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    original_profile = profile_file.read_text(encoding="utf-8")
    test_profile = yaml.safe_load(original_profile)

    test_profile["summary"] = "Summary with R&D, 50% focus on C# and {MRI}."
    test_profile["research_interests"] = [
        "Social & affective neuroscience",
        "50% methods",
        "C# pipelines",
        "{MRI}",
    ]

    try:
        profile_file.write_text(
            yaml.safe_dump(test_profile, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")
        profile_block = latex.split("\\section{Education}", 1)[0]

        escaped_summary = escape_latex(test_profile["summary"])
        escaped_interests = (
            r"{\small Social \& affective neuroscience \textperiodcentered{} "
            r"50\% methods \textperiodcentered{} C\# pipelines "
            r"\textperiodcentered{} \{MRI\}}"
        )

        assert "\\section{Profile}" not in latex
        assert "\\section{Research Interests}" not in latex
        assert f"{escaped_summary}\\\\" in profile_block
        assert escaped_interests in profile_block
        assert profile_block.index(escaped_summary) < profile_block.index(escaped_interests)
        assert "·" not in profile_block
        assert "��" not in latex
    finally:
        profile_file.write_text(original_profile, encoding="utf-8")
        if original_output is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_output, encoding="utf-8")


def test_publications_abbreviate_and_bold_scott_name():
    output_file = ROOT / "cv" / "cv.tex"
    original_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None

    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")

        assert "\\textbf{Love SA}" in latex
        assert "\\textbf{Scott A. Love}" not in latex
        assert "\\textbf{Scott A Love}" not in latex
    finally:
        if original_output is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_output, encoding="utf-8")


def test_publications_render_other_and_preprints_with_dedup_doi_and_italics():
    output_file = ROOT / "cv" / "cv.tex"
    publications_file = ROOT / "data" / "publications.json"
    original_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    original_publications = publications_file.read_text(encoding="utf-8")

    test_publications = [
        {
            "hal_id": "hal-journal",
            "category": "Journal article",
            "authors": ["Scott A. Love"],
            "title": "Peer reviewed article",
            "year": 2026,
            "journal": "Test Journal",
            "doi": None,
        },
        {
            "hal_id": "hal-report",
            "category": "Report",
            "authors": ["Scott A. Love"],
            "title": "Report entry",
            "year": 2025,
        },
        {
            "hal_id": "hal-book",
            "category": "Book chapter",
            "authors": ["Scott A. Love"],
            "title": "Book chapter entry",
            "year": 2025,
            "book_title": "Collected Works",
        },
        {
            "hal_id": "hal-other",
            "category": "Other scientific contribution",
            "authors": ["Scott A. Love", "Marie Curie"],
            "title": "Published contribution",
            "year": 2024,
            "doi": "10.1000/other",
        },
        {
            "hal_id": "hal-preprint-duplicate",
            "category": "Preprint",
            "authors": ["Scott A Love", "Marie Curie"],
            "title": "Published contribution",
            "year": 2027,
            "doi": "10.1000/preprint-duplicate",
        },
        {
            "hal_id": "hal-preprint-unique",
            "category": "Preprint",
            "authors": ["Scott A. Love", "Jane Doe"],
            "title": "Standalone preprint",
            "year": 2027,
            "doi": "10.1000/preprint-unique",
        },
        {
            "hal_id": "hal-journal-cyto",
            "category": "Journal article",
            "authors": [
                "Camille Pluchot",
                "Mélody Morisse",
                "Maryse Meurisse",
                "Jean-Marie Graïc",
                "Elodie Chaillou",
                "Scott A. Love",
            ],
            "title": "Cytoarchitecture and myeloarchitecture of the sheep auditory cortex",
            "year": 2025,
            "journal": "Journal of Anatomy",
            "doi": "10.1111/joa.70072",
        },
        {
            "hal_id": "hal-legacy-preprint-duplicate",
            "hal_type": "UNDEFINED",
            "category": "Other scientific contribution",
            "authors": ["Scott A Love", "Marie Curie"],
            "title": "Published contribution",
            "year": 2022,
            "doi": "10.5281/zenodo.10000001",
        },
        {
            "hal_id": "hal-legacy-preprint-cyto-duplicate",
            "hal_type": "UNDEFINED",
            "category": "Other scientific contribution",
            "authors": [
                "Camille Pluchot",
                "Mélody Morisse",
                "Maryse Meurisse",
                "Jean-Marie Graïc",
                "Elodie Chaillou",
                "Scott A. Love",
            ],
            "title": "Cytoarchitecture and Myeloarchitecture of the sheep (Ovis aries) auditory cortex",
            "year": 2025,
            "doi": "10.5281/zenodo.14824490",
        },
        {
            "hal_id": "hal-legacy-preprint-unique",
            "hal_type": "UNDEFINED",
            "category": "Other scientific contribution",
            "authors": ["Scott A. Love", "Jane Roe"],
            "title": "Legacy standalone preprint",
            "year": 2021,
            "doi": "10.5281/zenodo.10000002",
        },
    ]

    try:
        publications_file.write_text(
            json.dumps(test_publications, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        latex = output_file.read_text(encoding="utf-8")

        assert "\\subsection{Journal Articles (2)}" in latex
        assert "\\subsection{Book Chapters (1)}" in latex
        assert "\\subsection{Other Scientific Contributions (1)}" in latex
        assert "\\subsection{Preprints (2)}" in latex
        assert "\\subsection{Reports" not in latex
        assert "Report entry" not in latex
        assert "Published contribution" in latex
        assert "\\textit{Published contribution}" in latex
        assert "\\textbf{Published contribution}" not in latex
        assert "10.1000/other" in latex
        assert "Standalone preprint" in latex
        assert "\\textit{Standalone preprint}" in latex
        assert "\\textbf{Standalone preprint}" not in latex
        assert "10.1000/preprint-unique" in latex
        assert "Legacy standalone preprint" in latex
        assert "10.5281/zenodo.10000002" in latex
        assert "10.1000/preprint-duplicate" not in latex
        assert "10.5281/zenodo.10000001" not in latex
        assert "10.5281/zenodo.14824490" not in latex
        assert latex.index("\\subsection{Book Chapters (1)}") < latex.index(
            "\\subsection{Preprints (2)}"
        )
        assert "Reports:" not in result.stdout
    finally:
        publications_file.write_text(original_publications, encoding="utf-8")
        if original_output is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_output, encoding="utf-8")


def test_funding_omit_coordinator_line_when_role_is_coordinator():
    output_file = ROOT / "cv" / "cv.tex"
    funding_file = ROOT / "data" / "funding.yml"

    original_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    original_funding = funding_file.read_text(encoding="utf-8")

    test_funding = [
        {
            "title": "Local Coordination Project",
            "funder": "Funder A",
            "start": 2024,
            "end": 2026,
            "role": "  LOCAL   coordinator  ",
            "coordinator": "C. Kemere",
        },
        {
            "title": "Main Coordination Project",
            "funder": "Funder B",
            "start": 2021,
            "end": 2024,
            "role": " Coordinator ",
            "coordinator": "Scott A. Love",
        },
        {
            "title": "Partner Project",
            "funder": "Funder C",
            "start": 2020,
            "end": 2021,
            "role": "Partner",
            "coordinator": "E. Chaillou",
        },
    ]

    try:
        funding_file.write_text(
            yaml.safe_dump(test_funding, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")

        assert "\\textbf{Role:} LOCAL coordinator" in latex
        assert "\\textbf{Role:} Coordinator" in latex
        assert "\\textbf{Role:} Partner" in latex
        assert "\\textbf{Coordinator:} E. Chaillou" in latex
        assert "Coordinator: C. Kemere" not in latex
        assert "Coordinator: Scott A. Love" not in latex
    finally:
        funding_file.write_text(original_funding, encoding="utf-8")
        if original_output is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_output, encoding="utf-8")


def test_employment_dates_use_readable_mixed_precision_formatting():
    output_file = ROOT / "cv" / "cv.tex"
    original_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None

    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")
        employment_start = latex.index("\\section{Professional Experience}")
        funding_start = latex.index("\\section{Funding}")
        employment_block = latex[employment_start:funding_start]

        assert "\\cventry{Nov~2017~--~Present}" in employment_block
        assert "\\cventry{Nov~2015~--~Aug~2017}" in employment_block
        assert "\\cventry{Apr~2015~--~Oct~2015}" in employment_block
        assert "\\cventry{2013~--~2015}" in employment_block
        assert "\\cventry{2011~--~2013}" in employment_block
        assert "2015-11 -- 2017-08" not in employment_block
        assert "2017-11 -- present" not in employment_block
    finally:
        if original_output is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_output, encoding="utf-8")


def test_supervision_uses_structured_layout_and_optional_fields():
    output_file = ROOT / "cv" / "cv.tex"
    supervision_file = ROOT / "data" / "supervision.yml"

    original_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    original_supervision = supervision_file.read_text(encoding="utf-8")

    test_supervision = [
        {
            "name": "Alice Example",
            "level": "PhD",
            "institution": "University of Tours",
            "start": "2024",
            "end": "present",
            "role": "Main supervisor",
            "topic": "Brain & behavior",
        },
        {
            "name": "Bob Example",
            "level": "Master 2",
            "institution": "University of Tours",
            "period": "2025",
        },
    ]

    try:
        supervision_file.write_text(
            yaml.safe_dump(test_supervision, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
            check=True,
            cwd=ROOT,
        )
        latex = output_file.read_text(encoding="utf-8")

        assert "\\cventry{2024 -- present}{Alice Example}{PhD}{University of Tours}{}{" in latex
        assert "\\item \\textbf{Role:} Main supervisor" in latex
        assert "\\item \\textbf{Topic:} Brain \\& behavior" in latex
        assert "\\cventry{2025}{Bob Example}{Master 2}{University of Tours}{}{" in latex
        supervision_start = latex.index("\\section{Supervision}")
        publications_start = latex.index("\\section{Publications}")
        supervision_block = latex[supervision_start:publications_start]
        assert supervision_block.count("\\textbf{Role:}") == 1
        assert supervision_block.count("\\textbf{Topic:}") == 1
    finally:
        supervision_file.write_text(original_supervision, encoding="utf-8")
        if original_output is None:
            output_file.unlink(missing_ok=True)
        else:
            output_file.write_text(original_output, encoding="utf-8")
