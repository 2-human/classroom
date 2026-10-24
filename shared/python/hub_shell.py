"""Three-panel hub shell shared by every classroom tool and by the catalog.

The layout is the Crēdo Marketing Hub shell (MH-10), as reused in gentree/public/hub/hub.css:
a top bar (brand · crumbs · controls) over a grid `navigation | main`, plus a drawer on the
right with the details of whatever was chosen in the navigation or in main. Every entity
exists once; extra information about it belongs in the drawer, not in a second copy.

Classroom tools must stay single self-contained HTML files that work from file://, so the
shell is inlined: a renderer puts SHELL_CSS first in its <style> (its own rules follow and
may override) and SHELL_JS in a <script> before its own script.

Markup contract:
  body.app-body
  header.app-bar     #app-menu (☰, optional) · a.brand · nav.app-crumbs · .bar-right
  div.app-grid       nav.app-nav#app-nav (input.app-filter#app-filter; rows carry
                     data-filter="text"; a [data-filter-group] hides when all its rows do)
                     main.app-main
  aside.app-drawer   .drawer-head (h2 + .drawer-close) · .drawer-body · .drawer-foot
  .bar-menu-wrap     button[data-menu="<id>"] + .bar-menu#<id>   (the ⋯ menu; clicks inside
                     [data-keep-menus] leave open menus alone)
The drawer opens with `.open`. At ≥1200px an open drawer docks (main narrows so nothing is
covered); below that it overlays. The navigation collapses under ☰ at ≤760px, the classroom
mobile breakpoint. The shell sets --htop to the bar's height; its own tokens are --hub-* so a tool's --accent etc. stay its own.
"""
import html as _html
import os
import pathlib

PREDMET_TITLES = {
    "geografija": "Geografija",
    "biologija": "Biologija",
    "hemija": "Hemija",
    "fizika": "Fizika",
    "matematika": "Matematika",
    "istorija": "Istorija",
    "srpski": "Srpski jezik",
    "strani-jezici": "Strani jezici",
    "umetnost": "Likovna kultura",
    "muzicka-kultura": "Muzička kultura",
    "informatika": "Informatika",
}

BRAND = "classroom"


def predmet_title(predmet):
    return PREDMET_TITLES.get(predmet, predmet.replace("-", " ").title())


def _repo_root(start):
    p = pathlib.Path(start).resolve()
    for parent in [p, *p.parents]:
        if (parent / "shared" / "python").is_dir():
            return parent
    return None


def brand_and_crumbs(output_path, title):
    """Brand link to the catalog + `Predmet › Tool` crumbs for a tool at tools/{predmet}/{slug}/."""
    out = pathlib.Path(output_path).resolve()
    root = _repo_root(out.parent)
    catalog = os.path.relpath(root / "index.html", out.parent) if root else "index.html"
    catalog = catalog.replace(os.sep, "/")
    predmet = out.parent.parent.name
    slug = out.parent.name
    esc = _html.escape
    return (
        f'<a class="brand" href="{esc(catalog)}">{BRAND}</a>'
        '<nav class="app-crumbs" aria-label="Putanja">'
        f'<a href="{esc(catalog)}#/{esc(predmet)}">{esc(predmet_title(predmet))}</a>'
        '<span class="sep">›</span>'
        f'<a class="cur" href="{esc(catalog)}#/{esc(predmet)}/{esc(slug)}">{esc(title)}</a>'
        '</nav>'
    )


