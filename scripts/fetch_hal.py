#!/usr/bin/env python3

import json
from pathlib import Path

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]

PROFILE_FILE = ROOT / "data" / "profile.yml"
OUTPUT_FILE = ROOT / "data" / "publications.json"

API_URL = "https://api.archives-ouvertes.fr/search/"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

with open(PROFILE_FILE, encoding="utf-8") as f:
    profile = yaml.safe_load(f)

IDHAL = profile["hal"]


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


def classify_document(doc_type, invited):
    """
    Map HAL document types onto CV categories.

    For COMM records, use HAL's invitedCommunication_s field to
    distinguish invited talks from ordinary oral presentations.
    """

    if doc_type == "ART":
        return {
            "category": "Journal article",
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
        return {
            "category": "Report",
            "presentation_type": None,
        }

    return {
        "category": "Other scientific contribution",
        "presentation_type": None,
    }


# ---------------------------------------------------------------------------
# Query HAL
# ---------------------------------------------------------------------------

params = {
    "q": f"authIdHal_s:{IDHAL}",
    "rows": 1000,
    "sort": "producedDateY_i desc",
    "wt": "json",
    "fl": ",".join(FIELDS),
}

print(f"Querying HAL for idHAL '{IDHAL}'...")

response = requests.get(
    API_URL,
    params=params,
    timeout=60,
)

response.raise_for_status()

result = response.json()["response"]

docs = result["docs"]
total = result["numFound"]

print(f"HAL reports {total} records.")

if total > 1000:
    raise RuntimeError(
        f"HAL returned {total} records, which exceeds the current "
        "1000-record limit. Pagination needs to be implemented."
    )


# ---------------------------------------------------------------------------
# Convert HAL records to our CV data model
# ---------------------------------------------------------------------------

publications = []

for doc in docs:

    hal_id = first_value(doc.get("halId_s"))
    doc_type = first_value(doc.get("docType_s"))

    invited = first_value(
        doc.get("invitedCommunication_s")
    )

    classification = classify_document(
        doc_type,
        invited,
    )

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
        "authors": clean_authors(
            doc.get("authFullName_s")
        ),
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

        "journal": first_value(
            doc.get("journalTitle_s")
        ),
        "doi": first_value(
            doc.get("doiId_s")
        ),

        # ---------------------------------------------------------------
        # Conference information
        # ---------------------------------------------------------------

        "conference": first_value(
            doc.get("conferenceTitle_s")
        ),
        "conference_start": first_value(
            doc.get("conferenceStartDate_s")
        ),
        "conference_end": first_value(
            doc.get("conferenceEndDate_s")
        ),
        "conference_organizer": first_value(
            doc.get("conferenceOrganizer_s")
        ),
        "city": first_value(
            doc.get("city_s")
        ),
        "country": first_value(
            doc.get("country_s")
        ),
        "conference_url": first_value(
            doc.get("publisherLink_s")
        ),

        # ---------------------------------------------------------------
        # Conference characteristics
        # ---------------------------------------------------------------

        "invited": invited,
        "peer_reviewed": first_value(
            doc.get("peerReviewing_s")
        ),
        "audience": first_value(
            doc.get("audience_s")
        ),
        "proceedings": first_value(
            doc.get("proceedings_s")
        ),

        # ---------------------------------------------------------------
        # Additional bibliographic information
        # ---------------------------------------------------------------

        "source": first_value(
            doc.get("source_s")
        ),
        "volume": first_value(
            doc.get("volume_s")
        ),
        "issue": first_value(
            doc.get("issue_s")
        ),
        "pages": first_value(
            doc.get("page_s")
        ),
        "publisher": first_value(
            doc.get("publisher_s")
        ),
        "series": first_value(
            doc.get("serie_s")
        ),

        # ---------------------------------------------------------------
        # Book chapter metadata
        # ---------------------------------------------------------------

        "book_title": first_value(
            doc.get("bookTitle_s")
        ),
        "editors": clean_authors(
            doc.get("editorFullName_s")
        ),
    }

    publications.append(publication)


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------

publications.sort(
    key=lambda p: (
        p["year"] or 0,
        p["hal_id"] or "",
    ),
    reverse=True,
)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        publications,
        f,
        indent=2,
        ensure_ascii=False,
    )

print(
    f"Saved {len(publications)} publications "
    f"to {OUTPUT_FILE}"
)
