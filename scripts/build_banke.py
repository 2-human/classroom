#!/usr/bin/env python3
"""Build the question-bank pages: one page per lesson, banka/{nivo}/{razred}/{predmet}/NN-slug/index.html.

Usage (from anywhere in the repo):
    python3 scripts/build_banke.py

Source: shared/banke/{nivo}/{razred}/{predmet}/NN-slug.yaml. A page lists the lesson's questions by
part, with filters; a question opens to its answer and links to the lesson section it comes from, its
book page and the quizzes that draw from the lesson. Anchor #{item id} opens one question.
"""
import json
import os
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))
from hub_shell import SHELL_CSS, SHELL_JS, BRAND, nivo_title, razred_title, predmet_title  # noqa: E402
from lekcija import lesson_dir  # noqa: E402
import veze  # noqa: E402

esc = veze.esc

PAGE = r"""<!DOCTYPE html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
__SHELL_CSS__
 .app-nav a{text-decoration:none}
 .app-nav .row{display:flex;gap:6px;justify-content:space-between;color:#2b2b2b;font-size:13px;padding:5px 8px;border-radius:5px;line-height:1.35}
 .app-nav .row:hover{background:#f6f1e4}
 .app-nav .row.cur{background:#efe7d2;font-weight:600}
 .bk{max-width:900px;padding:22px 28px 80px;color:#2b2b2b;line-height:1.5}
 .bk h1{font-size:24px;margin:0 0 4px;color:#3a3528}
 .bk .meta{color:#6b6456;font-size:13.5px;margin:0 0 8px}
 .bk .links{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
 .bk .links a{font-size:13px;color:#7a4b12;border:1px solid #ecd3a8;background:#fbf3e3;border-radius:12px;padding:2px 11px;text-decoration:none}
 .bk .links a.kv{color:#1f7a3a;border-color:#bfe0c8;background:#eef7f0}
 .flt{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 6px;position:sticky;top:0;background:var(--hub-bg);padding:8px 0;z-index:2}
 .flt button,.flt select,.flt input{font:inherit;font-size:13px;padding:4px 10px;border:1px solid #e6e0d2;border-radius:7px;background:#fff;color:#3a3528;cursor:pointer}
 .flt button.on{background:#3a3528;color:#fff;border-color:#3a3528}
 .flt input{cursor:text;flex:1 1 150px;min-width:120px}
 .flt .n{font-size:12.5px;color:#6b6456}
 .bk h2{font-size:15px;color:#b1271f;margin:22px 0 8px;padding-bottom:5px;border-bottom:1px solid #e6e0d2}
 details.q{background:#fff;border:1px solid #e6e0d2;border-radius:8px;margin:0 0 7px;scroll-margin-top:60px}
 details.q summary{cursor:pointer;padding:9px 12px;font-size:14.5px;list-style:none;display:flex;gap:9px;align-items:flex-start}
 details.q summary::-webkit-details-marker{display:none}
 details.q[open] summary{border-bottom:1px solid #f0ebe0}
 details.q .qt{flex:1 1 auto;min-width:0}
 details.q .qt ul{margin:5px 0 0;padding-left:20px}
 details.q .vr{flex:0 0 auto;font-size:11px;color:#6b6456;white-space:nowrap;margin-top:3px}
 details.q .src{display:block;font-size:13.5px;color:#4a4436;border-left:3px solid #e1d8c2;padding-left:9px;margin-bottom:5px}
 .tz{flex:0 0 auto;font-size:11px;font-weight:700;width:18px;height:18px;line-height:18px;text-align:center;border-radius:5px;margin-top:2px}
 .tz-lako{background:#e3f3e7;color:#1f7a3a} .tz-srednje{background:#fbf0d9;color:#9a6a12} .tz-tesko{background:#fbe3e0;color:#b1271f}
 .ans{padding:9px 13px 11px;font-size:14px}
 .ans .lbl{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:#6b6456;margin:8px 0 2px}
 .ans .lbl:first-child{margin-top:0}
 .ans .ok{color:#13602c;font-weight:600}
 .ans .ok b{font-weight:700} .ans ul,.ans ol{margin:3px 0;padding-left:20px}
 .ans .rel{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:9px;font-size:13px}
 .ans .rel a{color:#b1271f;font-weight:600;text-decoration:none}
 .ans .rel a.kv{color:#1f7a3a}
 details.q.hit{box-shadow:0 0 0 3px rgba(201,138,44,.5)}
 @media (max-width:760px){ .bk{padding:16px 16px 60px} details.q .vr{display:none} }
</style>
</head>
<body class="app-body">
<header class="app-bar">
 <button class="app-menu" id="app-menu" aria-label="Lekcije" aria-expanded="false">&#9776;</button>
 __BRAND_CRUMBS__
</header>
<div class="app-grid">
 <nav class="app-nav" id="app-nav" aria-label="Lekcije">__NAV__</nav>
 <main class="app-main" id="app-main"><div class="bk">__BODY__</div></main>
</div>
<script>__SHELL_JS__</script>
<script>
const qs = [...document.querySelectorAll('details.q')], n = document.getElementById('flt-n');
let tez = '', vrsta = '', txt = '';
const norm = s => String(s || '').toLowerCase().replace(/đ/g, 'dj').normalize('NFD').replace(/[̀-ͯ]/g, '');
function apply() {
  let c = 0;
  qs.forEach(q => { const on = (!tez || q.dataset.t === tez) && (!vrsta || q.dataset.v === vrsta) && (!txt || norm(q.textContent).includes(txt)); q.hidden = !on; if (on) c++; });
  document.querySelectorAll('.bk h2').forEach(h => { const zs = qs.filter(q => q.dataset.d === h.dataset.d); h.hidden = !zs.some(q => !q.hidden); });
  n.textContent = c + ' / ' + qs.length;
}
document.querySelectorAll('.flt [data-t]').forEach(b => b.addEventListener('click', () => {
  tez = b.dataset.t; document.querySelectorAll('.flt [data-t]').forEach(x => x.classList.toggle('on', x === b)); apply();
}));
document.getElementById('flt-v').addEventListener('change', e => { vrsta = e.target.value; apply(); });
document.getElementById('flt-s').addEventListener('input', e => { txt = norm(e.target.value.trim()); apply(); });
function hash() {
  const id = decodeURIComponent(location.hash.slice(1)), el = id && document.getElementById(id);
  if (!el) return; el.hidden = false; el.open = true; el.scrollIntoView({ block: 'start' }); el.classList.add('hit');
}
window.addEventListener('hashchange', hash);
apply(); setTimeout(hash, 50);
</script>
</body>
</html>
"""


