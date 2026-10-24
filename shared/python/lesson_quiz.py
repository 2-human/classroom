"""Render a lesson quiz ("lesson-quiz"): many item types for one lesson, on the hub shell.

One spec.yaml (see templates/lesson-quiz/spec.template.yaml) → one self-contained index.html.

Core mechanic, shared by every item type — the help ladder ("lestvica pomoći"):
    question → attempt → mistake → help step 1 (drawer) → attempt → mistake → help step 2 → …
    → correct: points by mistakes (0 → 3, 1 → 2, 2+ → 1)
    → a mistake after the last help step reveals the answer (0 points) with its explanation.
Modes: Učenje (help on) · Test (no help; same scoring) · Ispravka (the test items that were not
answered without mistakes, again, with help; test score stays). In Učenje, revealed items can be
repeated from the ⋯ menu.

Item types (`vrsta`):
    izbor          A  one or more correct options (one correct → click checks at once)
    tacno_netacno  B  true/false; a false statement then asks for its correction (`ispravke`)
                      (a wrong true/false guess on a TRUE statement reveals it — no free second guess)
    dopuni         C  text with {{blanks|alternative}}; optional word bank `ponudjene`
    povezi         D  match left↔right (`parovi`)
    zakljuci       K  reasoning: like izbor (one correct), help steps are reasoning steps
    karta_klik     H  click a country (`cilj: {drzava: ISO3}`) or a place (`cilj: {mesto: slug}`)
    gde_sam        I  clues appear one by one (each wrong click or "još jedan trag" = next clue)

Layout (hub shell): navigation = the items by lesson section with status and points · main = the
current item (map items get the map) · drawer = help ladder, then "Saznaj više" (explanation,
concepts, other lessons where they appear — read from the private lesson graph when present).

Progress persists to localStorage per STATE_VERSION (a bump drops saved progress; see CLAUDE.md).
"""
import json as _json
import math
import os
import pathlib
import re

import yaml

from projection import make_projection
from geojson_utils import load_geojson
from hub_shell import SHELL_CSS, SHELL_JS, brand_and_crumbs

VRSTE = {"izbor", "tacno_netacno", "dopuni", "povezi", "zakljuci", "karta_klik", "gde_sam"}


# ---------------------------------------------------------------------------
# Spec loading + validation
# ---------------------------------------------------------------------------

def load_spec(path):
    path = pathlib.Path(path).resolve()
    with open(path) as f:
        spec = yaml.safe_load(f)
    spec["_spec_dir"] = str(path.parent)
    if spec.get("karta"):
        spec["karta"]["_geo_data_resolved"] = str((path.parent / spec["karta"]["geo_data"]).resolve())
    ids = set()
    mesta = (spec.get("karta") or {}).get("mesta") or {}
    drzave = (spec.get("karta") or {}).get("drzave") or {}
    for deo in spec["delovi"]:
        for z in deo["zadaci"]:
            where = f"zadatak {z.get('id')!r}"
            if z.get("id") in ids or not z.get("id"):
                raise SystemExit(f"{where}: id missing or duplicated")
            ids.add(z["id"])
            v = z.get("vrsta")
            if v not in VRSTE:
                raise SystemExit(f"{where}: unknown vrsta {v!r}")
            if v in ("izbor", "zakljuci"):
                n = sum(1 for o in z["odgovori"] if o.get("tacan"))
                if n == 0 or (v == "zakljuci" and n != 1):
                    raise SystemExit(f"{where}: needs {'exactly one' if v == 'zakljuci' else 'a'} correct answer")
            if v == "tacno_netacno" and not z["tacno"]:
                if sum(1 for o in z.get("ispravke") or [] if o.get("tacan")) != 1:
                    raise SystemExit(f"{where}: a false statement needs `ispravke` with exactly one correct")
            if v == "dopuni" and not re.search(r"\{\{.+?\}\}", z.get("tekst", "")):
                raise SystemExit(f"{where}: `tekst` has no {{blanks}}")
            if v in ("karta_klik", "gde_sam"):
                c = z.get("cilj") or {}
                if not ((c.get("drzava") in drzave) or (c.get("mesto") in mesta)):
                    raise SystemExit(f"{where}: cilj must name a karta.drzave ISO or a karta.mesta slug")
            if v == "gde_sam" and len(z.get("tragovi") or []) < 2:
                raise SystemExit(f"{where}: gde_sam needs at least 2 tragovi")
    return spec


# ---------------------------------------------------------------------------
# Map (countries as SVG paths; South-Europe states clickable)
# ---------------------------------------------------------------------------

def _render_map(spec):
    k = spec["karta"]
    ext_lon, ext_lat = tuple(k["extent"]["lon"]), tuple(k["extent"]["lat"])
    W = float(k.get("width_px", 1000))
    px, W, H = make_projection(ext_lon, ext_lat, k["mid_lat_for_aspect"], W)
    drzave = k.get("drzave") or {}
    spoji = k.get("spoji") or {}
    geo = load_geojson(k["_geo_data_resolved"])
    pad = 4
    paths = []
    for f in geo["features"]:
        iso = f["properties"].get("ADM0_A3")
        g = f.get("geometry") or {}
        polys = g.get("coordinates", []) if g.get("type") == "MultiPolygon" else [g.get("coordinates", [])]
        d = []
        for poly in polys:
            for ring in poly:
                xs = [c[0] for c in ring]; ys = [c[1] for c in ring]
                if max(xs) < ext_lon[0] - pad or min(xs) > ext_lon[1] + pad or max(ys) < ext_lat[0] - pad or min(ys) > ext_lat[1] + pad:
                    continue
                pts, last = [], None
                for lon, lat in ring:
                    x, y = px(lon, lat)
                    p = f"{x:.1f},{y:.1f}"
                    if p != last:
                        pts.append(p); last = p
                if len(pts) > 2:
                    d.append("M" + "L".join(pts) + "Z")
        if not d:
            continue
        key = spoji.get(iso, iso)
        cls = "c se" if key in drzave else "c"
        paths.append(f'<path class="{cls}" data-iso="{key}" d="{"".join(d)}"/>')
    sx = W / (ext_lon[1] - ext_lon[0])
    sy = sx / math.cos(math.radians(k["mid_lat_for_aspect"]))
    proj = {"lon0": ext_lon[0], "lat1": ext_lat[1], "sx": sx, "sy": sy, "w": round(W), "h": round(H)}
    return "".join(paths), proj


# ---------------------------------------------------------------------------
# "Saznaj više": other lessons per concept, from the private lesson graph if present
# ---------------------------------------------------------------------------

def _lesson_links(spec, output_path):
    out = pathlib.Path(output_path).resolve()
    root = next((p for p in out.parents if (p / "shared" / "python").is_dir()), None)
    if not root:
        return {}, {}, ""
    predmet = out.parent.parent.name
    nivo, razred = spec.get("nivo"), spec.get("razred")
    titles = {}
    kur = root / "shared" / "kurikulum" / str(nivo) / str(razred) / f"{predmet}.yaml"
    if kur.exists():
        k = yaml.safe_load(kur.read_text()) or {}
        for pg in k.get("poglavlja") or []:
            for l in pg.get("lekcije") or []:
                titles[int(l["broj"])] = l["naslov"]
    concept_lessons = {}
    graf = root / "tools" / predmet / "_source" / f"pojmovi-{razred}"
    for slug in (spec.get("pojmovi") or {}):
        p = graf / f"{slug}.md"
        if p.exists():
            m = re.match(r"---\n(.*?)\n---", p.read_text(), re.S)
            fm = yaml.safe_load(m.group(1)) if m else {}
            nums = sorted({int(str(x).split("-")[0]) for x in (fm.get("lekcije") or []) if str(x)[:2].isdigit()})
            concept_lessons[slug] = nums
    catalog = os.path.relpath(root / "index.html", out.parent).replace(os.sep, "/")
    return concept_lessons, titles, f"{catalog}#/{nivo}/{razred}/{predmet}/"


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

