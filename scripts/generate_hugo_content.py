#!/usr/bin/env python3
"""Export canonical publication data as HugoBlox publication content bundles."""

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "publications.json"
DEFAULT_OUTPUT = ROOT / "build" / "hugo" / "content" / "en" / "publication"
DEFAULT_TYPE_MAP = ROOT / "scripts" / "publication_type_map.json"
MISSING_DATE = "1970-01-01T00:00:00Z"


@dataclass
class ExportReport:
    processed: int = 0
    written: int = 0
    excluded: int = 0
    excluded_by_category: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    planned_files: list[Path] = field(default_factory=list)


def load_type_map(path: Path) -> dict[str, list[str]]:
    """Load and validate source-category to HugoBlox publication type mappings."""
    try:
        with path.open(encoding="utf-8") as file:
            mapping = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not load type mapping from {path}: {error}") from error

    if not isinstance(mapping, dict) or not all(
        isinstance(category, str)
        and isinstance(types, list)
        and types
        and all(isinstance(value, str) and value.strip() for value in types)
        for category, types in mapping.items()
    ):
        raise ValueError("Type mapping must be an object of categories to non-empty string lists.")

    return mapping


def _non_empty_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _publication_date(record: dict[str, Any], label: str, report: ExportReport) -> str:
    conference_start = _non_empty_string(record.get("conference_start"))
    if conference_start:
        try:
            if len(conference_start) == 4 and conference_start.isdigit():
                date = datetime(int(conference_start), 1, 1, tzinfo=timezone.utc)
            else:
                date = datetime.fromisoformat(conference_start.replace("Z", "+00:00"))
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                else:
                    date = date.astimezone(timezone.utc)
            return (
                f"{date.year:04d}-{date.month:02d}-{date.day:02d}T"
                f"{date.hour:02d}:{date.minute:02d}:{date.second:02d}Z"
            )
        except ValueError:
            report.warnings.append(
                f"{label}: malformed conference_start {conference_start!r}; using year fallback."
            )

    year = record.get("year")
    try:
        year_number = int(year)
        if isinstance(year, bool) or not 1 <= year_number <= 9999:
            raise ValueError
    except (TypeError, ValueError):
        report.warnings.append(
            f"{label}: missing or invalid year and conference_start; "
            f"using placeholder date {MISSING_DATE}."
        )
        return MISSING_DATE

    # HAL usually supplies only a year; represent it deterministically as January 1 at UTC midnight.
    report.warnings.append(
        f"{label}: using January 1 00:00:00 UTC as the date fallback for year {year_number}."
    )
    return f"{year_number:04d}-01-01T00:00:00Z"


def _front_matter(
    record: dict[str, Any],
    hal_id: str,
    type_map: dict[str, list[str]],
    report: ExportReport,
    index: int,
) -> dict[str, Any]:
    label = f"Record {index} ({hal_id})"
    front_matter: dict[str, Any] = {"title": record["title"]}

    authors = record.get("authors")
    if isinstance(authors, str):
        authors = [authors]
    if isinstance(authors, list):
        authors = [author.strip() for author in authors if _non_empty_string(author)]
        if authors:
            front_matter["authors"] = authors

    front_matter["date"] = _publication_date(record, label, report)

    category = _non_empty_string(record.get("category"))
    if category in type_map:
        front_matter["publication_types"] = type_map[category]
    else:
        report.warnings.append(
            f"{label}: unknown publication category {category!r}; using ['misc']."
        )
        front_matter["publication_types"] = ["misc"]

    publication = next(
        (
            value
            for field_name in ("journal", "conference", "book_title")
            if (value := _non_empty_string(record.get(field_name)))
        ),
        None,
    )
    if publication:
        front_matter["publication"] = publication

    identifiers = {"hal": hal_id}
    doi = _non_empty_string(record.get("doi"))
    if doi:
        identifiers["doi"] = doi
    front_matter["hugoblox"] = {"ids": identifiers}

    hal_url = _non_empty_string(record.get("hal_url"))
    if hal_url:
        front_matter["links"] = [{"type": "url", "url": hal_url}]

    return front_matter


def generate_hugo_content(
    records: list[Any],
    output_dir: Path,
    type_map: dict[str, list[str]],
    *,
    dry_run: bool = False,
) -> ExportReport:
    """Validate records, then write one YAML-front-matter bundle per valid publication."""
    report = ExportReport(processed=len(records))
    prepared: list[tuple[Path, str]] = []
    seen_ids: set[str] = set()

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            report.errors.append(f"Record {index}: expected an object; skipped.")
            continue

        title = _non_empty_string(record.get("title"))
        hal_id = _non_empty_string(record.get("hal_id"))
        valid = True
        if not title:
            report.errors.append(f"Record {index}: missing non-empty title; skipped.")
            valid = False
        if not hal_id:
            report.errors.append(f"Record {index}: missing non-empty hal_id; skipped.")
            valid = False
        elif hal_id in seen_ids:
            report.errors.append(f"Record {index} ({hal_id}): duplicate hal_id; skipped.")
            valid = False
        else:
            seen_ids.add(hal_id)

        if hal_id and ("/" in hal_id or "\\" in hal_id or hal_id in {".", ".."}):
            report.errors.append(f"Record {index} ({hal_id}): unsafe hal_id path; skipped.")
            valid = False

        if not valid:
            continue

        category = record.get("category")
        if category != "Journal article":
            report.excluded += 1
            category_label = (
                category.strip() if isinstance(category, str) and category.strip() else "(missing)"
            )
            report.excluded_by_category[category_label] = (
                report.excluded_by_category.get(category_label, 0) + 1
            )
            continue

        record = {**record, "title": title}
        front_matter = _front_matter(record, hal_id, type_map, report, index)
        yaml_text = yaml.safe_dump(
            front_matter,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=1000,
        )
        bundle_file = output_dir / hal_id / "index.md"
        report.planned_files.append(bundle_file)
        prepared.append((bundle_file, f"---\n{yaml_text}---\n"))

    if not dry_run:
        for bundle_file, content in prepared:
            bundle_file.parent.mkdir(parents=True, exist_ok=True)
            bundle_file.write_text(content, encoding="utf-8")
        report.written = len(prepared)

    return report


def _print_report(report: ExportReport, *, dry_run: bool) -> None:
    print(f"Records processed: {report.processed}")
    print(f"Bundles written: {report.written}")
    print(f"Records excluded: {report.excluded}")
    print("Excluded by category:")
    if report.excluded_by_category:
        for category, count in sorted(report.excluded_by_category.items()):
            print(f"  {category}: {count}")
    else:
        print("  (none)")
    if dry_run:
        print(f"Bundles that would be written: {len(report.planned_files)}")
        for path in report.planned_files:
            print(f"  {path}")
    print(f"Warnings: {len(report.warnings)}")
    for warning in report.warnings:
        print(f"  WARNING: {warning}")
    print(f"Errors: {len(report.errors)}")
    for error in report.errors:
        print(f"  ERROR: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--type-map", type=Path, default=DEFAULT_TYPE_MAP)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        with args.input.open(encoding="utf-8") as file:
            records = json.load(file)
        if not isinstance(records, list):
            raise ValueError("Input JSON must contain a list of publication records.")
        type_map = load_type_map(args.type_map)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Fatal error: {error}")
        return 2

    report = generate_hugo_content(
        records,
        args.output,
        type_map,
        dry_run=args.dry_run,
    )
    _print_report(report, dry_run=args.dry_run)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
