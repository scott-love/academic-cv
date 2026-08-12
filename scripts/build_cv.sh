#!/bin/bash
# Build script for CV using ModernCV

set -e  # Exit on error

echo "================================================"
echo "Academic CV Builder (ModernCV)"
echo "================================================"
echo ""

# Get the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../" && pwd)"
CD_DIR="$ROOT_DIR/cv"

echo "[1/4] Installing dependencies..."
cd "$ROOT_DIR"
uv sync

echo ""
echo "[2/4] Fetching publications from HAL..."
uv run python scripts/fetch_hal.py

echo ""
echo "[3/4] Generating LaTeX CV from data..."
uv run python scripts/generate_cv_latex.py

echo ""
echo "[4/4] Compiling LaTeX to PDF..."
cd "$CD_DIR"

# Run pdflatex with nonstopmode to compile even if there are errors
pdflatex -interaction=nonstopmode -output-directory=. cv.tex

echo ""
echo "================================================"
echo "✓ Build complete!"
echo "================================================"
echo ""
echo "Output: cv/cv.pdf"
echo ""
