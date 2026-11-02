#!/usr/bin/env python3
"""Validate that response-letter \\rlink ids match manuscript revision ids."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


RLINK_RE = re.compile(
    r"\\rlink\s*\{([^{}]+)\}|\\rlinks\s*\{([^{}]+)\}"
)
REVISE_RE = re.compile(
    r"\\revise\s*\[([^\]]+)\]|\\rpoint\s*\{([^{}]+)\}|\\rlabel\s*\{([^{}]+)\}"
)
COMMENT_RE = re.compile(r"%.*?$", re.M)


def strip_comments(text: str) -> str:
    return COMMENT_RE.sub("", text)


def collect_letter_ids(tex: str) -> set[str]:
    ids: set[str] = set()
    for match in RLINK_RE.finditer(strip_comments(tex)):
        single, multi = match.groups()
        if single:
            ids.add(single.strip())
        if multi:
            for part in multi.split(","):
                part = part.strip()
                if part:
                    ids.add(part)
    return ids


def collect_manuscript_ids(tex: str) -> set[str]:
    ids: set[str] = set()
    for match in REVISE_RE.finditer(strip_comments(tex)):
        for group in match.groups():
            if group:
                ids.add(group.strip())
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--letter-tex", required=True)
    parser.add_argument("--manuscript-tex", required=True)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any id is missing on either side.",
    )
    args = parser.parse_args()

    letter_tex = Path(args.letter_tex).read_text(encoding="utf-8")
    manuscript_tex = Path(args.manuscript_tex).read_text(encoding="utf-8")

    letter_ids = collect_letter_ids(letter_tex)
    manuscript_ids = collect_manuscript_ids(manuscript_tex)

    missing_in_manuscript = sorted(letter_ids - manuscript_ids)
    missing_in_letter = sorted(manuscript_ids - letter_ids)
    shared = sorted(letter_ids & manuscript_ids)

    print(f"Linked ids (both sides): {len(shared)}")
    for item in shared:
        print(f"  OK  {item}")

    status = 0
    if missing_in_manuscript:
        print(f"Missing in manuscript ({len(missing_in_manuscript)}):")
        for item in missing_in_manuscript:
            print(f"  !!  {item}  (used by \\rlink, no \\revise/\\rpoint/\\rlabel)")
        status = 1
    if missing_in_letter:
        print(f"Unused manuscript marks ({len(missing_in_letter)}):")
        for item in missing_in_letter:
            print(f"  --  {item}  (in manuscript, never \\rlink-ed)")
        if args.strict:
            status = 1

    if status == 0 and not missing_in_manuscript and not missing_in_letter:
        print("ID check passed.")
    elif status == 0:
        print("ID check passed with warnings.")
    else:
        print("ID check failed.")
    return status


if __name__ == "__main__":
    sys.exit(main())
