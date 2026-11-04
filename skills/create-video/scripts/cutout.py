#!/usr/bin/env python3
"""Background removal for character art, product photos and reference frames.

Uses rembg (danielgatis/rembg, MIT). Model downloads on first run (u2net from GitHub
releases; isnet-general-use / birefnet-general also supported).

Usage: cutout.py in.png out.png [--model u2net] [--alpha-matting]
       cutout.py in_dir/ out_dir/            # batch: every png/jpg/webp in a folder
"""
import argparse
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--model", default="u2net")
    p.add_argument("--alpha-matting", action="store_true", help="cleaner hair/edge detail")
    a = p.parse_args()
    from PIL import Image
    from rembg import new_session, remove
    sess = new_session(a.model)
    pairs = []
    if os.path.isdir(a.src):
        os.makedirs(a.dst, exist_ok=True)
        for f in sorted(os.listdir(a.src)):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                pairs.append((os.path.join(a.src, f), os.path.join(a.dst, os.path.splitext(f)[0] + ".png")))
    else:
        pairs.append((a.src, a.dst))
    for src, dst in pairs:
        out = remove(Image.open(src), session=sess, alpha_matting=a.alpha_matting)
        out.save(dst)
        print(f"OK {dst} {out.size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
