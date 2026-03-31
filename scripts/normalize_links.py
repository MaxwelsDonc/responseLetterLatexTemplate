#!/usr/bin/env python3
from pathlib import Path
import argparse
import pikepdf


def extract_named_dest_from_uri(uri: str):
    marker = "#nameddest="
    if marker not in uri:
        return None
    return uri.split(marker, 1)[1]


def normalize_actions(response_pdf_path: Path, manuscript_pdf_path: Path, response_pdf_name: str, manuscript_pdf_name: str, anchor_prefix: str):
    changed = 0
    with pikepdf.open(response_pdf_path, allow_overwriting_input=True) as response_pdf:
        with pikepdf.open(manuscript_pdf_path) as manuscript_pdf:
            manuscript_to_response = {}
            overlay_refs = []
            for page in response_pdf.pages:
                annots = page.get("/Annots", None)
                if annots is None:
                    continue
                for annot_ref in annots:
                    annot = annot_ref
                    action = annot.get("/A", None)
                    if action is None or str(action.get("/S", "")) != "/GoToR":
                        continue
                    file_spec = action.get("/F", None)
                    file_name = None
                    if isinstance(file_spec, pikepdf.String):
                        file_name = str(file_spec)
                    elif isinstance(file_spec, pikepdf.Dictionary) and "/F" in file_spec:
                        file_name = str(file_spec["/F"])
                    dest = action.get("/D", None)
                    if file_name is None or Path(file_name).name != manuscript_pdf_name:
                        continue
                    if not isinstance(dest, pikepdf.Array) or len(dest) == 0:
                        continue
                    try:
                        manuscript_page_index = int(dest[0])
                    except Exception:
                        continue
                    manuscript_to_response[manuscript_page_index] = page
                    overlay_refs.append((page, annot_ref))

            for manuscript_index, manuscript_page in enumerate(manuscript_pdf.pages):
                annots = manuscript_page.get("/Annots", None)
                if annots is None:
                    continue
                response_page = manuscript_to_response.get(manuscript_index, None)
                if response_page is None:
                    continue
                if "/Annots" not in response_page:
                    response_page["/Annots"] = pikepdf.Array()
                response_annots = response_page["/Annots"]
                for manuscript_annot_ref in annots:
                    manuscript_annot = manuscript_annot_ref
                    action = manuscript_annot.get("/A", None)
                    if action is None or str(action.get("/S", "")) != "/GoToR":
                        continue
                    file_spec = action.get("/F", None)
                    file_name = None
                    if isinstance(file_spec, pikepdf.String):
                        file_name = str(file_spec)
                    elif isinstance(file_spec, pikepdf.Dictionary) and "/F" in file_spec:
                        file_name = str(file_spec["/F"])
                    if file_name is None or Path(file_name).name != response_pdf_name:
                        continue
                    dest = action.get("/D", None)
                    if not isinstance(dest, pikepdf.String):
                        continue
                    dest_name = str(dest)
                    if dest_name.startswith("nameddest="):
                        dest_name = dest_name.split("nameddest=", 1)[1]
                    if not dest_name.startswith(anchor_prefix):
                        continue
                    rect = manuscript_annot.get("/Rect", None)
                    if rect is None:
                        continue
                    new_annot = response_pdf.make_indirect(
                        pikepdf.Dictionary(
                            {
                                "/Type": pikepdf.Name("/Annot"),
                                "/Subtype": pikepdf.Name("/Link"),
                                "/Rect": rect,
                                "/Border": pikepdf.Array([0, 0, 0]),
                                "/A": pikepdf.Dictionary(
                                    {
                                        "/S": pikepdf.Name("/GoTo"),
                                        "/D": pikepdf.String(dest_name),
                                    }
                                ),
                            }
                        )
                    )
                    response_annots.append(new_annot)
                    changed += 1

            for page, annot_ref in overlay_refs:
                annots = page.get("/Annots", None)
                if annots is None:
                    continue
                new_annots = pikepdf.Array([x for x in annots if x != annot_ref])
                page["/Annots"] = new_annots
                changed += 1

        for page in response_pdf.pages:
            annots = page.get("/Annots", None)
            if annots is None:
                continue
            kept_annots = pikepdf.Array()
            for annot_ref in annots:
                annot = annot_ref
                if "/A" not in annot:
                    kept_annots.append(annot_ref)
                    continue
                action = annot["/A"]
                if "/S" not in action:
                    kept_annots.append(annot_ref)
                    continue
                action_type = str(action["/S"])
                if action_type == "/URI" and "/URI" in action:
                    uri = str(action["/URI"])
                    dest = extract_named_dest_from_uri(uri)
                    if dest and dest.startswith(anchor_prefix):
                        annot["/A"] = pikepdf.Dictionary({
                            "/S": pikepdf.Name("/GoTo"),
                            "/D": pikepdf.String(dest),
                        })
                        changed += 1
                    kept_annots.append(annot_ref)
                elif action_type == "/GoToR":
                    dest = action.get("/D", None)
                    file_spec = action.get("/F", None)
                    file_name = None
                    if file_spec is not None:
                        if isinstance(file_spec, pikepdf.String):
                            file_name = str(file_spec)
                        elif isinstance(file_spec, pikepdf.Dictionary) and "/F" in file_spec:
                            file_name = str(file_spec["/F"])
                    if isinstance(dest, pikepdf.String):
                        dest_name = str(dest)
                    else:
                        dest_name = None
                    if dest_name and dest_name.startswith(anchor_prefix):
                        if file_name is None or Path(file_name).name == response_pdf_name:
                            annot["/A"] = pikepdf.Dictionary({
                                "/S": pikepdf.Name("/GoTo"),
                                "/D": pikepdf.String(dest_name),
                            })
                            changed += 1
                    kept_annots.append(annot_ref)
                else:
                    kept_annots.append(annot_ref)
            page["/Annots"] = kept_annots
        response_pdf.save(response_pdf_path)
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--response-pdf", required=True)
    parser.add_argument("--manuscript-pdf", required=True)
    parser.add_argument("--response-pdf-name", required=True)
    parser.add_argument("--manuscript-pdf-name", required=True)
    parser.add_argument("--anchor-prefix", default="comment.")
    args = parser.parse_args()
    changed = normalize_actions(
        Path(args.response_pdf),
        Path(args.manuscript_pdf),
        args.response_pdf_name,
        args.manuscript_pdf_name,
        args.anchor_prefix,
    )
    print(f"Normalized links: {changed}")


if __name__ == "__main__":
    main()
