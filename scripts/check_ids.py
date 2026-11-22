#!/usr/bin/env python3
"""Validate letter \\elink ids against manuscript rev: labels in .aux."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ELINK_RE = re.compile(
    r"\\elink\s*\{([^{}]+)\}|\\elinks\s*\{([^{}]+)\}|"
    r"\\rlink\s*\{([^{}]+)\}|\\rlinks\s*\{([^{}]+)\}"
)
AUX_LABEL_RE = re.compile(r"\\newlabel\{rev:([^}]+)\}")
COMMENT_RE = re.compile(r"%.*?$", re.M)


def strip_comments(text: str) -> str:
    return COMMENT_RE.sub("", text)


def collect_letter_ids(tex: str) -> set[str]:
    ids: set[str] = set()
    for match in ELINK_RE.finditer(strip_comments(tex)):
        for group in match.groups():
            if not group:
                continue
            if "," in group:
                for part in group.split(","):
                    part = part.strip()
                    if part:
                        ids.add(part)
            else:
                ids.add(group.strip())
    return ids


def collect_manuscript_ids_from_aux(aux_text: str) -> set[str]:
    return {m.group(1) for m in AUX_LABEL_RE.finditer(aux_text)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--letter-tex", required=True)
    parser.add_argument("--manuscript-tex", required=True)
    parser.add_argument(
        "--manuscript-aux",
        default=None,
        help="Defaults to manuscript .tex with .aux suffix",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail when manuscript edits are never linked from the letter.",
    )
    args = parser.parse_args()

    letter_tex = Path(args.letter_tex).read_text(encoding="utf-8")
    manuscript_tex = Path(args.manuscript_tex)
    aux_path = (
        Path(args.manuscript_aux)
        if args.manuscript_aux
        else manuscript_tex.with_suffix(".aux")
    )

    if not aux_path.exists():
        print(f"Missing manuscript aux (compile manuscript first): {aux_path}")
        return 1

    letter_ids = collect_letter_ids(letter_tex)
    manuscript_ids = collect_manuscript_ids_from_aux(
        aux_path.read_text(encoding="utf-8", errors="ignore")
    )

    missing_in_manuscript = sorted(letter_ids - manuscript_ids)
    missing_in_letter = sorted(manuscript_ids - letter_ids)
    shared = sorted(letter_ids & manuscript_ids)

    print(f"Linked edit ids (both sides): {len(shared)}")
    for item in shared:
        print(f"  OK  {item}")

    status = 0
    if missing_in_manuscript:
        print(f"Missing in manuscript ({len(missing_in_manuscript)}):")
        for item in missing_in_manuscript:
            print(f"  !!  {item}  (used by \\elink, no rev:{item} in .aux)")
        status = 1
    if missing_in_letter:
        print(f"Unused manuscript edits ({len(missing_in_letter)}):")
        for item in missing_in_letter:
            print(f"  --  {item}  (in manuscript, never \\elink-ed)")
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