_HTML_TPL = r"""<!DOCTYPE html>
<html lang="__LOCALE__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
__SHELL_CSS__
 :root{--ink:#2b2b2b;--muted:#6b6456;--edge:#b1271f;--accent:#1f7a3a;--border:#e6e0d2;--soft:#fefcf7;--warn:#c98a2c;
       --sea:#cfe6f2;--land:#efeae0;--land-se:#f3ecd8;--bord:#8a8170}
 *{box-sizing:border-box}
 button{font:inherit;padding:7px 14px;border:1px solid var(--edge);background:#fff;color:var(--edge);border-radius:8px;cursor:pointer}
 button:hover{background:var(--edge);color:#fff}
 button.ok{border-color:var(--accent);color:var(--accent)} button.ok:hover{background:var(--accent);color:#fff}
 button:disabled{opacity:.45;cursor:default;background:#fff;color:inherit}
 .opt:disabled,.tn button:disabled,.mcell:disabled,.blank:disabled{opacity:1;cursor:default}
 .opt:disabled:not(.right):not(.wrong){opacity:.6}
 .bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:14px}
 .bar-menu-btn{padding:5px 12px;font-size:16px;line-height:1;border-color:var(--muted);color:#3a3528}
 .bar-menu-btn:hover{background:#f3ecd8;color:#3a3528}
 .bar-menu button{width:100%;text-align:left}
 .mode-switch{display:inline-flex}
 .ms-btn{padding:5px 12px;border-color:#6b6456;color:#3a3528;min-width:5.5em}
 .ms-btn:first-child{border-radius:8px 0 0 8px} .ms-btn:last-child{border-radius:0 8px 8px 0;border-left:none}
 .ms-btn:hover{background:#f3ecd8;color:#3a3528}
 .ms-btn.active{background:#3a3528;color:#fff;border-color:#3a3528}
 .stat{background:#f3ecd8;border:1px solid #e1d8c2;border-radius:8px;padding:4px 10px;white-space:nowrap}
 .stat b{font-size:15px;color:var(--accent)}
 .intro p{font-size:14px;color:#4a4434;line-height:1.6;margin:0 0 10px}
 .intro ul{margin:0 0 10px;padding-left:18px;font-size:13.5px;line-height:1.55}
 /* navigation: items */
 .it-row{display:flex;align-items:center;gap:8px;width:100%;border:0;border-radius:5px;background:none;color:var(--ink);font:inherit;font-size:13px;text-align:left;padding:5px 6px;cursor:pointer}
 .it-row:hover{background:#f6f1e4;color:var(--ink)}
 .it-row.sel{background:#efe7d2;font-weight:600}
 .it-row.off{opacity:.4}
 .it-row .st{flex:0 0 16px;text-align:center;color:#b9b2a0}
 .it-row.ok .st{color:var(--accent)} .it-row.rev .st,.it-row.fail .st{color:var(--edge)} .it-row.part .st{color:var(--warn)}
 .it-row .lbl{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .it-row .pt{flex:0 0 auto;font-size:11px;color:var(--muted);font-weight:400;font-variant-numeric:tabular-nums}
 /* main: item */
 .item{padding:20px 24px 40px;max-width:1100px}
 .ihead{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin-bottom:8px}
 .vchip{font-size:11px;text-transform:uppercase;letter-spacing:.05em;border:1px solid var(--border);border-radius:9px;padding:1px 8px;background:#fff}
 .item h2.q{font-size:18px;line-height:1.4;color:#3a3528;margin:0 0 14px}
 .opts{display:flex;flex-direction:column;gap:8px;max-width:640px}
 .opt{display:flex;gap:10px;align-items:flex-start;text-align:left;border:1px solid var(--border);background:#fff;color:var(--ink);border-radius:8px;padding:10px 12px;font-size:14.5px;line-height:1.4}
 .opt:hover{background:#fbf7ec;color:var(--ink)}
 .opt.picked{border-color:#3a3528;background:#f6f1e4}
 .opt.wrong{border-color:#e6b0b0;background:#fdecec;color:#8a2a22;text-decoration:line-through}
 .opt.right{border-color:#9fd5b6;background:#e8f5ec;color:#13602c;font-weight:600}
 .opt .box{flex:0 0 18px;height:18px;border:1.5px solid #6b6456;border-radius:4px;margin-top:1px}
 .opt.picked .box{background:#3a3528;box-shadow:inset 0 0 0 3px #fff}
 .opt.round .box{border-radius:50%}
 .tn{display:flex;gap:12px;margin:4px 0 14px}
 .tn button{min-width:8em;padding:10px 18px;font-size:15px}
 .tn button.right{background:var(--accent);border-color:var(--accent);color:#fff}
 .tn button.wrong{background:#fdecec;border-color:#e6b0b0;color:#8a2a22}
 .stmt{font-size:16px;line-height:1.5;border-left:3px solid #e1d8c2;padding:6px 12px;margin:0 0 14px;background:#fff}
 .sub-q{font-weight:600;color:#3a3528;margin:16px 0 8px}
 .cloze{font-size:16px;line-height:2.3;max-width:720px}
 .blank{display:inline-block;min-width:5.5em;border:0;border-bottom:2px solid #6b6456;background:#fff;text-align:center;font:inherit;font-weight:600;color:#3a3528;padding:0 6px;margin:0 3px;border-radius:4px 4px 0 0;cursor:pointer}
 input.blank{cursor:text;width:7em}
 .blank:hover{background:#fbf7ec;color:#3a3528}
 .blank.cur{border-bottom-color:var(--edge);background:#fff7f3}
 .blank.lock{border-bottom-color:var(--accent);background:#e8f5ec;color:#13602c;cursor:default}
 .blank.bad{border-bottom-color:var(--edge);background:#fdecec;color:#8a2a22}
 .blank.rev{border-bottom-color:var(--warn);background:#fdf3e2;color:#8a5a14}
 .bank{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
 .bank button{padding:5px 12px;border-color:#6b6456;color:#3a3528;border-radius:16px}
 .bank button:hover{background:#f3ecd8;color:#3a3528}
 .bank button.used{opacity:.3;pointer-events:none}
 .match{display:grid;grid-template-columns:1fr 1fr;gap:10px 28px;max-width:720px}
 .match .col{display:flex;flex-direction:column;gap:8px}
 .mcell{text-align:left;border:1px solid var(--border);background:#fff;color:var(--ink);border-radius:8px;padding:9px 12px;font-size:14px}
 .mcell:hover{background:#fbf7ec;color:var(--ink)}
 .mcell.cur{border-color:#3a3528;box-shadow:0 0 0 2px rgba(58,53,40,.15)}
 .mcell.done{border-color:#9fd5b6;background:#e8f5ec;color:#13602c;cursor:default}
 .mcell.rev{border-color:#ecc98a;background:#fdf3e2;color:#8a5a14;cursor:default}
 .mcell.bad{animation:shake .3s;border-color:#e6b0b0;background:#fdecec}
 .mcell .n{display:inline-block;min-width:1.4em;font-weight:700;margin-right:6px;color:var(--muted)}
 @keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)}}
 .iactions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:18px}
 .fb{font-size:14px;font-weight:600;min-height:1.4em}
 .fb.ok{color:var(--accent)} .fb.bad{color:var(--edge)} .fb.info{color:var(--muted);font-weight:400}
 .expl{margin-top:14px;padding:10px 14px;border-radius:8px;background:#e8f5ec;border:1px solid #bfe0c8;color:#13602c;font-size:14px;line-height:1.5;max-width:720px}
 .expl.rev{background:#fdf3e2;border-color:#f0d878;color:#6b4a10}
 .help-inline{display:none}
 /* map */
 .mapwrap{position:relative;margin-top:6px;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--sea);aspect-ratio:__MAP_W__/__MAP_H__;max-height:70vh;touch-action:none}
 .mapwrap svg{width:100%;height:100%;display:block;cursor:crosshair}
 .mapwrap svg.drag{cursor:grabbing}
 .mapwrap .c{fill:var(--land);stroke:var(--bord);stroke-width:.6;vector-effect:non-scaling-stroke}
 .mapwrap .c.se{fill:var(--land-se)}
 .mapwrap .c.se:hover{fill:#e9dcb8}
 .mapwrap .c.hit{fill:#bfe0c8} .mapwrap .c.miss{fill:#f3c9c4} .mapwrap .c.revc{fill:#f6dca6}
 .mapwrap .mk{pointer-events:none}
 .mapwrap .mk circle{stroke:#fff;vector-effect:non-scaling-stroke}
 .mapwrap .mk text{font-size:13px;font-weight:700;paint-order:stroke;stroke:#fff;stroke-width:3px;vector-effect:non-scaling-stroke}
 .zbar{position:absolute;right:10px;top:10px;display:flex;flex-direction:column;gap:6px}
 .zbar button{width:36px;height:36px;padding:0;font-size:18px;font-weight:700;background:#fff;border-color:#6b6456;color:#3a3528;box-shadow:0 1px 3px rgba(0,0,0,.2)}
 .zbar button:hover{background:#f3ecd8;color:#3a3528}
 .zhint{position:absolute;left:10px;bottom:8px;font-size:11.5px;color:var(--muted);background:rgba(255,255,255,.85);border-radius:6px;padding:3px 8px;pointer-events:none}
 .clues{list-style:none;margin:0 0 6px;padding:0;max-width:720px}
 .clues li{padding:7px 10px;margin:0 0 6px;border-left:3px solid #e1d8c2;background:#fff;font-size:14.5px;line-height:1.45}
 .clues li:last-child{border-left-color:var(--edge)}
 .clues .k{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-right:6px}
 /* drawer content */
 .hl h3{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:14px 0 6px}
 .hl ol{margin:0;padding-left:20px} .hl li{margin:0 0 10px;line-height:1.5}
 .hl li.new{animation:flash 1.2s}
 @keyframes flash{0%{background:#fff3c4}100%{background:transparent}}
 .hl .placeholder{color:#9b9387;font-style:italic}
 .hl .chips{display:flex;flex-wrap:wrap;gap:6px}
 .hl .pchip{font-size:12px;border:1px solid var(--border);border-radius:10px;padding:1px 9px;background:#fefcf7}
 .hl a{color:var(--edge);text-decoration:none}
 .hl ul{margin:0;padding-left:18px} .hl ul li{margin:3px 0}
 /* summary */
 .sum{padding:22px 26px 40px;max-width:860px}
 .sum h1{font-size:22px;margin:0 0 6px;color:#3a3528}
 .sum .big{font-size:30px;font-weight:700;color:var(--accent)}
 .sum .tbl{margin:14px 0}
 #msg{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:var(--edge);color:#fff;padding:9px 18px;border-radius:24px;font-size:14px;font-weight:600;opacity:0;transition:opacity .25s;pointer-events:none;z-index:99}
 #msg.show{opacity:1}
 @media (max-width:760px){
   .brand{display:none}
   .bar{flex-wrap:nowrap;gap:6px} .stat{padding:3px 7px;font-size:12px} .stat b{font-size:13px}
   .ms-btn{min-width:auto;padding:4px 8px;font-size:13px} .bar-menu-btn{padding:4px 9px}
   .item{padding:14px 14px 40px} .item h2.q{font-size:16.5px}
   .match{grid-template-columns:1fr 1fr;gap:8px 10px} .mcell{font-size:13px;padding:8px}
   .help-inline{display:block;margin-top:14px}
   .help-inline:empty{display:none}
   .help-inline .hl{border:1px solid #f0d878;background:#fffbe6;border-radius:8px;padding:2px 12px 4px}
   .mapwrap{aspect-ratio:auto;height:52vh}
 }
</style>
</head>
<body class="app-body">
<header class="app-bar">
 <button class="app-menu" id="app-menu" aria-label="Zadaci" aria-expanded="false">&#9776;</button>
 __BRAND_CRUMBS__
 <div class="bar bar-right">
  <span class="mode-switch"><button type="button" class="ms-btn" data-mode="ucenje">Učenje</button><button type="button" class="ms-btn" data-mode="test">Test</button></span>
  <span class="stat" id="score">Bodovi: <b id="scoreN">0</b> / <span id="scoreMax">0</span></span>
  <span class="bar-menu-wrap">
   <button type="button" class="bar-menu-btn" data-menu="barMenu" aria-label="Podešavanja" aria-expanded="false">&#8943;</button>
   <div class="bar-menu" id="barMenu">
    <button type="button" id="mIntro">Kako se igra</button>
    <button type="button" id="mRepeat">Ponovi otkrivene</button>
    <button type="button" id="mReset">Počni ispočetka</button>
   </div>
  </span>
 </div>
</header>
<div class="app-grid">
 <nav class="app-nav" id="app-nav" aria-label="Zadaci">
  <input class="app-filter" id="app-filter" type="search" placeholder="Nađi zadatak" aria-label="Nađi zadatak">
  <div id="navList"></div>
 </nav>
 <main class="app-main" id="main"></main>
</div>
<aside class="app-drawer" id="drawer" aria-hidden="true">
 <div class="drawer-head"><h2 id="drawerTitle">Pomoć</h2><button class="drawer-close" id="drawerClose" aria-label="Zatvori" title="Zatvori">&times;</button></div>
 <div class="drawer-body" id="drawerBody"></div>
</aside>
<template id="mapTpl"><svg viewBox="0 0 __MAP_W__ __MAP_H__" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet"><rect width="__MAP_W__" height="__MAP_H__" fill="var(--sea)"/>__MAP_PATHS__<g class="marks"></g></svg></template>
<div id="msg"></div>
<script>__SHELL_JS__</script>
<script>
const SPEC = __SPEC_JSON__;
const MAPI = __MAP_JSON__;            // {proj:{lon0,lat1,sx,sy,w,h}, drzave:{ISO:naziv}, mesta:{slug:{naziv,lat,lon,radius_km}}}
const INFO = __INFO_JSON__;           // {pojmovi:{slug:naziv}, lekcijePojma:{slug:[broj]}, naslovi:{broj:naslov}, katalog, lekcije:[broj]}
const STATE_KEY = 'classroom:' + window.location.pathname;
const STATE_VERSION = 1;
const VRSTA_LBL = {izbor:'Izbor', tacno_netacno:'Tačno / netačno', dopuni:'Dopuni', povezi:'Poveži', zakljuci:'Zaključi', karta_klik:'Na karti', gde_sam:'Gde sam?'};
const UPUTSTVO = {
  izbor: 'Izaberi tačan odgovor. Ako ih je više, označi sve tačne pa klikni Proveri.',
  zakljuci: 'Razmisli i izaberi najbolje objašnjenje. Posle greške pomoć vodi korak po korak kroz rasuđivanje.',
  tacno_netacno: 'Odluči da li je tvrdnja tačna. Ako je netačna, izaberi kako glasi tačno.',
  dopuni: 'Popuni praznine — klikni prazninu pa reč ispod (ili upiši), pa Proveri.',
  povezi: 'Klikni pojam levo, pa njegov par desno.',
  karta_klik: 'Klikni na kartu. Zumiraj točkićem ili dugmadima +/−, prevuci za pomeranje.',
  gde_sam: 'Pročitaj trag i klikni mesto na karti. Pogrešan klik ili „Još jedan trag” otkriva novi trag i nosi manje bodova.'
};
const HELP_LBL = ['Usmeri', 'Suzi', 'Iz lekcije', 'Još'];
const ITEMS = SPEC.delovi.flatMap((d, di) => d.zadaci.map(z => Object.assign({ deo: di }, z)));
const BY_ID = Object.fromEntries(ITEMS.map(z => [z.id, z]));

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
const norm = s => String(s || '').toLowerCase().replace(/đ/g, 'dj').normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/[„”“"'%]/g, '').replace(/,/g, '.').replace(/\s+/g, ' ').trim();
function seeded(str) { let h = 2166136261; for (const c of str) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)) >>> 0) / 4294967296; }
function shuffled(arr, key) { const r = seeded(key), a = arr.map((x, i) => [x, i]); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
let msgT = null;
function toast(t, ok) { const m = document.getElementById('msg'); m.textContent = t; m.style.background = ok ? '#1f7a3a' : '#b1271f'; m.classList.add('show'); clearTimeout(msgT); msgT = setTimeout(() => m.classList.remove('show'), 1300); }

// ---------- state ----------
function blankState() { return { v: STATE_VERSION, mode: 'ucenje', cur: ITEMS[0].id, b: { ucenje: {}, test: {}, ispravka: {} } }; }
function loadState() { try { const o = JSON.parse(localStorage.getItem(STATE_KEY)); return o && o.v === STATE_VERSION ? o : null; } catch (e) { return null; } }
let state = loadState() || blankState();
function save() { try { localStorage.setItem(STATE_KEY, JSON.stringify(state)); } catch (e) {} }
const helpOn = () => state.mode !== 'test';
function st(id) { const b = state.b[state.mode]; return b[id] || (b[id] = { miss: 0, status: 'open', pts: null, ui: {} }); }
function listIds() {   // the items of the current mode
  if (state.mode !== 'ispravka') return ITEMS.map(z => z.id);
  return ITEMS.map(z => z.id).filter(id => { const t = state.b.test[id]; return t && t.status !== 'open' && t.pts < 3; });
}
const isDone = s => s.status !== 'open';
function steps(z) { return z.vrsta === 'gde_sam' ? z.tragovi.length - 1 : (z.pomoc || []).length; }   // help steps before the reveal
const ptsFor = miss => miss === 0 ? 3 : miss === 1 ? 2 : 1;

// ---------- score + navigation ----------
function refreshScore() {
  const ids = listIds();
  let n = 0;
  for (const id of ids) { const s = state.b[state.mode][id]; if (s && s.pts) n += s.pts; }
  document.getElementById('scoreN').textContent = n;
  document.getElementById('scoreMax').textContent = ids.length * 3;
  document.querySelectorAll('.ms-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === (state.mode === 'ispravka' ? 'test' : state.mode)));
  const rep = ITEMS.filter(z => (state.b.ucenje[z.id] || {}).status === 'revealed').length;
  const mr = document.getElementById('mRepeat');
  mr.textContent = 'Ponovi otkrivene (' + rep + ')'; mr.disabled = state.mode !== 'ucenje' || !rep;
}
const NUM = Object.fromEntries(ITEMS.map((z, i) => [z.id, i + 1]));
function rowLabel(z) {
  if (z.vrsta === 'gde_sam') return 'Gde sam? ' + z.tragovi[0];
  return z.pitanje && !/^Dopuni rečenicu/.test(z.pitanje) ? z.pitanje : (z.tvrdnja || (z.tekst || '').replace(/\{\{(.+?)\}\}/g, '…'));
}
function renderNav() {
  const ids = new Set(listIds());
  let h = '';
  SPEC.delovi.forEach((d, di) => {
    const zs = d.zadaci.filter(z => ids.has(z.id));
    if (!zs.length) return;
    const done = zs.filter(z => isDone(st(z.id))).length;
    h += '<div data-filter-group><div class="sec"><span>' + esc(d.naslov) + '</span><span class="cnt">' + done + ' / ' + zs.length + '</span></div>';
    for (const z of zs) {
      const s = st(z.id), n = NUM[z.id];
      const cls = s.status === 'ok' ? (s.pts === 3 ? 'ok' : 'part') : s.status === 'revealed' ? 'rev' : s.status === 'failed' ? 'fail' : '';
      const icon = s.status === 'ok' ? '✓' : s.status === 'open' ? (s.miss ? '◐' : '○') : '✗';
      h += '<button type="button" class="it-row ' + cls + (z.id === state.cur ? ' sel' : '') + '" data-id="' + z.id + '" data-filter="' + esc(rowLabel(z) + ' ' + VRSTA_LBL[z.vrsta]) + '">' +
           '<span class="st">' + icon + '</span><span class="lbl">' + n + '. ' + esc(rowLabel(z)) + '</span><span class="pt">' + (s.pts != null ? s.pts + ' b' : '') + '</span></button>';
    }
    h += '</div>';
  });
  const allDone = listIds().every(id => isDone(st(id)));
  h += '<div class="sec"><span>Kraj</span></div><button type="button" class="it-row' + (state.cur === '_sum' ? ' sel' : '') + (allDone ? ' ok' : '') + '" data-id="_sum"><span class="st">' + (allDone ? '★' : '·') + '</span><span class="lbl">Rezultat</span></button>';
  document.getElementById('navList').innerHTML = h;
  if (document.getElementById('app-filter').value) HubShell.applyFilter();
}
document.getElementById('navList').addEventListener('click', e => { const r = e.target.closest('.it-row'); if (r) go(r.dataset.id); });

// ---------- drawer: help ladder → "Saznaj više" ----------
const drawer = document.getElementById('drawer');
const drawerBody = document.getElementById('drawerBody');
const mobile = () => HubShell.navOverlay();
function openDrawer() { drawer.classList.add('open'); drawer.setAttribute('aria-hidden', 'false'); }
function closeDrawer() { drawer.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true'); }
document.getElementById('drawerClose').addEventListener('click', () => { closeDrawer(); if (drawer.dataset.intro) { delete drawer.dataset.intro; try { localStorage.setItem(STATE_KEY + ':intro', '1'); } catch (e) {} renderDrawer(); } });
function moreHTML(z) {
  const slugs = z.pojmovi || [];
  let h = '';
  if (slugs.length) h += '<h3>Pojmovi</h3><div class="chips">' + slugs.map(s => '<span class="pchip">' + esc(INFO.pojmovi[s] || s) + '</span>').join('') + '</div>';
  const other = {};
  for (const s of slugs) for (const b of INFO.lekcijePojma[s] || []) if (!INFO.lekcije.includes(b)) (other[b] = other[b] || []).push(INFO.pojmovi[s] || s);
  const bs = Object.keys(other).map(Number).sort((a, b) => a - b);
  if (bs.length) h += '<h3>Pojavljuje se i u lekcijama</h3><ul>' + bs.map(b => '<li><a href="' + INFO.katalog + b + '">' + b + '. ' + esc(INFO.naslovi[b] || '') + '</a> — ' + esc(other[b].join(', ')) + '</li>').join('') + '</ul>';
  return h;
}
function helpHTML(z, s, fresh) {
  if (isDone(s)) {
    const rev = s.status !== 'ok';
    return '<div class="hl"><h3>' + (rev ? (s.status === 'failed' ? 'Netačno' : 'Odgovor') : 'Tačno · ' + s.pts + ' b') + '</h3>' +
      (s.status === 'failed' ? '<p class="placeholder">U testu se odgovor ne otkriva — vežbaćeš ga u Ispravci.</p>' : '<p>' + fmt(z.objasnjenje || '') + '</p>') + moreHTML(z) + '</div>';
  }
  if (!helpOn()) return '<div class="hl"><p class="placeholder">Test: bez pomoći. ' + esc(UPUTSTVO[z.vrsta]) + '</p></div>';
  if (z.vrsta === 'gde_sam') return '<div class="hl"><h3>Tragovi</h3><p class="placeholder">Tragovi se otkrivaju u zadatku — svaki novi nosi manje bodova (' + ptsFor(s.miss) + ' b za tačan klik sada).</p></div>';
  if (!s.miss) return '<div class="hl"><h3>Kako se radi</h3><p class="placeholder">' + esc(UPUTSTVO[z.vrsta]) + '</p><p class="placeholder">Posle svake greške ovde stiže sledeći stepenik pomoći.</p></div>';
  const shown = (z.pomoc || []).slice(0, s.miss);
  return '<div class="hl"><h3>Pomoć (' + shown.length + ' / ' + (z.pomoc || []).length + ')</h3><ol>' +
    shown.map((p, i) => '<li' + (fresh && i === shown.length - 1 ? ' class="new"' : '') + '>' +   // a step that names itself ("Korak 1:", "Iz lekcije:") keeps its own label
      (/^[^:]{1,20}:/.test(p) ? fmt(p).replace(/^([^:]{1,20}):/, '<b>$1:</b>') : '<b>' + HELP_LBL[Math.min(i, 3)] + ':</b> ' + fmt(p)) + '</li>').join('') + '</ol>' +
    '<p class="placeholder">Sada nosi ' + ptsFor(s.miss) + ' b. Još jedna greška posle poslednje pomoći otkriva odgovor.</p></div>';
}
function renderDrawer(fresh) {
  if (drawer.dataset.intro) return;
  const z = BY_ID[state.cur];
  const inl = document.getElementById('helpInline');
  if (!z) { document.getElementById('drawerTitle').textContent = 'Rezultat'; drawerBody.innerHTML = ''; return; }
  const s = st(z.id), h = helpHTML(z, s, fresh);
  document.getElementById('drawerTitle').textContent = isDone(s) ? 'Saznaj više' : 'Pomoć';
  drawerBody.innerHTML = h;
  if (inl) inl.innerHTML = (s.miss && !isDone(s) && helpOn() && z.vrsta !== 'gde_sam') ? h : '';
}
function showIntro() {
  drawer.dataset.intro = '1';
  document.getElementById('drawerTitle').textContent = 'Kako se igra';
  drawerBody.innerHTML = '<div class="intro"><p>' + esc(SPEC.description || '') + '</p><ul>' +
    '<li><b>Učenje</b> — posle svake greške u ovoj fioci stiže sledeći stepenik pomoći: <i>usmeri</i> → <i>suzi</i> → <i>iz lekcije</i>. Greška posle poslednjeg stepenika otkriva odgovor.</li>' +
    '<li><b>Bodovi</b> — tačno bez greške 3, uz jednu pomoć 2, uz više pomoći 1, otkriveno 0.</li>' +
    '<li><b>Test</b> — bez pomoći. Na kraju <b>Ispravka</b>: zadaci koji nisu rešeni iz prve, ponovo, sa pomoći.</li>' +
    '<li>Levo su svi zadaci po delovima lekcije; možeš ih rešavati bilo kojim redom.</li></ul>' +
    '<button type="button" class="ok" id="introOk">Razumem</button></div>';
  openDrawer();
  document.getElementById('introOk').addEventListener('click', () => document.getElementById('drawerClose').click());
}
document.getElementById('mIntro').addEventListener('click', showIntro);

// ---------- outcome ----------
function fail(z, text) {
  const s = st(z.id);
  s.miss++;
  if (s.miss > steps(z)) { s.status = helpOn() ? 'revealed' : 'failed'; s.pts = 0; toast(helpOn() ? 'Evo odgovora' : 'Netačno', false); }
  else toast(text || 'Netačno — pokušaj ponovo', false);
  save(); renderItem(true); renderNav(); refreshScore();
  if (helpOn() && !mobile()) openDrawer();
}
function succeed(z) {
  const s = st(z.id);
  s.status = 'ok'; s.pts = ptsFor(s.miss);
  toast('Tačno! +' + s.pts, true);
  save(); renderItem(false); renderNav(); refreshScore();
  if (!mobile()) openDrawer();
}

// ---------- item renderers ----------
const main = document.getElementById('main');
function frame(z, s, inner) {
  const n = NUM[z.id];
  const pts = isDone(s) ? (s.status === 'ok' ? '✓ ' + s.pts + ' b' : s.status === 'failed' ? '✗ 0 b' : 'otkriveno · 0 b') : (s.miss ? 'sada ' + ptsFor(s.miss) + ' b' : 'do 3 b');
  return '<div class="item"><div class="ihead"><span class="vchip">' + VRSTA_LBL[z.vrsta] + '</span><span>' + esc(SPEC.delovi[z.deo].naslov) + ' · zadatak ' + n + ' / ' + ITEMS.length + '</span><span>' + pts + '</span></div>' +
    inner + '<div class="help-inline" id="helpInline"></div><div class="iactions" id="actions"></div>' +
    (isDone(s) ? '<div class="expl' + (s.status === 'ok' ? '' : ' rev') + '">' + (s.status === 'failed' ? 'Netačno. Odgovor ćeš videti u Ispravci.' : fmt(z.objasnjenje || '')) + '</div>' : '') + '</div>';
}
function actions(btns) {
  const a = document.getElementById('actions');
  a.innerHTML = btns.map(b => '<button type="button" id="' + b[0] + '"' + (b[2] ? ' class="' + b[2] + '"' : '') + '>' + b[1] + '</button>').join('');
}
function nextButton(z) {
  const s = st(z.id);
  if (!isDone(s)) return;
  const a = document.getElementById('actions');
  a.insertAdjacentHTML('beforeend', '<button type="button" class="ok" id="btnNext">Sledeći ›</button>' + (mobile() ? '<button type="button" id="btnMore">Saznaj više</button>' : ''));
  document.getElementById('btnNext').addEventListener('click', goNext);
  const m = document.getElementById('btnMore'); if (m) m.addEventListener('click', openDrawer);
}

function renderChoice(z, s) {   // izbor + zakljuci (+ the correction step of tacno_netacno)
  const opts = shuffled(z.odgovori, z.id);
  const multi = z.odgovori.filter(o => o.tacan).length > 1;
  const ui = s.ui; ui.wrong = ui.wrong || []; ui.pick = ui.pick || [];
  const done = isDone(s), showRight = s.status === 'ok' || s.status === 'revealed';
  main.innerHTML = frame(z, s, '<h2 class="q">' + fmt(z.pitanje) + '</h2><div class="opts">' + opts.map(([o, i]) =>
    '<button type="button" class="opt' + (multi ? '' : ' round') + (ui.wrong.includes(i) ? ' wrong' : '') + (showRight && o.tacan ? ' right' : '') +
    (!done && ui.pick.includes(i) ? ' picked' : '') + '" data-i="' + i + '"' + (done || ui.wrong.includes(i) ? ' disabled' : '') + '><span class="box"></span><span>' + fmt(o.tekst) + '</span></button>').join('') + '</div>');
  if (!done && multi) actions([['btnCheck', 'Proveri', 'ok']]);
  main.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => {
    const i = +b.dataset.i;
    if (!multi) { if (z.odgovori[i].tacan) succeed(z); else { ui.wrong.push(i); fail(z); } return; }
    ui.pick = ui.pick.includes(i) ? ui.pick.filter(x => x !== i) : ui.pick.concat(i);
    b.classList.toggle('picked'); save();
  }));
  const chk = document.getElementById('btnCheck');
  if (chk) chk.addEventListener('click', () => {
    if (!ui.pick.length) { toast('Označi bar jedan odgovor', false); return; }
    const right = z.odgovori.map((o, i) => o.tacan ? i : -1).filter(i => i >= 0);
    const wrongPicked = ui.pick.filter(i => !z.odgovori[i].tacan);
    if (!wrongPicked.length && right.every(i => ui.pick.includes(i))) { succeed(z); return; }
    ui.wrong = ui.wrong.concat(wrongPicked); ui.pick = ui.pick.filter(i => z.odgovori[i].tacan);
    fail(z, wrongPicked.length ? 'Neki od označenih nisu tačni' : 'Nedostaje još tačnih odgovora');
  });
  nextButton(z);
}

function renderTN(z, s) {
  const ui = s.ui, done = isDone(s), showAns = s.status === 'ok' || s.status === 'revealed';
  let inner = '<h2 class="q">Tačno ili netačno?</h2><p class="stmt">' + fmt(z.tvrdnja) + '</p><div class="tn">' +
    [[true, 'Tačno'], [false, 'Netačno']].map(([v, t]) => '<button type="button" data-v="' + v + '" class="' +
      ((showAns || ui.phase === 'fix') && v === z.tacno ? 'right' : (ui.tnWrong === v ? 'wrong' : '')) + '"' + (done || ui.phase === 'fix' || ui.tnWrong === v ? ' disabled' : '') + '>' + t + '</button>').join('') + '</div>';
  if (!z.tacno && (ui.phase === 'fix' || showAns)) {
    ui.wrong = ui.wrong || [];
    inner += '<p class="sub-q">Kako glasi tačno?</p><div class="opts">' + shuffled(z.ispravke, z.id + 'fix').map(([o, i]) =>
      '<button type="button" class="opt round fix' + (ui.wrong.includes(i) ? ' wrong' : '') + (showAns && o.tacan ? ' right' : '') + '" data-i="' + i + '"' +
      (done || ui.wrong.includes(i) ? ' disabled' : '') + '><span class="box"></span><span>' + fmt(o.tekst) + '</span></button>').join('') + '</div>';
  }
  main.innerHTML = frame(z, s, inner);
  main.querySelectorAll('.tn button').forEach(b => b.addEventListener('click', () => {
    const v = b.dataset.v === 'true';
    if (v !== z.tacno) {   // a binary guess: a wrong one on a true statement leaves nothing to find → revealed;
      ui.tnWrong = v;       // on a false one the pupil still has to find the correction
      if (z.tacno) st(z.id).miss = steps(z); else ui.phase = 'fix';
      fail(z); return;
    }
    if (z.tacno) { succeed(z); return; }
    ui.phase = 'fix'; save(); renderItem(false); toast('Tačno — sad je ispravi', true);
  }));
  main.querySelectorAll('.opt.fix').forEach(b => b.addEventListener('click', () => {
    const i = +b.dataset.i;
    if (z.ispravke[i].tacan) succeed(z); else { ui.wrong.push(i); fail(z); }
  }));
  nextButton(z);
}

function parseCloze(t) {   // → [text, {answers}, text, …]
  const parts = []; let last = 0;
  t.replace(/\{\{(.+?)\}\}/g, (m, inner, at) => { parts.push(t.slice(last, at)); parts.push({ answers: inner.split('|') }); last = at + m.length; return m; });
  parts.push(t.slice(last));
  return parts;
}
function renderCloze(z, s) {
  const ui = s.ui; ui.val = ui.val || {}; ui.lock = ui.lock || {};
  const parts = parseCloze(z.tekst), blanks = parts.filter(p => typeof p === 'object');
  const done = isDone(s), bank = z.ponudjene && z.ponudjene.length;
  if (ui.cur == null || ui.lock[ui.cur]) ui.cur = blanks.findIndex((_, i) => !ui.lock[i]);
  let bi = -1;
  const html = parts.map(p => {
    if (typeof p === 'string') return fmt(p);
    bi++;
    const val = done && !ui.lock[bi] ? p.answers[0] : (ui.val[bi] || '');
    const cls = 'blank' + (ui.lock[bi] ? ' lock' : '') + (done && !ui.lock[bi] ? ' rev' : '') + (!done && ui.bad && ui.bad.includes(bi) ? ' bad' : '') + (!done && !bank && false ? '' : '') + (!done && bi === ui.cur && bank ? ' cur' : '');
    return bank || done || ui.lock[bi] ? '<button type="button" class="' + cls + '" data-b="' + bi + '"' + (done || ui.lock[bi] ? ' disabled' : '') + '>' + (esc(val) || '&nbsp;') + '</button>'
      : '<input class="' + cls + '" data-b="' + bi + '" value="' + esc(val) + '" autocomplete="off" spellcheck="false">';
  }).join('');
  const used = Object.values(ui.val);
  main.innerHTML = frame(z, s, '<h2 class="q">' + fmt(z.pitanje || 'Dopuni rečenicu.') + '</h2><div class="cloze">' + html + '</div>' +
    (bank && !done ? '<div class="bank">' + z.ponudjene.map(w => '<button type="button"' + (used.includes(w) ? ' class="used"' : '') + ' data-w="' + esc(w) + '">' + esc(w) + '</button>').join('') + '</div>' : ''));
  if (!done) actions([['btnCheck', 'Proveri', 'ok']]);
  main.querySelectorAll('button.blank').forEach(b => b.addEventListener('click', () => { const i = +b.dataset.b; if (ui.val[i]) delete ui.val[i]; ui.cur = i; ui.bad = []; save(); renderItem(false); }));
  main.querySelectorAll('input.blank').forEach(inp => {
    inp.addEventListener('input', () => { ui.val[+inp.dataset.b] = inp.value; save(); });
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('btnCheck').click(); });
  });
  main.querySelectorAll('.bank button').forEach(b => b.addEventListener('click', () => {
    let i = ui.cur; if (i == null || i < 0 || ui.lock[i] || ui.val[i]) i = blanks.findIndex((_, k) => !ui.lock[k] && !ui.val[k]);
    if (i < 0) return;
    ui.val[i] = b.dataset.w; ui.bad = [];
    ui.cur = blanks.findIndex((_, k) => !ui.lock[k] && !ui.val[k]);
    save(); renderItem(false);
  }));
  const chk = document.getElementById('btnCheck');
  if (chk) chk.addEventListener('click', () => {
    const open = blanks.map((_, i) => i).filter(i => !ui.lock[i]);
    if (open.some(i => !norm(ui.val[i]))) { toast('Popuni sve praznine', false); return; }
    ui.bad = [];
    for (const i of open) { if (blanks[i].answers.map(norm).includes(norm(ui.val[i]))) ui.lock[i] = true; else { ui.bad.push(i); delete ui.val[i]; } }
    if (!ui.bad.length) succeed(z); else fail(z, ui.bad.length === 1 ? 'Jedna praznina nije tačna' : 'Neke praznine nisu tačne');
  });
  nextButton(z);
}

function renderMatch(z, s) {
  const ui = s.ui; ui.done = ui.done || [];
  const done = isDone(s), right = shuffled(z.parovi.map(p => p[1]), z.id);
  const num = i => ui.done.indexOf(i) + 1;
  main.innerHTML = frame(z, s, '<h2 class="q">' + fmt(z.pitanje) + '</h2><div class="match"><div class="col">' +
    z.parovi.map((p, i) => { const m = ui.done.includes(i), rv = done && !m;
      return '<button type="button" class="mcell L' + (m ? ' done' : rv ? ' rev' : '') + (ui.left === i && !done ? ' cur' : '') + '" data-i="' + i + '"' + (m || done ? ' disabled' : '') + '>' +
        (m || rv ? '<span class="n">' + (m ? num(i) : '→') + '</span>' : '') + fmt(p[0]) + '</button>'; }).join('') +
    '</div><div class="col">' + right.map(([t, i]) => { const m = ui.done.includes(i), rv = done && !m;
      return '<button type="button" class="mcell R' + (m ? ' done' : rv ? ' rev' : '') + '" data-i="' + i + '"' + (m || done ? ' disabled' : '') + '>' +
        (m ? '<span class="n">' + num(i) + '</span>' : rv ? '<span class="n">←</span>' : '') + fmt(t) + (rv ? ' <small>(' + esc(z.parovi[i][0]) + ')</small>' : '') + '</button>'; }).join('') + '</div></div>');
  main.querySelectorAll('.mcell.L').forEach(b => b.addEventListener('click', () => { ui.left = +b.dataset.i; save(); renderItem(false); }));
  main.querySelectorAll('.mcell.R').forEach(b => b.addEventListener('click', () => {
    if (ui.left == null) { toast('Prvo klikni pojam levo', false); return; }
    const i = +b.dataset.i;
    if (i === ui.left) { ui.done.push(i); ui.left = null; if (ui.done.length === z.parovi.length) succeed(z); else { save(); renderItem(false); } }
    else { b.classList.add('bad'); ui.left = null; setTimeout(() => fail(z, 'Nisu par'), 280); }
  }));
  nextButton(z);
}

// ---------- map (H: karta_klik, I: gde_sam) ----------
const P = MAPI.proj;
const toLonLat = (x, y) => [P.lon0 + x / P.sx, P.lat1 - y / P.sy];
const toXY = (lon, lat) => [(lon - P.lon0) * P.sx, (P.lat1 - lat) * P.sy];
function km(a, b) { const r = Math.PI / 180, dLa = (b[1] - a[1]) * r, dLo = (b[0] - a[0]) * r;
  const h = Math.sin(dLa / 2) ** 2 + Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLo / 2) ** 2; return 12742 * Math.asin(Math.sqrt(h)); }
function targetLonLat(c) {
  if (c.mesto) { const m = MAPI.mesta[c.mesto]; return [m.lon, m.lat]; }
  return null;
}
function mountMap(z, s, onClick) {
  const wrap = document.getElementById('mapwrap');
  wrap.innerHTML = document.getElementById('mapTpl').innerHTML + '<div class="zbar"><button type="button" data-z="1.5">+</button><button type="button" data-z="0.667">−</button><button type="button" data-z="0">⟳</button></div><div class="zhint">Točkić / +− za zum · prevuci za pomeranje</div>';
  const svg = wrap.querySelector('svg'), marks = svg.querySelector('.marks');
  let vb = s.ui.vb || [0, 0, P.w, P.h];
  const setVB = () => { svg.setAttribute('viewBox', vb.join(' ')); s.ui.vb = vb; };
  setVB();
  function zoom(f, cx, cy) {
    if (!f) { vb = [0, 0, P.w, P.h]; setVB(); return; }
    const nw = Math.min(P.w, Math.max(P.w / 14, vb[2] / f)), nh = nw * P.h / P.w;
    cx = cx == null ? vb[0] + vb[2] / 2 : cx; cy = cy == null ? vb[1] + vb[3] / 2 : cy;
    const rx = (cx - vb[0]) / vb[2], ry = (cy - vb[1]) / vb[3];
    vb = [cx - rx * nw, cy - ry * nh, nw, nh]; clamp(); setVB();
  }
  function clamp() { vb[0] = Math.min(Math.max(vb[0], 0), P.w - vb[2]); vb[1] = Math.min(Math.max(vb[1], 0), P.h - vb[3]); }
  const svgPt = e => { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); };
  wrap.querySelectorAll('.zbar button').forEach(b => b.addEventListener('click', () => zoom(+b.dataset.z)));
  svg.addEventListener('wheel', e => { e.preventDefault(); const p = svgPt(e); zoom(e.deltaY < 0 ? 1.25 : 0.8, p.x, p.y); }, { passive: false });
  let down = null;
  svg.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY, vb: vb.slice(), moved: false, target: e.target }; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener('pointermove', e => {
    if (!down) return;
    const dx = e.clientX - down.x, dy = e.clientY - down.y;
    if (!down.moved && Math.hypot(dx, dy) < 5) return;
    down.moved = true; svg.classList.add('drag');
    const k = vb[2] / svg.getBoundingClientRect().width;
    vb = [down.vb[0] - dx * k, down.vb[1] - dy * k, vb[2], vb[3]]; clamp(); setVB();
  });
  svg.addEventListener('pointerup', e => {
    const d = down; down = null; svg.classList.remove('drag');
    if (!d || d.moved) { save(); return; }
    const p = svgPt(e), hit = d.target.closest && d.target.closest('path.c');
    onClick({ x: p.x, y: p.y, iso: hit ? hit.dataset.iso : null, el: hit });
  });
  return { svg, marks,
    mark(x, y, color, label) { const r = vb[2] / 150; marks.insertAdjacentHTML('beforeend', '<g class="mk"><circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + color + '"/>' + (label ? '<text x="' + (x + r * 1.4) + '" y="' + (y + r * .5) + '" fill="' + color + '" style="font-size:' + (vb[2] / 70) + 'px">' + esc(label) + '</text>' : '') + '</g>'); },
    country(iso, cls) { svg.querySelectorAll('path[data-iso="' + iso + '"]').forEach(p => p.classList.add(cls)); } };
}
function renderMapItem(z, s) {
  const ui = s.ui; ui.clicks = ui.clicks || [];
  const done = isDone(s), gs = z.vrsta === 'gde_sam';
  const nClues = gs ? Math.min(z.tragovi.length, done ? z.tragovi.length : s.miss + 1) : 0;
  main.innerHTML = frame(z, s, '<h2 class="q">' + fmt(z.pitanje) + '</h2>' +
    (gs ? '<ul class="clues">' + z.tragovi.slice(0, nClues).map((t, i) => '<li><span class="k">Trag ' + (i + 1) + '</span>' + fmt(t) + '</li>').join('') + '</ul>' : '') +
    '<div class="mapwrap" id="mapwrap"></div>');
  const tgt = z.cilj;
  const m = mountMap(z, s, c => {
    if (isDone(st(z.id))) return;
    const ll = toLonLat(c.x, c.y);
    let ok = false, why = '';
    if (tgt.drzava) { ok = c.iso === tgt.drzava; why = c.iso ? (MAPI.drzave[c.iso] ? 'To je ' + MAPI.drzave[c.iso] : 'To nije država Južne Evrope') : 'To je more'; }
    else { const d = km(ll, targetLonLat(tgt)); ok = d <= MAPI.mesta[tgt.mesto].radius_km; why = helpOn() ? 'Promašaj — oko ' + Math.round(d / 10) * 10 + ' km od cilja' : 'Promašaj'; }
    ui.clicks.push([c.x, c.y, ok ? 1 : 0, c.iso || '']);
    if (ok) succeed(z); else fail(z, why);
  });
  for (const [x, y, ok, iso] of ui.clicks) { if (iso && tgt.drzava && !ok) m.country(iso, 'miss'); if (!tgt.drzava || !iso) m.mark(x, y, ok ? '#1f7a3a' : '#b1271f'); }
  if (done && s.status !== 'failed') {
    if (tgt.drzava) m.country(tgt.drzava, s.status === 'ok' ? 'hit' : 'revc');
    else { const [x, y] = toXY(MAPI.mesta[tgt.mesto].lon, MAPI.mesta[tgt.mesto].lat); m.mark(x, y, s.status === 'ok' ? '#1f7a3a' : '#c98a2c', MAPI.mesta[tgt.mesto].naziv); }
  }
  if (gs && !done) { actions([['btnClue', 'Još jedan trag']]); document.getElementById('btnClue').addEventListener('click', () => fail(z, 'Novi trag')); }
  nextButton(z);
}

// ---------- main view ----------
function renderItem(fresh) {
  const z = BY_ID[state.cur];
  if (!z) { renderSummary(); renderDrawer(); return; }
  const s = st(z.id);
  ({ izbor: renderChoice, zakljuci: renderChoice, tacno_netacno: renderTN, dopuni: renderCloze, povezi: renderMatch, karta_klik: renderMapItem, gde_sam: renderMapItem })[z.vrsta](z, s);
  renderDrawer(fresh);
}
function renderSummary() {
  const ids = listIds();
  let tot = 0, rows = '';
  SPEC.delovi.forEach(d => {
    const zs = d.zadaci.filter(z => ids.includes(z.id)); if (!zs.length) return;
    const p = zs.reduce((a, z) => a + (st(z.id).pts || 0), 0); tot += p;
    rows += '<tr><td>' + esc(d.naslov) + '</td><td class="num">' + zs.filter(z => isDone(st(z.id))).length + ' / ' + zs.length + '</td><td class="num">' + p + ' / ' + zs.length * 3 + '</td></tr>';
  });
  const left = ids.filter(id => !isDone(st(id))).length;
  const failed = ITEMS.filter(z => { const t = state.b.test[z.id]; return t && isDone(t) && t.pts < 3; }).length;
  const label = { ucenje: 'Učenje', test: 'Test', ispravka: 'Ispravka' }[state.mode];
  main.innerHTML = '<div class="sum"><h1>Rezultat — ' + label + '</h1><p><span class="big">' + tot + '</span> / ' + ids.length * 3 + ' bodova' +
    (left ? ' · nerešeno još ' + left : '') + '</p><table class="tbl"><thead><tr><th>Deo lekcije</th><th class="num">Urađeno</th><th class="num">Bodovi</th></tr></thead><tbody>' + rows + '</tbody></table>' +
    '<div class="iactions">' + (state.mode === 'test' && !left && failed ? '<button type="button" class="ok" id="btnFix">Ispravka (' + failed + ')</button>' : '') +
    (state.mode === 'ispravka' ? '<button type="button" id="btnBackTest">Nazad na rezultat testa</button>' : '') + '</div></div>';
  const f = document.getElementById('btnFix'); if (f) f.addEventListener('click', () => { state.mode = 'ispravka'; state.b.ispravka = {}; state.cur = listIds()[0]; save(); refresh(); });
  const bt = document.getElementById('btnBackTest'); if (bt) bt.addEventListener('click', () => { state.mode = 'test'; state.cur = '_sum'; save(); refresh(); });
}
function go(id) { state.cur = id; save(); HubShell.setNav(false); refresh(); main.scrollTop = 0; }
function goNext() {
  const ids = listIds(), i = ids.indexOf(state.cur);
  const next = ids.slice(i + 1).concat(ids.slice(0, i)).find(id => !isDone(st(id)));
  go(next || '_sum');
}
function refresh() { renderNav(); refreshScore(); renderItem(false); if (!BY_ID[state.cur] || !isDone(st(state.cur))) { if (!drawer.dataset.intro && !(st(state.cur || '').miss)) closeDrawer(); } }

// ---------- bar ----------
document.querySelectorAll('.ms-btn').forEach(b => b.addEventListener('click', () => {
  const m = b.dataset.mode;
  if (m === state.mode || (m === 'test' && state.mode === 'ispravka')) return;
  state.mode = m; state.cur = listIds().find(id => !isDone(st(id))) || '_sum'; save(); refresh();
}));
document.getElementById('mReset').addEventListener('click', () => {
  if (!confirm('Obrisati odgovore u režimu „' + ({ ucenje: 'Učenje', test: 'Test', ispravka: 'Test' })[state.mode] + '”?')) return;
  if (state.mode === 'ucenje') state.b.ucenje = {}; else { state.b.test = {}; state.b.ispravka = {}; state.mode = 'test'; }
  state.cur = ITEMS[0].id; save(); refresh();
});
document.getElementById('mRepeat').addEventListener('click', () => {
  const rev = ITEMS.filter(z => (state.b.ucenje[z.id] || {}).status === 'revealed').map(z => z.id);
  rev.forEach(id => { delete state.b.ucenje[id]; });
  if (rev.length) { state.cur = rev[0]; save(); refresh(); }
});

// ---------- init ----------
if (!BY_ID[state.cur] && state.cur !== '_sum') state.cur = ITEMS[0].id;
refresh();
let introSeen = false; try { introSeen = localStorage.getItem(STATE_KEY + ':intro') === '1'; } catch (e) {}
if (!introSeen) showIntro();
</script>
</body>
</html>"""


