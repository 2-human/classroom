#!/usr/bin/env python3
"""Regenerate top-level classroom/index.html from tools/*/*/spec.yaml files.

Run after adding a new tool, or whenever a tool's spec.yaml changes its title
or description. Idempotent — safe to run repeatedly.

Usage (from anywhere in the repo):
    python3 scripts/regenerate_index.py

What it does:
    1. Walks tools/{predmet}/{slug}/spec.yaml for every tool.
    2. Groups tools by predmet (the immediate parent folder of the tool).
    3. Writes classroom/index.html with a section per predmet listing all tools.
    4. Detects whether radna.pdf / resenja.pdf exist beside the tool's index.html;
       only emits PDF links if the files are there.

The generated file is fully self-contained HTML; no build, no JS framework. It uses the same
three-panel hub shell as the tools (shared/python/hub_shell.py): navigation = subjects and their
tools, main = the tools of the chosen subject (all subjects by default), drawer = the chosen
tool's description and links. Routes: #/{predmet} and #/{predmet}/{slug} (the tools' crumbs
link here).
"""
import html
import json
import pathlib
import sys
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "shared" / "python"))
from hub_shell import SHELL_CSS, SHELL_JS, BRAND, predmet_title  # noqa: E402


# Predmet ordering for the catalog. Predmeti not in this list appear after,
# alphabetically. Edit this list to change top-level catalog ordering.
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
    """Return dict {predmet: [tool_info, ...]} sorted within each predmet by slug."""
    tools = {}
    tools_dir = repo_root / "tools"
    if not tools_dir.is_dir():
        return tools

    for spec_path in sorted(tools_dir.glob("*/*/spec.yaml")):
        slug = spec_path.parent.name
        predmet = spec_path.parent.parent.name
        try:
            with open(spec_path) as f:
                spec = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"  WARNING: failed to read {spec_path}: {e}", file=sys.stderr)
            continue

        tool_folder = spec_path.parent
        info = {
            "slug": slug,
            "predmet": predmet,
            "title": spec.get("title") or spec.get("title_short") or slug,
            "description": (spec.get("description") or "").strip(),
            "rel_path": f"tools/{predmet}/{slug}/",
            "has_html": (tool_folder / "index.html").exists(),
            "has_radna_pdf": (tool_folder / "radna.pdf").exists(),
            "has_resenja_pdf": (tool_folder / "resenja.pdf").exists(),
        }
        tools.setdefault(predmet, []).append(info)

    for predmet in tools:
        tools[predmet].sort(key=lambda t: t["slug"])

    return tools


def ordered_predmeti(tools):
    """Return predmet keys in catalog order: PREDMET_ORDER first, then alphabetical."""
    known = [p for p in PREDMET_ORDER if p in tools]
    unknown = sorted([p for p in tools if p not in PREDMET_ORDER])
    return known + unknown


def render_nav(tools):
    out = []
    for predmet in ordered_predmeti(tools):
        rows = "".join(
            f'<a class="row" href="#/{predmet}/{t["slug"]}" data-route="{predmet}/{t["slug"]}" '
            f'data-filter="{html.escape(t["title"])}">{html.escape(t["title"])}</a>'
            for t in tools[predmet]
        )
        out.append(
            f'<div data-filter-group><a class="sec" href="#/{predmet}" data-route="{predmet}">'
            f'{html.escape(predmet_title(predmet))} <span class="cnt">{len(tools[predmet])}</span></a>{rows}</div>'
        )
    return "".join(out)


