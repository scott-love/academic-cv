import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generator_emits_clickable_profile_links_in_extrainfo():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_cv_latex.py")],
        check=True,
        cwd=ROOT,
    )

    latex = (ROOT / "cv" / "cv.tex").read_text(encoding="utf-8")

    expected = (
        r"\extrainfo{\href{https://orcid.org/0000-0001-7416-9210}{ORCID: 0000-0001-7416-9210}"
        r"\enspace\textbar\enspace"
        r"\href{https://hal.science/scott-love}{HAL: scott-love}"
        r"\enspace\textbar\enspace"
        r"\href{https://github.com/scott-love}{GitHub: scott-love}"
        r"\enspace\textbar\enspace"
        r"\href{https://scott-love.github.io}{scott-love.github.io}}"
    )

    assert expected in latex
