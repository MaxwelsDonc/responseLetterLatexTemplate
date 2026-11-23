"""Publish independently laid-out review pages with exact revision links."""

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import math
import re
import shutil
import tempfile

import pikepdf
import pypdfium2


LETTER_NAME = "responseLetter.pdf"
MANUSCRIPT_NAME = "manuscript.pdf"
RECORD = r"\ReviewLinkRecord"
IDENTIFIER = r"[A-Za-z0-9][A-Za-z0-9_.-]*"
LINK_RECORD = re.compile(rf"{re.escape(RECORD)}\s*\{{({IDENTIFIER})\}}\{{({IDENTIFIER})\}}")
RENDER_SCALE = 2
EDGE_INSET = 8
BUTTON_GAP = 4
BADGE_OFFSETS = (0, 16, -16, 32, -32, 48, -48, 64, -64)
REVIEW_CONTEXT_POINTS = 160


class ReviewLinkError(ValueError):
    pass


@dataclass(frozen=True)
class Anchor:
    page: int
    x: float
    y: float


def read_link_records(aux_path):
    links = []
    for line in aux_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(RECORD):
            match = LINK_RECORD.fullmatch(line)
            if match is None:
                raise ReviewLinkError(f"Invalid reply or revision ID in {line}")
            links.append(match.groups())
    if not links:
        raise ReviewLinkError("The response letter contains no review links. Use \\elink{revision-id}.")
    return links


def named_anchors(pdf, prefix):
    names = pdf.Root.get("/Names", {}).get("/Dests")
    if names is None:
        return {}
    pages = {page.obj.objgen: index for index, page in enumerate(pdf.pages)}
    anchors = {}
    for name, destination in pikepdf.NameTree(names).items():
        if not name.startswith(prefix):
            continue
        if isinstance(destination, pikepdf.Dictionary):
            destination = destination.get("/D")
        if (
            not isinstance(destination, pikepdf.Array)
            or len(destination) != 5
            or destination[1] != pikepdf.Name.XYZ
            or getattr(destination[0], "objgen", None) not in pages
            or destination[2] is None
            or destination[3] is None
        ):
            raise ReviewLinkError(f"Anchor {name} must identify an exact position on a page.")
        revision_id = name.removeprefix(prefix)
        anchors[revision_id] = Anchor(pages[destination[0].objgen], float(destination[2]), float(destination[3]))
    return anchors


def check_forward_links(letter, records, revisions, replies, strict):
    expected = Counter(revision for _, revision in records)
    missing = sorted(expected.keys() - revisions.keys())
    if missing:
        raise ReviewLinkError(f"Missing manuscript anchors: {', '.join(missing)}")
    missing = sorted({reply for reply, _ in records} - replies.keys())
    if missing:
        raise ReviewLinkError(f"Missing response anchors: {', '.join(missing)}")
    unused = sorted(revisions.keys() - expected.keys())
    if unused:
        message = f"Unlinked manuscript revisions: {', '.join(unused)}"
        if strict:
            raise ReviewLinkError(message)
        print(message)

    actual = Counter()
    links = []
    for page in letter.pages:
        for annotation in page.obj.get("/Annots", []):
            action = annotation.get("/A", {})
            if str(action.get("/S")) != "/GoToR" or str(action.get("/F")) != MANUSCRIPT_NAME:
                continue
            target = str(action.get("/D"))
            if target.startswith("revision."):
                actual[target.removeprefix("revision.")] += 1
                links.append((annotation, target))
    mismatches = sorted(
        revision for revision in expected.keys() | actual.keys()
        if expected[revision] != actual[revision]
    )
    if mismatches:
        raise ReviewLinkError(f"Missing or extra forward links in the response PDF: {', '.join(mismatches)}")
    return links


def review_badges(letter, edits):
    badges = {}
    for page in letter.pages:
        for _, form in page.resources.get("/XObject", {}).items():
            if "/ReviewBadge" in form:
                badges[str(form.ReviewBadge)] = form
    missing = sorted(edits.keys() - badges.keys())
    if missing:
        raise ReviewLinkError(f"Missing response badge artwork: {', '.join(missing)}. Rebuild the response letter.")
    return badges


