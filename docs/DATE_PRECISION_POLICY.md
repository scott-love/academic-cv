# Publication Date Precision Policy

## Overview

The publication exporter standardizes date output across records with varying source precision. This document defines the policy, priority chain, and handling rules.

## Priority Chain

Dates are extracted using a tiered priority system. The first non-empty, valid field is used:

### Priority 1: `conference_start` (Highest Precision)
Full datetime or date information from conference/event metadata.

**Accepted Formats:**
- Year only: `"2023"` → `2023-01-01T00:00:00Z`
- Date: `"2023-05-15"` → `2023-05-15T00:00:00Z`
- ISO8601 datetime: `"2023-05-15T14:30:00Z"` → `2023-05-15T14:30:00Z`
- ISO8601 with timezone: `"2023-05-15T14:30:00+02:00"` → Converted to UTC

**Default Behavior:**
- Dates without time default to midnight UTC (00:00:00Z)
- Timezones are converted to UTC
- Invalid values trigger warning and cascade to Priority 2

### Priority 2: `year_month_day` (Medium Precision)
Date-only field in YYYY-MM-DD format, typically from structured metadata (e.g., HAL).

**Accepted Format:**
- Date: `"2023-05-15"` → `2023-05-15T00:00:00Z`

**Default Behavior:**
- Always assumes midnight UTC (00:00:00Z)
- Invalid values trigger warning and cascade to Priority 3

### Priority 3: `year` (Lowest Precision)
Year integer, often the only available metadata.

**Accepted Format:**
- Year: `2023` → `2023-01-01T00:00:00Z`

**Default Behavior:**
- Always represents as January 1 at midnight UTC
- Invalid/missing values cascade to placeholder fallback

## Output Format

All returned dates follow ISO8601 with UTC timezone: