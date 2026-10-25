Continue building the grade 7 history quiz in `~/work/projects/classroom` (read `CLAUDE.md`, `templates/lesson-quiz/README.md` and `tasks/kviz-istorija-7.md` first). The work so far is committed on `main` (b8f16d1…c5d1e91); nothing is pushed.

## Goal
Lesson quizzes for the grade 7 history textbook (1780–1918, Cyrillic book, quizzes in Serbian Latin) that build understanding, not memorisation. The design extends the shared `lesson-quiz` engine and combines the grade 6 history timeline (`tools/istorija/balkan-vremenska-osa`) with the grade 7 geography lesson quizzes (help ladder, L/S/T banks, Učenje/Test/Ispravka, saved tests).

The operator chose:
- all new mechanics: per-option "why it's wrong", cause→effect chains, source analysis, compare-two, lesson timeline, spaced reinforcement, "Ko sam?", "Objasni svojim rečima";
- build the 4 lessons we have now, extend later;
- extend the shared engine, so geography gets the new mechanics too.

## Done
- **Source notes** (private, gitignored) in `tools/istorija/_source/`:
  - `stranice-7/` (pp. 10–38) and `lekcije-7/` with 4 notes: 01 = 1.1, 02 = 1.2, 03 = 2.1, 04 = 2.2;
  - `slike-7/` (37 crops) and `pojmovi-7/` (203 concepts).
  - Missing pages: 15, 20–27, 33, 39. There may be a lesson 1.3 on pp. 20–27; if so, renumber the lessons.
- **Curriculum:** `shared/kurikulum/osnovna/7/istorija.yaml` (lessons 1–4).
- **Engine** (`shared/python/lesson_quiz.py`):
  - new `vrsta` values: `datum`, `poredjaj`, `lanac`, `izvor`, `uporedi`, `ko_sam`, `objasni`, all validated in `load_spec`;
  - `zasto` on any option in `odgovori` / `ispravke` and on `uporedi.tvrdnje`;
  - optional `osa: {naziv, od, do?, traka?}` on any item, plus spec-level `osa: {od, do, trake}` and a "Vremenska osa" view (`_osa`);
  - "Moje znanje" view (`_znanje`): Leitner boxes per concept, intervals 0/1/3/7/14 days. Učenje draws `sastav.ponavljanje`% (default 50) from due concepts, preferring a different item type, and marks those items ↻;
  - `objasni` is self-graded (all ideas = 3, at least half = 2, some = 1) and is left out of tests. The operator hasn't confirmed this; mention it.
  - Ispravka doesn't change mastery. `STATE_VERSION` is now 4 (old progress drops).
  - Fixes: the strike-through applies only to option text (`.ot`), and the intro/start text mentions the states database only when `BAZA`.
- **Pilot quiz:** `tools/istorija/prosvetiteljstvo-kviz/` (lesson 4, 13 items, one or more of every new type). It is built. Use its `spec.yaml` / `banka.yaml` as the format example.
- **Checked so far:** the pilot loads with no console errors, and a wrong `izbor` shows its `zasto`. Use preview server `classroom` (port 8661) from `/Users/milos.funl/Claude Code/.claude/launch.json`; `file://` can't be scripted in the pane. `tools/geografija/srbija-kviz/index.html` was rebuilt with the new engine and builds fine.

## Next
1. In the browser (1440 and 375), verify every new type end to end:
   - datum (earlier/later feedback, ranges), poredjaj, lanac, izvor, uporedi, ko_sam (clues + "Još jedan trag"), objasni (write → compare → tick);
   - placement on the timeline and the `_osa` view (labels stacking, faded entries for revealed answers);
   - `_znanje` after a few answers (fake `state.znanje[x].due` into the past and check that the next session draws ↻ items);
   - Test excludes `objasni`; review page and CSV for the new types; the strike-through fix.
   Fix whatever breaks.
2. Rebuild all 11 geography quizzes and spot-check one (help ladder, map, test) for regressions.
3. Update the docs:
   - the `lesson_quiz.py` docstring;
   - `templates/lesson-quiz/README.md` (new types table, `zasto`, `osa`, Moje znanje);
   - `templates/lesson-quiz/spec.template.yaml`;
   - CLAUDE.md ("Current versions": `lesson_quiz.py` = 4).
4. Write the banks: one subagent per lesson, with a shared brief.
   - Folders: `tools/istorija/{osnovne-odlike-1780-1918,istorijski-izvori-1780-1918,industrijska-revolucija,prosvetiteljstvo}-kviz/`; extend the pilot for lesson 4.
   - Aim for ~100–140 items per lesson covering every fact in the note. Put the weight on why / cause→effect / source / compare.
   - Every type in all three difficulty levels. Every wrong option gets a `zasto`. Use `iz_udzbenika` with `slika` from `slike-7/`.
   - Give dated events consistent `osa` / `naziv` values so each event is one point on the timeline.
   - Write questions in your own words and never copy book text. Don't answer what the book doesn't (e.g. Semiramida, the Anastas Jovanović photo).
   - Validate each bank with `make.py`.
5. Run `python3 scripts/regenerate_index.py` and `python3 scripts/build_zasticeno.py tools/istorija/{slug}` for each quiz (password in Keychain `classroom-zasticeno`; never print it).
6. Commit one coherent change at a time, following the repo's message convention:
   - `shared/python/lesson_quiz: …`;
   - each tool;
   - `index.html`.
   Don't touch `_commit-h11-cleanups.sh`, which isn't ours.

Working style (operator): Serbian UI and content, Socratic — ask before design decisions, verify before calling anything done.

## Stanje 2026-10-25 (urađeno — „Next” 1–6)
- Provereno u pregledaču (1440 i 375): sve nove vrste, osa, Moje znanje, test bez objasni, pregled rada, CSV, precrtavanje.
  Popravljeno: natpisi na osi blizu kraja (sada levo od trake), pokvaren YAML u pilotu (load_spec sada odbija takve ključeve),
  uporedi sa dugim nazivima (A/B + legenda).
- Operater: `objasni` ostaje samoprocena u Učenju, bez testa. Događaji koje knjiga datira delom veka: `oznaka` (reči knjige) na osi.
- Banke: 1.1 = 139, 1.2 = 123, 2.1 = 136, 2.2 = 140 zadataka; svi pogrešni odgovori imaju zasto; osa dosledna.
- Regresija geografije OK; katalog i zaštićene kopije (istorija + geografija) napravljeni; 14 commit-a ispred origin, ništa push-ovano.
- Otvoreno: str. 15, 20–27, 33, 39 nisu snimljene (rezimei, pitanja na kraju lekcija, moguća lekcija 1.3).
