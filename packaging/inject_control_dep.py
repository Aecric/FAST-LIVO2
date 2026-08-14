#!/usr/bin/env python3
"""Append a dependency to the first binary stanza in debian/control."""

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: inject_control_dep.py <control> <dependency>", file=sys.stderr)
        return 2

    control = Path(sys.argv[1])
    dependency = sys.argv[2]
    lines = control.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("Depends:"):
            continue
        end = index + 1
        while end < len(lines) and lines[end].startswith(" "):
            end += 1
        if dependency not in "\n".join(lines[index:end]):
            lines[end - 1] = lines[end - 1].rstrip() + f",\n {dependency}"
        control.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 0

    print(f"{control}: Depends field not found", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
