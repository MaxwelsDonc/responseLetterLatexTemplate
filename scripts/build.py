#!/usr/bin/env python3
"""Build the manuscript and response letter, then link the review PDFs."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - fallback for minimal envs
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "project_config.yaml"


def parse_config(file_path: Path) -> dict:
    text = file_path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise SystemExit(f"Invalid config: {file_path}")
        return data

    data = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.lower() == "true":
            data[key] = True
        elif value.lower() == "false":
            data[key] = False
        else:
            data[key] = value
    return data


def run(cmd, cwd, env=None):
    print("$", " ".join(cmd))
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=merged,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stdout.flush()
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def tex_env():
    # Prefer project-root sty/cls files (commands.sty, revision-marks.sty, ar2rc.cls).
    root = str(ROOT)
    existing = os.environ.get("TEXINPUTS", "")
    return {"TEXINPUTS": f"{root}//:{existing}"}


def ensure_file(path):
    if not path.is_file():
        raise SystemExit(f"Missing: {path}")


def latex_command(source, job, flag=None):
    if flag:
        source = rf"\def\{flag}{{1}}\input{{{source}}}"
    return ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"-jobname={job}", source]


def build_manuscript(cfg, combined):
    manuscript_tex = ROOT / cfg["manuscript_tex"]
    manuscript_dir = manuscript_tex.parent
    manuscript_file = manuscript_tex.name
    manuscript_doc = cfg["manuscript_doc"]
    print("[1/5] Building manuscript...")
    env = tex_env()
    flag = "BuildCombinedReviewPDF" if combined else None
    latex = latex_command(manuscript_file, manuscript_doc, flag)
    run(latex, manuscript_dir, env)
    # Demo has no bibliography; ignore bibtex failures for minimal papers.
    bib = subprocess.run(
        ["bibtex", manuscript_doc],
        cwd=manuscript_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if bib.returncode == 0:
        sys.stdout.write(bib.stdout)
    else:
        print("bibtex skipped/failed (ok for demos without .bib).")
    run(latex, manuscript_dir, env)
    run(latex, manuscript_dir, env)


def build_response_letter(cfg, work_dir=None):
    response_tex = cfg["response_letter_tex"]
    response_doc = cfg["response_letter_doc"]
    print("[2/5] Building response letter...")
    env = tex_env()
    flag = "BuildManagedReviewPDF" if work_dir else None
    latex = latex_command(response_tex, response_doc, flag)
    biber = ["biber"]
    if work_dir:
        work_dir.mkdir(parents=True, exist_ok=True)
        latex.insert(1, f"-output-directory={work_dir}")
        biber.extend([f"--input-directory={work_dir}", f"--output-directory={work_dir}"])
    run(latex, ROOT, env)
    run([*biber, response_doc], ROOT, env)
    run(latex, ROOT, env)
    run(latex, ROOT, env)


def check_ids(cfg, strict: bool):
    print("[3/5] Checking revision ids...")
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "check_ids.py"),
        "--letter-tex",
        str(ROOT / cfg["response_letter_tex"]),
        "--manuscript-tex",
        str(ROOT / cfg["manuscript_tex"]),
    ]
    if strict:
        cmd.append("--strict")
    run(cmd, ROOT)


def normalize_links(cfg):
    if not cfg.get("enable_link_normalization", False):
        print("[4/5] Skipping link normalization.")
        return
    print("[4/5] Normalizing embedded PDF links...")
    run(
        [
            sys.executable,
            "scripts/normalize_links.py",
            "--response-pdf",
            str(ROOT / cfg["response_letter_pdf"]),
            "--manuscript-pdf",
            str(ROOT / cfg["manuscript_pdf"]),
            "--response-pdf-name",
            Path(cfg["response_letter_pdf"]).name,
            "--manuscript-pdf-name",
            Path(cfg["manuscript_pdf"]).name,
            "--anchor-prefix",
            cfg.get("anchor_prefix", "response."),
        ],
        ROOT,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(CONFIG_FILE),
        help="Path to project_config.yaml",
    )
    parser.add_argument("--letter-only", action="store_true")
    parser.add_argument("--manuscript-only", action="store_true")
    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--combined", action="store_true", help="Build the letter with the manuscript appended (default).")
    formats.add_argument("--separate", action="store_true", help="Build the review letter and manuscript as two PDFs.")
    parser.add_argument("--skip-normalize", action="store_true")
    parser.add_argument("--skip-id-check", action="store_true")
    parser.add_argument(
        "--strict-ids",
        action="store_true",
        help="Fail when manuscript marks are never referenced by \\rlink.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Missing: {config_path}")

    cfg = parse_config(config_path)
    if args.letter_only and args.manuscript_only:
        raise SystemExit("Use only one of --letter-only / --manuscript-only")

    output_dir = cfg.get("review_output_dir")
    if args.separate and not output_dir:
        raise SystemExit("Set review_output_dir in the config to build two review PDFs.")
    manuscript_pdf = ROOT / cfg["manuscript_pdf"]
    if not args.letter_only:
        ensure_file(ROOT / cfg["manuscript_tex"])
        build_manuscript(cfg, combined=not output_dir and not args.manuscript_only)
    else:
        print("[1/5] Skipping manuscript build.")
    ensure_file(manuscript_pdf)

    if args.manuscript_only:
        print(f"Done. Open {cfg['manuscript_pdf']}.")
        return

    ensure_file(ROOT / cfg["response_letter_tex"])
    work_dir = ROOT / "output" / "review-build" if output_dir else None
    build_response_letter(cfg, work_dir)

    if output_dir:
        stem = cfg["response_letter_doc"]
        if args.skip_normalize:
            print(f"Done. The unprocessed reply is at {work_dir / (stem + '.pdf')}.")
            return
        from link_review_pdfs import ReviewLinkError, link_review_pdfs

        print("[3/5] Checking exact revision and reply anchors...")
        try:
            link_review_pdfs(
                work_dir / f"{stem}.pdf",
                manuscript_pdf,
                work_dir / f"{stem}.aux",
                ROOT / output_dir,
                strict=args.strict_ids and not args.skip_id_check,
                separate=args.separate,
            )
        except ReviewLinkError as error:
            raise SystemExit(str(error)) from error
        print(f"[5/5] Done. Open {output_dir}/responseLetter.pdf.")
        return

    if args.skip_id_check:
        print("[3/5] Skipping id check.")
    else:
        check_ids(cfg, strict=args.strict_ids)

    if args.skip_normalize:
        print("[4/5] Skipping link normalization.")
    else:
        normalize_links(cfg)

    print(f"[5/5] Done. Open {cfg['response_letter_pdf']} to verify links.")


if __name__ == "__main__":
    main()
