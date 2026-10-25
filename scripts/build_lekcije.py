#!/usr/bin/env python3
"""Build the password-protected lesson pages: the textbook's page scans in order, with our notes.

Usage (from anywhere in the repo):
    python3 scripts/build_lekcije.py                 # every lesson that has notes
    python3 scripts/build_lekcije.py istorija        # one subject

Sources (private, gitignored): tools/{predmet}/_source/lekcije-{razred}/NN-slug.md (notes in our own
words; NN = the lesson's `broj` in shared/kurikulum), stranice-{razred}/sNN.jpg (the page scans, which
carry the book's full text) and slike-{razred}/NN-slug/*.jpg (the crops of the images).
Output: zasticeno/lekcije/{predmet}/{razred}/NN-slug/ (bundle.enc + gate index.html, see
shared/python/zasticeno.py). Book sections with pages in their heading (`## Uvod (str. 28)`) are
placed under their page; notes without pages come after all the pages. Anchors: #str-N for a page,
#o-{slug} for a section (the quizzes' "Iz udžbenika" drawer links to them).
Rerun scripts/regenerate_index.py afterwards so the catalog links the lessons.
"""
import html as _html
import os
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))
from hub_shell import SHELL_CSS, SHELL_JS, BRAND, nivo_title, razred_title, predmet_title  # noqa: E402
from lekcija import parse_note, md_to_html, pojmovi_titles, lesson_dir, slugify  # noqa: E402
from lesson_quiz import _data_uri  # noqa: E402
from zasticeno import write_protected  # noqa: E402

esc = _html.escape
INTRO = {"vec-smo-ucili", "kljucni-pojmovi", "ukratko"}