def render_html(spec, output_path):
    output_path = pathlib.Path(output_path).resolve()
    map_paths, proj = _render_map(spec) if spec.get("karta") else ("", {"w": 1, "h": 1})
    concept_lessons, titles, katalog = _lesson_links(spec, output_path)
    k = spec.get("karta") or {}
    clean = {"description": spec.get("description", ""),
             "delovi": [{"naslov": d["naslov"], "zadaci": d["zadaci"]} for d in spec["delovi"]]}
    info = {"pojmovi": spec.get("pojmovi") or {}, "lekcijePojma": concept_lessons, "naslovi": titles,
            "katalog": katalog, "lekcije": spec.get("lekcije") or []}
    mapj = {"proj": proj, "drzave": k.get("drzave") or {}, "mesta": k.get("mesta") or {}}
    js = lambda o: _json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    repl = {
        "__SHELL_CSS__": SHELL_CSS,
        "__SHELL_JS__": SHELL_JS,
        "__BRAND_CRUMBS__": brand_and_crumbs(output_path, spec.get("title_short") or spec["title"], spec),
        "__LOCALE__": spec.get("locale", "sr"),
        "__TITLE__": spec["title"],
        "__MAP_PATHS__": map_paths,
        "__MAP_W__": str(proj["w"]),
        "__MAP_H__": str(proj["h"]),
        "__SPEC_JSON__": js(clean),
        "__MAP_JSON__": js(mapj),
        "__INFO_JSON__": js(info),
    }
    html = _HTML_TPL
    for key, v in repl.items():
        html = html.replace(key, v)
    output_path.write_text(html, encoding="utf-8")
    return output_path