SHELL_CSS = r"""
 :root{--hub-bg:#faf8f2;--hub-card:#fff;--hub-ink:#2b2b2b;--hub-head:#3a3528;--hub-mute:#6b6456;--hub-line:#e6e0d2;--hub-soft:#f3ecd8;--hub-accent:#b1271f;--hub-ok:#1f7a3a;--hub-nav-w:280px;--hub-drawer-w:440px}
 html:has(.app-body){overflow:hidden}
 .app-body{margin:0;height:100vh;height:100dvh;overflow:hidden;display:flex;flex-direction:column;max-width:100vw;background:var(--hub-bg);color:var(--hub-ink);font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif}
 .app-bar{flex:0 0 auto;display:flex;align-items:center;gap:14px;padding:8px 16px;background:var(--hub-card);border-bottom:1px solid var(--hub-line);min-width:0;position:relative;z-index:50}
 .app-bar .app-menu{display:none;padding:0;width:36px;height:34px;font-size:18px;line-height:1;border:1px solid var(--hub-line);background:var(--hub-card);color:var(--hub-head);border-radius:7px;cursor:pointer}
 .app-bar .app-menu:hover{background:var(--hub-soft);color:var(--hub-head)}
 .brand{font-weight:700;font-size:15px;color:var(--hub-head);text-decoration:none;white-space:nowrap}
 .brand:hover{color:var(--hub-accent)}
 .app-crumbs{display:flex;gap:6px;align-items:center;font-size:13px;color:var(--hub-mute);min-width:0;overflow:hidden;white-space:nowrap}
 .app-crumbs a{color:var(--hub-mute);text-decoration:none}
 .app-crumbs a:hover{color:var(--hub-accent)}
 .app-crumbs .sep{color:#b9b2a0}
 .app-crumbs .cur{color:var(--hub-head);font-weight:600;overflow:hidden;text-overflow:ellipsis}
 .bar-right{margin-left:auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end;min-width:0}
 .app-grid{flex:1 1 auto;display:grid;grid-template-columns:var(--hub-nav-w) minmax(0,1fr);min-height:0}
 .app-nav{background:var(--hub-card);border-right:1px solid var(--hub-line);overflow:auto;padding:10px 10px 40px;min-height:0}
 .app-filter{width:100%;font:inherit;font-size:13px;padding:7px 9px;border:1px solid var(--hub-line);border-radius:6px;margin:0 0 4px;background:#fff;color:var(--hub-ink)}
 .app-filter:focus{outline:none;border-color:var(--hub-mute)}
 .app-nav .sec{display:flex;justify-content:space-between;align-items:baseline;gap:8px;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--hub-mute);padding:12px 6px 4px}
 .app-nav .cnt{font-size:11px;color:var(--hub-mute);font-variant-numeric:tabular-nums;letter-spacing:0;text-transform:none}
 .f-hide{display:none!important}
 .app-main{position:relative;overflow:auto;min-width:0;min-height:0;transition:margin-right .18s ease}
 .app-drawer{position:fixed;top:var(--htop,50px);right:0;bottom:0;width:var(--hub-drawer-w);max-width:100vw;background:var(--hub-card);border-left:1px solid var(--hub-line);box-shadow:-8px 0 24px rgba(58,53,40,.10);transform:translateX(105%);transition:transform .18s ease;z-index:60;display:flex;flex-direction:column}
 .app-drawer.open{transform:none}
 .drawer-head{display:flex;align-items:flex-start;gap:10px;padding:14px 16px 10px;border-bottom:1px solid var(--hub-line)}
 .drawer-head h2{margin:0;font-size:16px;color:var(--hub-head);flex:1 1 auto;overflow-wrap:anywhere}
 .app-drawer .drawer-close{border:0;background:none;padding:0 4px;font-size:24px;line-height:1;cursor:pointer;color:var(--hub-mute)}
 .app-drawer .drawer-close:hover{background:none;color:var(--hub-accent)}
 .drawer-body{flex:1 1 auto;overflow:auto;padding:12px 16px 24px;font-size:13px;line-height:1.55}
 .drawer-foot{flex:0 0 auto;border-top:1px solid var(--hub-line);padding:10px 16px;font-size:12px;color:var(--hub-mute)}
 .mtabs{display:flex;gap:2px;border-bottom:1px solid var(--hub-line);flex-wrap:wrap;background:var(--hub-card);padding:0 12px}
 .mtabs a{text-decoration:none;color:var(--hub-mute);font-size:13px;padding:9px 12px 8px;border-bottom:2px solid transparent}
 .mtabs a[aria-current="page"]{color:var(--hub-head);border-bottom-color:var(--hub-accent);font-weight:600}
 .bar-menu-wrap{position:relative}
 .bar-menu{display:none;position:absolute;right:0;top:calc(100% + 8px);z-index:70;background:var(--hub-card);border:1px solid var(--hub-line);border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.16);padding:8px;min-width:240px}
 .bar-menu.open{display:flex;flex-direction:column;align-items:stretch;gap:6px}
 .tbl{width:100%;border-collapse:collapse;background:var(--hub-card);border:1px solid var(--hub-line);border-radius:6px;font-size:13px}
 .tbl th{text-align:left;font-weight:600;font-size:11.5px;color:var(--hub-mute);padding:8px 10px;border-bottom:1px solid var(--hub-line);background:#fcfaf4;white-space:nowrap}
 .tbl td{padding:7px 10px;border-bottom:1px solid #f0ebe0;vertical-align:top}
 .tbl td.num,.tbl th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
 .tbl tr.clk{cursor:pointer} .tbl tr.clk:hover td{background:#fbf7ec}
 @media (min-width:1200px){ .app-body:has(.app-drawer.open) .app-main{margin-right:var(--hub-drawer-w)} }
 @media (max-width:760px){
   .app-bar{gap:10px;padding:8px 12px}
   .app-bar .app-menu{display:inline-block}
   .app-crumbs{display:none}
   .app-grid{grid-template-columns:minmax(0,1fr)}
   .app-nav{position:fixed;top:var(--htop,50px);left:0;bottom:0;width:300px;max-width:88vw;z-index:55;transform:translateX(-105%);transition:transform .18s ease;box-shadow:8px 0 24px rgba(58,53,40,.10)}
   .app-nav.open{transform:none}
   .app-drawer{width:100vw}
 }
 @media print{
   html:has(.app-body){overflow:visible}
   .app-body{height:auto;overflow:visible;display:block}
   .app-grid{display:block}
   .app-main,.app-nav{overflow:visible}
   .app-drawer,.app-filter,.app-menu,.bar-menu-wrap,.mtabs{display:none!important}
 }
"""

