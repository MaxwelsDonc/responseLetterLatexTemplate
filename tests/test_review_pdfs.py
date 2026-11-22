"""Build and verify the bundled ACM example in isolation."""

from collections import Counter
from contextlib import closing
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import ImageChops
import pikepdf
import pypdfium2

from scripts.link_review_pdfs import ReviewLinkError, link_review_pdfs, named_anchors


ROOT = Path(__file__).resolve().parents[1]
SCALE = 2


def run(*command, cwd):
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise RuntimeError("\n".join(result.stdout.splitlines()[-35:]))


def remote_links(pdf):
    for index, page in enumerate(pdf.pages):
        for annotation in page.obj.get("/Annots", []):
            action = annotation.get("/A", {})
            if str(action.get("/S")) == "/GoToR":
                yield index, annotation, str(action.F), str(action.D)


def render(path, index):
    with pypdfium2.PdfDocument(path) as document, closing(document[index]) as page:
        with closing(page.render(scale=SCALE, draw_annots=True)) as bitmap:
            return bitmap.to_pil().convert("RGB")


class ReviewPDFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace = tempfile.TemporaryDirectory(prefix="review-pdf-test-")
        cls.addClassCleanup(workspace.cleanup)
        cls.project = Path(workspace.name)
        files = (
            "ar2rc.cls", "commands.sty", "project_config.yaml", "ref.bib",
            "responseLetter.tex", "revision-marks.sty", "demo/main.tex",
            "scripts/build.py", "scripts/check_ids.py", "scripts/link_review_pdfs.py",
        )
        for name in files:
            target = cls.project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        run(sys.executable, "scripts/build.py", "--strict-ids", cwd=cls.project)
        cls.letter = cls.project / "output/pdf/responseLetter.pdf"
        cls.paper = cls.project / "output/pdf/manuscript.pdf"
        cls.original = cls.project / "demo/main.pdf"

    def test_precise_destinations_and_shared_revision(self):
        with pikepdf.open(self.letter) as letter, pikepdf.open(self.paper) as paper:
            revisions = named_anchors(paper, "revision.")
            replies = named_anchors(letter, "reply.")
            self.assertEqual(len(letter.pages), 5)
            self.assertEqual(len(paper.pages), 1)
            self.assertEqual(revisions["E1"].page, revisions["E5"].page)
            self.assertGreater(revisions["E1"].y, revisions["E5"].y)
            forward = Counter((page, filename, target) for page, _, filename, target in remote_links(letter))
            self.assertEqual(forward, {
                (2, "manuscript.pdf", "revision.E1"): 1,
                (2, "manuscript.pdf", "revision.E3"): 1,
                (2, "manuscript.pdf", "revision.E4"): 1,
                (3, "manuscript.pdf", "revision.E2"): 1,
                (4, "manuscript.pdf", "revision.E2"): 1,
                (4, "manuscript.pdf", "revision.E5"): 1,
            })
            back = {str(annot.NM): (filename, target) for _, annot, filename, target in remote_links(paper)}
            self.assertEqual(len(back), 6)
            self.assertEqual(back["review:E2:R2-C1"], ("responseLetter.pdf", "reply.R2-C1"))
            self.assertEqual(back["review:E2:R3-C2"], ("responseLetter.pdf", "reply.R3-C2"))
            self.assertEqual((replies["R2-C1"].page, replies["R3-C2"].page), (3, 4))

    def test_body_matches_acm_baseline_and_only_margin_buttons_appear(self):
        demo = self.original.parent
        source = (demo / "main.tex").read_text(encoding="utf-8")
        baseline = re.sub(r"\\rpoint\[[^\]]+\]", "", source)
        for command in (
            r"\usepackage{revision-marks}", r"\setresponseletter{responseLetter}",
            r"\showrevmarksfalse", r"\ifdefined\BuildCombinedReviewPDF\showrevmarkstrue\fi",
        ):
            baseline = baseline.replace(command + "\n", "")
        (demo / "baseline.tex").write_text(baseline, encoding="utf-8")
        run("pdflatex", "-halt-on-error", "-interaction=nonstopmode", "baseline.tex", cwd=demo)
        original = render(self.original, 0)
        baseline = render(demo / "baseline.pdf", 0)
        self.assertIsNone(ImageChops.difference(original, baseline).getbbox())

        linked = render(self.paper, 0)
        self.assertEqual(original.size, linked.size)
        difference = ImageChops.difference(original, linked)
        with pikepdf.open(self.paper) as paper:
            for _, annotation, _, _ in remote_links(paper):
                left, bottom, right, top = map(float, annotation.Rect)
                box = (
                    int(left * SCALE) - 1, original.height - int(top * SCALE) - 1,
                    int(right * SCALE) + 1, original.height - int(bottom * SCALE) + 1,
                )
                self.assertIsNotNone(difference.crop(box).getbbox())
                difference.paste((0, 0, 0), box)
        self.assertIsNone(difference.getbbox())

    def test_missing_anchor_keeps_the_previous_pair(self):
        raw = self.project / "output/review-build"
        aux = raw / "responseLetter.aux"
        bad_aux = raw / "bad.aux"
        bad_aux.write_text(aux.read_text(encoding="utf-8").replace("{E5}", "{E404}"), encoding="utf-8")
        originals = (self.letter.read_bytes(), self.paper.read_bytes())
        with self.assertRaisesRegex(ReviewLinkError, "Missing manuscript anchors: E404"):
            link_review_pdfs(raw / "responseLetter.pdf", self.original, bad_aux, self.letter.parent)
        self.assertEqual((self.letter.read_bytes(), self.paper.read_bytes()), originals)
