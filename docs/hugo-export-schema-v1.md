# Hugo Export Schema v1

hugo-export-schema: v1

## Purpose
Defines the canonical export contract for publication bundles produced by `academic-cv` and consumed by `scott-love.github.io`.

## Ownership model

### Canonical (academic-cv-owned)
These fields are authoritative from the exporter and should be treated as source-of-truth:
- `hal_id`
- `title`
- `authors`
- publication date/year fields
- publication type/category
- canonical links
- core bibliographic metadata (journal/booktitle/volume/issue/pages/doi, when present)

### Website-owned editorial fields
These are managed in website content and should not be overwritten by exporter output:
- local display/editorial overrides
- manually curated presentation fields
- site-specific annotations/tags not part of canonical publication metadata

## Required fields
- `hal_id` (string; stable unique identifier)
- `title` (string)
- `authors` (non-empty array)
- `publication_type` (string)
- date/year handling fields (s- date/year handling fields (s- date/year n - date/year handling f## - date/year handling i`
- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- date/yal`- d
## N## N## N## N## N#g
-------------------------------refe-------------------------------refe-------------------------------refe----------------ts.
- Empty strings should not be emit- Empty strings should not be`n- Empty strings should thors` must be non-empt- Empty strings should not be emit- Empty strings should not be`n- Empty strings scts:
  - `links` may be omitted if no links are available.

## Date policy
- If full date is known, emit `date` as `YYYY-MM-DD` - If full date is known, emit `dafor- If full date is known, emit `datt yea- If full date is known, emit `date` as `YYYY-MM-DD` - If full date is xport - If full datebe de- If full date is known, emit `date` as `YY.

## Publication type## Publication type## Publiter## Publication type## Publicegories to stable output values in `publication_type`.
Mapping changes are contract changes and must be reviewed.

## Version## Version## Version## Version## Version## Version## Version## Version## Version## Version## Version## Version## Version## Version = "v1"` when emitted.

Breaking changes require a new schema version.
