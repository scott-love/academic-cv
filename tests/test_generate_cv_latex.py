import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


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
        expected_parts.append(f"\\href{{https://orcid.org/{orcid}}}{{ORCID: {orcid}}}")

    hal = str(profile.get("hal", "")).strip()
    if hal:
        expected_parts.append(f"\\href{{https://hal.science/{hal}}}{{HAL: {hal}}}")

    github = str(profile.get("github", "")).strip()
    if github:
        expected_parts.append(f"\\href{{https://github.com/{github}}}{{GitHub: {github}}}")

    homepage = str(profile.get("homepage", "")).strip()
    if homepage:
        homepage_url = homepage if homepage.startswith(("http://", "https://")) else f"https://{homepage}"
        expected_parts.append(f"\\href{{{homepage_url}}}{{{homepage}}}")

    if expected_parts:
        assert "\\extrainfo{" in latex
        for part in expected_parts:
            assert part in latex
    else:
        assert "\\extrainfo{" not in latex
