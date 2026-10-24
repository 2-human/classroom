#!/usr/bin/env python3
"""Regenerate top-level classroom/index.html (the catalog) from the tools and the curriculum.

Run after adding a new tool, or whenever a tool's spec.yaml or a curriculum file changes.
Idempotent — safe to run repeatedly.

Usage (from anywhere in the repo):
    python3 scripts/regenerate_index.py

Information architecture: školski nivo › razred › predmet › lekcija › alati.
    - Tools: tools/{predmet}/{slug}/spec.yaml with `nivo` (osnovna | srednja), `razred` and,
      optionally, `lekcije: [broj, ...]`. A tool without `lekcije` belongs to the whole subject.
    - Curriculum: shared/kurikulum/{nivo}/{razred}/{predmet}.yaml — textbook, chapters and
      lessons. Optional: a subject without one lists only its tools. Every lesson is shown,
      also the ones that have no tool yet.
    - Levels come from hub_shell.NIVOI; a level without tools is listed as empty.
    - PDF links only when radna.pdf / resenja.pdf exist beside the tool's index.html.
    - Where zasticeno/{predmet}/{slug}/bundle.enc exists (scripts/build_zasticeno.py), the
      password-protected copy with the textbook images is the default "Otvori kviz"; the public
      copy without images is the secondary link.

The generated file is self-contained HTML on the same three-panel hub shell as the tools
(shared/python/hub_shell.py): navigation = the tree, main = the chosen node, drawer = the
chosen tool. Routes: #/{nivo}[/{razred}[/{predmet}[/{lekcija}]]], plus ?t={slug} for a tool
of the subject in the route (the tools' crumbs link here).
"""
import json
import pathlib
import sys
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "shared" / "python"))
from hub_shell import (SHELL_CSS, SHELL_JS, BRAND, NIVOI, predmet_title,  # noqa: E402
                       nivo_title, razred_title)


# Predmet ordering for the catalog. Predmeti not in this list appear after,
# alphabetically. Edit this list to change the catalog ordering.
PREDMET_ORDER = [
    "geografija",
    "biologija",
    "hemija",
    "fizika",
    "matematika",
    "istorija",
    "srpski",
    "strani-jezici",
    "umetnost",
    "muzicka-kultura",
    "informatika",
]
# Subject titles live in shared/python/hub_shell.py (PREDMET_TITLES), shared with the tools' crumbs.


def find_repo_root(start):
    """Walk up from `start` until we find a folder containing shared/python/."""
    p = pathlib.Path(start).resolve()
    for parent in [p, *p.parents]:
        if (parent / "shared" / "python").is_dir():
            return parent
    raise SystemExit(f"Could not find classroom repo root from {start}")


def collect_tools(repo_root):
    """Return a list of tool info dicts, one per tools/{predmet}/{slug}/spec.yaml."""
    tools = []
    for spec_path in sorted((repo_root / "tools").glob("*/*/spec.yaml")):
        slug = spec_path.parent.name
        predmet = spec_path.parent.parent.name
        try:
            with open(spec_path) as f:
                spec = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"  WARNING: failed to read {spec_path}: {e}", file=sys.stderr)
            continue
        folder = spec_path.parent
        rel = f"tools/{predmet}/{slug}/"
        pdfs = []
        if (folder / "radna.pdf").exists():
            pdfs.append({"label": "PDF (radna)", "href": rel + "radna.pdf"})
        if (folder / "resenja.pdf").exists():
            pdfs.append({"label": "PDF (rešenja)", "href": rel + "resenja.pdf"})
        tools.append({
            "slug": slug,
            "predmet": predmet,
            "nivo": spec.get("nivo"),
            "razred": spec.get("razred"),
            "lekcije": [int(n) for n in (spec.get("lekcije") or [])],
            "title": spec.get("title") or spec.get("title_short") or slug,
            "description": (spec.get("description") or "").strip(),
            "href": rel + "index.html" if (folder / "index.html").exists() else "",
            "pdfs": pdfs,
            "zasticeno": f"zasticeno/{predmet}/{slug}/" if (repo_root / "zasticeno" / predmet / slug / "bundle.enc").exists() else "",
        })
    return tools


def load_kurikulum(repo_root):
    """{(nivo, razred, predmet): curriculum dict} from shared/kurikulum/{nivo}/{razred}/{predmet}.yaml."""
    out = {}
    for p in sorted((repo_root / "shared" / "kurikulum").glob("*/*/*.yaml")):
        with open(p) as f:
            k = yaml.safe_load(f) or {}
        out[(p.parent.parent.name, int(p.parent.name), p.stem)] = k
    return out


