#!/usr/bin/env python3

import json
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]

PROFILE_FILE = ROOT / "data" / "profile.yml"
OUTPUT_FILE = ROOT / "data" / "publications.json"

API_URL = "https://api.archives-ouvertes.fr/search/"
REQUEST_TIMEOUT_SECONDS = 60
MAX_FETCH_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1


FIELDS = [
    # Identifiers
    "docid",
    "halId_s",
    "uri_s",
    # General bibliographic information
    "docType_s",
    "title_s",
    "authFullName_s",
    "producedDateY_i",
    # Journal information
    "journalTitle_s",
    "doiId_s",
    # Conference information
    "conferenceTitle_s",
    "conferenceStartDate_s",
    "conferenceEndDate_s",
    "conferenceOrganizer_s",
    "city_s",
    "country_s",
    "publisherLink_s",
    # Conference characteristics
    "invitedCommunication_s",
    "peerReviewing_s",
    "audience_s",
    "proceedings_s",
    # Other potentially useful bibliographic information
    "source_s",
    "volume_s",
    "issue_s",
    "page_s",
    "publisher_s",
    "serie_s",
    # Book chapter/container metadata (if available)
    "bookTitle_s",
    "editorFullName_s",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def first_value(value):
    """Return the first value if HAL provides a list."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def clean_authors(authors):
    """Return a clean list of author names."""
    if not authors:
        return []

    if isinstance(authors, str):
        return [authors]

    return authors


def is_peer_reviewed(value):
    """Return True when HAL marks the record as peer-reviewed."""
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes"}


def classify_document(doc_type, invited, peer_reviewed):
    """
    Map HAL document types onto CV categories.

    For COMM records, use HAL's invitedCommunication_s field to
    distinguish invited talks from ordinary oral presentations.
    """

    if doc_type == "ART":
        category = "Journal article" if is_peer_reviewed(peer_reviewed) else "Other scientific contribution"
        return {
            "category": category,
            "presentation_type": None,
        }

    if doc_type == "COUV":
        return {
            "category": "Book chapter",
            "presentation_type": None,
        }

    if doc_type == "COMM":
        if invited == "1":
            presentation_type = "Invited talk"
        elif invited == "0":
            presentation_type = "Oral presentation"
        else:
            presentation_type = "Oral presentation"

        return {
            "category": "Conference presentation",
            "presentation_type": presentation_type,
        }

    if doc_type == "POSTER":
        return {
            "category": "Conference presentation",
            "presentation_type": "Poster",
        }

    if doc_type == "REPORT":
        return None

    if doc_type == "PREPRINT":
        return {
            "category": "Preprint",
            "presentation_type": None,
        }

    return {
        "category": "Other scientific contribution",
        "presentation_type": None,
    }


def load_idhal(profile_file):
    with open(profile_file, encoding="utf-8") as f:
        profile = yaml.safe_load(f) or {}
    return profile["hal"]


def is_retryable_error(error):
    if isinstance(
        error,
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    ):
        return True

    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        if response is not None and 500 <= response.status_code < 600:
            return True

    return False


def fetch_hal_records(idhal, *, get=requests.get, sleep=time.sleep):
    params = {
        "q": f"authIdHal_s:{idhal}",
        "rows": 1000,
        "sort": "producedDateY_i desc",
        "wt": "json",
        "fl": ",".join(FIELDS),
    }

    print(f"Querying HAL for idHAL '{idhal}'...")

    last_error = None
    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        try:
            response = get(
                API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            result = response.json()["response"]
            docs = result["docs"]
            total = result["numFound"]
            print(f"HAL reports {total} records.")
            return docs, total
        except requests.exceptions.RequestException as error:
            last_error = error
            retryable = is_retryable_error(error)
            if not retryable or attempt == MAX_FETCH_ATTEMPTS:
                break
            backoff_seconds = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            print(
                f"Warning: HAL fetch attempt {attempt}/{MAX_FETCH_ATTEMPTS} failed "
                f"({error.__class__.__name__}: {error}). "
                f"Retrying in {backoff_seconds} second(s)..."
            )
            sleep(backoff_seconds)
        except (ValueError, KeyError, TypeError) as error:
            last_error = error
            break

    raise RuntimeError(
        f"HAL fetch failed after {MAX_FETCH_ATTEMPTS} attempt(s): {last_error}"
    ) from last_error


def cache_is_readable(output_file):
    if not output_file.exists():
        return False

    try:
        with open(output_file, encoding="utf-8") as f:
            json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        print(
            f"Error: local publications cache exists but cannot be read: "
            f"{output_file} ({error})"
        )
        return False

    return True


def main(
    *,
    get=requests.get,
    sleep=time.sleep,
    output_file=OUTPUT_FILE,
    profile_file=PROFILE_FILE,
):
    idhal = load_idhal(profile_file)

    try:
        docs, total = fetch_hal_records(idhal, get=get, sleep=sleep)
    except RuntimeError as error:
        if cache_is_readable(output_file):
            print(f"Warning: {error}. Using existing local publications cache at {output_file}.")
            return 0

        print(
            f"Error: {error}. No readable local publications cache found at "
            f"{output_file}. Run this command again when HAL is reachable."
        )
        return 1

    if total > 1000:
        raise RuntimeError(
            f"HAL returned {total} records, which exceeds the current "
            "1000-record limit. Pagination needs to be implemented."
        )

    publications = []
    for doc in docs:
        hal_id = first_value(doc.get("halId_s"))
        doc_type = first_value(doc.get("docType_s"))
        invited = first_value(doc.get("invitedCommunication_s"))
        peer_reviewed = first_value(doc.get("peerReviewing_s"))
        classification = classify_document(
            doc_type,
            invited,
            peer_reviewed,
        )
        if classification is None:
            continue
        publication = {
            # ---------------------------------------------------------------
            # Identifiers
            # ---------------------------------------------------------------
            "hal_id": hal_id,
            "docid": doc.get("docid"),
            "hal_url": first_value(doc.get("uri_s")),
            # ---------------------------------------------------------------
            # General bibliographic information
            # ---------------------------------------------------------------
            "title": first_value(doc.get("title_s")),
            "authors": clean_authors(doc.get("authFullName_s")),
            "year": doc.get("producedDateY_i"),
            # ---------------------------------------------------------------
            # HAL classification
            # ---------------------------------------------------------------
            "hal_type": doc_type,
            "category": classification["category"],
            "presentation_type": classification["presentation_type"],
            # ---------------------------------------------------------------
            # Journal information
            # ---------------------------------------------------------------
            "journal": first_value(doc.get("journalTitle_s")),
            "doi": first_value(doc.get("doiId_s")),
            # ---------------------------------------------------------------
            # Conference information
            # ---------------------------------------------------------------
            "conference": first_value(doc.get("conferenceTitle_s")),
            "conference_start": first_value(doc.get("conferenceStartDate_s")),
            "conference_end": first_value(doc.get("conferenceEndDate_s")),
            "conference_organizer": first_value(doc.get("conferenceOrganizer_s")),
            "city": first_value(doc.get("city_s")),
            "country": first_value(doc.get("country_s")),
            "conference_url": first_value(doc.get("publisherLink_s")),
            # ---------------------------------------------------------------
            # Conference characteristics
            # ---------------------------------------------------------------
            "invited": invited,
            "peer_reviewed": peer_reviewed,
            "audience": first_value(doc.get("audience_s")),
            "proceedings": first_value(doc.get("proceedings_s")),
            # ---------------------------------------------------------------
            # Additional bibliographic information
            # ---------------------------------------------------------------
            "source": first_value(doc.get("source_s")),
            "volume": first_value(doc.get("volume_s")),
            "issue": first_value(doc.get("issue_s")),
            "pages": first_value(doc.get("page_s")),
            "publisher": first_value(doc.get("publisher_s")),
            "series": first_value(doc.get("serie_s")),
            # ---------------------------------------------------------------
            # Book chapter metadata
            # ---------------------------------------------------------------
            "book_title": first_value(doc.get("bookTitle_s")),
            "editors": clean_authors(doc.get("editorFullName_s")),
        }

        publications.append(publication)

    publications.sort(
        key=lambda p: (
            p["year"] or 0,
            p["hal_id"] or "",
        ),
        reverse=True,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            publications,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Saved {len(publications)} publications to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
