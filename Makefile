.PHONY: help sync fetch-publications generate-latex render render-short render-all build build-all clean

.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make sync                - Install Python dependencies"
	@echo "  make fetch-publications  - Fetch publications from HAL"
	@echo "  make generate-latex      - Generate LaTeX CV from data"
	@echo "  make render              - Compile LaTeX to PDF with xelatex"
	@echo "  make render-short        - Compile the short LaTeX CV to PDF"
	@echo "  make render-all          - Compile both LaTeX CV PDFs"
	@echo "  make build               - Full pipeline: sync, fetch, generate, render"
	@echo "  make build-all           - Full pipeline: sync, fetch, generate, render both PDFs"
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
	cd cv && xelatex -interaction=nonstopmode cv.tex && cd ..

render-short: generate-latex
	@echo "Compiling short LaTeX CV to PDF..."
	cd cv && xelatex -interaction=nonstopmode cv_short.tex && cd ..

render-all: generate-latex
	@echo "Compiling both LaTeX CV PDFs..."
	cd cv && xelatex -interaction=nonstopmode cv.tex && xelatex -interaction=nonstopmode cv_short.tex && cd ..

build: sync fetch-publications render
	@echo "\n✓ CV build complete!"
	@echo "Output: cv/cv.pdf"

build-all: sync fetch-publications render-all
	@echo "\n✓ CV builds complete!"
	@echo "Outputs: cv/cv.pdf, cv/cv_short.pdf"

clean:
	@echo "Cleaning up generated files..."
	cd cv && rm -f *.aux *.log *.out *.pdf && cd ..
	@echo "Done."
