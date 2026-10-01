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
- date/year handling fields (s- date/year handling fields (s- date/year n - date/year handling 
## ## ## ## ## ## #- `doi`
## ## rnal`
- `booktitle`
- `volume`
- `issue`
- `pages`
- `abstract`
- `publisher`
- other bibliographic fields supported by exporter

## Null/empty handling
- Optional scalar fields:
  - Prefe  - Prefe  - Prefe  - Prefe  - Prefe  - Prefe  - Prefe  - Prefe  - Prefe  - Prefe  - Pref
---------tri--------ld not be emitted; normalize to omitted or `n---------tri--------ld noors---------tri----pt---------tri--------ld not be emitted; normalize to omitted or `n---------tri--------:
                              no lin                              no lin                              no lin           DD`.                           but year is known, emit `year` as integer.
- If - If - If - If - If - If - If - If - If - If - If - If - If - If - If - Ifsing/partial date inputs.

## Publication type/category mapping
The The The The Thmap sThe The The The Thmap sTh to stable output values in `publication_type` (and `category` if used).  
Any mapping changes are considered contract changes and Any mapping changes arVersiAny maphis cAny mappin froAny mapp1:
Any mgo-exAny mgchemAny mg
- mach- mach- able s- mach- mach- able s- mach- mach- able s- macion = "- mach- mach- able s-reaking changes require a new schema version.
