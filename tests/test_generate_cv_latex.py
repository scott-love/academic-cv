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
    for char, replacement in replacements.items():
        if char == "\\":
            continue
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
            url = escape_latex_url(f"https://orcid.org/{orcid}")
            expected_parts.append(f"\\href{{{url}}}{{{escape_latex(f'ORCID: {orcid}')}}}")

        hal = str(profile.get("hal", "")).strip()
        if hal:
            url = escape_latex_url(f"https://hal.science/{hal}")
            expected_parts.append(f"\\href{{{url}}}{{{escape_latex(f'HAL: {hal}')}}}")

        github = str(profile.get("github", "")).strip()
        if github:
            url = escape_latex_url(f"https://github.com/{github}")
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
