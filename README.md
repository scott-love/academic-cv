# academic-cv

A data-driven academic CV generator using **Quarto**, **Python**, and **HAL**.

The CV is built from structured data files (YAML and JSON) and automatically generates formatted PDF and HTML versions. Publications are retrieved from HAL and formatted automatically.

## Features

- Automatic retrieval of publications from HAL
- Structured CV sections stored separately from formatting:
  - Profile
  - Employment
  - Education
  - Teaching
  - Grants and funding
  - Languages
  - Honors and awards
  - Supervision
  - Publications
- Automatic formatting of:
  - Journal articles
  - Book chapters
  - Conference presentations
  - Reports
  - Other scientific contributions
- Highlighting of Scott A. Love in publication author lists
- Automatic sorting of publications by year
- Automatic counts for publication categories
- PDF and HTML rendering using Quarto

## Repository structure

    .
    ├── cv/
    │   └── cv.qmd
    │
    ├── data/
    │   ├── profile.yml
    │   ├── education.yml
    │   ├── employment.yml
    │   ├── teaching.yml
    │   ├── grants.yml
    │   ├── supervision.yml
    │   ├── languages.yml
    │   ├── honors_awards.yml
    │   └── publications.json
    │
    ├── scripts/
    │   └── fetch_hal.py
    │
    ├── outputs/
    │
    ├── _quarto.yml
    ├── pyproject.toml
    └── uv.lock

## Requirements

- Python 3.10+
- Quarto
- uv

## Setup

Install the Python dependencies:

    uv sync

## Update publications from HAL

Publications are retrieved using the HAL identifier configured in:

    scripts/fetch_hal.py

Run:

    uv run python scripts/fetch_hal.py

This updates:

    data/publications.json

## Render the CV

Render the complete Quarto project:

    quarto render

Render only the CV:

    quarto render cv/cv.qmd

Generated files are placed in:

    _site/

The CV is currently generated in both HTML and PDF formats.

## Preview locally

Preview the CV locally:

    quarto preview

## Editing the CV

Most CV content should be edited in:

    data/

The main data files are:

- `profile.yml` — personal information and research interests
- `education.yml` — education history
- `employment.yml` — employment history
- `teaching.yml` — teaching activities
- `grants.yml` — research funding
- `supervision.yml` — supervision activities
- `languages.yml` — languages
- `honors_awards.yml` — honors and awards
- `publications.json` — publications retrieved from HAL

The file:

    cv/cv.qmd

contains the rendering and formatting logic.

This separation means that CV information can generally be updated without changing the formatting code.

## Publications

Publications are retrieved from HAL and automatically divided into:

- Journal Articles
- Book Chapters
- Conference Presentations
  - Invited Talks
  - Oral Presentations
  - Posters
- Reports
- Other Scientific Contributions

Publications are sorted from newest to oldest, and the number of entries in each category is calculated automatically.

Conference presentations include:

- Conference name
- Dates
- Location
- Presentation type

when these details are available from HAL.

## Automated builds

A GitHub Actions workflow is included:

    .github/workflows/build.yml

The workflow can automatically:

1. Check out the repository
2. Set up Python
3. Install Quarto
4. Install dependencies
5. Retrieve publications from HAL
6. Render the CV
7. Deploy generated output

## Project philosophy

The CV content is kept separate from the presentation logic.

Structured data belongs in `data/`, publication retrieval is handled by `scripts/`, and formatting and rendering are handled by `cv/cv.qmd`.

This makes the CV easier to maintain and allows changes to individual sections without rewriting the document.