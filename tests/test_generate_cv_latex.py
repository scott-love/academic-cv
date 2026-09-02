import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parents[1]


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
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def test_generator_emits_clickable_profile_links_in_extrainfo():
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
            expected_parts.append(f"\\href{{{url}}}{{{escape_latex(f'ORCID: {orcid}')}}}")

        hal = str(profile.get("hal", "")).strip()
        if hal:
            url = escape_latex_url(f"https://hal.science/{quote(hal, safe='')}")
            expected_parts.append(f"\\href{{{url}}}{{{escape_latex(f'HAL: {hal}')}}}")

        github = str(profile.get("github", "")).strip()
        if github:
            url = escape_latex_url(f"https://github.com/{quote(github, safe='')}")
            expected_parts.append(f"\\href{{{url}}}{{{escape_latex(f'GitHub: {github}')}}}")

        homepage = str(profile.get("homepage", "")).strip()
        if homepage:
            homepage_url = (
                homepage if homepage.startswith(("http://", "https://")) else f"https://{homepage}"
            )
            expected_parts.append(
                f"\\href{{{escape_latex_url(homepage_url)}}}{{{escape_latex(homepage)}}}"
            )

        if expected_parts:
            assert "\\extrainfo{" in latex
            for part in expected_parts:
                assert part in latex
        else:
            assert "\\extrainfo{" not in latex
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
