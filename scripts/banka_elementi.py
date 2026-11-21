#!/usr/bin/env python3
"""Write the chemistry question bank "simbol → element" from shared/data/elementi.yaml.

Usage:
    python3 scripts/banka_elementi.py

Output: shared/banke/osnovna/7/hemija/01-hemijski-elementi-i-simboli.yaml (generated; edit the data
file, not the bank). Per element three items, all tied to it with `element: SIMBOL` (the quiz then shows
the periodic table with it highlighted and its details in the drawer):
    lako     izbor  — the name among three other elements with different initials
    srednje  izbor  — the name among elements with similar symbols (`slicni`)
    tesko    dopuni — the full name typed in, no word bank; any case form (`oblici`) and small typos
                      (`priblizno`) count as correct, and the pupil is told the nominative spelling
Every wrong option says whose symbol it is; the help ladder is the element's `pomoc`.
"""
import pathlib
import random

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "shared" / "banke" / "osnovna" / "7" / "hemija" / "01-hemijski-elementi-i-simboli.yaml"
DELOVI = [("Metali", {"metal"}), ("Nemetali", {"nemetal"}), ("Plemeniti gasovi i polumetali", {"plemeniti gas", "polumetal"})]


FLEETING_A = {"bakar": "bakr", "kositar": "kositr"}   # a that drops in the other cases (bakar → bakra)


def oblici(n):
    """The other singular case forms of an element's name (genitive, dative, accusative, instrumental, locative)."""
    if n.endswith("um"):
        s = n[:-2] + "um"
        return [s + "a", s + "u", s + "om"]
    if n.endswith("a"):
        s = n[:-1]
        return [s + "e", s + "i", s + "u", s + "om"]
    if n.endswith("o"):
        s = n[:-1]
        return [s + "a", s + "u", s + "om"]
    if n.endswith("e"):
        s = n[:-1]
        return [s + "a", s + "u", s + "em"]
    s = FLEETING_A.get(n, n)
    return [s + "a", s + "u", s + ("em" if s[-1] in "jcčćđšž" or s.endswith(("lj", "nj")) else "om")]


def slug(s):
    return s.lower().translate(str.maketrans("čćšđž", "ccsdz")).replace(" ", "-")


def main():
    data = yaml.safe_load((ROOT / "shared" / "data" / "elementi.yaml").read_text())
    els = data["elementi"]
    by = {e["simbol"]: e for e in els}
    r = random.Random(7)

    def option(e, ok, za):
        o = {"tekst": e["naziv"], "tacan": ok}
        if not ok:
            o["zasto"] = f"{e['naziv'][0].upper() + e['naziv'][1:]} ima simbol {e['simbol']}, a ne {za['simbol']}."
        return o

    def izbor(e, others, tez):
        opts = [option(e, True, e)] + [option(o, False, e) for o in others]
        r.shuffle(opts)
        return {"id": f"l01-{slug(e['simbol'])}-izbor-{tez}", "vrsta": "izbor", "tezina": tez, "element": e["simbol"],
                "pojmovi": [slug(e["naziv"])], "pitanje": f"Koji hemijski element ima simbol **{e['simbol']}**?",
                "odgovori": opts, "pomoc": e["pomoc"], "objasnjenje": f"**{e['simbol']}** je simbol elementa koji se zove {e['naziv']}. Simbol potiče od: {e['poreklo']}."}

    delovi = []
    for naslov, vrste in DELOVI:
        zadaci = []
        for e in [x for x in els if x["vrsta"] in vrste]:
            far = [o for o in els if o is not e and o["naziv"][0] != e["naziv"][0] and o["simbol"][0] != e["simbol"][0]]
            zadaci.append(izbor(e, r.sample(far, 3), "lako"))
            near = [by[s] for s in e.get("slicni", []) if s in by][:3]
            fill = [o for o in els if o is not e and o not in near and o["simbol"][0] == e["simbol"][0]]
            near += r.sample(fill, min(3 - len(near), len(fill)))
            near += r.sample([o for o in els if o is not e and o not in near], 3 - len(near))
            zadaci.append(izbor(e, near, "srednje"))
            names = [e["naziv"]] + e.get("varijante", [])
            zadaci.append({"id": f"l01-{slug(e['simbol'])}-dopuni", "vrsta": "dopuni", "tezina": "tesko", "element": e["simbol"],
                           "oblici": [o for n in names for o in oblici(n)], "priblizno": True,
                           "pojmovi": [slug(e["naziv"])], "tekst": f"Hemijski simbol **{e['simbol']}** označava element {{{{{'|'.join(names)}}}}}.",
                           "pomoc": e["pomoc"], "objasnjenje": f"**{e['simbol']}** je simbol elementa koji se zove {e['naziv']}. Simbol potiče od: {e['poreklo']}."})
        delovi.append({"naslov": naslov, "zadaci": zadaci})
    bank = {"lekcija": 1, "naslov": "Hemijski elementi i njihovi simboli",
            "pojmovi": {slug(e["naziv"]): e["naziv"] for e in els}, "delovi": delovi}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("# Banka pitanja: hemijski elementi i simboli (hemija, 7. razred). GENERISANO iz shared/data/elementi.yaml\n"
                   "# skriptom scripts/banka_elementi.py: menja se podatak, ne ovaj fajl.\n"
                   + yaml.safe_dump(bank, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {sum(len(d['zadaci']) for d in delovi)} pitanja, {len(els)} elemenata")


if __name__ == "__main__":
    main()
