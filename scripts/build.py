#!/usr/bin/env python3
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "project_config.yaml"


def parse_simple_yaml(file_path: Path):
    data = {}
    for raw in file_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
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


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdout.write(p.stdout)
    sys.stdout.flush()
    if p.returncode != 0:
        sys.exit(p.returncode)


def ensure_files(cfg):
    manuscript_tex = ROOT / cfg["manuscript_tex"]
    response_tex = ROOT / cfg["response_letter_tex"]
    if not manuscript_tex.exists():
        sys.stderr.write(f"Missing: {manuscript_tex}\n")
        sys.exit(1)
    if not response_tex.exists():
        sys.stderr.write(f"Missing: {response_tex}\n")
        sys.exit(1)


def build_manuscript(cfg):
    manuscript_tex = ROOT / cfg["manuscript_tex"]
    manuscript_dir = manuscript_tex.parent
    manuscript_file = manuscript_tex.name
    manuscript_doc = cfg["manuscript_doc"]
    print("[1/4] Building manuscript...")
    run(["pdflatex", manuscript_file], manuscript_dir)
    run(["bibtex", manuscript_doc], manuscript_dir)
    run(["pdflatex", manuscript_file], manuscript_dir)
    run(["pdflatex", manuscript_file], manuscript_dir)


def build_response_letter(cfg):
    response_tex = cfg["response_letter_tex"]
    response_doc = cfg["response_letter_doc"]
    print("[2/4] Building response letter...")
    run(["pdflatex", response_tex], ROOT)
    run(["biber", response_doc], ROOT)
    run(["pdflatex", response_tex], ROOT)
    run(["pdflatex", response_tex], ROOT)


def normalize_links(cfg):
    if not cfg.get("enable_link_normalization", False):
        return
    print("[3/4] Normalizing embedded PDF links...")
    response_pdf = ROOT / cfg["response_letter_pdf"]
    response_pdf_name = Path(cfg["response_letter_pdf"]).name
    manuscript_pdf_name = Path(cfg["manuscript_pdf"]).name
    anchor_prefix = cfg.get("anchor_prefix", "response.")
    run(
        [
            sys.executable,
            "scripts/normalize_links.py",
            "--response-pdf",
            str(response_pdf),
            "--manuscript-pdf",
            str(ROOT / cfg["manuscript_pdf"]),
            "--response-pdf-name",
            response_pdf_name,
            "--manuscript-pdf-name",
            manuscript_pdf_name,
            "--anchor-prefix",
            anchor_prefix,
        ],
        ROOT,
    )


def main():
    if not CONFIG_FILE.exists():
        sys.stderr.write(f"Missing: {CONFIG_FILE}\n")
        sys.exit(1)
    cfg = parse_simple_yaml(CONFIG_FILE)
    ensure_files(cfg)
    build_manuscript(cfg)
    build_response_letter(cfg)
    normalize_links(cfg)
    print(f"[4/4] Done. Open {cfg['response_letter_pdf']} to verify links.")


if __name__ == "__main__":
    main()
