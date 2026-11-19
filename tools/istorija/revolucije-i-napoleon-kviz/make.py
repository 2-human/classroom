#!/usr/bin/env python3
"""Rebuild this lesson quiz's index.html from spec.yaml.

Usage:
    python3 make.py
"""
import pathlib
import sys

# Locate classroom/shared/python by walking up from this file.
_here = pathlib.Path(__file__).resolve().parent
for _p in [_here, *_here.parents]:
    if (_p / "shared" / "python" / "lesson_quiz.py").exists():
        sys.path.insert(0, str(_p / "shared" / "python"))
        break
else:
    raise SystemExit("Could not find classroom/shared/python/ — is this file inside the classroom repo?")

from lesson_quiz import load_spec, render_html


def main():
    spec = load_spec(_here / "spec.yaml")
    n = sum(len(d["zadaci"]) for d in spec["delovi"])
    out = render_html(spec, _here / "index.html")
    print(f"Loaded {n} items in {len(spec['delovi'])} sections; wrote {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
