.PHONY: help sync fetch-publications generate-latex render clean

.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make sync                - Install Python dependencies"
	@echo "  make fetch-publications  - Fetch publications from HAL"
	@echo "  make generate-latex      - Generate LaTeX CV from data"
	@echo "  make render              - Compile LaTeX to PDF"
	@echo "  make build               - Full pipeline: sync, fetch, generate, render"
	@echo "  make clean               - Remove generated files"

sync:
	@echo "Installing Python dependencies..."
	uv sync

fetch-publications: sync
	@echo "Fetching publications from HAL..."
	uv run python scripts/fetch_hal.py

generate-latex: sync
	@echo "Generating LaTeX CV..."
	uv run python scripts/generate_cv_latex.py

render: generate-latex
	@echo "Compiling LaTeX to PDF..."
	cd cv && pdflatex -interaction=nonstopmode cv.tex && cd ..

build: sync fetch-publications render
	@echo "\n✓ CV build complete!"
	@echo "Output: cv/cv.pdf"

clean:
	@echo "Cleaning up generated files..."
	cd cv && rm -f *.aux *.log *.out *.pdf && cd ..
	@echo "Done.
