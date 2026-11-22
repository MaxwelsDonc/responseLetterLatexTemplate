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

from scripts.link_review_pdfs import (
    REVIEW_CONTEXT_POINTS, Anchor, ReviewLinkError, link_review_pdfs, named_anchors, review_destination,
)


ROOT = Path(__file__).resolve().parents[1]
SCALE = 2


def run(*command, cwd):
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise RuntimeError("\n".join(result.stdout.splitlines()[-35:]))


def review_links(pdf):
    for index, page in enumerate(pdf.pages):
        for annotation in page.obj.get("/Annots", []):
            action = annotation.get("/A", {})
            target = str(action.get("/D"))
            if target.startswith(("revision.", "reply.")):
                yield index, annotation, target


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
        cls.review = cls.project / "output/pdf/responseLetter.pdf"
        cls.original = cls.project / "demo/main.pdf"

    def test_precise_destinations_and_shared_revision(self):
        with pikepdf.open(self.review) as review:
            revisions = named_anchors(review, "revision.")
            replies = named_anchors(review, "reply.")
            self.assertEqual(len(review.pages), 6)
            self.assertEqual(list(self.review.parent.glob("*.pdf")), [self.review])
            self.assertEqual(revisions["E1"].page, 5)
            self.assertEqual(revisions["E1"], revisions["E2"])
            self.assertGreater(revisions["E1"].y, revisions["E5"].y)
            links = list(review_links(review))
            self.assertTrue(all(annotation.A.S == pikepdf.Name.GoTo for _, annotation, _ in links))
            self.assertTrue(all("/F" not in annotation.A for _, annotation, _ in links))
            forward = Counter((page, target) for page, _, target in links if target.startswith("revision."))
            self.assertEqual(forward, {
                (2, "revision.E3"): 1,
                (2, "revision.E4"): 1,
                (2, "revision.E5"): 1,
                (3, "revision.E1"): 1,
                (4, "revision.E2"): 1,
                (4, "revision.E6"): 1,
            })
            back = [(page, str(annot.NM), target) for page, annot, target in links if target.startswith("reply.")]
            self.assertEqual(len(back), 6)
            shared = {
                name: (page, replies[target.removeprefix("reply.")].page)
                for page, name, target in back if name in {"review:E1", "review:E2"}
            }
            self.assertEqual(shared, {"review:E1": (5, 3), "review:E2": (5, 4)})
            with review.open_outline() as outline:
                self.assertEqual(outline.root[-1].title, "Revised Manuscript")

    def test_same_location_buttons_have_distinct_labels_and_share_a_row(self):
        with pikepdf.open(self.review) as review, pypdfium2.PdfDocument(self.review) as pdf:
            badges = {}
            with closing(pdf[5]) as page, closing(page.get_textpage()) as text:
                for index, annotation, _ in review_links(review):
                    if index == 5:
                        rectangle = tuple(map(float, annotation.Rect))
                        label = " ".join(text.get_text_bounded(*rectangle).split())
                        badges[label] = rectangle
            self.assertCountEqual(badges, ["E1", "E2", "E3", "E4", "E5", "E6"])
            self.assertEqual(badges["E1"][1], badges["E2"][1])
            self.assertLess(badges["E1"][2], badges["E2"][0])

    def test_links_leave_reading_context_and_keep_the_current_zoom(self):
        raw_letter = self.project / "output/review-build/responseLetter.pdf"
        with pikepdf.open(self.review) as review:
            destinations = pikepdf.NameTree(review.Root.Names.Dests)
            for path, prefix, offset in ((self.original, "revision.", 5), (raw_letter, "reply.", 0)):
                with pikepdf.open(path) as source:
                    for name, anchor in named_anchors(source, prefix).items():
                        page = review.pages[offset + anchor.page]
                        dest = destinations[prefix + name]
                        self.assertEqual(dest[0].objgen, page.obj.objgen)
                        self.assertEqual(dest[1], pikepdf.Name.XYZ)
                        self.assertAlmostEqual(float(dest[2]), anchor.x)
                        self.assertAlmostEqual(float(dest[3]), min(float(page.cropbox[3]), anchor.y + REVIEW_CONTEXT_POINTS))
                        self.assertIsNone(dest[4])

    def test_view_near_page_top_stays_within_crop_box(self):
        with pikepdf.Pdf.new() as pdf:
            page = pdf.add_blank_page()
            page.cropbox = pikepdf.Array([10, 10, 602, 782])
            dest = review_destination(page, Anchor(page=0, x=72, y=750))
            self.assertEqual(dest[3], 782)

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

        linked = render(self.review, 5)
        self.assertEqual(original.size, linked.size)
        difference = ImageChops.difference(original, linked)
        with pikepdf.open(self.review) as review:
            for index, annotation, _ in review_links(review):
                if index != 5:
                    continue
                left, bottom, right, top = map(float, annotation.Rect)
                box = (
                    int(left * SCALE) - 1, original.height - int(top * SCALE) - 1,
                    int(right * SCALE) + 1, original.height - int(bottom * SCALE) + 1,
                )
                self.assertIsNotNone(difference.crop(box).getbbox())
                difference.paste((0, 0, 0), box)
        self.assertIsNone(difference.getbbox())

    def test_missing_anchor_keeps_the_previous_review_pdf(self):
        raw = self.project / "output/review-build"
        aux = raw / "responseLetter.aux"
        bad_aux = raw / "bad.aux"
        bad_aux.write_text(aux.read_text(encoding="utf-8").replace("{E5}", "{E404}"), encoding="utf-8")
        original = self.review.read_bytes()
        with self.assertRaisesRegex(ReviewLinkError, "Missing manuscript anchors: E404"):
            link_review_pdfs(raw / "responseLetter.pdf", self.original, bad_aux, self.review.parent)
        self.assertEqual(self.review.read_bytes(), original)

    def test_a_label_cannot_return_to_two_different_replies(self):
        raw = self.project / "output/review-build"
        aux = raw / "responseLetter.aux"
        bad_aux = raw / "duplicate-label.aux"
        bad_aux.write_text(aux.read_text(encoding="utf-8").replace("{E2}", "{E1}"), encoding="utf-8")
        original = self.review.read_bytes()
        with self.assertRaisesRegex(ReviewLinkError, "Revision label E1 points back to more than one reply"):
            link_review_pdfs(raw / "responseLetter.pdf", self.original, bad_aux, self.review.parent)
        self.assertEqual(self.review.read_bytes(), original)
