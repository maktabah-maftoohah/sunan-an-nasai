"""
scripts/download_scanned_editions.py
CLI tool to download scanned primary PDF editions of Sunan an-Nasa'i.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "scanned_editions.json"
DOCS_DIR = BASE_DIR / "documents"

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def download_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [Already exists] {dest.name} ({dest.stat().st_size / (1024*1024):.1f} MB)")
        return

    print(f"  Downloading: {dest.name} from {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Maktabah Maftoohah Downloader)"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
        total = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            total += len(chunk)
            print(f"    Downloaded {total / (1024*1024):.1f} MB...", end="\r")
    print(f"\n  Done: {dest.name} ({total / (1024*1024):.2f} MB)")

def main():
    parser = argparse.ArgumentParser(description="Download scanned PDF editions of Sunan an-Nasa'i")
    parser.add_argument("--edition", choices=["dar-al-taseel", "abu-ghuddah", "darussalam-bilingual"], default="dar-al-taseel", help="Edition ID")
    parser.add_argument("--volume", type=int, help="Specific volume number to download")
    parser.add_argument("--all", action="store_true", help="Download all volumes for this edition")
    parser.add_argument("--output-dir", type=str, help="Custom output directory")
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print(f"Error: {DATA_FILE} not found.")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)

    target_ed = None
    for ed in registry.get("editions", []):
        if ed["id"] == args.edition:
            target_ed = ed
            break

    if not target_ed:
        print(f"Error: Edition '{args.edition}' not found in registry.")
        sys.exit(1)

    out_dir = Path(args.output_dir) if args.output_dir else DOCS_DIR
    volumes = target_ed.get("volumes", [])

    print(f"=== Downloading {target_ed['name']} ===")
    if args.volume:
        vol = next((v for v in volumes if v["volume"] == args.volume), None)
        if not vol:
            print(f"Error: Volume {args.volume} not found for this edition.")
            sys.exit(1)
        download_file(vol["download_url"], out_dir / vol["filename"])
    elif args.all:
        for v in volumes:
            download_file(v["download_url"], out_dir / v["filename"])
    else:
        # Default: download Volume 1
        vol = volumes[0]
        download_file(vol["download_url"], out_dir / vol["filename"])

    print("Completed download operations.")

if __name__ == "__main__":
    main()