def rectangles_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def is_blank(rect, bounds, image, occupied):
    if any(rectangles_overlap(rect, other) for other in occupied):
        return False
    left, bottom, right, top = rect
    page_left, _, _, page_top = bounds
    box = (
        math.floor((left - page_left) * RENDER_SCALE),
        math.floor((page_top - top) * RENDER_SCALE),
        math.ceil((right - page_left) * RENDER_SCALE),
        math.ceil((page_top - bottom) * RENDER_SCALE),
    )
    return image.crop(box).getextrema()[0] >= 250


def margin_rectangle(width, height, anchor, bounds, image, occupied, offset):
    left, bottom, right, top = bounds
    if width > right - left - 2 * EDGE_INSET or height > top - bottom - 2 * EDGE_INSET:
        return None
    y = min(max(anchor.y - height / 2, bottom + EDGE_INSET), top - EDGE_INSET - height) + offset
    if y < bottom + EDGE_INSET or y + height > top - EDGE_INSET:
        return None
    for x in (right - EDGE_INSET - width, left + EDGE_INSET):
        rect = (x, y, x + width, y + height)
        if is_blank(rect, bounds, image, occupied):
            return rect


def badge_columns(sizes, rows):
    columns = [sizes[start:start + rows] for start in range(0, len(sizes), rows)]
    heights = [sum(height for _, _, height in column) + BUTTON_GAP * (len(column) - 1) for column in columns]
    height = max(heights)
    placements = []
    x = 0
    for column in columns:
        width = max(width for _, width, _ in column)
        top = height
        for edit, badge_width, badge_height in column:
            bottom = top - badge_height
            placements.append((edit, (x + width - badge_width, bottom, x + width, top)))
            top = bottom - BUTTON_GAP
        x += width + BUTTON_GAP
    return x - BUTTON_GAP, height, placements


def margin_badges(edits, badges, anchor, bounds, image, occupied):
    sizes = []
    for edit in edits:
        box = pikepdf.Rectangle(badges[edit].BBox)
        sizes.append((edit, float(box.width), float(box.height)))
    layouts = [badge_columns(sizes, rows) for rows in range(len(sizes), 0, -1)]
    # Try both margins near the anchor before shifting farther. With equal
    # proximity, prefer one column and then wrap at the original badge size.
    for offset in BADGE_OFFSETS:
        for width, height, placements in layouts:
            rect = margin_rectangle(width, height, anchor, bounds, image, occupied, offset)
            if rect is not None:
                x, y, _, _ = rect
                return [
                    (edit, (x + left, y + bottom, x + right, y + top))
                    for edit, (left, bottom, right, top) in placements
                ]

    # Use separate gaps if neither margin has room for the whole group.
    placements = []
    reserved = occupied.copy()
    for edit, width, height in sizes:
        for offset in BADGE_OFFSETS:
            rect = margin_rectangle(width, height, anchor, bounds, image, reserved, offset)
            if rect is not None:
                break
        if rect is None:
            raise ReviewLinkError(f"No blank margin for revision {edit} on manuscript page {anchor.page + 1}.")
        placements.append((edit, rect))
        reserved.append(rect)
    return placements


def add_button(pdf, page, badge, edit, target, rect, *, internal):
    page.add_overlay(badge, pikepdf.Rectangle(*rect), shrink=False, expand=False)
    if "/Annots" not in page.obj:
        page.obj.Annots = pikepdf.Array()
    action = pikepdf.Dictionary(S=pikepdf.Name.GoTo, D=pikepdf.String(target))
    if not internal:
        action.S = pikepdf.Name.GoToR
        action.F = pikepdf.String(LETTER_NAME)
    annotation = pikepdf.Dictionary(
        Type=pikepdf.Name.Annot,
        Subtype=pikepdf.Name.Link,
        Rect=pikepdf.Array(rect),
        Border=pikepdf.Array([0, 0, 0]),
        NM=pikepdf.String(f"review:{edit}"),
        Contents=pikepdf.String(f"Return to the response for revision {edit}"),
        A=action,
    )
    page.obj.Annots.append(pdf.make_indirect(annotation))


