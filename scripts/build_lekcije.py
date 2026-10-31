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
import json
import os
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))
from hub_shell import SHELL_CSS, SHELL_JS, BRAND, nivo_title, razred_title, predmet_title  # noqa: E402
from lekcija import parse_note, lesson_dir, lesson_body, LESSON_CSS, LESSON_JS  # noqa: E402
import veze  # noqa: E402
from zasticeno import write_protected  # noqa: E402

esc = _html.escape

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
__LESSON_CSS__
 .les .rel{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 10px}
 .les .rel a{font-size:13px;color:#7a4b12;border:1px solid #ecd3a8;background:#fbf3e3;border-radius:12px;padding:2px 11px;text-decoration:none}
 .les .rel a.kv{color:#1f7a3a;border-color:#bfe0c8;background:#eef7f0}
 .qbtn{font:inherit;font-size:12px;font-weight:400;margin-left:9px;padding:1px 9px;border:1px solid #ecd3a8;background:#fbf3e3;color:#7a4b12;border-radius:11px;cursor:pointer;white-space:nowrap}
 .pit{list-style:none;margin:0;padding:0}
 .pit a{display:flex;gap:8px;padding:7px 4px;border-bottom:1px solid #f0ebe0;color:#2b2b2b;text-decoration:none;font-size:14px;line-height:1.4}
 .pit a:hover{background:#f6f1e4}
 .pit .src{display:block;font-size:12.5px;color:#6b6456}
 .pit ul{margin:3px 0 0;padding-left:18px}
 .pit .tz{flex:0 0 auto;font-size:11px;font-weight:700;width:18px;height:18px;line-height:18px;text-align:center;border-radius:5px}
 .tz-lako{background:#e3f3e7;color:#1f7a3a} .tz-srednje{background:#fbf0d9;color:#9a6a12} .tz-tesko{background:#fbe3e0;color:#b1271f}
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
<aside class="app-drawer" id="drawer" aria-hidden="true">
 <div class="drawer-head"><h2 id="drawerTitle">Pitanja iz banke</h2><button class="drawer-close" id="drawerClose" aria-label="Zatvori" title="Zatvori">&times;</button></div>
 <div class="drawer-body" id="drawerBody"></div>
</aside>
<script>__SHELL_JS__</script>
<script>
__LESSON_JS__
bindLesson(document);
const PITANJA = __PITANJA__, drawer = document.getElementById('drawer'), TZ = { lako: 'L', srednje: 'S', tesko: 'T' };
document.querySelectorAll('.qbtn').forEach(b => b.addEventListener('click', e => {
  e.stopPropagation();
  const s = b.closest('section');
  document.getElementById('drawerTitle').textContent = s.querySelector('h2,h3').firstChild.textContent;
  document.getElementById('drawerBody').innerHTML = '<ul class="pit">' + PITANJA.sec[b.dataset.sec].map(q =>
    '<li><a href="' + PITANJA.url + '#' + q.id + '"><span class="tz tz-' + q.t + '">' + TZ[q.t] + '</span><span>' + q.q + '</span></a></li>').join('') + '</ul>';
  drawer.classList.add('open'); drawer.setAttribute('aria-hidden', 'false');
}));
document.getElementById('drawerClose').addEventListener('click', () => { drawer.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true'); });
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


def related(nivo, razred, predmet, broj, stem, out_dir, sections):
    """What a lesson links to: quizzes drawing from it, its bank page and its questions by section."""
    rel = lambda t: os.path.relpath(ROOT / t, out_dir).replace(os.sep, "/") + ("/" if t.endswith("/") else "")
    qz = [(q["title"], rel(q["href"])) for q in veze.quizzes(ROOT, nivo, razred, predmet) if broj in q["lekcije"]]
    bank = veze.banks(ROOT, nivo, razred, predmet).get(broj)
    if not bank:
        return qz, "", 0, {}
    url = rel(veze.bank_dir(nivo, razred, predmet, stem))
    its = veze.items(bank)[1]
    by_sec = {}
    for z in its:
        s = veze.item_section(sections, z)
        if s:
            by_sec.setdefault(s["id"], []).append({"id": z["id"], "t": z["tezina"], "q": veze.question_html(z)})
    return qz, url, len(its), by_sec


def build(note_file):
    predmet = note_file.parents[2].name
    note = parse_note(note_file)
    fm, stem = note["fm"], note_file.stem
    nivo, razred, broj = fm.get("nivo", "osnovna"), int(fm.get("razred") or 7), int(stem[:2])
    src = note_file.parents[1]
    out_dir = ROOT / lesson_dir(predmet, razred, stem)
    catalog = os.path.relpath(ROOT / "index.html", out_dir).replace(os.sep, "/")

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

    qz, bank_url, bank_n, by_sec = related(nivo, razred, predmet, broj, stem, out_dir, note["sections"])
    chips = {sid: f'<button type="button" class="qbtn" data-sec="{sid}">Pitanja iz banke ({len(v)})</button>' for sid, v in by_sec.items()}
    les = lesson_body(ROOT, note_file, note, chips)
    pages, scans_n, crops_n, secs, od, do = les["pages"], les["skenova"], les["slika"], note["sections"], les["od"], les["do"]
    body = [les["html"]]

    i = next((j for j, l in enumerate(ordered) if int(l["broj"]) == broj), None)
    link = lambda l: (f'<a href="../{notes[int(l["broj"])]}/">' if int(l["broj"]) in notes else f'<a href="{catalog}#/{nivo}/{razred}/{predmet}/{l["broj"]}">')
    pager = '<div class="pager">' + (
        (link(ordered[i - 1]) + "‹ " + esc(ordered[i - 1]["naslov"]) + "</a>") if i else "<span></span>") + (
        (link(ordered[i + 1]) + esc(ordered[i + 1]["naslov"]) + " ›</a>") if i is not None and i + 1 < len(ordered) else "<span></span>") + "</div>"

    head = (f'<h1>{esc(naslov)}</h1><p class="meta">{esc(predmet_title(predmet))} · {esc(razred_title(razred))}'
            + (f' · {esc(chapter["naslov"])}' if chapter else "")
            + (f" · udžbenik, str. {od}–{do}" if od else "")
            + "</p>" + '<div class="rel">' + (f'<a href="{esc(bank_url)}">Banka pitanja: {bank_n} ›</a>' if bank_url else "")
            + "".join(f'<a class="kv" href="{esc(h)}">{esc(t)} ›</a>' for t, h in qz) + "</div>")

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
    if bank_url:
        nav += f'<div class="sec">Banka pitanja</div><a class="row" href="{esc(bank_url)}">{bank_n} pitanja ove lekcije</a>'
    if qz:
        nav += '<div class="sec">Kvizovi</div>' + "".join(f'<a class="row" href="{esc(h)}">{esc(t)}</a>' for t, h in qz)

    sep = '<span class="sep">›</span>'
    crumbs = (f'<a class="brand" href="{catalog}">{BRAND}</a><nav class="app-crumbs" aria-label="Putanja">'
              + sep.join([f'<a href="{catalog}#/{nivo}">{esc(nivo_title(nivo))}</a>',
                          f'<a href="{catalog}#/{nivo}/{razred}">{esc(razred_title(razred))}</a>',
                          f'<a href="{catalog}#/{nivo}/{razred}/{predmet}">{esc(predmet_title(predmet))}</a>',
                          f'<a class="cur" href="{catalog}#/{nivo}/{razred}/{predmet}/{broj}">{esc(naslov)}</a>']) + "</nav>")
    html = (PAGE.replace("__SHELL_CSS__", SHELL_CSS).replace("__SHELL_JS__", SHELL_JS)
                .replace("__LESSON_CSS__", LESSON_CSS).replace("__LESSON_JS__", LESSON_JS)
                .replace("__BRAND_CRUMBS__", crumbs).replace("__NAV__", nav)
                .replace("__BODY__", head + "".join(body) + pager).replace("__TITLE__", esc(naslov))
                .replace("__PITANJA__", json.dumps({"url": bank_url, "sec": by_sec}, ensure_ascii=False).replace("</", "<\\/")))
    if os.environ.get("LEKCIJE_PREVIEW"):   # plain copy for checking, inside the gitignored _source (same depth)
        pv = src / "_preview" / stem / "index.html"
        pv.parent.mkdir(parents=True, exist_ok=True)
        pv.write_text(html, encoding="utf-8")
    size = write_protected(ROOT, out_dir, html, naslov, crumbs, f"{esc(naslov)} — tekst lekcije",
                           "Ova stranica sadrži strane udžbenika i namenjena je samo učenicima.", "Otvori lekciju")
    print(f"{lesson_dir(predmet, razred, stem)}  {scans_n}/{len(pages)} strana, "
          f"{crops_n} slika, {len(secs)} odeljaka, {size // 1024} KB")


def main(args):
    preds = args or sorted(p.name for p in (ROOT / "tools").iterdir() if (p / "_source").is_dir())
    for predmet in preds:
        for f in sorted((ROOT / "tools" / predmet / "_source").glob("lekcije-*/[0-9][0-9]-*.md")):
            build(f)


if __name__ == "__main__":
    if sys.argv[1:2] in (["-h"], ["--help"]):
        raise SystemExit(__doc__)
    main(sys.argv[1:])
