#!/usr/bin/env python3
"""Check question-bank files (shared/banke/{nivo}/{razred}/{predmet}/{NN-slug}.yaml).

Usage:
    python3 scripts/proveri_banku.py shared/banke/srednja/1/istorija                 # every lesson
    python3 scripts/proveri_banku.py shared/banke/srednja/1/istorija/03-*.yaml       # some lessons

Runs the quiz engine's validation on each file and adds the bank rules: ids unique across the whole
subject, every wrong option has a `zasto`, every `pojmovi` slug is named, every
item has `iz_udzbenika` with a page inside the lesson, and one timeline event keeps one set of years
across the subject. Prints the item count per type and level.
"""
import collections
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))
from lesson_quiz import check_spec  # noqa: E402
from lekcija import note_path, parse_note  # noqa: E402

VRSTE = ["izbor", "tacno_netacno", "dopuni", "povezi", "zakljuci", "datum", "poredjaj", "lanac", "izvor", "uporedi", "ko_sam", "objasni"]


def main(args):
    files = []
    for a in args:
        p = pathlib.Path(a).resolve()
        files += sorted(p.glob("[0-9][0-9]-*.yaml")) if p.is_dir() else [p]
    folder = files[0].parent
    predmet, razred, nivo = folder.name, int(folder.parent.name), folder.parent.parent.name
    kur = yaml.safe_load((ROOT / "shared" / "kurikulum" / nivo / str(razred) / f"{predmet}.yaml").read_text())
    trake = kur.get("osa_trake") or []
    ids, errors, warnings, events = collections.Counter(), [], [], collections.defaultdict(set)
    for other in sorted(folder.glob("[0-9][0-9]-*.yaml")):   # ids and years are checked across the subject
        for d in (yaml.safe_load(other.read_text()) or {}).get("delovi") or []:
            for z in d["zadaci"]:
                ids[z.get("id")] += 1
                for e in ([z["osa"]] if z.get("osa") else []) + (z.get("stavke") or []) + ([{"naziv": z.get("dogadjaj"), "od": z.get("od", z.get("godina")), "do": z.get("do")}] if z.get("vrsta") == "datum" else []):
                    if e.get("naziv") and e.get("od", e.get("godina")) is not None:
                        events[e["naziv"]].add((e.get("od", e.get("godina")), e.get("do")))
    errors += [f"id used twice: {k}" for k, n in ids.items() if n > 1]
    errors += [f"timeline {k}: years differ {sorted(v, key=str)}" for k, v in events.items() if len(v) > 1]
    for f in files:
        b = yaml.safe_load(f.read_text()) or {}
        broj = int(f.name[:2])
        note = note_path(ROOT, predmet, razred, broj)
        od, do = (parse_note(note)["fm"].get("strane") or [0, 999])[:2]
        # map items are checked with their quiz (the map lives in its spec.yaml)
        plain = [{"naslov": d["naslov"], "zadaci": [z for z in d["zadaci"] if z["vrsta"] not in ("karta_klik", "gde_sam")]} for d in b["delovi"]]
        check_spec({"delovi": plain, "osa": {"trake": trake}, "sastav": {}})
        items = [z for d in b["delovi"] for z in d["zadaci"]]
        pojmovi = b.get("pojmovi") or {}
        for z in items:
            i = z["id"]
            for o in (z.get("odgovori") or []) + (z.get("ispravke") or []):
                if not o.get("tacan") and not o.get("zasto"):
                    warnings.append(f"{i}: wrong option without zasto")
            if any(not t.get("zasto") for t in z.get("tvrdnje") or []):
                warnings.append(f"{i}: uporedi statement without zasto")
            errors += [f"{i}: pojam {s} is not in pojmovi" for s in z.get("pojmovi") or [] if s not in pojmovi]
            iz = z.get("iz_udzbenika") or {}
            if not (isinstance(iz.get("strana"), int) and od <= iz["strana"] <= do):
                warnings.append(f"{i}: iz_udzbenika.strana {iz.get('strana')!r} is outside pages {od}–{do}")
            if z["vrsta"] not in ("ko_sam", "objasni") and len(z.get("pomoc") or []) < 2:
                warnings.append(f"{i}: needs at least 2 pomoc steps")
        c = collections.Counter((z["vrsta"], z["tezina"]) for z in items)
        print(f"{f.name}: {len(items)} items {dict(collections.Counter(z['tezina'] for z in items))}")
        print("  " + " · ".join(f"{v} {[c[(v, t)] for t in ('lako', 'srednje', 'tesko')]}" for v in VRSTE))
    if warnings:
        print(f"{len(warnings)} warnings (older items without zasto/pomoc), first: {warnings[0]}")
    print("\n".join(errors[:60]) or "OK")
    if errors:
        raise SystemExit(f"{len(errors)} problems")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        raise SystemExit(__doc__)
    main(sys.argv[1:])
