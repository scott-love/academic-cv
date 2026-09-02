import importlib.util
import json
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
FETCH_HAL_PATH = ROOT / "scripts" / "fetch_hal.py"


def load_fetch_hal_module():
    spec = importlib.util.spec_from_file_location("fetch_hal_module", FETCH_HAL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_fetch_hal_main_success_writes_publications(tmp_path):
    fetch_hal = load_fetch_hal_module()

    profile_file = tmp_path / "profile.yml"
    output_file = tmp_path / "publications.json"
    profile_file.write_text(yaml.safe_dump({"hal": "test-id"}), encoding="utf-8")

    calls = []

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        return FakeResponse(
            {
                "response": {
                    "numFound": 1,
                    "docs": [
                        {
                            "docid": 123,
                            "halId_s": ["hal-123"],
                            "uri_s": ["https://hal.science/hal-123"],
                            "docType_s": ["ART"],
                            "peerReviewing_s": ["1"],
                            "title_s": ["A paper"],
                            "authFullName_s": ["Scott Love"],
                            "producedDateY_i": 2026,
                        }
                    ],
                }
            }
        )

    exit_code = fetch_hal.main(
        get=fake_get,
        sleep=lambda _: None,
        output_file=output_file,
        profile_file=profile_file,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][2] == fetch_hal.REQUEST_TIMEOUT_SECONDS

    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["hal_id"] == "hal-123"
    assert saved[0]["category"] == "Journal article"


def test_fetch_hal_main_classifies_non_peer_reviewed_art_preprints_and_omits_reports(tmp_path):
    fetch_hal = load_fetch_hal_module()

    profile_file = tmp_path / "profile.yml"
    output_file = tmp_path / "publications.json"
    profile_file.write_text(yaml.safe_dump({"hal": "test-id"}), encoding="utf-8")

    def fake_get(url, params, timeout):
        return FakeResponse(
            {
                "response": {
                    "numFound": 4,
                    "docs": [
                        {
                            "docid": 100,
                            "halId_s": ["hal-peer"],
                            "uri_s": ["https://hal.science/hal-peer"],
                            "docType_s": ["ART"],
                            "peerReviewing_s": ["1"],
                            "title_s": ["Peer reviewed paper"],
                            "authFullName_s": ["Scott Love"],
                            "producedDateY_i": 2026,
                        },
                        {
                            "docid": 101,
                            "halId_s": ["hal-non-peer"],
                            "uri_s": ["https://hal.science/hal-non-peer"],
                            "docType_s": ["ART"],
                            "peerReviewing_s": ["0"],
                            "title_s": ["Non peer reviewed paper"],
                            "authFullName_s": ["Scott Love"],
                            "producedDateY_i": 2025,
                        },
                        {
                            "docid": 102,
                            "halId_s": ["hal-report"],
                            "uri_s": ["https://hal.science/hal-report"],
                            "docType_s": ["REPORT"],
                            "title_s": ["A report"],
                            "authFullName_s": ["Scott Love"],
                            "producedDateY_i": 2024,
                        },
                        {
                            "docid": 103,
                            "halId_s": ["hal-preprint"],
                            "uri_s": ["https://hal.science/hal-preprint"],
                            "docType_s": ["PREPRINT"],
                            "title_s": ["A preprint"],
                            "authFullName_s": ["Scott Love"],
                            "producedDateY_i": 2023,
                        },
                    ],
                }
            }
        )

    exit_code = fetch_hal.main(
        get=fake_get,
        sleep=lambda _: None,
        output_file=output_file,
        profile_file=profile_file,
    )

    assert exit_code == 0
    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert [pub["hal_id"] for pub in saved] == ["hal-peer", "hal-non-peer", "hal-preprint"]
    assert [pub["category"] for pub in saved] == [
        "Journal article",
        "Other scientific contribution",
        "Preprint",
    ]


def test_fetch_hal_main_uses_cache_on_retryable_failure(tmp_path, capsys):
    fetch_hal = load_fetch_hal_module()

    profile_file = tmp_path / "profile.yml"
    output_file = tmp_path / "publications.json"
    profile_file.write_text(yaml.safe_dump({"hal": "test-id"}), encoding="utf-8")
    output_file.write_text('[{"cached": true}]', encoding="utf-8")

    attempts = []
    backoffs = []

    def failing_get(url, params, timeout):
        attempts.append((url, params, timeout))
        raise requests.exceptions.ConnectTimeout("connect timeout")

    exit_code = fetch_hal.main(
        get=failing_get,
        sleep=lambda seconds: backoffs.append(seconds),
        output_file=output_file,
        profile_file=profile_file,
    )

    assert exit_code == 0
    assert len(attempts) == fetch_hal.MAX_FETCH_ATTEMPTS
    assert backoffs == [1, 2]
    assert json.loads(output_file.read_text(encoding="utf-8")) == [{"cached": True}]

    captured = capsys.readouterr()
    assert "Using existing local publications cache" in captured.out


def test_fetch_hal_main_fails_when_no_cache_available(tmp_path, capsys):
    fetch_hal = load_fetch_hal_module()

    profile_file = tmp_path / "profile.yml"
    output_file = tmp_path / "missing-publications.json"
    profile_file.write_text(yaml.safe_dump({"hal": "test-id"}), encoding="utf-8")

    attempts = []

    def failing_get(url, params, timeout):
        attempts.append((url, params, timeout))
        raise requests.exceptions.ConnectTimeout("connect timeout")

    exit_code = fetch_hal.main(
        get=failing_get,
        sleep=lambda _: None,
        output_file=output_file,
        profile_file=profile_file,
    )

    assert exit_code == 1
    assert len(attempts) == fetch_hal.MAX_FETCH_ATTEMPTS
    assert not output_file.exists()

    captured = capsys.readouterr()
    assert "No readable local publications cache found" in captured.out
