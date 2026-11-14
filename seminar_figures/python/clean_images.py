#!/usr/bin/env python3
"""
clean_images.py - repairs applied to downloaded figure panels.

Three things kept going wrong with images pulled off the web and out of
screenshots, and each has a fix here:

  --trim      Screenshots arrive letterboxed: a band of flat background
              above and below the actual picture. Crops to the bounding box
              of everything that differs from the corner pixel colour.

  --sharpen   A logo or caption inside a downloaded banner can be too soft
              to read once it is scaled into a document. Upscales to a target
              width with LANCZOS and applies an unsharp mask. This is what
              made "UNIVERSITY of WASHINGTON" legible in the RFD4-Proteina
              figure.

  --flatten   Transparent PNGs go black in some Word/PDF pipelines.
              Composites onto white and drops the alpha channel.

Usage:
    python clean_images.py --trim in.png out.png
    python clean_images.py --sharpen in.png out.png --width 1500
    python clean_images.py --flatten in.png out.png
"""

import argparse
import sys

from PIL import Image, ImageFilter


def trim(im, tolerance=12):
    """Crop flat borders, using the top-left pixel as the background colour."""
    im = im.convert("RGB")
    bg = Image.new("RGB", im.size, im.getpixel((0, 0)))
    from PIL import ImageChops
    diff = ImageChops.difference(im, bg).convert("L")
    mask = diff.point(lambda p: 255 if p > tolerance else 0)
    box = mask.getbbox()
    return im.crop(box) if box else im


def sharpen(im, width=1500, radius=2.2, percent=190, threshold=2):
    """Upscale to `width` then unsharp-mask, so small text becomes readable."""
    im = im.convert("RGB")
    if im.width < width:
        h = int(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=radius,
                                             percent=percent,
                                             threshold=threshold))


def flatten(im):
    """Composite any transparency onto white."""
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--trim", action="store_true")
    ap.add_argument("--sharpen", action="store_true")
    ap.add_argument("--flatten", action="store_true")
    ap.add_argument("--width", type=int, default=1500)
    ap.add_argument("--tolerance", type=int, default=12)
    args = ap.parse_args()

    if not (args.trim or args.sharpen or args.flatten):
        ap.error("pick at least one of --trim, --sharpen, --flatten")

    im = Image.open(args.src)
    if args.flatten:
        im = flatten(im)
    if args.trim:
        im = trim(im, args.tolerance)
    if args.sharpen:
        im = sharpen(im, args.width)

    im.save(args.dst)
    print("%s -> %s  (%dx%d)" % (args.src, args.dst, im.width, im.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
