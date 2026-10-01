import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPORTER_PATH = ROOT / "scripts" / "generate_hugo_content.py"


def load_exporter_module():
    spec = importlib.util.spec_from_file_location("generate_hugo_content_module", EXPORTER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def type_map():
    return {
        "Journal article": ["article-journal"],
        "Conference presentation": ["paper-conference"],
    }


@pytest.fixture
def publication_factory():
    def make_publication(**overrides):
        publication = {
            "hal_id": "hal-123",
            "title": "A publication",
            "authors": ["A. Author"],
            "year": 2024,
            "category": "Journal article",
            "journal": "Example Journal",
            "doi": "10.1234/example",
            "hal_url": "https://hal.example/hal-123",
        }
        publication.update(overrides)
        return publication

    return make_publication


def read_front_matter(path):
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    front_matter = content.split("---", 2)[1]
    assert content.endswith("---\n")
    return yaml.safe_load(front_matter)


def test_generates_publication_bundles_and_collects_validation_results(
    tmp_path, type_map, publication_factory
):
    exporter = load_exporter_module()
    records = [
        publication_factory(),
        publication_factory(
            hal_id="hal-no-doi",
            doi=None,
            hal_url=None,
        ),
        publication_factory(
            hal_id="hal-conference",
            category="Conference presentation",
            journal=None,
            conference="Example Conference",
            conference_start="2023-05-23",
        ),
        publication_factory(
            hal_id="hal-poster",
            category="Poster",
            authors=None,
        ),
        publication_factory(hal_id="hal-no-title", title=" "),
        publication_factory(hal_id=None),
        publication_factory(hal_id="hal-duplicate"),
        publication_factory(hal_id="hal-duplicate"),
        publication_factory(
            hal_id="hal-year-only",
            year=2019,
            conference_start=None,
        ),
    ]

    report = exporter.generate_hugo_content(records, tmp_path, type_map)

    assert report.processed == 9
    assert report.written == 4
    assert report.excluded == 2
    assert report.excluded_by_category == {
        "Conference presentation": 1,
        "Poster": 1,
    }
    assert len(report.errors) == 3
    assert any("missing non-empty title" in error for error in report.errors)
    assert any("missing non-empty hal_id" in error for error in report.errors)
    assert any("duplicate hal_id" in error for error in report.errors)
    assert any("date fallback for year 2019" in warning for warning in report.warnings)

    article = read_front_matter(tmp_path / "hal-123" / "index.md")
    assert article["title"] == "A publication"
    assert article["authors"] == ["A. Author"]
    assert article["date"] == "2024-01-01T00:00:00Z"
    assert article["publication_types"] == ["article-journal"]
    assert article["publication"] == "Example Journal"
    assert article["hugoblox"]["ids"] == {"hal": "hal-123", "doi": "10.1234/example"}
    assert article["links"] == [{"type": "url", "url": "https://hal.example/hal-123"}]

    no_doi = read_front_matter(tmp_path / "hal-no-doi" / "index.md")
    assert no_doi["hugoblox"]["ids"] == {"hal": "hal-no-doi"}
    assert "links" not in no_doi

    assert not (tmp_path / "hal-conference" / "index.md").exists()
    assert not (tmp_path / "hal-poster" / "index.md").exists()
    assert read_front_matter(tmp_path / "hal-year-only" / "index.md")["date"] == (
        "2019-01-01T00:00:00Z"
    )
    assert read_front_matter(tmp_path / "hal-duplicate" / "index.md")["title"] == ("A publication")
    assert not (tmp_path / "hal-no-title" / "index.md").exists()


def test_missing_year_uses_documented_placeholder_and_warning(
    tmp_path, type_map, publication_factory
):
    exporter = load_exporter_module()
    report = exporter.generate_hugo_content(
        [publication_factory(hal_id="hal-no-date", year=None, conference_start=None)],
        tmp_path,
        type_map,
    )

    assert report.written == 1
    assert any("using placeholder date 1970-01-01T00:00:00Z" in w for w in report.warnings)
    assert read_front_matter(tmp_path / "hal-no-date" / "index.md")["date"] == (
        "1970-01-01T00:00:00Z"
    )


def test_dry_run_reports_planned_files_without_writing(tmp_path, type_map, publication_factory):
    exporter = load_exporter_module()
    report = exporter.generate_hugo_content(
        [publication_factory()],
        tmp_path,
        type_map,
        dry_run=True,
    )

    assert report.written == 0
    assert len(report.planned_files) == 1
    assert not list(tmp_path.rglob("index.md"))


@pytest.mark.parametrize("dry_run", [False, True])
def test_cli_reports_excluded_categories_in_all_run_modes(tmp_path, capsys, dry_run):
    exporter = load_exporter_module()
    input_path = tmp_path / "publications.json"
    input_path.write_text(
        '[{"hal_id":"hal-article","title":"Article","category":"Journal article"},'
        '{"hal_id":"hal-conference","title":"Conference","category":"Conference presentation"},'
        '{"hal_id":"hal-poster","title":"Poster","category":"Poster"}]',
        encoding="utf-8",
    )
    args = ["--input", str(input_path), "--output", str(tmp_path / "out")]
    if dry_run:
        args.append("--dry-run")

    exit_code = exporter.main(args)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Records excluded: 2" in output
    assert "Excluded by category:\n  Conference presentation: 1\n  Poster: 1" in output
    assert (tmp_path / "out" / "hal-article" / "index.md").exists() is not dry_run


def test_malformed_json_is_fatal(tmp_path, capsys):
    exporter = load_exporter_module()
    input_path = tmp_path / "malformed.json"
    input_path.write_text("{", encoding="utf-8")

    exit_code = exporter.main(["--input", str(input_path), "--output", str(tmp_path / "out")])

    assert exit_code == 2
    assert "Fatal error:" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_validation_errors_return_nonzero(tmp_path, capsys):
    exporter = load_exporter_module()
    input_path = tmp_path / "invalid.json"
    input_path.write_text(
        '[{"hal_id": "hal-missing-title", "category": "Conference presentation"}]',
        encoding="utf-8",
    )

    exit_code = exporter.main(["--input", str(input_path), "--output", str(tmp_path / "out")])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Errors: 1" in output
    assert "Records excluded: 0" in output
    assert not (tmp_path / "out").exists()
