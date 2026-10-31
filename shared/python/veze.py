"""The three objects of a subject and the links between them.

Gradivo   tools/{predmet}/_source/lekcije-{razred}/NN-slug.md → protected page zasticeno/lekcije/…
Banka     shared/banke/{nivo}/{razred}/{predmet}/NN-slug.yaml → public page banka/{nivo}/{razred}/{predmet}/NN-slug/
Kvizovi   tools/{predmet}/{slug}/spec.yaml with `banka_lekcije`, protected copy zasticeno/{predmet}/{slug}/

A lesson's number (`broj`, NN) is what ties them together; a bank item ties to a section of the lesson
through `iz_udzbenika` (lekcija.match_section).
"""
import html as _html
import pathlib
import re

import yaml

from lekcija import note_path, parse_note, match_section, lesson_dir

esc = lambda s: _html.escape(str(s), quote=True)
TEZ_KR = {"lako": "L", "srednje": "S", "tesko": "T"}
TEZ_LBL = {"lako": "lako", "srednje": "srednje", "tesko": "teško"}
VRSTA_LBL = {"izbor": "Izbor", "tacno_netacno": "Tačno / netačno", "dopuni": "Dopuni", "povezi": "Poveži", "zakljuci": "Zaključi",
             "karta_klik": "Na karti", "gde_sam": "Gde sam?", "datum": "Kada?", "poredjaj": "Poređaj", "lanac": "Lanac", "izvor": "Istorijski izvor",
             "uporedi": "Uporedi", "ko_sam": "Ko sam?", "objasni": "Objasni"}


def banks(root, nivo, razred, predmet):
    """{broj: bank file}, in lesson order."""
    folder = pathlib.Path(root) / "shared" / "banke" / str(nivo) / str(razred) / predmet
    return {int(p.name[:2]): p for p in sorted(folder.glob("[0-9][0-9]-*.yaml"))}


def bank_dir(nivo, razred, predmet, stem):
    """Folder of a lesson's bank page, relative to the repo root."""
    return f"banka/{nivo}/{razred}/{predmet}/{stem}/"


def items(bank_file):
    with open(bank_file) as f:
        b = yaml.safe_load(f) or {}
    return b, [dict(z, deoNaslov=d["naslov"]) for d in b.get("delovi") or [] for z in d["zadaci"]]


def quizzes(root, nivo, razred, predmet):
    """Every quiz of the subject: [{slug, title, lekcije, prot: protected folder exists}]."""
    out = []
    for sp in sorted((pathlib.Path(root) / "tools" / predmet).glob("*/spec.yaml")):
        s = yaml.safe_load(sp.read_text()) or {}
        nums = s.get("banka_lekcije") or s.get("lekcije") or []
        if s.get("nivo") == nivo and s.get("razred") == razred and nums:
            out.append({"slug": sp.parent.name, "title": s.get("title_short") or s.get("title") or sp.parent.name, "lekcije": [int(n) for n in nums],
                        "href": f"zasticeno/{predmet}/{sp.parent.name}/" if (pathlib.Path(root) / "zasticeno" / predmet / sp.parent.name / "bundle.enc").exists()
                        else f"tools/{predmet}/{sp.parent.name}/index.html"})
    return out


def sections_of(root, predmet, razred, broj):
    note = note_path(root, predmet, razred, broj)
    return (parse_note(note)["sections"], note) if note else ([], None)


def item_section(sections, z):
    iz = z.get("iz_udzbenika") or {}
    return match_section(sections, iz.get("odeljak"), iz.get("strana")) if sections and iz else None


def _b(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))


def fmt_year(y):
    return f"{-y} pre n. e." if y < 0 else str(y)


def years(z):
    if z.get("oznaka"):
        return z["oznaka"]
    if z.get("godina") is not None:
        return fmt_year(z["godina"])
    a, b = z.get("od"), z.get("do")
    if b is None:
        return fmt_year(a)
    return f"{-a}–{fmt_year(b)}" if a < 0 and b < 0 else f"{fmt_year(a)}–{fmt_year(b)}"


def question_html(z):
    v = z["vrsta"]
    if v == "tacno_netacno":
        return _b(z["tvrdnja"])
    if v == "dopuni":
        return _b(re.sub(r"\{\{(.+?)\}\}", "____", z["tekst"]))
    if v in ("ko_sam", "gde_sam"):
        return ("Gde sam? " if v == "gde_sam" else "Ko sam? ") + _b(" · ".join(z["tragovi"]))
    if v == "datum":
        return _b(z.get("pitanje") or "Kada?") + " " + _b(z.get("dogadjaj") or "")
    if v == "lanac":
        return _b(z.get("pitanje") or "") + " " + " → ".join("<b>?</b>" if i == z["praznina"] else _b(k) for i, k in enumerate(z["karike"]))
    if v == "izvor":
        i = z["izvor"]
        return (f'<span class="src">{_b((i.get("autor") + ": ") if i.get("autor") else "")}{_b(i.get("naslov") or "")} {_b(i["tekst"])}</span> ' + _b(z.get("pitanje") or ""))
    if v == "uporedi":
        return _b(z.get("pitanje") or f'{z["a"]} ili {z["b"]}?') + "<ul>" + "".join(f"<li>{_b(t['tekst'])}</li>" for t in z["tvrdnje"]) + "</ul>"
    if v == "povezi":
        return _b(z.get("pitanje") or "Poveži parove.")
    return _b(z.get("pitanje") or "")


def answer_html(z, mape=None):
    v = z["vrsta"]
    if v in ("izbor", "zakljuci", "lanac", "izvor", "ko_sam"):
        return "; ".join(_b(o["tekst"]) for o in z["odgovori"] if o.get("tacan"))
    if v == "datum":
        return esc(years(z))
    if v == "poredjaj":
        return " → ".join(_b(s["tekst"]) + (f' ({esc(s.get("oznaka") or fmt_year(s["godina"]))})' if s.get("godina") is not None else "") for s in z["stavke"])
    if v == "uporedi":
        lbl = {"a": z["a"], "b": z["b"], "oba": "oba", "nijedan": "nijedan"}
        return "<ol>" + "".join(f"<li>{esc(lbl[t['odgovor']])}</li>" for t in z["tvrdnje"]) + "</ol>"
    if v == "objasni":
        return _b(z["uzor"]) + "<ul>" + "".join(f"<li>{_b(i if isinstance(i, str) else i.get('tekst', ''))}</li>" for i in z["ideje"]) + "</ul>"
    if v == "tacno_netacno":
        return "Tačno" if z["tacno"] else "Netačno — " + _b(next(o["tekst"] for o in z["ispravke"] if o.get("tacan")))
    if v == "dopuni":
        return re.sub(r"\{\{(.+?)\}\}", lambda m: "<b>" + esc(m.group(1).split("|")[0]) + "</b>", esc(z["tekst"]).replace("&#x27;", "'"))
    if v == "povezi":
        return "<ul>" + "".join(f"<li>{_b(p[0])} → {_b(p[1])}</li>" for p in z["parovi"]) + "</ul>"
    c = z.get("cilj") or {}
    return esc((mape or {}).get(c.get("drzava") or c.get("mesto")) or c.get("drzava") or c.get("mesto") or "")