def rel(page_dir, target):
    return os.path.relpath(ROOT / target, page_dir).replace(os.sep, "/") + ("/" if target.endswith("/") else "")


def build_subject(nivo, razred, predmet):
    files = veze.banks(ROOT, nivo, razred, predmet)
    k_file = ROOT / "shared" / "kurikulum" / nivo / str(razred) / f"{predmet}.yaml"
    k = yaml.safe_load(k_file.read_text()) if k_file.exists() else {}
    quizzes = veze.quizzes(ROOT, nivo, razred, predmet)
    counts = {b: len(veze.items(f)[1]) for b, f in files.items()}
    for broj, f in files.items():
        stem = f.stem
        page_dir = ROOT / veze.bank_dir(nivo, razred, predmet, stem)
        page_dir.mkdir(parents=True, exist_ok=True)
        bank, its = veze.items(f)
        secs, note = veze.sections_of(ROOT, predmet, razred, broj)
        lesson = lesson_dir(predmet, razred, stem)
        has_page = (ROOT / lesson / "bundle.enc").exists()
        kv = [q for q in quizzes if broj in q["lekcije"]]
        catalog = rel(page_dir, "index.html")
        subj = f"{catalog}#/{nivo}/{razred}/{predmet}"
        naslov = bank.get("naslov") or stem

        kv_links = "".join(f'<a class="kv" href="{esc(rel(page_dir, q["href"]))}">{esc(q["title"])}</a>' for q in kv)
        links = '<div class="links">' + (f'<a href="{esc(rel(page_dir, lesson))}">Gradivo ›</a>' if has_page else "") + kv_links + "</div>"
        vrste = sorted({z["vrsta"] for z in its}, key=lambda v: veze.VRSTA_LBL[v])
        flt = ('<div class="flt"><button class="on" data-t="">Sva</button>' + "".join(f'<button data-t="{t}">{veze.TEZ_LBL[t]}</button>' for t in veze.TEZ_LBL) +
               '<select id="flt-v" aria-label="Vrsta"><option value="">sve vrste</option>' + "".join(f'<option value="{v}">{veze.VRSTA_LBL[v]}</option>' for v in vrste) +
               '</select><input id="flt-s" type="search" placeholder="Nađi pitanje" aria-label="Nađi pitanje"><span class="n" id="flt-n"></span></div>')
        mape = {k: (v.get("naziv") if isinstance(v, dict) else v) for k, v in (bank.get("mesta") or {}).items()}
        for q in kv:   # map targets are named in the quiz's map
            karta = (yaml.safe_load((ROOT / "tools" / predmet / q["slug"] / "spec.yaml").read_text()) or {}).get("karta") or {}
            mape.update(karta.get("drzave") or {})
            mape.update({k: v.get("naziv") for k, v in (karta.get("mesta") or {}).items()})
        cards, cur = [], None
        for z in its:
            if z["deoNaslov"] != cur:
                cur = z["deoNaslov"]
                cards.append(f'<h2 data-d="{esc(cur)}">{esc(cur)}</h2>')
            iz = z.get("iz_udzbenika") or {}
            s = veze.item_section(secs, z)
            rels = []
            if has_page and s:
                rels.append(f'<a href="{esc(rel(page_dir, lesson))}#{esc(s["id"])}">Gradivo: {esc(s["naslov"])} ›</a>')
            if has_page and iz.get("strana"):
                rels.append(f'<a href="{esc(rel(page_dir, lesson))}#str-{iz["strana"]}">Strana {iz["strana"]} ›</a>')
            rels += [f'<a class="kv" href="{esc(rel(page_dir, q["href"]))}">Kviz: {esc(q["title"])} ›</a>' for q in kv]
            ans = ('<div class="lbl">Odgovor</div><div class="ok">' + veze.answer_html(z, mape) + "</div>" +
                   (f'<div class="lbl">Objašnjenje</div><div>{veze._b(z["objasnjenje"])}</div>' if z.get("objasnjenje") else "") +
                   (f'<div class="lbl">Iz gradiva</div><div>{veze._b(iz["tekst"])}</div>' if iz.get("tekst") else "") +
                   (f'<div class="rel">{"".join(rels)}</div>' if rels else ""))
            cards.append(f'<details class="q" id="{esc(z["id"])}" data-t="{z["tezina"]}" data-v="{z["vrsta"]}" data-d="{esc(cur)}">'
                         f'<summary><span class="tz tz-{z["tezina"]}" title="{veze.TEZ_LBL[z["tezina"]]}">{veze.TEZ_KR[z["tezina"]]}</span>'
                         f'<span class="qt">{veze.question_html(z)}</span><span class="vr">{veze.VRSTA_LBL[z["vrsta"]]}</span></summary><div class="ans">{ans}</div></details>')
        nav = f'<a class="row" href="{subj}/banka"><span>‹ Cela banka predmeta</span></a>'
        for pg in k.get("poglavlja") or []:
            rows = [l for l in pg.get("lekcije") or [] if int(l["broj"]) in files]
            if rows:
                nav += f'<div class="sec">{esc(pg.get("naslov", ""))}</div>'
            for l in rows:
                b = int(l["broj"])
                nav += (f'<a class="row{" cur" if b == broj else ""}" href="../{files[b].stem}/"><span>{esc(l["naslov"])}</span><span class="cnt">{counts[b]}</span></a>')
        sep = '<span class="sep">›</span>'
        crumbs = (f'<a class="brand" href="{catalog}">{BRAND}</a><nav class="app-crumbs" aria-label="Putanja">' + sep.join([
            f'<a href="{catalog}#/{nivo}">{esc(nivo_title(nivo))}</a>', f'<a href="{catalog}#/{nivo}/{razred}">{esc(razred_title(razred))}</a>',
            f'<a href="{subj}">{esc(predmet_title(predmet))}</a>', f'<a href="{subj}/banka">Banka</a>', f'<span class="cur">{esc(naslov)}</span>']) + "</nav>")
        body = (f'<h1>{esc(naslov)}</h1><p class="meta">Banka pitanja · {esc(predmet_title(predmet))} · {esc(razred_title(razred))} · {len(its)} pitanja. '
                "Klikni pitanje da vidiš odgovor.</p>" + links + flt + "".join(cards))
        html = (PAGE.replace("__SHELL_CSS__", SHELL_CSS).replace("__SHELL_JS__", SHELL_JS).replace("__BRAND_CRUMBS__", crumbs)
                .replace("__NAV__", nav).replace("__BODY__", body).replace("__TITLE__", esc(f"{naslov} — banka pitanja")))
        (page_dir / "index.html").write_text(html, encoding="utf-8")
    return len(files), sum(counts.values())


def main():
    for folder in sorted((ROOT / "shared" / "banke").glob("*/*/*")):
        nivo, razred, predmet = folder.parent.parent.name, int(folder.parent.name), folder.name
        print(f"{nivo}/{razred}/{predmet}:", *build_subject(nivo, razred, predmet))


if __name__ == "__main__":
    main()
