#!/bin/bash
# Quick update script - just fetch publications and rebuild LaTeX/PDF

set -e

echo "Updating CV..."
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../" && pwd)"
CD_DIR="$ROOT_DIR/cv"

echo "[1/3] Fetching publications from HAL..."
cd "$ROOT_DIR"
uv run python scripts/fetch_hal.py

echo ""
echo "[2/3] Generating LaTeX..."
uv run python scripts/generate_cv_latex.py

echo ""
echo "[3/3] Compiling PDF..."
cd "$CD_DIR"
pdflatex -interaction=nonstopmode -output-directory=. cv.tex

echo ""
echo "✓ CV updated!"
echo ""