def predmet_key(predmet):
    return (PREDMET_ORDER.index(predmet), "") if predmet in PREDMET_ORDER else (len(PREDMET_ORDER), predmet)


def build_tree(tools, kurikulum):
    """Levels › grades › subjects › chapters › lessons, with tool slugs attached where they belong."""
    unplaced = [t for t in tools if not (t["nivo"] and t["razred"])]
    for t in unplaced:
        print(f"  WARNING: tools/{t['predmet']}/{t['slug']} has no nivo/razred in spec.yaml — "
              "listed under 'Nerazvrstano'", file=sys.stderr)
    levels = list(NIVOI)
    known = {n for n, _ in levels}
    for t in tools:
        if t["nivo"] and t["nivo"] not in known:
            levels.append((t["nivo"], nivo_title(t["nivo"])))
            known.add(t["nivo"])

    tree = []
    for nivo, ntitle in levels:
        razredi = sorted({t["razred"] for t in tools if t["nivo"] == nivo} |
                         {r for (n, r, _) in kurikulum if n == nivo})
        grades = []
        for razred in razredi:
            here = [t for t in tools if t["nivo"] == nivo and t["razred"] == razred]
            predmeti = sorted({t["predmet"] for t in here} |
                              {p for (n, r, p) in kurikulum if n == nivo and r == razred}, key=predmet_key)
            subjects = []
            for predmet in predmeti:
                st = [t for t in here if t["predmet"] == predmet]
                k = kurikulum.get((nivo, razred, predmet)) or {}
                numbers = set()
                chapters = []
                for pg in k.get("poglavlja") or []:
                    lessons = []
                    for l in pg.get("lekcije") or []:
                        n = int(l["broj"])
                        numbers.add(n)
                        lessons.append({"broj": n, "naslov": l["naslov"],
                                        "tools": [t["slug"] for t in st if n in t["lekcije"]]})
                    chapters.append({"naslov": pg.get("naslov", ""), "lekcije": lessons})
                for t in st:
                    missing = [n for n in t["lekcije"] if n not in numbers]
                    if missing:
                        print(f"  WARNING: tools/{predmet}/{t['slug']}: lekcije {missing} are not in "
                              f"shared/kurikulum/{nivo}/{razred}/{predmet}.yaml", file=sys.stderr)
                subjects.append({
                    "predmet": predmet, "title": predmet_title(predmet), "udzbenik": k.get("udzbenik", ""),
                    "poglavlja": chapters,
                    "whole": [t["slug"] for t in st if not (set(t["lekcije"]) & numbers)],
                    "tools": [t["slug"] for t in st],
                })
            grades.append({"razred": razred, "title": razred_title(razred), "subjects": subjects})
        tree.append({"nivo": nivo, "title": ntitle, "grades": grades})
    if unplaced:
        tree.append({"nivo": "nerazvrstano", "title": "Nerazvrstano", "grades": [], "loose": [
            {"predmet": t["predmet"], "slug": t["slug"]} for t in unplaced]})
    return tree


