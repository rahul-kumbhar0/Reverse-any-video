#!/usr/bin/env python3
"""Fetch real CC-licensed sound effects from Freesound (freesound.org, via its API v2).

Needs a free API key: https://freesound.org/apiv2/apply  ->  export FREESOUND_API_KEY=...
Downloads the high-quality preview MP3 (no OAuth needed) and records the license +
attribution so credits can be generated. Falls back to synth_sfx.py when unavailable.

Usage: fetch_sfx.py "whoosh soft" out.mp3 [--max-duration 1.5] [--license cc0]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("out")
    p.add_argument("--max-duration", type=float, default=2.0)
    p.add_argument("--license", default="cc0", choices=["cc0", "any"])
    a = p.parse_args()
    key = os.environ.get("FREESOUND_API_KEY")
    if key:
        flt = f"duration:[0 TO {a.max_duration}]"
        if a.license == "cc0":
            flt += ' license:"Creative Commons 0"'
        q = urllib.parse.urlencode({"query": a.query, "filter": flt, "sort": "rating_desc",
                                    "fields": "id,name,username,license,previews", "token": key, "page_size": 5})
        try:
            res = json.load(urllib.request.urlopen(f"https://freesound.org/apiv2/search/text/?{q}", timeout=30))
            hit = res["results"][0]
            data = urllib.request.urlopen(hit["previews"]["preview-hq-mp3"], timeout=60).read()
            open(a.out, "wb").write(data)
            meta = {k: hit[k] for k in ("id", "name", "username", "license")}
            json.dump(meta, open(a.out + ".credit.json", "w"), indent=1)
            print(f"OK freesound #{hit['id']} '{hit['name']}' by {hit['username']} ({hit['license']})")
            return 0
        except Exception as e:  # noqa: BLE001
            print(f"freesound failed ({e}); synthesizing instead", file=sys.stderr)
    kind = next((k for k in ("whoosh", "tap", "click", "pop", "impact", "riser", "shimmer") if k in a.query.lower()), "whoosh")
    wav = os.path.splitext(a.out)[0] + ".wav"
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "synth_sfx.py"), kind, wav], check=True)
    print(f"OK synthesized {kind} -> {wav}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