PAGE = r"""<!DOCTYPE html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>__TITLE__</title>
<style>
__SHELL_CSS__
 .app-nav a{text-decoration:none}
 .app-nav .row{display:block;color:#2b2b2b;font-size:13px;padding:5px 8px;border-radius:5px;line-height:1.35}
 .app-nav .row:hover{background:#f6f1e4}
 .app-nav .row.cur{background:#efe7d2;font-weight:600}
 .app-nav .row.off{color:#9b9387}
 .app-nav .row.sub{padding-left:20px;font-size:12.5px}
 .app-nav .row.pg{color:#6b6456;font-size:12px}
 .les{max-width:860px;padding:22px 28px 80px;line-height:1.6;color:#2b2b2b}
 .les h1{font-size:25px;margin:0 0 4px;color:#3a3528}
 .les .meta{color:#6b6456;font-size:13.5px;margin:0 0 6px}
 .les .meta a{color:#b1271f;text-decoration:none}
 .les section{margin:22px 0;scroll-margin-top:12px}
 .les h2{font-size:18px;color:#3a3528;margin:0 0 8px;padding-bottom:5px;border-bottom:1px solid #e6e0d2}
 .les h3{font-size:15.5px;color:#3a3528;margin:0 0 6px}
 .les section.l3{margin-left:14px;padding-left:12px;border-left:3px solid #f3ecd8}
 .les .str{font-size:12px;font-weight:400;color:#6b6456;margin-left:6px;white-space:nowrap}
 .les ul,.les ol{padding-left:22px;margin:6px 0} .les li{margin:3px 0}
 .les p{margin:6px 0}
 .les a{color:#b1271f}
 .les .pojam{border-bottom:1px dotted #b9b2a0}
 .les blockquote{margin:8px 0;padding:6px 14px;border-left:3px solid #c98a2c;background:#fefcf7}
 .les .tbl{overflow-x:auto} .les table{border-collapse:collapse;font-size:14px;margin:8px 0}
 .les th,.les td{border:1px solid #e6e0d2;padding:4px 8px;text-align:left;vertical-align:top} .les th{background:#f3ecd8}
 .strana{margin:26px 0 14px;scroll-margin-top:12px;background:#fff;border:1px solid #e6e0d2;border-radius:10px;overflow:hidden}
 .strana .pg{display:flex;justify-content:space-between;align-items:center;padding:7px 12px;font-size:12.5px;color:#6b6456;background:#fbf7ec;border-bottom:1px solid #e6e0d2}
 .strana .pg b{color:#3a3528}
 .strana .pg button{font:inherit;font-size:12px;border:1px solid #e6e0d2;background:#fff;border-radius:6px;padding:2px 9px;cursor:pointer;color:#3a3528}
 .strana img{display:block;width:100%;height:auto;cursor:zoom-in}
 .strana.zoom{overflow-x:auto} .strana.zoom img{width:auto;max-width:none;cursor:zoom-out}
 .strana.nema{padding:12px;color:#9b9387;font-size:13.5px;background:#fefcf7}
 .notes-lbl{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:#1f7a3a;margin:0 0 -12px}
 .gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-top:8px}
 .gal figure{margin:0;background:#fff;border:1px solid #e6e0d2;border-radius:8px;overflow:hidden;scroll-margin-top:12px}
 .gal img{display:block;width:100%;height:auto} .gal figcaption{font-size:12.5px;color:#6b6456;padding:6px 9px}
 .hit{animation:hit 2.4s ease-out} @keyframes hit{0%{box-shadow:0 0 0 4px rgba(201,138,44,.55)}100%{box-shadow:0 0 0 4px rgba(201,138,44,0)}}
 .pager{display:flex;justify-content:space-between;gap:12px;margin-top:34px;font-size:13.5px} .pager a{color:#b1271f;text-decoration:none}
 @media (max-width:760px){ .les{padding:16px 16px 60px} .les section.l3{margin-left:4px} }
</style>
</head>
<body class="app-body">
<header class="app-bar">
 <button class="app-menu" id="app-menu" aria-label="Lekcije i sadržaj" aria-expanded="false">&#9776;</button>
 __BRAND_CRUMBS__
</header>
<div class="app-grid">
 <nav class="app-nav" id="app-nav" aria-label="Poglavlje i sadržaj lekcije">__NAV__</nav>
 <main class="app-main" id="app-main"><article class="les">__BODY__</article></main>
</div>
<script>__SHELL_JS__</script>
<script>
document.querySelectorAll('.strana button, .strana img').forEach(el => el.addEventListener('click', () => {
  const f = el.closest('.strana'); f.classList.toggle('zoom');
  const b = f.querySelector('button'); if (b) b.textContent = f.classList.contains('zoom') ? 'Umanji' : 'Uvećaj';
}));
function go() {
  const id = decodeURIComponent(location.hash.slice(1)); const el = id && document.getElementById(id);
  if (!el) return; el.scrollIntoView({ block: 'start' }); el.classList.remove('hit'); void el.offsetWidth; el.classList.add('hit');
}
window.addEventListener('hashchange', go);
document.querySelectorAll('#app-nav a[href^="#"]').forEach(a => a.addEventListener('click', () => HubShell.setNav(false)));
setTimeout(go, 50);
</script>
</body>
</html>
"""


def kurikulum(predmet, nivo, razred):
    p = ROOT / "shared" / "kurikulum" / nivo / str(razred) / f"{predmet}.yaml"
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def quizzes(predmet, razred, broj):
    out = []
    for sp in sorted((ROOT / "tools" / predmet).glob("*/spec.yaml")):
        s = yaml.safe_load(sp.read_text()) or {}
        if s.get("razred") == razred and broj in (s.get("lekcije") or []):
            prot = ROOT / "zasticeno" / predmet / sp.parent.name / "bundle.enc"
            href = f"../../../../{predmet}/{sp.parent.name}/" if prot.exists() else f"../../../../../tools/{predmet}/{sp.parent.name}/index.html"
            out.append((s.get("title_short") or s.get("title") or sp.parent.name, href))
    return out


