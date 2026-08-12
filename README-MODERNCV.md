# ModernCV Migration Guide

This document describes the new ModernCV-based CV generation system.

## Architecture

The project maintains the **data-driven philosophy** while migrating to ModernCV styling:

- **Data Layer**: YAML/JSON files in `data/` directory (unchanged)
- **Generation Layer**: Python scripts that convert data to LaTeX
- **Rendering Layer**: ModernCV LaTeX template with pdflatex compilation

```
data/                          # Structured CV content
├── profile.yml
├── education.yml
├── employment.yml
├── teaching.yml
├── grants.yml
├── supervision.yml
├── languages.yml
├── honors_awards.yml
└── publications.json           # Fetched from HAL

scripts/
├── fetch_hal.py               # HAL publication fetching (unchanged)
└── generate_cv_latex.py        # NEW: Generates LaTeX from data

cv/
├── cv.tex                      # ModernCV template
├── moderncv/                   # ModernCV class files
│   ├── moderncv.cls
│   ├── moderncvstyle*.sty
│   └── moderncvcolor*.sty
└── cv.pdf                      # Generated PDF output
```

## Build Pipeline

### Quick Build

```bash
make build
```

This runs the full pipeline:
1. Install dependencies (`uv sync`)
2. Fetch publications from HAL
3. Generate LaTeX from data
4. Compile LaTeX to PDF

### Partial Builds

```bash
# Just install dependencies
make sync

# Fetch publications only
make fetch-publications

# Generate LaTeX only (don't compile)
make generate-latex

# Render PDF (assumes LaTeX already generated)
make render

# Clean generated files
make clean
```

### Using Scripts

```bash
# Full build
scripts/build_cv.sh

# Quick update (fetch + generate + render)
scripts/update_cv.sh
```

## Python Generation Script

The `scripts/generate_cv_latex.py` script:

1. **Loads data** from all YAML/JSON files
2. **Applies formatting logic**:
   - Categorizes publications by type
   - Highlights Scott A. Love in author lists
   - Abbreviates other authors (surname + initials)
   - Sorts publications by year (newest first)
   - Formats dates and references
3. **Generates LaTeX** using ModernCV commands:
   - `\cventry{}` for jobs/degrees
   - `\cvitem{}` for publications and details
   - `\section{}` for section headings
   - `\subsection{}` for categories
4. **Outputs** to `cv/cv.tex`

## Customization

### Styling

Modify `cv/cv.tex` preamble to change appearance:

```latex
% Change style: 'casual', 'classic', 'oldstyle', 'banking'
\moderncvstyle{casual}

% Change color: 'blue', 'orange', 'green', 'red', 'purple', 'grey', 'black'
\moderncvcolor{blue}
```

### Content Order

The Python script generates sections in this order:
1. Personal information (from `profile.yml`)
2. Education (from `education.yml`)
3. Employment (from `employment.yml`)
4. Publications (from `publications.json`)

To reorder, modify `CVGenerator.generate_latex()` in `scripts/generate_cv_latex.py`.

### Adding Sections

Add new data files (e.g., `data/skills.yml`) and modify `generate_cv_latex.py` to include new sections.

## Comparison with Quarto Approach

| Aspect | Quarto (old) | Python + ModernCV (new) |
|--------|--------------|------------------------| 
| Template Language | Quarto/Python mix | Pure LaTeX |
| Data Format | YAML/JSON | YAML/JSON (same) |
| Output Formats | PDF + HTML | PDF (focus on PDF) |
| Dependencies | Quarto + Python | Python + pdflatex |
| Build Speed | Slower | Faster |
| Styling Flexibility | High (multiple themes) | High (ModernCV themes) |
| Version Control | Better (pure LaTeX) | Better (pure LaTeX) |

## Migration Notes

- The old Quarto files (`cv/cv.qmd`, `_quarto.yml`) are no longer used
- All data files remain compatible
- The `fetch_hal.py` script is unchanged
- GitHub Actions workflow updated to use new build process
- See `Makefile` for all available commands

## Dependencies

- **Python 3.10+**
- **pdflatex** (from TeX Live)
- **Python packages**: `pyyaml`, `requests` (see `pyproject.toml`)

## Troubleshooting

### PDF doesn't compile

```bash
# Check for LaTeX errors
cd cv
pdflatex -interaction=nonstopmode cv.tex
```

### Publications not showing up

```bash
# Re-fetch from HAL
make fetch-publications

# Then rebuild
make render
```

### LaTeX encoding issues

The script uses UTF-8 encoding. If you see character issues:
1. Ensure your data files are UTF-8 encoded
2. Check `data/publications.json` for special characters

## Future Improvements

- [ ] Add support for more publication fields (DOI links, URLs)
- [ ] Support for CV photo
- [ ] Additional sections (awards, skills, languages)
- [ ] LaTeX to HTML conversion for web display
- [ ] Incremental builds (only update changed sections)
