"""Build and verify the bundled ACM examples in isolation."""

from collections import Counter
from contextlib import closing
from ctypes import byref, c_float, c_int
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageChops
import pikepdf
import pypdfium2
from pypdfium2 import raw as pdfium

from scripts.link_review_pdfs import (
    REVIEW_CONTEXT_POINTS, Anchor, ReviewLinkError, link_review_pdfs, margin_badges, named_anchors, review_destination,
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


def build_example(test_class, files, config):
    workspace = tempfile.TemporaryDirectory(prefix="review-pdf-test-")
    test_class.addClassCleanup(workspace.cleanup)
    project = Path(workspace.name)
    for name in (
        "ar2rc.cls", "commands.sty", "ref.bib", "revision-marks.sty",
        "scripts/build.py", "scripts/check_ids.py", "scripts/link_review_pdfs.py",
        config, *files,
    ):
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    run(sys.executable, "scripts/build.py", "--config", config, "--strict-ids", cwd=project)
    return project


def assert_manuscript_rendering(test, original, review_path):
    source = original.with_suffix(".tex").read_text(encoding="utf-8")
    baseline = re.sub(r"\\rpoint\[[^\]]+\]", "", source)
    for command in (
        r"\usepackage{revision-marks}", r"\setresponseletter{responseLetter}",
        r"\showrevmarksfalse", r"\ifdefined\BuildCombinedReviewPDF\showrevmarkstrue\fi",
    ):
        baseline = baseline.replace(command + "\n", "")
    baseline_path = original.with_name("baseline.tex")
    baseline_pdf_path = baseline_path.with_suffix(".pdf")
    baseline_path.write_text(baseline, encoding="utf-8")
    for _ in range(3):
        run("pdflatex", "-halt-on-error", "-interaction=nonstopmode", baseline_path.name, cwd=original.parent)
    with (
        pikepdf.open(original) as manuscript,
        pikepdf.open(baseline_pdf_path) as baseline_pdf,
        pikepdf.open(review_path) as review,
    ):
        test.assertEqual(len(manuscript.pages), len(baseline_pdf.pages))
        offset = len(review.pages) - len(manuscript.pages)
        for index in range(len(manuscript.pages)):
            with test.subTest(manuscript_page=index + 1):
                clean = render(original, index)
                baseline_image = render(baseline_pdf_path, index)
                test.assertEqual(clean.size, baseline_image.size)
                test.assertIsNone(ImageChops.difference(clean, baseline_image).getbbox())

                linked = render(review_path, offset + index)
                test.assertEqual(clean.size, linked.size)
                difference = ImageChops.difference(clean, linked)
                for page, annotation, target in review_links(review):
                    if page != offset + index or not target.startswith("reply."):
                        continue
                    left, bottom, right, top = map(float, annotation.Rect)
                    box = (
                        int(left * SCALE) - 1, clean.height - int(top * SCALE) - 1,
                        int(right * SCALE) + 1, clean.height - int(bottom * SCALE) + 1,
                    )
                    test.assertEqual(clean.crop(box).getextrema(), ((255, 255),) * 3)
                    test.assertIsNotNone(difference.crop(box).getbbox())
                    difference.paste((0, 0, 0), box)
                test.assertIsNone(difference.getbbox())


class ReviewPDFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = build_example(
            cls, ("responseLetter.tex", "demo/main.tex"), "project_config.yaml",
        )
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

    def test_same_location_buttons_have_distinct_labels_and_stack_vertically(self):
        with pikepdf.open(self.review) as review, pypdfium2.PdfDocument(self.review) as pdf:
            badges = {}
            with closing(pdf[5]) as page, closing(page.get_textpage()) as text:
                for index, annotation, _ in review_links(review):
                    if index == 5:
                        rectangle = tuple(map(float, annotation.Rect))
                        label = " ".join(text.get_text_bounded(*rectangle).split())
                        badges[label] = rectangle
            self.assertCountEqual(badges, ["E1", "E2", "E3", "E4", "E5", "E6"])
            self.assertEqual(badges["E1"][2], badges["E2"][2])
            self.assertGreater(badges["E1"][1], badges["E2"][3])
            with pikepdf.open(self.original) as manuscript:
                anchor = named_anchors(manuscript, "revision.")["E1"]
            self.assertLess(badges["E2"][1], anchor.y)
            self.assertGreater(badges["E1"][3], anchor.y)

    def test_reply_badges_have_no_printed_page_reference(self):
        with pypdfium2.PdfDocument(self.review) as pdf:
            for index in (2, 3, 4):
                with closing(pdf[index]) as page, closing(page.get_textpage()) as text:
                    self.assertNotRegex(text.get_text_range(), r"\bE[1-6]\s*\(p\.\s*\d+")

    def test_manuscript_badges_reuse_the_letter_artwork_at_its_original_size(self):
        with pikepdf.open(self.review) as review:
            def badges(pages):
                return {
                    str(form.ReviewBadge): form
                    for page in pages
                    for _, form in page.resources.get("/XObject", {}).items()
                    if "/ReviewBadge" in form
                }

            letter = badges(review.pages[:5])
            margin = badges([review.pages[5]])
            self.assertCountEqual(margin, ["E1", "E2", "E3", "E4", "E5", "E6"])
            for index, annotation, _ in review_links(review):
                if index != 5:
                    continue
                label = str(annotation.NM).removeprefix("review:")
                self.assertEqual(margin[label].objgen, letter[label].objgen)
                box = pikepdf.Rectangle(margin[label].BBox)
                clickable = pikepdf.Rectangle(annotation.Rect)
                self.assertAlmostEqual(box.width, clickable.width, places=5)
                self.assertAlmostEqual(box.height, clickable.height, places=5)

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
        assert_manuscript_rendering(self, self.original, self.review)

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


class TwoColumnReviewPDFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo = "demo/two-column"
        cls.project = build_example(
            cls, (f"{demo}/manuscript.tex", f"{demo}/response.tex"),
            f"{demo}/project_config.yaml",
        )
        cls.original = cls.project / demo / "manuscript.pdf"
        cls.letter = cls.project / "output/review-build/two-column-response.pdf"
        cls.review = cls.project / "output/pdf/two-column/responseLetter.pdf"

    def test_cross_page_badges_resolve_to_the_expected_anchors(self):
        with (
            pikepdf.open(self.original) as manuscript,
            pikepdf.open(self.letter) as letter,
            pikepdf.open(self.review) as review,
            pypdfium2.PdfDocument(self.review) as reader,
        ):
            self.assertEqual(len(manuscript.pages), 2)
            self.assertEqual(len(letter.pages), 3)
            self.assertEqual(len(review.pages), 5)
            left, _, right, _ = map(float, manuscript.pages[0].cropbox)
            column_boundary = (left + right) / 2
            revisions = named_anchors(manuscript, "revision.")
            self.assertLess(revisions["E3"].x, column_boundary)
            self.assertGreater(revisions["E4"].x, column_boundary)
            self.assertGreater(revisions["E1"].x, column_boundary)
            self.assertEqual(revisions["E1"], revisions["E2"])
            self.assertEqual(
                {label: anchor.page for label, anchor in revisions.items()},
                {"E1": 1, "E2": 1, "E3": 0, "E4": 0},
            )
            replies = named_anchors(letter, "reply.")
            self.assertEqual(
                {label: replies[label].page for label in ("R1-C1", "R2-C1", "R2-C2")},
                {"R1-C1": 1, "R2-C1": 2, "R2-C2": 2},
            )
            self.assertGreater(replies["R2-C1"].y, replies["R2-C2"].y)

            expected = {
                "E1": "R1-C1", "E2": "R2-C1", "E3": "R1-C1", "E4": "R2-C2",
            }
            forward = {}
            back = {}
            for source_page, annotation, target in review_links(review):
                if target.startswith("revision."):
                    label = target.removeprefix("revision.")
                    self.assertNotIn(label, forward)
                    forward[label] = source_page
                    anchor = revisions[label]
                    target_page = anchor.page + len(letter.pages)
                else:
                    label = str(annotation.NM).removeprefix("review:")
                    self.assertNotIn(label, back)
                    self.assertEqual(target, f"reply.{expected[label]}")
                    back[label] = source_page
                    anchor = replies[expected[label]]
                    target_page = anchor.page
                with self.subTest(label=label, source_page=source_page, target=target):
                    self.assertNotEqual(source_page, target_page)
                    self.assert_click_destination(reader, source_page, annotation, target_page, anchor, review)
            self.assertEqual(forward, {label: replies[reply].page for label, reply in expected.items()})
            self.assertEqual(back, {label: revisions[label].page + len(letter.pages) for label in expected})

    def assert_click_destination(self, reader, source_page, annotation, target_page, anchor, review):
        left, bottom, right, top = map(float, annotation.Rect)
        with closing(reader[source_page]) as page:
            hit = pdfium.FPDFLink_GetLinkAtPoint(page.raw, (left + right) / 2, (bottom + top) / 2)
            self.assertTrue(hit)
            action = pdfium.FPDFLink_GetAction(hit)
            self.assertTrue(action)
            self.assertEqual(pdfium.FPDFAction_GetType(action), pdfium.PDFACTION_GOTO)
            destination = pdfium.FPDFAction_GetDest(reader.raw, action)
            self.assertTrue(destination)
            self.assertEqual(pdfium.FPDFDest_GetDestPageIndex(reader.raw, destination), target_page)
            has_x, has_y, has_zoom = c_int(), c_int(), c_int()
            x, y, zoom = c_float(), c_float(), c_float()
            self.assertTrue(pdfium.FPDFDest_GetLocationInPage(
                destination, byref(has_x), byref(has_y), byref(has_zoom),
                byref(x), byref(y), byref(zoom),
            ))
            self.assertEqual((has_x.value, has_y.value, has_zoom.value), (1, 1, 0))
            self.assertAlmostEqual(x.value, anchor.x, places=3)
            crop_top = float(review.pages[target_page].cropbox[3])
            self.assertAlmostEqual(y.value, min(crop_top, anchor.y + REVIEW_CONTEXT_POINTS), places=3)

    def test_both_pages_match_the_unmarked_acm_baseline_outside_the_badges(self):
        assert_manuscript_rendering(self, self.original, self.review)


class MarginBadgeTests(unittest.TestCase):
    def test_narrow_margin_keeps_three_badges_by_the_anchor_above_the_footer(self):
        bounds = (0, 0, 120, 100)
        image = Image.new("L", (120 * SCALE, 100 * SCALE), 255)
        # Body copy leaves a right margin wide enough for one badge.
        image.paste(0, (0, 0, 96 * SCALE, 72 * SCALE))
        image.paste(0, (0, 86 * SCALE, 96 * SCALE, 90 * SCALE))
        artwork = {edit: pikepdf.Dictionary(BBox=[0, 0, 14, 8]) for edit in ("E1", "E2", "E3")}

        placed = margin_badges(artwork, artwork, Anchor(page=0, x=80, y=45), bounds, image, [])

        self.assertEqual(placed, [
            ("E1", (98, 53, 112, 61)),
            ("E2", (98, 41, 112, 49)),
            ("E3", (98, 29, 112, 37)),
        ])

    def test_short_space_wraps_to_a_second_column_at_full_size(self):
        bounds = (0, 0, 120, 100)
        image = Image.new("L", (120 * SCALE, 100 * SCALE), 255)
        image.paste(0, (0, 0, 120 * SCALE, 28 * SCALE))
        image.paste(0, (0, 52 * SCALE, 120 * SCALE, 100 * SCALE))
        artwork = {edit: pikepdf.Dictionary(BBox=[0, 0, 14, 8]) for edit in ("E1", "E2", "E3")}

        placed = margin_badges(artwork, artwork, Anchor(page=0, x=60, y=60), bounds, image, [])

        self.assertEqual(placed, [
            ("E1", (80, 62, 94, 70)),
            ("E2", (80, 50, 94, 58)),
            ("E3", (98, 62, 112, 70)),
        ])
