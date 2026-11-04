#!/usr/bin/env python3
"""Download CC0 assets: Poly Haven HDRIs/textures and ambientCG PBR materials.

Poly Haven (polyhaven.com, CC0) via its public API; ambientCG (ambientcg.com, CC0).
Needs network access to api.polyhaven.com / dl.polyhaven.org / ambientcg.com.

Usage:
  fetch_assets.py hdri studio_small_09 [--res 2k] [--dir ~/.cache/reverse-any-video/assets]
  fetch_assets.py texture brushed_concrete [--res 2k]
  fetch_assets.py ambientcg Metal032 [--res 2K]
  fetch_assets.py search hdris studio           # list matching Poly Haven assets

Then: RAV_HDRI=<path to .hdr> python3 scene.py ...   (blender_kit.studio_environment picks it up)
"""
import argparse
import io
import json
import os
import sys
import urllib.request
import zipfile

UA = {"User-Agent": "reverse-any-video/0.2"}
DEFAULT = os.path.expanduser("~/.cache/reverse-any-video/assets")


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def polyhaven_files(asset):
    return json.loads(get(f"https://api.polyhaven.com/files/{asset}"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["hdri", "texture", "ambientcg", "search"])
    p.add_argument("name")
    p.add_argument("query", nargs="?")
    p.add_argument("--res", default="2k")
    p.add_argument("--dir", default=DEFAULT)
    a = p.parse_args()
    os.makedirs(a.dir, exist_ok=True)
    try:
        if a.kind == "search":
            assets = json.loads(get(f"https://api.polyhaven.com/assets?t={a.name}"))
            q = (a.query or "").lower()
            hits = [k for k, v in assets.items() if q in k or q in " ".join(v.get("tags", [])).lower()]
            print("\n".join(sorted(hits)[:60]))
            return 0
        if a.kind == "hdri":
            info = polyhaven_files(a.name)["hdri"][a.res]["hdr"]
            out = os.path.join(a.dir, f"{a.name}_{a.res}.hdr")
            open(out, "wb").write(get(info["url"]))
            print(f"OK {out}\nexport RAV_HDRI={out}")
        elif a.kind == "texture":
            files = polyhaven_files(a.name)
            folder = os.path.join(a.dir, a.name)
            os.makedirs(folder, exist_ok=True)
            for mp in ("Diffuse", "Rough", "nor_gl", "Displacement", "arm"):
                if mp in files and a.res in files[mp]:
                    fmt = "png" if "png" in files[mp][a.res] else next(iter(files[mp][a.res]))
                    url = files[mp][a.res][fmt]["url"]
                    open(os.path.join(folder, os.path.basename(url)), "wb").write(get(url))
            print(f"OK {folder}")
        else:
            res = a.res.upper()
            data = get(f"https://ambientcg.com/get?file={a.name}_{res}-PNG.zip")
            folder = os.path.join(a.dir, a.name)
            zipfile.ZipFile(io.BytesIO(data)).extractall(folder)
            print(f"OK {folder}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}. If this is a network block, allow api.polyhaven.com, dl.polyhaven.org "
              "and ambientcg.com, or run locally. blender_kit falls back to a gradient studio world.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
