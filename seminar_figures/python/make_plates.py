#!/usr/bin/env python3
"""
make_plates.py - build the multi-panel figure plates used in the seminar.

Takes the single-panel images downloaded by the PowerShell scripts and
composites them side by side at a common height, with a panel label under
each one.

Why the labels are just (a), (b), (c)
-------------------------------------
The first version of this script drew a descriptive label under each panel
("(a) Venom milked from the mamba", "(b) Designed binder bound to a
neurotoxin"). Those strings were wider than the panels they sat under, so
neighbouring labels ran into each other INSIDE the PNG. Nothing in the
document could fix it, because the overlap was baked into the image.

Two changes stop that happening again:
  1. labels are short - the description belongs in the figure caption;
  2. the font is shrunk until every label measurably fits inside its own
     panel before anything is drawn (see the while loop in plate()).

Usage:
    python make_plates.py --pdb  <folder of PDB panel images>
                          --extra <folder of other panel images>
                          --out  <folder to write plates into>
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_width(font, s):
    box = font.getbbox(s)
    return box[2] - box[0]


def plate(paths, labels, out, height=520, gap=48, pad=14, label_size=34):
    """Composite images side by side at a common height, label each panel."""
    for p in paths:
        if not os.path.exists(p):
            print("  missing panel, skipping plate: %s" % p)
            return False

    ims = [Image.open(p).convert("RGB") for p in paths]
    ims = [i.resize((max(1, int(i.width * height / i.height)), height), Image.LANCZOS)
           for i in ims]

    # shrink the label font until every label fits inside its own panel
    size = label_size
    while size > 14:
        font = load_font(size)
        if all(text_width(font, lab) <= im.width - 6 for lab, im in zip(labels, ims)):
            break
        size -= 2
    font = load_font(size)

    strip = size + 16
    width = sum(i.width for i in ims) + gap * (len(ims) - 1) + pad * 2
    canvas = Image.new("RGB", (width, height + strip + pad), "white")
    draw = ImageDraw.Draw(canvas)

    x = pad
    for im, lab in zip(ims, labels):
        canvas.paste(im, (x, 0))
        draw.text((x + (im.width - text_width(font, lab)) // 2, height + 6),
                  lab, font=font, fill=(20, 20, 20))
        x += im.width + gap

    canvas.save(out)
    print("  %-28s %dx%d  label %dpt" % (os.path.basename(out),
                                         canvas.width, canvas.height, size))
    return True


# figure number -> (output name, [panel files], [labels])
# "pdb:" prefix means the panel comes from the PDB folder, "extra:" the other.
PLATES = [
    ("F02_levels.png",
     ["pdb:fig02a_4INS.png", "pdb:fig02b_1MBN.png",
      "pdb:fig02c_1LYZ.png", "pdb:fig02d_1A3N.png"],
     ["(a)", "(b)", "(c)", "(d)"]),

    ("F03_helix_sheet.png",
     ["pdb:fig03a_1MBN.png", "pdb:fig03b_1EMA.png"],
     ["(a)", "(b)"]),

    ("F04_methods.png",
     ["extra:fig04a_xray_diffractometer.png",
      "extra:fig04b_cryoEM_microscope.png",
      "extra:fig04c_NMR_spectrometer.png"],
     ["(a)", "(b)", "(c)"]),

    ("F05_biologics.png",
     ["pdb:fig05a_7KI0.png", "pdb:fig05b_1N8Z.png"],
     ["(a)", "(b)"]),

    ("F10_skycovione.png",
     ["pdb:fig10_7SGE.png", "extra:fig10b_skycovione_product.png"],
     ["(a)", "(b)"]),

    ("F13_neo215.png",
     ["pdb:fig12_6DG5.png", "pdb:fig12opt_2B5I.png"],
     ["(a)", "(b)"]),

    ("F14_antivenom.png",
     ["extra:fig14a_antivenom_milking.png", "pdb:fig13_9BK5.png"],
     ["(a)", "(b)"]),

    ("F15_antibodies.png",
     ["extra:fig15a_immunise_monoclonals.png", "pdb:fig14_9NFU.png"],
     ["(a)", "(b)"]),

    ("F16_diagnostics.png",
     ["pdb:fig15a_8GJI.png", "pdb:fig15b_9DEG.png"],
     ["(a)", "(b)"]),
]

# single-panel figures are copied straight through, no labels needed
SINGLES = [
    ("F01_amino_acid.png", "extra:fig01a_amino_acid_structure.png"),
    ("F06_induced_fit.png", "extra:fig06b_induced_fit.png"),
    ("F07_binder_HA.png", "pdb:fig07_8SK7.png"),
    ("F12_lcb1.png", "pdb:fig11_7JZU.png"),
    ("F17_pipeline.png", "extra:fig17_fda_pipeline.png"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdb", required=True, help="folder of PDB panel images")
    ap.add_argument("--extra", required=True, help="folder of other panel images")
    ap.add_argument("--out", required=True, help="folder to write plates into")
    ap.add_argument("--height", type=int, default=520)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    roots = {"pdb": args.pdb, "extra": args.extra}

    def resolve(tag):
        kind, name = tag.split(":", 1)
        return os.path.join(roots[kind], name)

    print("multi-panel plates:")
    made = 0
    for name, panels, labels in PLATES:
        if plate([resolve(p) for p in panels], labels,
                 os.path.join(args.out, name), height=args.height):
            made += 1

    print("single-panel figures:")
    for name, tag in SINGLES:
        src = resolve(tag)
        if not os.path.exists(src):
            print("  missing: %s" % src)
            continue
        Image.open(src).convert("RGB").save(os.path.join(args.out, name))
        print("  %s" % name)
        made += 1

    print("\n%d figures written to %s" % (made, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
