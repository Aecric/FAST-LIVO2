#!/usr/bin/env python3
"""Download matching Debian assets from a GitHub release."""

from pathlib import Path
import json
import re
import sys
import urllib.request


def request(url: str):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "fast-livo2-deb-builder"}),
        timeout=60,
    )


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: fetch_release_debs.py <owner/repo> <tag|latest> "
            "<asset-regex> <output-dir> <expected-count>",
            file=sys.stderr,
        )
        return 2

    repository, tag, pattern, output_dir, expected_text = sys.argv[1:]
    expected = int(expected_text)
    release_path = "latest" if tag == "latest" else f"tags/{tag}"
    api_url = f"https://api.github.com/repos/{repository}/releases/{release_path}"
    with request(api_url) as response:
        release = json.load(response)

    matcher = re.compile(pattern)
    assets = [asset for asset in release.get("assets", []) if matcher.fullmatch(asset["name"])]
    if len(assets) != expected:
        available = ", ".join(asset["name"] for asset in release.get("assets", []))
        raise SystemExit(
            f"expected {expected} asset(s) matching {pattern!r}, found {len(assets)}; "
            f"release assets: {available or '<none>'}"
        )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for asset in assets:
        output = destination / asset["name"]
        print(f"downloading {asset['browser_download_url']} -> {output}")
        with request(asset["browser_download_url"]) as response, output.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