SHELL_JS = r"""
(function () {
  const root = document.documentElement;
  const bar = document.querySelector('.app-bar');
  function setTop() { if (bar) root.style.setProperty('--htop', bar.offsetHeight + 'px'); }
  window.addEventListener('resize', setTop);
  setTop();

  // ☰ navigation (only shown at ≤760px)
  const nav = document.getElementById('app-nav');
  const navBtn = document.getElementById('app-menu');
  const navOverlay = () => window.matchMedia && window.matchMedia('(max-width:760px)').matches;
  function setNav(open) {
    if (!nav) return;
    nav.classList.toggle('open', !!open);
    if (navBtn) navBtn.setAttribute('aria-expanded', String(!!open));
  }
  if (navBtn) navBtn.addEventListener('click', e => { e.stopPropagation(); setNav(!nav.classList.contains('open')); });

  // navigation filter: case- and diacritic-insensitive (š, č, ć, ž, đ)
  const filter = document.getElementById('app-filter');
  const norm = s => String(s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
  function applyFilter() {
    const q = norm(filter.value.trim());
    document.querySelectorAll('#app-nav [data-filter]').forEach(el =>
      el.classList.toggle('f-hide', !!q && !norm(el.dataset.filter).includes(q)));
    document.querySelectorAll('#app-nav [data-filter-group]').forEach(g =>
      g.classList.toggle('f-hide', !!q && !g.querySelector('[data-filter]:not(.f-hide)')));
  }
  if (filter) filter.addEventListener('input', applyFilter);

  // ⋯ menus: a button with data-menu="<id>" toggles .bar-menu#<id>; a button inside closes it
  function setMenu(m, open) {
    m.classList.toggle('open', !!open);
    const b = document.querySelector('[data-menu="' + m.id + '"]');
    if (b) b.setAttribute('aria-expanded', String(!!open));
  }
  document.querySelectorAll('[data-menu]').forEach(btn => {
    const m = document.getElementById(btn.dataset.menu);
    if (!m) return;
    btn.addEventListener('click', e => { e.stopPropagation(); setMenu(m, !m.classList.contains('open')); });
    m.addEventListener('click', e => { e.stopPropagation(); if (e.target.closest('button')) setMenu(m, false); });
  });
  document.addEventListener('click', e => {
    // composedPath: the clicked node may already be re-rendered away (e.g. a step's "next" button)
    if (!e.composedPath().some(n => n.dataset && n.dataset.keepMenus)) document.querySelectorAll('.bar-menu.open').forEach(m => setMenu(m, false));
    if (nav && nav.classList.contains('open') && navOverlay() && !nav.contains(e.target)) setNav(false);
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.bar-menu.open').forEach(m => setMenu(m, false));
    const x = document.querySelector('.app-drawer.open .drawer-close');
    if (x && x.offsetParent !== null) x.click();
  });

  window.HubShell = { setNav, setMenu, applyFilter, navOverlay };
})();
"""