PAGE = r"""<!DOCTYPE html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>classroom — interaktivni alati za nastavu</title>
<style>
__SHELL_CSS__
 :root{--muted:#6b6456;--edge:#b1271f;--accent:#1f7a3a;--border:#e6e0d2}
 .app-nav a.sec{text-decoration:none;border-radius:5px}
 .app-nav a.sec:hover{background:#f6f1e4}
 .app-nav a.row{display:block;color:#2b2b2b;text-decoration:none;font-size:13px;padding:5px 8px;border-radius:5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .app-nav a.row:hover{background:#f6f1e4}
 .app-nav .cur{background:#efe7d2;font-weight:600}
 .cat{padding:26px 28px 60px;max-width:980px}
 .cat h1{font-size:24px;margin:0 0 6px;color:#3a3528}
 .cat .lead{margin:0 0 6px;color:var(--muted);max-width:680px;line-height:1.5}
 .cat .meta{font-size:12.5px;color:var(--muted);margin:10px 0 0}
 .cat .meta a,.dr a{color:var(--edge);text-decoration:none}
 .cat h2{font-size:15px;color:var(--edge);margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
 .tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
 .tile{display:block;text-align:left;font:inherit;color:inherit;cursor:pointer;border:1px solid var(--border);border-radius:8px;padding:14px 16px;background:#fefcf7;text-decoration:none}
 .tile:hover{border-color:var(--accent);background:#fff}
 .tile.sel{border-color:var(--accent);background:#fff;box-shadow:0 0 0 2px rgba(31,122,58,.15)}
 .tile b{display:block;font-size:15px;color:#3a3528;margin-bottom:6px}
 .tile span{font-size:13px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
 .empty{padding:20px 22px;background:#fff;border:1px dashed var(--border);border-radius:10px;color:var(--muted);text-align:center}
 .dr p{margin:0 0 12px;color:#2b2b2b;line-height:1.55}
 .dr .chip{display:inline-block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border:1px solid var(--border);border-radius:9px;padding:1px 8px;margin-bottom:12px}
 .dr .open{display:inline-block;background:var(--accent);color:#fff!important;border-radius:8px;padding:9px 16px;font-weight:600;margin:4px 0 14px}
 .dr ul{margin:0;padding-left:18px} .dr li{margin:4px 0}
</style>
</head>
<body class="app-body">
<header class="app-bar">
 <button class="app-menu" id="app-menu" aria-label="Predmeti" aria-expanded="false">&#9776;</button>
 <a class="brand" href="#/">__BRAND__</a>
 <nav class="app-crumbs" id="app-crumbs" aria-label="Putanja"></nav>
</header>
<div class="app-grid">
 <nav class="app-nav" id="app-nav" aria-label="Predmeti i alati">
  <input class="app-filter" id="app-filter" type="search" placeholder="Nađi alat" aria-label="Nađi alat">
  __NAV__
 </nav>
 <main class="app-main" id="app-main"></main>
</div>
<aside class="app-drawer" id="drawer" aria-hidden="true">
 <div class="drawer-head"><h2 id="drawerTitle"></h2><button class="drawer-close" id="drawerClose" aria-label="Zatvori" title="Zatvori">&times;</button></div>
 <div class="drawer-body dr" id="drawerBody"></div>
</aside>
<script>__SHELL_JS__</script>
<script>
const TOOLS = __TOOLS_JSON__;   // [{predmet, predmetTitle, slug, title, description, href, pdfs:[{label, href}]}]
const main = document.getElementById('app-main');
const crumbs = document.getElementById('app-crumbs');
const drawer = document.getElementById('drawer');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const subjects = [...new Set(TOOLS.map(t => t.predmet))];
function tiles(list, selSlug) {
  return '<div class="tiles">' + list.map(t =>
    '<a class="tile' + (t.slug === selSlug ? ' sel' : '') + '" href="#/' + t.predmet + '/' + t.slug + '"><b>' + esc(t.title) +
    '</b><span>' + esc(t.description) + '</span></a>').join('') + '</div>';
}
function route() {
  const [predmet, slug] = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent);
  const inSubject = predmet && subjects.includes(predmet);
  const tool = inSubject && slug ? TOOLS.find(t => t.predmet === predmet && t.slug === slug) : null;
  // main: one subject, or every subject
  if (!TOOLS.length) {
    main.innerHTML = '<div class="cat"><h1>__BRAND__</h1><div class="empty">Još uvek nema alata. Dodaj prvi alat u <code>tools/{predmet}/{slug}/</code>.</div></div>';
  } else if (inSubject) {
    const list = TOOLS.filter(t => t.predmet === predmet);
    main.innerHTML = '<div class="cat"><h1>' + esc(list[0].predmetTitle) + '</h1>' + tiles(list, slug) + '</div>';
  } else {
    main.innerHTML = '<div class="cat"><h1>__BRAND__</h1>' + INTRO +
      subjects.map(p => { const list = TOOLS.filter(t => t.predmet === p);
        return '<h2>' + esc(list[0].predmetTitle) + '</h2>' + tiles(list); }).join('') + '</div>';
  }
  // crumbs + navigation highlight
  let c = '';
  if (inSubject) c += '<a href="#/' + predmet + '">' + esc(TOOLS.find(t => t.predmet === predmet).predmetTitle) + '</a>';
  if (tool) c += '<span class="sep">›</span><span class="cur">' + esc(tool.title) + '</span>';
  crumbs.innerHTML = c;
  const cur = tool ? predmet + '/' + slug : (inSubject ? predmet : '');
  document.querySelectorAll('#app-nav [data-route]').forEach(a => a.classList.toggle('cur', a.dataset.route === cur));
  // drawer: the chosen tool
  if (tool) {
    document.getElementById('drawerTitle').textContent = tool.title;
    document.getElementById('drawerBody').innerHTML = '<span class="chip">' + esc(tool.predmetTitle) + '</span>' +
      (tool.description ? '<p>' + esc(tool.description) + '</p>' : '') +
      (tool.href ? '<a class="open" href="' + tool.href + '">Otvori interaktivni alat ›</a>' : '') +
      (tool.pdfs.length ? '<ul>' + tool.pdfs.map(p => '<li><a href="' + p.href + '">' + esc(p.label) + '</a></li>').join('') + '</ul>' : '');
    drawer.classList.add('open'); drawer.setAttribute('aria-hidden', 'false');
  } else {
    drawer.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true');
  }
  HubShell.setNav(false);
}
const INTRO = '<p class="lead">Interaktivni alati za nastavu u osnovnoj školi, srednjoj školi i edukaciji odraslih. Svaki alat radi u browseru bez login-a i bez naloga. Mnogi imaju i verziju za štampu.</p>' +
  '<p class="meta">Repo: <a href="https://github.com/tnosugar/classroom">github.com/tnosugar/classroom</a> · Generisano automatski pomoću scripts/regenerate_index.py</p>';
document.getElementById('drawerClose').addEventListener('click', () => {
  const [predmet] = location.hash.replace(/^#\/?/, '').split('/');
  location.hash = predmet ? '#/' + predmet : '#/';
});
window.addEventListener('hashchange', route);
route();
</script>
</body>
</html>
"""


