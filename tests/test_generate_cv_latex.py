import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def escape_latex(text):
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

    result = str(text).replace("\\", r"\textbackslash{}")
    for char, replacement in list(replacements.items())[1:]:
        result = result.replace(char, replacement)
    return result


def escape_latex_url(url):
    return (
        str(url)
        .replace("%", r"\%")
        .replace("\\", r"\%5C")
        .replace("#", r"\#")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace(" ", "%20")
    )


def test_generator_emits_clickable_profile_links_in_extrainfo():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
        check=True,
        cwd=ROOT,
    )

    latex = (ROOT / "cv" / "cv.tex").read_text(encoding="utf-8")

    profile = yaml.safe_load((ROOT / "data" / "profile.yml").read_text(encoding="utf-8")) or {}

    expected_parts = []

    orcid = str(profile.get("orcid", "")).strip()
    if orcid:
        url = escape_latex_url(f"https://orcid.org/{orcid}")
        expected_parts.append(f"\\href{{{url}}}{{ORCID: {orcid}}}")

    hal = str(profile.get("hal", "")).strip()
    if hal:
        url = escape_latex_url(f"https://hal.science/{hal}")
        expected_parts.append(f"\\href{{{url}}}{{HAL: {hal}}}")

    github = str(profile.get("github", "")).strip()
    if github:
        url = escape_latex_url(f"https://github.com/{github}")
        expected_parts.append(f"\\href{{{url}}}{{GitHub: {github}}}")

    homepage = str(profile.get("homepage", "")).strip()
    if homepage:
        homepage_url = homepage if homepage.startswith(("http://", "https://")) else f"https://{homepage}"
        expected_parts.append(
            f"\\href{{{escape_latex_url(homepage_url)}}}{{{escape_latex(homepage)}}}"
        )

    if expected_parts:
        assert "\\extrainfo{" in latex
        for part in expected_parts:
            assert part in latex
    else:
        assert "\\extrainfo{" not in latex