def add_return_links(pdf, renderer, targets, revisions, badges, *, manuscript_offset=None):
    by_page = defaultdict(lambda: defaultdict(list))
    for edit in targets:
        anchor = revisions[edit]
        by_page[anchor.page][anchor].append(edit)
    for index, groups in by_page.items():
        page = pdf.pages[(manuscript_offset or 0) + index]
        occupied = [tuple(map(float, annot.Rect)) for annot in page.obj.get("/Annots", []) if "/Rect" in annot]
        with closing(renderer[index]) as rendered_page:
            if rendered_page.get_rotation() != 0:
                raise ReviewLinkError(f"Cannot place margin links on rotated manuscript page {index + 1}.")
            bounds = rendered_page.get_bbox()
            with closing(rendered_page.render(scale=RENDER_SCALE, grayscale=True, draw_annots=True)) as bitmap:
                image = bitmap.to_pil()
                for anchor, edits in groups.items():
                    for edit, rect in margin_badges(edits, badges, anchor, bounds, image, occupied):
                        add_button(pdf, page, badges[edit], edit, targets[edit], rect, internal=manuscript_offset is not None)
                        occupied.append(rect)


def review_destination(page, anchor):
    _, bottom, _, top = map(float, page.cropbox)
    # XYZ aligns the given point to the top-left of the viewer.
    view_top = min(top, max(bottom, anchor.y + REVIEW_CONTEXT_POINTS))
    return pikepdf.Array([page.obj, pikepdf.Name.XYZ, anchor.x, view_top, None])


def append_manuscript(letter, manuscript, revisions, replies, forward_links):
    offset = len(letter.pages)
    duplicates = named_anchors(letter, "revision.").keys() & revisions.keys()
    if duplicates:
        raise ReviewLinkError(f"Revision anchors already in the response PDF: {', '.join(sorted(duplicates))}")
    with letter.open_outline() as outline:
        outline_offset = len(outline.root)
    letter.add_pages_from(manuscript)
    with letter.open_outline() as outline:
        appendix = pikepdf.OutlineItem("Revised Manuscript", offset)
        appendix.children = outline.root[outline_offset:]
        outline.root[outline_offset:] = [appendix]
    destinations = pikepdf.NameTree(letter.Root.Names.Dests)
    for edit, anchor in revisions.items():
        destinations[f"revision.{edit}"] = review_destination(letter.pages[offset + anchor.page], anchor)
    for reply, anchor in replies.items():
        destinations[f"reply.{reply}"] = review_destination(letter.pages[anchor.page], anchor)
    for annotation, target in forward_links:
        annotation.A = pikepdf.Dictionary(S=pikepdf.Name.GoTo, D=pikepdf.String(target))
    return offset


def link_review_pdfs(
    letter_path: Path, manuscript_path: Path, aux_path: Path, output_dir: Path, *, strict=False, separate=False,
):
    """Stage the finished review PDF before publishing it."""
    output_names = (LETTER_NAME, MANUSCRIPT_NAME) if separate else (LETTER_NAME,)
    outputs = [output_dir / name for name in output_names]
    if {path.resolve() for path in outputs} & {letter_path.resolve(), manuscript_path.resolve()}:
        raise ReviewLinkError("The review output directory must not overwrite the unprocessed PDFs.")
    records = read_link_records(aux_path)
    targets = {}
    for reply, edit in records:
        target = f"reply.{reply}"
        if targets.setdefault(edit, target) != target:
            raise ReviewLinkError(
                f"Revision label {edit} points back to more than one reply. "
                "Use a distinct label for each reply at the same manuscript location."
            )
    with pikepdf.open(letter_path) as letter, pikepdf.open(manuscript_path) as manuscript:
        revisions = named_anchors(manuscript, "revision.")
        replies = named_anchors(letter, "reply.")
        forward_links = check_forward_links(letter, records, revisions, replies, strict)
        badges = review_badges(letter, targets)
        offset = None if separate else append_manuscript(letter, manuscript, revisions, replies, forward_links)
        print(f"[4/5] Adding one return link for each of {len(targets)} revisions...")
        with pypdfium2.PdfDocument(manuscript_path) as renderer:
            add_return_links(manuscript if separate else letter, renderer, targets, revisions, badges, manuscript_offset=offset)
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_dir) as staging:
            stage = Path(staging)
            if separate:
                manuscript.save(stage / MANUSCRIPT_NAME)
                shutil.copyfile(letter_path, stage / LETTER_NAME)
            else:
                letter.save(stage / LETTER_NAME)
            for destination in outputs:
                (stage / destination.name).replace(destination)
