#!/usr/bin/env python3
"""Build the password-protected copy of a lesson quiz: the quiz WITH the textbook images, encrypted.

Usage (from anywhere in the repo):
    python3 scripts/build_zasticeno.py tools/geografija/juzna-evropa-kviz

Why: the textbook crops are private (tools/{predmet}/_source/, gitignored) and the classroom repo is
public on GitHub Pages, so the public quiz shows no textbook images. This script renders the same quiz
with the crops (and the lesson's own notes for the drawer) embedded, encrypts it and writes only the
ciphertext and a small gate page to zasticeno/{predmet}/{slug}/. Encryption, gate and password:
shared/python/zasticeno.py (same password and key as the protected lesson pages).
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))
from lesson_quiz import load_spec, render_html  # noqa: E402
from hub_shell import brand_and_crumbs  # noqa: E402
from zasticeno import write_protected  # noqa: E402


def main(tool):
    tool = (ROOT / tool).resolve() if not pathlib.Path(tool).is_absolute() else pathlib.Path(tool)
    spec = load_spec(tool / "spec.yaml")
    predmet, slug = tool.parent.name, tool.name
    out_dir = ROOT / "zasticeno" / predmet / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "index.html"

    html = render_html(spec, page, embed_images=True, write=False)
    n_img = html.count("data:image/jpeg;base64,")
    title = spec.get("title_short") or spec["title"]
    size = write_protected(ROOT, out_dir, html, title, brand_and_crumbs(page, title, spec),
                           f"{title} — sa slikama iz udžbenika",
                           "Ova verzija kviza sadrži slike iz udžbenika i namenjena je samo učenicima.", "Otvori kviz")
    print(f"{n_img} slika ugrađeno; {size // 1024} KB gzip → {out_dir.relative_to(ROOT)}/bundle.enc + index.html")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        raise SystemExit(__doc__)
    for t in sys.argv[1:]:
        main(t)
