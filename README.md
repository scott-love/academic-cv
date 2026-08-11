# academic-cv

Automatically generate an academic CV and publication website from HAL.

## Setup

Create environment:

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Fetch publications:

```bash
python scripts/fetch_hal.py
```

Render website:

```bash
quarto render
```

Serve locally:

```bash
quarto preview
```