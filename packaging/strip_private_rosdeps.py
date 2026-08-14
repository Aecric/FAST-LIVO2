#!/usr/bin/env python3
"""Remove locally supplied ROS dependencies before bloom resolves rosdep keys."""

from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: strip_private_rosdeps.py <package.xml> <key>...", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    private_keys = set(sys.argv[2:])
    tree = ET.parse(path)
    root = tree.getroot()
    removed = []
    for element in list(root):
        if element.tag.endswith("depend") and (element.text or "").strip() in private_keys:
            removed.append((element.tag, (element.text or "").strip()))
            root.remove(element)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print("removed private rosdep keys:", ", ".join(f"{tag}:{key}" for tag, key in removed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
