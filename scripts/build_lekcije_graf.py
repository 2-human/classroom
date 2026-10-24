#!/usr/bin/env python3
"""Build the lesson knowledge graph for a folder of lesson notes (private `_source/` material).

Usage:
    python3 scripts/build_lekcije_graf.py tools/geografija/_source/lekcije-7

Input — the folder's lesson notes `{NN-slug}.md`, each with frontmatter `lekcija, naslov, redosled,
strane, prethodna, sledeca, pojmovi: [slug, ...]`, and image notes in `../slike-{X}/{lekcija}/*.md`
with frontmatter `pojmovi: [...]` (X = the folder suffix, e.g. `7`).

Output (idempotent; rerun after adding or editing notes):
    - `../pojmovi-{X}/{slug}.md` — one page per concept: which lessons teach it, which images show it,
      and a link to the shared node `shared/znanje/{slug}/index.md` when that exists. Lesson notes link
      concepts as `[[slug]]`, so the pages also work as an Obsidian vault.
    - a generated block at the end of every lesson note: lessons that share concepts with it,
      strongest link first (between `<!-- graf:auto -->` markers; everything else is left as written).
    - `INDEX.md` in the lesson folder: the lessons in order, pages, gaps in the page numbers,
      concept counts.
"""
import collections
import pathlib
import re
import sys

import yaml

START, END = "<!-- graf:auto -->", "<!-- /graf:auto -->"


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}, text


def label(slug):
    return slug.replace("-", " ").capitalize()


def main(folder):
    les_dir = pathlib.Path(folder).resolve()
    suffix = les_dir.name.split("-")[-1]
    root = les_dir.parent
    img_dir = root / f"slike-{suffix}"
    poj_dir = root / f"pojmovi-{suffix}"
    repo = next((p for p in les_dir.parents if (p / "shared" / "znanje").is_dir()), None)

    lessons = []
    for p in sorted(les_dir.glob("[0-9]*.md")):
        fm, _ = frontmatter(p)
        fm["_path"] = p
        fm["lekcija"] = p.stem   # the file name is the lesson id (notes have used both forms)
        fm["redosled"] = int(str(fm.get("redosled") or 0))   # "08" is a string in YAML 1.1
        fm["pojmovi"] = list(dict.fromkeys(fm.get("pojmovi") or []))
        lessons.append(fm)
    lessons.sort(key=lambda l: l.get("redosled", 0))

    images = []
    for p in sorted(img_dir.glob("*/*.md")):
        fm, _ = frontmatter(p)
        fm["_path"] = p
        images.append(fm)

    # concept → lessons / images
    in_lessons = collections.defaultdict(list)
    for l in lessons:
        for s in l["pojmovi"]:
            in_lessons[s].append(l)
    in_images = collections.defaultdict(list)
    for im in images:
        for s in im.get("pojmovi") or []:
            in_images[s].append(im)

    # concept pages
    poj_dir.mkdir(exist_ok=True)
    concepts = sorted(set(in_lessons) | set(in_images))
    for old in poj_dir.glob("*.md"):
        if old.stem not in concepts:
            old.unlink()
    for s in concepts:
        rel = lambda p: pathlib.Path("..") / p.relative_to(root)
        out = [f"---\npojam: {s}\nlekcije: [{', '.join(l['lekcija'] for l in in_lessons[s])}]\n---",
               f"# {label(s)}", ""]
        if repo and (repo / "shared" / "znanje" / s / "index.md").exists():
            out += [f"Zajednički čvor grafa: [shared/znanje/{s}]({pathlib.Path('..') / '..' / '..' / '..' / 'shared' / 'znanje' / s / 'index.md'})", ""]
        if in_lessons[s]:
            out += ["## Lekcije"] + [f"- [{l.get('naslov', l['lekcija'])}]({rel(l['_path'])})" for l in in_lessons[s]] + [""]
        if in_images[s]:
            out += ["## Slike"] + [f"- [{im['_path'].stem}]({rel(im['_path'])}) — {im.get('lekcija', '')}" for im in in_images[s]] + [""]
        (poj_dir / f"{s}.md").write_text("\n".join(out), encoding="utf-8")

    # related lessons, by shared concepts
    for l in lessons:
        mine = set(l["pojmovi"])
        rel_l = []
        for o in lessons:
            if o is l:
                continue
            shared = [s for s in o["pojmovi"] if s in mine]
            if shared:
                rel_l.append((len(shared), o, shared))
        rel_l.sort(key=lambda x: (-x[0], x[1].get("redosled", 0)))
        block = [START, "## Povezane lekcije (generisano: zajednički pojmovi)", ""]
        block += [f"- [{o.get('naslov', o['lekcija'])}]({o['_path'].name}) — {n}: "
                  + ", ".join(f"[[{s}]]" for s in shared[:12]) + (" …" if n > 12 else "")
                  for n, o, shared in rel_l] or ["- (nema zajedničkih pojmova)"]
        block.append(END)
        text = l["_path"].read_text(encoding="utf-8")
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), "", text, flags=re.S).rstrip() + "\n\n"
        l["_path"].write_text(text + "\n".join(block) + "\n", encoding="utf-8")

    # INDEX.md
    pages = sorted({p for l in lessons for p in range(l["strane"][0], l["strane"][-1] + 1)} if lessons else [])
    gaps = [p for p in range(pages[0], pages[-1] + 1) if p not in pages] if pages else []
    idx = ["# Lekcije — indeks (generisano)", "",
           f"Graf: {len(lessons)} lekcija · {len(concepts)} pojmova (`../pojmovi-{suffix}/`) · {len(images)} slika (`../slike-{suffix}/`).",
           f"Stranice: {pages[0]}–{pages[-1]}" + (f"; nedostaju: {', '.join(map(str, gaps))}" if gaps else "") if pages else "", "",
           "| # | Lekcija | Strane | Pojmova | Slika |", "|---|---|---|---|---|"]
    for l in lessons:
        n_img = sum(1 for im in images if im.get("lekcija") == l["lekcija"])
        idx.append(f"| {l.get('redosled')} | [{l.get('naslov')}]({l['_path'].name}) | {l['strane'][0]}–{l['strane'][-1]} | {len(l['pojmovi'])} | {n_img} |")
    shared_most = sorted(concepts, key=lambda s: -len(in_lessons[s]))[:20]
    idx += ["", "## Pojmovi koji povezuju najviše lekcija", ""]
    idx += [f"- [[{s}]] — {len(in_lessons[s])} lekcija" for s in shared_most if len(in_lessons[s]) > 1]
    (les_dir / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    print(f"{len(lessons)} lekcija, {len(concepts)} pojmova, {len(images)} slika → {poj_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