PAGE = r"""<!DOCTYPE html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>classroom — interaktivni alati za nastavu</title>
<style>
__SHELL_CSS__
 :root{--muted:#6b6456;--edge:#b1271f;--accent:#1f7a3a;--border:#e6e0d2}
 .app-nav a{text-decoration:none}
 .app-nav .sec{border-radius:5px}
 .app-nav a.sec:hover{background:#f6f1e4}
 .app-nav .row{display:flex;align-items:baseline;gap:6px;color:#2b2b2b;font-size:13px;padding:5px 8px;border-radius:5px}
 .app-nav .row:hover{background:#f6f1e4}
 .app-nav .row .lbl{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .app-nav .row.g{font-weight:600;color:#3a3528}
 .app-nav .row.s{padding-left:18px}
 .app-nav .row.l,.app-nav .row.t{padding-left:30px;font-size:12.5px}
 .app-nav .row.l:not(.has){color:#9b9387}
 .app-nav .row.t .lbl{font-style:italic}
 .app-nav .cur{background:#efe7d2;font-weight:600}
 .app-nav .none{font-size:12px;color:#9b9387;padding:2px 8px 6px}
 .app-nav .les{display:none}
 .app-nav .les.open,.app-nav.filtering .les{display:block}
 .cat{padding:26px 28px 60px;max-width:1000px}
 .cat h1{font-size:24px;margin:0 0 6px;color:#3a3528}
 .cat .lead{margin:0 0 6px;color:var(--muted);max-width:720px;line-height:1.5}
 .cat .meta{font-size:12.5px;color:var(--muted);margin:10px 0 0}
 .cat .meta a,.dr a{color:var(--edge);text-decoration:none}
 .cat h2{font-size:15px;color:var(--edge);margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
 .tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
 .tile{display:block;color:inherit;border:1px solid var(--border);border-radius:8px;padding:14px 16px;background:#fefcf7;text-decoration:none}
 .tile:hover{border-color:var(--accent);background:#fff}
 .tile.sel{border-color:var(--accent);background:#fff;box-shadow:0 0 0 2px rgba(31,122,58,.15)}
 .tile b{display:block;font-size:15px;color:#3a3528;margin-bottom:6px}
 .tile span{font-size:13px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
 .empty{padding:16px 18px;background:#fff;border:1px dashed var(--border);border-radius:10px;color:var(--muted)}
 .lessons{list-style:none;margin:0;padding:0;border:1px solid var(--border);border-radius:8px;background:#fff}
 .lessons li{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px;padding:8px 12px;border-bottom:1px solid #f0ebe0}
 .lessons li:last-child{border-bottom:0}
 .lessons a.ln{color:#3a3528;text-decoration:none;flex:1 1 260px}
 .lessons a.ln:hover{color:var(--edge)}
 .lessons li.none a.ln{color:#9b9387}
 .tchip{font-size:12px;color:var(--accent);border:1px solid #bfe0c8;background:#eef7f0;border-radius:10px;padding:1px 9px;text-decoration:none;white-space:nowrap}
 .tchip:hover{background:#d8f0dd}
 .pager{display:flex;justify-content:space-between;gap:12px;margin-top:24px;font-size:13px}
 .pager a{color:var(--edge);text-decoration:none}
 .dr p{margin:0 0 12px;color:#2b2b2b;line-height:1.55}
 .dr .chip{display:inline-block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border:1px solid var(--border);border-radius:9px;padding:1px 8px;margin-bottom:12px}
 .dr h3{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:16px 0 6px}
 .dr .ref{font-size:12.5px;color:var(--muted);margin:0 0 12px}
 .dr .open{display:inline-block;background:var(--accent);color:#fff!important;border-radius:8px;padding:9px 16px;font-weight:600;margin:4px 0 6px}
 .dr ul{margin:0;padding-left:18px} .dr li{margin:4px 0}
</style>
</head>
<body class="app-body">
<header class="app-bar">
 <button class="app-menu" id="app-menu" aria-label="Razredi i predmeti" aria-expanded="false">&#9776;</button>
 <a class="brand" href="#/">__BRAND__</a>
 <nav class="app-crumbs" id="app-crumbs" aria-label="Putanja"></nav>
</header>
<div class="app-grid">
 <nav class="app-nav" id="app-nav" aria-label="Nivoi, razredi, predmeti i lekcije">
  <input class="app-filter" id="app-filter" type="search" placeholder="Nađi lekciju ili alat" aria-label="Nađi lekciju ili alat">
  <div id="tree"></div>
 </nav>
 <main class="app-main" id="app-main"></main>
</div>
<aside class="app-drawer" id="drawer" aria-hidden="true">
 <div class="drawer-head"><h2 id="drawerTitle"></h2><button class="drawer-close" id="drawerClose" aria-label="Zatvori" title="Zatvori">&times;</button></div>
 <div class="drawer-body dr" id="drawerBody"></div>
</aside>
<script>__SHELL_JS__</script>
<script>
const TREE = __TREE_JSON__;     // [{nivo, title, grades:[{razred, title, subjects:[{predmet, title, udzbenik, poglavlja:[{naslov, lekcije:[{broj, naslov, tools}]}], whole, tools}]}]}]
const TOOLS = __TOOLS_JSON__;   // [{predmet, slug, nivo, razred, lekcije, title, description, href, pdfs}]
const INTRO = '<p class="lead">Interaktivni alati za nastavu, po školskom nivou, razredu, predmetu i lekciji. Svaki alat radi u browseru bez login-a i bez naloga. Mnogi imaju i verziju za štampu.</p>' +
  '<p class="meta">Repo: <a href="https://github.com/tnosugar/classroom">github.com/tnosugar/classroom</a> · Generisano automatski pomoću scripts/regenerate_index.py</p>';
const main = document.getElementById('app-main');
const crumbs = document.getElementById('app-crumbs');
const drawer = document.getElementById('drawer');
const nav = document.getElementById('app-nav');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const tool = (predmet, slug) => TOOLS.find(t => t.predmet === predmet && t.slug === slug);
const plural = (n, one, few, many) => n + ' ' + (n % 10 === 1 && n % 100 !== 11 ? one : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? few : many));
const nAlata = n => plural(n, 'alat', 'alata', 'alata');
const lessonsOf = s => s.poglavlja.flatMap(p => p.lekcije.map(l => Object.assign({ poglavlje: p.naslov }, l)));

// --- navigation tree (levels › grades › subjects › lessons; a subject's lessons unfold when it is current) ---
function renderNav() {
  let h = '';
  for (const lv of TREE) {
    h += '<div data-filter-group><a class="sec" href="#/' + lv.nivo + '" data-route="' + lv.nivo + '">' + esc(lv.title) + '</a>';
    if (!lv.grades.length && !(lv.loose || []).length) h += '<div class="none">Još nema alata</div>';
    for (const t of lv.loose || []) {
      const x = tool(t.predmet, t.slug);
      h += '<a class="row t" href="' + esc(x.href) + '" data-filter="' + esc(x.title) + '"><span class="lbl">' + esc(x.title) + '</span></a>';
    }
    for (const g of lv.grades) {
      const gr = lv.nivo + '/' + g.razred;
      h += '<div data-filter-group><a class="row g" href="#/' + gr + '" data-route="' + gr + '"><span class="lbl">' + esc(g.title) + '</span></a>';
      for (const s of g.subjects) {
        const sr = gr + '/' + s.predmet;
        h += '<div data-filter-group><a class="row s" href="#/' + sr + '" data-route="' + sr + '"><span class="lbl">' + esc(s.title) +
             '</span><span class="cnt">' + s.tools.length + '</span></a><div class="les" data-subj="' + sr + '">';
        for (const slug of s.whole) {
          const x = tool(s.predmet, slug);
          h += '<a class="row t" href="#/' + sr + '?t=' + slug + '" data-route="' + sr + '?t=' + slug + '" data-filter="' +
               esc(g.title + ' ' + s.title + ' ' + x.title) + '"><span class="lbl">' + esc(x.title) + '</span></a>';
        }
        for (const l of lessonsOf(s)) {
          const names = l.tools.map(slug => tool(s.predmet, slug).title).join(' ');
          h += '<a class="row l' + (l.tools.length ? ' has' : '') + '" href="#/' + sr + '/' + l.broj + '" data-route="' + sr + '/' + l.broj +
               '" data-filter="' + esc(g.title + ' ' + s.title + ' ' + l.broj + '. ' + l.naslov + ' ' + names) + '"><span class="lbl">' +
               l.broj + '. ' + esc(l.naslov) + '</span>' + (l.tools.length ? '<span class="cnt">' + l.tools.length + '</span>' : '') + '</a>';
        }
        h += '</div></div>';
      }
      h += '</div>';
    }
    h += '</div>';
  }
  document.getElementById('tree').innerHTML = h;
}
document.getElementById('app-filter').addEventListener('input', e => nav.classList.toggle('filtering', !!e.target.value.trim()));

// --- main views ---
function toolTiles(predmet, slugs, base, sel) {
  return '<div class="tiles">' + slugs.map(slug => { const t = tool(predmet, slug);
    return '<a class="tile' + (slug === sel ? ' sel' : '') + '" href="#/' + base + '?t=' + slug + '"><b>' + esc(t.title) +
           '</b><span>' + esc(t.description) + '</span></a>'; }).join('') + '</div>';
}
function gradeTiles(lv) {
  if (!lv.grades.length) return '<div class="empty">Još nema alata.</div>';
  return '<div class="tiles">' + lv.grades.map(g => '<a class="tile" href="#/' + lv.nivo + '/' + g.razred + '"><b>' + esc(g.title) +
    '</b><span>' + g.subjects.map(s => esc(s.title) + ' · ' + nAlata(s.tools.length)).join('<br>') + '</span></a>').join('') + '</div>';
}
function subjectView(lv, g, s, sel) {
  const base = lv.nivo + '/' + g.razred + '/' + s.predmet;
  let h = '<h1>' + esc(s.title) + '</h1><p class="lead">' + esc(g.title) + ' · ' + esc(lv.title) +
          (s.udzbenik ? ' · udžbenik: ' + esc(s.udzbenik) : '') + '</p>';
  if (s.whole.length) h += '<h2>' + (s.poglavlja.length ? 'Za ceo predmet' : 'Alati') + '</h2>' + toolTiles(s.predmet, s.whole, base, sel);
  if (!s.poglavlja.length && !s.whole.length) h += '<div class="empty">Još nema alata.</div>';
  if (!s.poglavlja.length && s.whole.length) h += '<p class="meta">Lekcije za ovaj predmet još nisu unete (shared/kurikulum/' + base + '.yaml).</p>';
  for (const p of s.poglavlja) {
    h += '<h2>' + esc(p.naslov) + '</h2><ul class="lessons">' + p.lekcije.map(l =>
      '<li' + (l.tools.length ? '' : ' class="none"') + '><a class="ln" href="#/' + base + '/' + l.broj + '">' + l.broj + '. ' + esc(l.naslov) + '</a>' +
      l.tools.map(slug => '<a class="tchip" href="#/' + base + '/' + l.broj + '?t=' + slug + '">' + esc(tool(s.predmet, slug).title) + '</a>').join('') +
      '</li>').join('') + '</ul>';
  }
  return h;
}
function lessonView(lv, g, s, l, sel) {
  const base = lv.nivo + '/' + g.razred + '/' + s.predmet;
  const all = lessonsOf(s), i = all.findIndex(x => x.broj === l.broj);
  const link = x => x ? '<a href="#/' + base + '/' + x.broj + '">' : '<span>';
  return '<h1>' + l.broj + '. ' + esc(l.naslov) + '</h1><p class="lead">' + esc(s.title) + ' · ' + esc(g.title) + ' · ' + esc(l.poglavlje) + '</p>' +
    (l.tools.length ? '<h2>Alati</h2>' + toolTiles(s.predmet, l.tools, base + '/' + l.broj, sel) : '<div class="empty">Za ovu lekciju još nema alata.</div>') +
    '<div class="pager">' + (all[i - 1] ? link(all[i - 1]) + '‹ ' + all[i - 1].broj + '. ' + esc(all[i - 1].naslov) + '</a>' : '<span></span>') +
    (all[i + 1] ? link(all[i + 1]) + all[i + 1].broj + '. ' + esc(all[i + 1].naslov) + ' ›</a>' : '<span></span>') + '</div>';
}

// --- drawer: the chosen tool ---
function showTool(t, lv, g, s) {
  const base = lv.nivo + '/' + g.razred + '/' + s.predmet;
  const les = lessonsOf(s).filter(l => t.lekcije.includes(l.broj));
  document.getElementById('drawerTitle').textContent = t.title;
  document.getElementById('drawerBody').innerHTML = '<span class="chip">' + esc(g.title) + ' · ' + esc(s.title) + '</span>' +
    (t.description ? '<p>' + esc(t.description) + '</p>' : '') +
    // the version with the textbook images (password) is the default where it exists
    (t.zasticeno ? '<a class="open" href="' + t.zasticeno + '">Otvori kviz ›</a><p class="ref">Sa slikama iz udžbenika — lozinku daje nastavnik.' +
      (t.href ? ' <a href="' + t.href + '">Verzija bez slika (bez lozinke)</a>' : '') + '</p>'
      : (t.href ? '<a class="open" href="' + t.href + '">Otvori interaktivni alat ›</a>' : '')) +
    (les.length ? '<h3>Lekcije</h3><ul>' + les.map(l => '<li><a href="#/' + base + '/' + l.broj + '?t=' + t.slug + '">' + l.broj + '. ' + esc(l.naslov) + '</a></li>').join('') + '</ul>' : '') +
    (t.pdfs.length ? '<h3>Za štampu</h3><ul>' + t.pdfs.map(p => '<li><a href="' + p.href + '">' + esc(p.label) + '</a></li>').join('') + '</ul>' : '');
  drawer.classList.add('open'); drawer.setAttribute('aria-hidden', 'false');
}

function route() {
  const [path, query] = location.hash.replace(/^#\/?/, '').split('?');
  const [nivo, razred, predmet, broj] = path.split('/').filter(Boolean).map(decodeURIComponent);
  const sel = new URLSearchParams(query || '').get('t');
  const lv = TREE.find(x => x.nivo === nivo);
  const g = lv && lv.grades.find(x => String(x.razred) === razred);
  const s = g && g.subjects.find(x => x.predmet === predmet);
  const l = s && lessonsOf(s).find(x => String(x.broj) === broj);
  const t = s && sel && s.tools.includes(sel) ? tool(s.predmet, sel) : null;

  let h;
  if (l) h = lessonView(lv, g, s, l, sel);
  else if (s) h = subjectView(lv, g, s, sel);
  else if (g) h = '<h1>' + esc(g.title) + '</h1><p class="lead">' + esc(lv.title) + '</p>' + (g.subjects.length ? '<div class="tiles">' +
      g.subjects.map(x => '<a class="tile" href="#/' + lv.nivo + '/' + g.razred + '/' + x.predmet + '"><b>' + esc(x.title) + '</b><span>' +
      (x.poglavlja.length ? plural(lessonsOf(x).length, 'lekcija', 'lekcije', 'lekcija') + ' · ' : '') + nAlata(x.tools.length) + '</span></a>').join('') + '</div>'
      : '<div class="empty">Još nema predmeta.</div>');
  else if (lv) h = '<h1>' + esc(lv.title) + '</h1>' + gradeTiles(lv);
  else h = '<h1>__BRAND__</h1>' + INTRO + TREE.filter(x => !x.loose).map(x => '<h2>' + esc(x.title) + '</h2>' + gradeTiles(x)).join('');
  main.innerHTML = '<div class="cat">' + h + '</div>';

  const trail = [];
  if (lv) trail.push(['#/' + lv.nivo, lv.title]);
  if (g) trail.push(['#/' + lv.nivo + '/' + g.razred, g.title]);
  if (s) trail.push(['#/' + lv.nivo + '/' + g.razred + '/' + s.predmet, s.title]);
  if (l) trail.push(['#/' + lv.nivo + '/' + g.razred + '/' + s.predmet + '/' + l.broj, l.broj + '. ' + l.naslov]);
  if (t) trail.push(['', t.title]);
  crumbs.innerHTML = trail.map(([href, txt], i) => i === trail.length - 1 ? '<span class="cur">' + esc(txt) + '</span>'
    : '<a href="' + href + '">' + esc(txt) + '</a>').join('<span class="sep">›</span>');

  const cur = [nivo, razred, predmet, broj].filter(Boolean).join('/');
  const curRoute = s && !l && t && s.whole.includes(t.slug) ? cur + '?t=' + t.slug : cur;
  nav.querySelectorAll('[data-route]').forEach(a => a.classList.toggle('cur', a.dataset.route === curRoute));
  nav.querySelectorAll('.les').forEach(d => d.classList.toggle('open', !!s && d.dataset.subj === lv.nivo + '/' + g.razred + '/' + s.predmet));
  const c = nav.querySelector('.cur'); if (c) c.scrollIntoView({ block: 'nearest' });

  if (t) showTool(t, lv, g, s);
  else { drawer.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true'); }
  HubShell.setNav(false);
}
document.getElementById('drawerClose').addEventListener('click', () => { location.hash = location.hash.split('?')[0] || '#/'; });
window.addEventListener('hashchange', route);
renderNav();
route();
</script>
</body>
</html>
"""


def main():
    repo_root = find_repo_root(__file__)
    tools = collect_tools(repo_root)
    kurikulum = load_kurikulum(repo_root)
    out_path = repo_root / "index.html"

    tree = build_tree(tools, kurikulum)
    tools.sort(key=lambda t: (predmet_key(t["predmet"]), t["slug"]))
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    html_out = (PAGE
                .replace("__SHELL_CSS__", SHELL_CSS)
                .replace("__SHELL_JS__", SHELL_JS)
                .replace("__TREE_JSON__", js(tree))
                .replace("__TOOLS_JSON__", js(tools))
                .replace("__BRAND__", BRAND))

    # Only write if content actually changed (helps git diff stay clean)
    if out_path.exists() and out_path.read_text(encoding="utf-8") == html_out:
        print("index.html unchanged (no diff)")
        return
    out_path.write_text(html_out, encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"  {len(tools)} tool(s):")
    for t in tools:
        where = f"{t['nivo']}/{t['razred']}/{t['predmet']}" + (f" lekcije {t['lekcije']}" if t["lekcije"] else " (ceo predmet)")
        print(f"    {t['slug']}: {where}")


if __name__ == "__main__":
    main()