def build(note_file):
    predmet = note_file.parents[2].name
    note = parse_note(note_file)
    fm, stem = note["fm"], note_file.stem
    nivo, razred, broj = fm.get("nivo", "osnovna"), int(fm.get("razred") or 7), int(stem[:2])
    src = note_file.parents[1]
    out_dir = ROOT / lesson_dir(predmet, razred, stem)
    catalog = os.path.relpath(ROOT / "index.html", out_dir).replace(os.sep, "/")
    ctx = {"pojmovi": pojmovi_titles(ROOT, predmet, razred)}

    # lessons of this lesson's chapter (the nav), and where this one sits in the whole subject
    k = kurikulum(predmet, nivo, razred)
    notes = {int(p.stem[:2]): p.stem for p in (src / f"lekcije-{razred}").glob("[0-9][0-9]-*.md")}
    chapter, ordered = None, []
    for pg in k.get("poglavlja") or []:
        for l in pg.get("lekcije") or []:
            ordered.append(l)
            if int(l["broj"]) == broj:
                chapter = pg
    naslov = next((l["naslov"] for l in ordered if int(l["broj"]) == broj), note["naslov"])

    # pages: scans that exist, in the lesson's page range
    od, do = (fm.get("strane") or [None, None])[:2]
    scans = {int(m.group(1)): p for p in (src / f"stranice-{razred}").glob("s*.jpg") if (m := re.match(r"s(\d+)$", p.stem))}
    pages = list(range(int(od), int(do) + 1)) if od and do else sorted(scans)

    def page_html(n):
        if n not in scans:
            return f'<div class="strana nema" id="str-{n}">Strana {n} nije snimljena.</div>'
        return (f'<figure class="strana" id="str-{n}"><div class="pg"><b>Strana {n}</b><button type="button">Uvećaj</button></div>'
                f'<img src="{_data_uri(scans[n], 1500)}" alt="Udžbenik, strana {n}" loading="lazy"></figure>')

    crops = sorted((src / f"slike-{razred}" / stem).glob("*.jpg"))

    def gallery():
        figs = []
        for c in crops:
            md = c.with_suffix(".md")
            m = re.search(r"^# (.+)$", md.read_text(encoding="utf-8"), re.M) if md.exists() else None
            cap = m.group(1).strip() if m else c.stem
            figs.append(f'<figure id="sl-{esc(c.stem)}"><img src="{_data_uri(c, 900)}" alt="{esc(cap)}" loading="lazy"><figcaption>{esc(cap)}</figcaption></figure>')
        return '<div class="gal">' + "".join(figs) + "</div>"

    def section_html(s):
        body = gallery() if s["naslov"].lower().startswith("slike i karte") and crops else md_to_html(s["body"], ctx)
        st = s["strane"]
        tag = f'<span class="str">str. {st[0]}{"–" + str(st[1]) if st[1] != st[0] else ""}</span>' if st and s["level"] == 2 else ""
        h = "h2" if s["level"] == 2 else "h3"
        return f'<section class="l{s["level"]}" id="{s["id"]}"><{h}>{esc(s["naslov"])}{tag}</{h}>{body}</section>'

    secs = note["sections"]
    paged = any(s["strane"] for s in secs)
    body, shown = [], set()

    def pages_upto(n):
        out = [p for p in pages if p not in shown and (n is None or p <= n)]
        shown.update(out)
        return "".join(page_html(p) for p in out)

    for s in secs:
        if paged and s["strane"] and s["level"] == 2:
            body.append(pages_upto(s["strane"][0]))
        elif not paged and slugify(s["naslov"]) not in INTRO and not shown:
            body.append('<p class="notes-lbl">Udžbenik</p>' + pages_upto(None) + '<p class="notes-lbl">Beleške</p>')
        elif paged and not s["strane"] and s["level"] == 2 and any(x["strane"] for x in secs[:secs.index(s)]):
            body.append(pages_upto(None))
        body.append(section_html(s))
    body.append(pages_upto(None))

    i = next((j for j, l in enumerate(ordered) if int(l["broj"]) == broj), None)
    link = lambda l: (f'<a href="../{notes[int(l["broj"])]}/">' if int(l["broj"]) in notes else f'<a href="{catalog}#/{nivo}/{razred}/{predmet}/{l["broj"]}">')
    pager = '<div class="pager">' + (
        (link(ordered[i - 1]) + "‹ " + esc(ordered[i - 1]["naslov"]) + "</a>") if i else "<span></span>") + (
        (link(ordered[i + 1]) + esc(ordered[i + 1]["naslov"]) + " ›</a>") if i is not None and i + 1 < len(ordered) else "<span></span>") + "</div>"

    qz = quizzes(predmet, razred, broj)
    head = (f'<h1>{esc(naslov)}</h1><p class="meta">{esc(predmet_title(predmet))} · {esc(razred_title(razred))}'
            + (f' · {esc(chapter["naslov"])}' if chapter else "")
            + (f" · udžbenik, str. {od}–{do}" if od else "")
            + "".join(f' · <a href="{esc(h)}">{esc(t)} ›</a>' for t, h in qz) + "</p>")

    nav = ""
    if chapter:
        nav += f'<div class="sec">{esc(chapter["naslov"])}</div>'
        for l in chapter.get("lekcije") or []:
            n = int(l["broj"])
            cls = "cur" if n == broj else ("" if n in notes else "off")
            href = f"../{notes[n]}/" if n in notes else f'{catalog}#/{nivo}/{razred}/{predmet}/{n}'
            nav += f'<a class="row {cls}" href="{esc(href)}">{esc(l["naslov"])}</a>'
    nav += '<div class="sec">Sadržaj</div>'
    for s in secs:
        nav += f'<a class="row{" sub" if s["level"] == 3 else ""}" href="#{s["id"]}">{esc(s["naslov"])}</a>'
    nav += '<div class="sec">Strane udžbenika</div>' + "".join(f'<a class="row pg" href="#str-{p}">Strana {p}</a>' for p in pages)
    if qz:
        nav += '<div class="sec">Kvizovi</div>' + "".join(f'<a class="row" href="{esc(h)}">{esc(t)}</a>' for t, h in qz)

    sep = '<span class="sep">›</span>'
    crumbs = (f'<a class="brand" href="{catalog}">{BRAND}</a><nav class="app-crumbs" aria-label="Putanja">'
              + sep.join([f'<a href="{catalog}#/{nivo}">{esc(nivo_title(nivo))}</a>',
                          f'<a href="{catalog}#/{nivo}/{razred}">{esc(razred_title(razred))}</a>',
                          f'<a href="{catalog}#/{nivo}/{razred}/{predmet}">{esc(predmet_title(predmet))}</a>',
                          f'<a class="cur" href="{catalog}#/{nivo}/{razred}/{predmet}/{broj}">{esc(naslov)}</a>']) + "</nav>")
    html = (PAGE.replace("__SHELL_CSS__", SHELL_CSS).replace("__SHELL_JS__", SHELL_JS)
                .replace("__BRAND_CRUMBS__", crumbs).replace("__NAV__", nav)
                .replace("__BODY__", head + "".join(body) + pager).replace("__TITLE__", esc(naslov)))
    if os.environ.get("LEKCIJE_PREVIEW"):   # plain copy for checking, inside the gitignored _source (same depth)
        pv = src / "_preview" / stem / "index.html"
        pv.parent.mkdir(parents=True, exist_ok=True)
        pv.write_text(html, encoding="utf-8")
    size = write_protected(ROOT, out_dir, html, naslov, crumbs, f"{esc(naslov)} — tekst lekcije",
                           "Ova stranica sadrži strane udžbenika i namenjena je samo učenicima.", "Otvori lekciju")
    print(f"{lesson_dir(predmet, razred, stem)}  {len([p for p in pages if p in scans])}/{len(pages)} strana, "
          f"{len(crops)} slika, {len(secs)} odeljaka, {size // 1024} KB")


def main(args):
    preds = args or sorted(p.name for p in (ROOT / "tools").iterdir() if (p / "_source").is_dir())
    for predmet in preds:
        for f in sorted((ROOT / "tools" / predmet / "_source").glob("lekcije-*/[0-9][0-9]-*.md")):
            build(f)


if __name__ == "__main__":
    if sys.argv[1:2] in (["-h"], ["--help"]):
        raise SystemExit(__doc__)
    main(sys.argv[1:])