def tool_json(t):
    rel = t["rel_path"]
    pdfs = []
    if t["has_radna_pdf"]:
        pdfs.append({"label": "PDF (radna)", "href": rel + "radna.pdf"})
    if t["has_resenja_pdf"]:
        pdfs.append({"label": "PDF (rešenja)", "href": rel + "resenja.pdf"})
    return {
        "predmet": t["predmet"], "predmetTitle": predmet_title(t["predmet"]), "slug": t["slug"],
        "title": t["title"], "description": t["description"],
        "href": rel + "index.html" if t["has_html"] else "", "pdfs": pdfs,
    }


def main():
    repo_root = find_repo_root(__file__)
    tools = collect_tools(repo_root)
    out_path = repo_root / "index.html"

    tool_list = [tool_json(t) for p in ordered_predmeti(tools) for t in tools[p]]
    html_out = (PAGE
                .replace("__SHELL_CSS__", SHELL_CSS)
                .replace("__SHELL_JS__", SHELL_JS)
                .replace("__NAV__", render_nav(tools))
                .replace("__TOOLS_JSON__", json.dumps(tool_list, ensure_ascii=False).replace("</", "<\\/"))
                .replace("__BRAND__", BRAND))

    # Only write if content actually changed (helps git diff stay clean)
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        if existing == html_out:
            print(f"index.html unchanged (no diff)")
            return

    out_path.write_text(html_out, encoding="utf-8")

    total_tools = sum(len(v) for v in tools.values())
    print(f"Wrote {out_path}")
    print(f"  {total_tools} tool(s) across {len(tools)} predmet(a):")
    for predmet in ordered_predmeti(tools):
        names = ", ".join(t["slug"] for t in tools[predmet])
        print(f"    {predmet}: {names}")


if __name__ == "__main__":
    main()
