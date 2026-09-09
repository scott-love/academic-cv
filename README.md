# academic-cv

A data-driven academic CV generator built around:

`data/` → Python scripts → `cv/cv.tex` / `cv/cv_short.tex` → `cv/cv.pdf` / `cv/cv_short.pdf`

Publications are refreshed from HAL, the CV content is assembled into ModernCV-flavored LaTeX, and the final outputs are full and short CV PDFs.

## Architecture

- `data/` stores structured CV content in YAML and JSON.
- `scripts/fetch_hal.py` refreshes publications from HAL into `data/publications.json`.
- `scripts/generate_cv_latex.py` reads the data files and generates `cv/cv.tex` and `cv/cv_short.tex` (build artifacts, not tracked in git).
- `cv/moderncv/` provides the ModernCV LaTeX class assets used to compile `cv/cv.pdf` and `cv/cv_short.pdf`.

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/)
- TeX Live with `xelatex` available on `PATH`
  - On Debian/Ubuntu, the GitHub workflow installs:
    - `texlive-latex-base`
    - `texlive-latex-extra`
    - `texlive-fonts-extra`
    - `texlive-xetex`

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
- `make generate-latex` — regenerate `cv/cv.tex` and `cv/cv_short.tex`
- `make render` — compile `cv/cv.tex` to `cv/cv.pdf` with `xelatex`
- `make render-short` — compile `cv/cv_short.tex` to `cv/cv_short.pdf`
- `make render-all` — compile both LaTeX outputs to PDFs
- `make build` — run the full pipeline
- `make build-all` — run the full pipeline and compile both PDFs
- `make clean` — remove generated LaTeX build artifacts and PDF output

Optional helper wrappers are also available in `scripts/build_cv.sh` and `scripts/update_cv.sh`; both now compile the full and short CV PDFs.

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

For CI resilience, `scripts/fetch_hal.py` retries transient HAL request failures
with exponential backoff. If HAL remains unavailable but an existing
`data/publications.json` cache is readable, the script keeps that cache and exits
successfully so CV generation can continue. It only exits non-zero when HAL
fetching fails and no readable local cache is available.

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
4. Installs TeX Live / `xelatex`
5. Runs `uv sync`
6. Refreshes HAL publications
7. Regenerates `cv/cv.tex` and `cv/cv_short.tex`
8. Compiles the PDF outputs
9. Commits `data/publications.json` back to `main` if the HAL refresh changed it
10. Uploads the generated CV PDFs as artifacts

If LaTeX compilation fails, the workflow also uploads `cv/cv.log` for debugging.
If the HAL API is unreachable, `scripts/fetch_hal.py` keeps the existing
`data/publications.json` cache and no publication refresh commit is created.

### Publishing a GitHub Release

The workflow also creates a GitHub Release after each successful non-PR run on
`main` and after each successful manual dispatch. The release job automatically
creates a date-based tag for that run and attaches the generated CV PDFs as
release assets.

**Automatic tag format:** `YYYY-MM-DD` with an optional same-day suffix when
multiple releases are created on the same day.

| Tag | When to use |
|-----|-------------|
| `2026-08-13` | First release created on a given day |
| `2026-08-13.1` | Second release created on the same day |
| `2026-08-13.2` | Third release created on the same day |

**How to trigger a release:**

- Push a qualifying change to `main`, or
- Run the `Build CV` workflow manually from GitHub Actions.

Each qualifying run produces its own independent GitHub Release entry with
`cv.pdf` and `cv_short.pdf` attached. The artifact upload (for CI inspection) is
preserved for every build, and the workflow manages the release tag creation
automatically.

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── build-cv.yml
├── cv/
│   ├── moderncv/
│   └── pictures/
│       └── scott.jpg
├── data/
│   ├── education.yml
│   ├── employment.yml
│   ├── funding.yml
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

Regenerate the LaTeX sources before compiling if you have changed data:

```bash
make generate-latex
```

Compile locally and inspect the logs:

```bash
cd cv
xelatex -interaction=nonstopmode -halt-on-error -output-directory=. cv.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=. cv_short.tex
```

Common checks:

- Review `cv/cv.log` for the first LaTeX error.
- Confirm `xelatex` is installed and on `PATH`.
- Re-run `make fetch-publications` if `data/publications.json` is stale.
- Check the GitHub Actions log for the `Fetch publications from HAL` step if the
  cache is not refreshing; the build currently talks to the official HAL API at
  `https://api.archives-ouvertes.fr/search/` and will reuse the existing cache on
  repeated connection failures.
- Verify edits in `data/` remain valid YAML/JSON before regenerating the LaTeX file.
