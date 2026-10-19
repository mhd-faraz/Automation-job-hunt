"""Deterministic filter that runs BEFORE any LLM call.

This is the whole cost story: ~2000 raw jobs -> ~40 candidates for ~0 rupees,
so Claude only ever reads jobs that already passed title + location + freshness
+ required-experience.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from .fetch import Job

REMOTE_HINTS = ("remote", "anywhere", "work from home", "wfh", "distributed")

# --- required-experience detection -----------------------------------------
# Finds lines like "2-5 years of experience", "3+ years experience",
# "experience of 5+ years", "minimum 4 years". For a range we take the lower
# bound. If a posting has several mentions we use the LOWEST one, so a job is
# only dropped when every mention asks for more than max_required_years.
_N = r"(?<!\d)(\d{1,2})"
_RANGE = r"\s*(?:\+|(?:-|–|to)\s*\d{1,2}\+?)?\s*\+?\s*"
_YEARS = [
    re.compile(_N + _RANGE + r"years?[^.\n]{0,60}?(?:experience|exp\b)", re.I),
    re.compile(r"(?:experience|exp\b)[^.\n]{0,40}?" + _N + _RANGE + r"years?", re.I),
    re.compile(r"(?:minimum|at least|min\.?)\s*(?:of\s*)?" + _N + r"\s*\+?\s*years?", re.I),
]


def _min_years_required(text: str | None) -> int | None:
    found = [int(m.group(1)) for rx in _YEARS for m in rx.finditer(text or "")]
    return min(found) if found else None


def _any_match(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    v = value.replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.fromisoformat(v) if fmt is None else datetime.strptime(v, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def prefilter(jobs: list[Job], cfg: dict) -> list[Job]:
    inc = cfg.get("include_titles") or [r"."]
    exc = cfg.get("exclude_titles") or []
    locs = [l.lower() for l in (cfg.get("locations") or [])]
    allow_remote = bool(cfg.get("allow_remote", True))
    max_age = cfg.get("max_age_days")
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age) if max_age else None
    # Drop a job if it asks for MORE than this many years. null/missing = off.
    max_years = cfg.get("max_required_years")

    kept, stats = [], {"title": 0, "location": 0, "age": 0, "exp": 0}
    for j in jobs:
        if not _any_match(inc, j.title) or (exc and _any_match(exc, j.title)):
            stats["title"] += 1
            continue

        if locs:
            hay = f"{j.location} {j.title}".lower()
            is_remote = allow_remote and any(h in hay for h in REMOTE_HINTS)
            if not is_remote and not any(l in hay for l in locs):
                stats["location"] += 1
                continue

        if cutoff:
            posted = _parse_date(j.posted_at)
            if posted and posted < cutoff:
                stats["age"] += 1
                continue

        if max_years is not None:
            need = _min_years_required(j.description)
            if need is not None and need > max_years:
                stats["exp"] += 1
                continue

        kept.append(j)

    print(f"  prefilter: {len(jobs)} -> {len(kept)} "
          f"(dropped title={stats['title']} location={stats['location']} "
          f"stale={stats['age']} exp={stats['exp']})")
    return kept