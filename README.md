# academic-cv

A data-driven academic CV generator built around:

`data/` → Python scripts → `cv/cv.tex` → `cv/cv.pdf`

Publications are refreshed from HAL, the CV content is assembled into ModernCV-flavored LaTeX, and the final output is a PDF.

## Architecture

- `data/` stores structured CV content in YAML and JSON.
- `scripts/fetch_hal.py` refreshes publications from HAL into `data/publications.json`.
- `scripts/generate_cv_latex.py` reads the data files and generates `cv/cv.tex`.
- `cv/moderncv/` provides the ModernCV LaTeX class assets used to compile `cv/cv.pdf`.

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/)
- TeX Live with `pdflatex` available on `PATH`
  - On Debian/Ubuntu, the GitHub workflow installs:
    - `texlive-latex-base`
    - `texlive-latex-extra`
    - `texlive-fonts-extra`

## Local build

Install Python dependencies:

```bash
make sync
```

Run the full supported pipeline:

```bash
make build
```

Available Makefile targets:

- `make sync` — install Python dependencies with `uv sync`
- `make fetch-publications` — refresh `data/publications.json` from HAL
- `make generate-latex` — regenerate `cv/cv.tex`
- `make render` — compile `cv/cv.tex` to `cv/cv.pdf`
- `make build` — run the full pipeline
- `make clean` — remove generated LaTeX build artifacts and PDF output

Optional helper wrappers are also available in `scripts/build_cv.sh` and `scripts/update_cv.sh`.

## Refresh HAL publications

The HAL identifier is read from `data/profile.yml`.

To refresh publications only:

```bash
make fetch-publications
```

Or run the underlying command directly:

```bash
uv run python scripts/fetch_hal.py
```

## GitHub Actions

The only supported CI workflow is:

```text
.github/workflows/build-cv.yml
```

It runs on manual dispatch and on pushes to `main` that change files under:

- `data/**`
- `scripts/**`
- `cv/**`

The workflow:

1. Checks out the repository
2. Sets up Python 3.10
3. Installs `uv`
4. Installs TeX Live / `pdflatex`
5. Runs `uv sync`
6. Refreshes HAL publications
7. Regenerates `cv/cv.tex`
8. Compiles `cv/cv.pdf`
9. Uploads `cv/cv.pdf` as an artifact

If LaTeX compilation fails, the workflow also uploads `cv/cv.log` for debugging.

### Publishing a GitHub Release

The workflow also creates a GitHub Release and attaches `cv/cv.pdf` as a release
asset whenever you push a date-based tag.

**Supported tag format:** `YYYY-MM-DD` with an optional same-day suffix.

| Tag | When to use |
|-----|-------------|
| `2026-08-13` | First release on a given day |
| `2026-08-13.1` | Second release on the same day |
| `2026-08-13.2` | Third release on the same day |
| `2026-08-13-a` | Alternative suffix style |

**Create a release:**

```bash
git tag 2026-08-13
git push origin 2026-08-13
```

**Create a second release on the same day:**

```bash
git tag 2026-08-13.1
git push origin 2026-08-13.1
```

Each tag produces its own independent GitHub Release entry with `cv.pdf` attached.
The artifact upload (for CI inspection) is preserved for every build regardless of
whether a tag was pushed.

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── build-cv.yml
├── cv/
│   ├── cv.tex
│   └── moderncv/
├── data/
│   ├── education.yml
│   ├── employment.yml
│   ├── grants.yml
│   ├── honors_awards.yml
│   ├── languages.yml
│   ├── profile.yml
│   ├── publications.json
│   ├── supervision.yml
│   └── teaching.yml
├── scripts/
│   ├── build_cv.sh
│   ├── fetch_hal.py
│   ├── generate_cv_latex.py
│   └── update_cv.sh
├── Makefile
├── pyproject.toml
└── uv.lock
```

## Troubleshooting

Regenerate the LaTeX source before compiling if you have changed data:

```bash
make generate-latex
```

Compile locally and inspect the log:

```bash
cd cv
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=. cv.tex
```

Common checks:

- Review `cv/cv.log` for the first LaTeX error.
- Confirm `pdflatex` is installed and on `PATH`.
- Re-run `make fetch-publications` if `data/publications.json` is stale.
- Verify edits in `data/` remain valid YAML/JSON before regenerating the LaTeX file.
