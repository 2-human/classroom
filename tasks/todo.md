# Kvizovi na hub šablonu (tri panela)

Datum: 2026-10-24 · Status: **urađeno (nije commit-ovano)**

## Šta postoji

| Alat | Generator | Raspored danas |
|---|---|---|
| `tools/geografija/evropa-kviz` | `shared/python/labeled_location_quiz.py` (2.895 linija) | zaglavlje sa ~10 kontrola · spisak pojmova (levo) · karta (sredina) + analiza ispod karte u testu · panel sa opisom/pitanjima (desno, statična kolona) · uvodni modal · poseban mobilni tok ekran-po-ekran |
| `tools/istorija/balkan-vremenska-osa` | `shared/python/timeline_mcq_quiz.py` (946 linija) | zaglavlje (naslov, opis, Tačno/Greške, reset) · kartice događaja sa unosom godina i pitanjima (levo, 360–480px) · vremenska osa (desno) |

Hub šablon = Crēdo Marketing Hub (MH-10), najčistija kopija u `gentree/public/hub/` (`index.html` + `hub.css` + `app.js`):
traka (brend · putanja · desno: čipovi) → mreža `navigacija 300px | glavni deo` → fioka sa desne strane (440px, kartice),
na ≤900px navigacija se izvlači ispod ☰, fioka preko celog ekrana. Pravilo: svaki entitet postoji jednom, dodatne informacije su kartice na njemu.

## Raspodela po panelima

| Panel | Geografija | Istorija |
|---|---|---|
| Traka | `classroom › Geografija › Evropa` · Učenje/Test · čipovi Mapa/Pitanja/Greške · meni ⋯ (Opis, Počni ispočetka, Granice, broj pitanja, CSV) | `classroom › Istorija › Balkan XIV–XV` · čipovi Tačno/Greške · meni ⋯ (Opis, Počni ispočetka) |
| Navigacija | filter + spisak pojmova (Demo · Pojmovi), status po pojmu (✓, oznake pitanja) — i dalje izvor prevlačenja | filter + događaji grupisani po trakama (Vladari, Države, Bitke, Događaji) sa brojem rešenih |
| Glavni deo | karta preko celog prostora (`flush`); u Testu kartice `Karta · Rezultati` (analiza se seli ispod karte → svoja kartica) | vremenska osa preko celog prostora |
| Fioka | izabrani pojam: `Opis` (Učenje) / `Pitanja` (Test) — isti sadržaj kao današnji `panelcol` | izabrani događaj: `Datum` (unos godina) · `Pitanja` (MCQ) |

## Koraci

- [x] `shared/python/hub_shell.py`: CSS školjke (preneto iz gentree `hub.css`, bez grafa) + funkcija koja vraća kostur (traka, nav, main, fioka) i malo zajedničkog JS-a (☰, zatvaranje fioke, Esc). Ugrađuje se u HTML — alat ostaje jedan fajl koji radi sa `file://`.
- [x] Boje: tokeni hub-a (`--accent`, `--bar`, `--bg`…) dobijaju vrednosti iz classroom palete (krem/crvena), ne tamnu Crēdo traku — *odluka ispod*.
- [x] `labeled_location_quiz.py`: `header .bar` → traka + meni; `.qcol` → nav; `.mapcol` → main; `.panelcol` → fioka (isti id-jevi `panelBody`, `panelTitle`… da JS ostane netaknut); analiza → kartica u main-u. Mobilni tok ostaje (spisak = nav, karta = main, rezultat = fioka), samo preko klasa školjke.
- [x] `timeline_mcq_quiz.py`: kartice događaja → stavke u nav; unos godina + pitanja → fioka; osa → main — *odluka ispod*.
- [x] `STATE_VERSION` ostaje (oblik stanja se ne menja).
- [x] `python3 make.py` u oba alata; provera u pregledaču na 1440 i 375: učenje, test, prevlačenje, nastavak sesije, štampa, `file://`.
- [x] Commit po promeni (shared modul, pa svaki alat), poruke po konvenciji repo-a.

## UX: šta poboljšati (predlozi, nisu u ovom koraku osim ako se odobri)

1. **Zaglavlje geografije je preopterećeno** (Opis, mod, reset, granice, broj pitanja, CSV, statistika u jednom redu). Hub: u traci samo mod + čipovi; ostalo u meni ⋯. Isti obrazac kao mobilni meni koji već postoji — desktop i mobilni dobijaju istu strukturu.
2. **Treća kolona je prazna dok se ništa ne postavi** (desno samo „Prevuci pojam na kartu…”). Kao fioka se otvara tek kad ima šta da pokaže — karta dobija ~440px više.
3. **Uvodni modal blokira prvi ekran.** Uputstvo kao prazno stanje fioke („Kako se igra”) ili kartica u main-u; modal samo pri prvom otvaranju.
4. **Analiza rezultata je ispod karte** i ne vidi se bez skrolovanja (a karta je visoka). Kartica `Rezultati` u main-u, sa brojem grešaka po pojmu (tabela `.tbl` iz hub-a) pa tek onda AI analiza.
5. **Istorija: levo su 66 kartica sa poljima** — duga kolona, osa je stalno daleko. Kompaktan spisak u nav-u + unos u fioci = osa uvek vidljiva, klik na događaj na osi otvara isti događaj (entitet jednom).
6. **Filter u nav-u** (hub ga ima) — „nađi Krit” umesto skrolovanja kroz 42 pojma / 66 događaja; plus brojači po grupi (rešeno/ukupno).
7. **Putanja `classroom › predmet › alat`** u traci daje povratak na katalog — danas iz alata nema puta nazad.
8. **Katalog (`index.html`) na istoj školjci** — nav = predmeti › alati, main = opis alata, „Otvori” vodi u alat. Svi alati izgledaju kao jedna aplikacija.
9. **Istorija nema mod Učenje/Test** ni opis događaja posle tačnog odgovora (geografija ima oba). Školjka daje mesto (kartica `Opis` u fioci) kad se doda sadržaj iz `_source/lekcije`.
10. **AI analiza traži ključ `sk-ant-…` u pregledaču** (čuva se u localStorage) — za učenike rizično; predlog: sakriti iza nastavničkog moda ili ukloniti iz javne verzije.

Odluke (operater, 2026-10-24): istorija → unos u fioci; boje classroom; UX 1, 2, 4, 6, 7 + 3 (uvod u fioci) + 8 (katalog) + 10 (AI analiza samo uz `?nastavnik`).

## Pregled

- `shared/python/hub_shell.py` — školjka (CSS/JS ugrađeni u svaku stranu, tokeni `--hub-*`), `PREDMET_TITLES` premeštene ovde iz `scripts/regenerate_index.py`.
- Geografija: id-jevi i logika kviza netaknuti; menjani samo kostur, uvod (modal → fioka), kartica Rezultati, `?nastavnik`, brojač u nav-u, ⋯ meni (i koraci demo-a koji pokazuju na njega). `STATE_VERSION` ostaje 5.
- Istorija: kartice događaja su iste, samo žive u fioci (vidi se izabrana); nav = lista po trakama sa statusom ○ ◐ ✓ i godinom; klik na osi otvara isti događaj; Prethodni/Sledeći. `STATE_VERSION` ostaje 1.
- Katalog: nav predmeti › alati, main pločice, fioka opis + „Otvori”; rute `#/predmet/alat` (na njih vode putanje iz alata).
- Provereno u pregledaču (1440 i 375): uvod, ⋯ meni, filter, ceo demo (18 koraka), Test → Rezultati, `#nastavnik`, mobilni tok geografije (spisak → karta), istorija unos → osa → pitanja → Sledeći, klik na osu, nastavak sesije, katalog sa rutom. Konzola bez grešaka.
- **Nije provereno:** otvaranje sa `file://`, štampa (Ctrl+P), stvarno prevlačenje mišem (demo radi isto preko istog koda). PDF-ovi nisu regenerisani — lokalni Python nema matplotlib; render_pdf nije menjan.
- Primećeno: osa u istoriji koristi `preserveAspectRatio="none"`, pa se tekst sabije kad je fioka otvorena (osa je uža) — bilo je i pre, sada je vidljivije. Kandidat za sledeći korak.

# Katalog: nivo › razred › predmet › lekcija

Datum: 2026-10-24 · Status: **urađeno (nije commit-ovano)**

- [x] `shared/kurikulum/osnovna/6/istorija.yaml` — 30 lekcija u 4 poglavlja (Todosijević, Eduka 2021; naslovi iz `_source/lekcije`)
- [x] `spec.yaml`: istorija `nivo: osnovna, razred: 6, lekcije: [17–22]`; geografija `nivo: osnovna, razred: 6` (operater; kviz pokriva deo programa, bez lekcija dok se ne unese kurikulum)
- [x] `hub_shell`: `NIVOI` (osnovna, srednja), putanje alata `Nivo › Razred › Predmet › Alat`
- [x] `scripts/regenerate_index.py`: stablo u navigaciji (lekcije izabranog predmeta se rasklope; filter traži lekcije i alate), pogledi za nivo / razred / predmet (poglavlja i sve lekcije, i one bez alata) / lekciju (alati, prethodna/sledeća), fioka alata sa listom lekcija
- [x] Provereno u pregledaču: početna (srednja škola prazna), predmet, lekcija + alat, filter, geografija bez kurikuluma; konzola čista

**Sledeće:** operater dostavlja slike stranica udžbenika geografije za 6. razred (privatno, u `tools/geografija/_source/slike/`, gitignored) → `shared/kurikulum/osnovna/6/geografija.yaml` + `lekcije` za evropa-kviz.

# Geografija 7: lekcije, slike, graf

Datum: 2026-10-24 · Status: **urađeno (nije commit-ovano)**

- [x] 25 skenova (str. 8–37; nedostaju 10–13 i 34) → `tools/geografija/_source/` (gitignored): `stranice-7/`, 11 beleški u `lekcije-7/`, 74 isečene slike + opisi u `slike-7/`
- [x] Graf: `scripts/build_lekcije_graf.py` → `pojmovi-7/` (407 pojmova sa povratnim vezama), „Povezane lekcije” u svakoj belešci, `lekcije-7/INDEX.md`; spojene varijante slugova (klima ×2, romani, Šar-planina)
- [x] `shared/kurikulum/osnovna/7/geografija.yaml` — 11 lekcija u 2 poglavlja; katalog prikazuje 7. razred
- [ ] Za proveru u knjizi: str. 16 vrh i 17 dno odsečeni (tabela 17 država nepotpuna); str. 23 zadatak 2 (poveži) odsečen; T/N „najviša planina Crne Gore je Durmitor” (knjiga vs. Zla Kolata 2.534 m)
- [x] Pilot kviz Južna Evropa (novi tip `lesson-quiz`): 28 zadataka, lestvica pomoći, Učenje/Test/Ispravka, karta (klikni, Gde sam?) — provereno u pregledaču (1440 i 375)

# Kviz: testovi iz baze + beleženje

Datum: 2026-10-24 · Status: **urađeno (nije commit-ovano)**

- [x] Test se svaki put sastavlja nanovo: 2 nasumična zadatka po delu lekcije + 5 generisanih iz baze 17 država (glavni gradovi, klikni državu, poluostrvo, „Gde sam?” za glavni grad)
- [x] Svaki test se beleži (localStorage): zadaci, svi odgovori učenika po zadatku, bodovi, Ispravka, ime; „Moji testovi”, Pregled rada, CSV za nastavnika
- [x] Provereno u pregledaču: dva testa različitog sastava (preklapanje 5/15), generisani zadaci rešeni kroz kartu, Ispravka, pregled, CSV (16 redova)
- [x] Slike iz udžbenika: zaštićena (šifrovana, lozinka) verzija `zasticeno/geografija/juzna-evropa-kviz/` — `scripts/build_zasticeno.py`, lozinka u Keychain-u; javni kviz bez slika, sa linkom ka zaštićenoj; katalog nudi obe. Provereno: pogrešna lozinka odbijena, tačna otvara kviz sa 13 slika, reload ne traži ponovo (ključ u sessionStorage).
- STATE_VERSION 1 → 2 (stari lokalni napredak se briše — bio je samo test)

# Velika banka + težine (pilot Južna Evropa)

Datum: 2026-10-24 · Status: **urađeno (nije commit-ovano)**

- [x] banka.yaml: 136 zadataka (51 lako / 55 srednje / 30 teško), svih 7 vrsta u sve 3 težine; 28 starih zadržano; ispravljen presečen odgovor „agrumi (limun, pomorandža)”
- [x] Generator: `tezina` obavezna, oznake L/S/T u listi i zaglavlju, Učenje = izvučena sesija (20), Test = 15, odnos 40/40/20, ravnomerno po delovima pa vrstama; generisani zadaci dobijaju težinu iz baze; `banka:` fajl; STATE_VERSION 3
- [x] Provereno u pregledaču: 4 sesije 8/8/4 i test 6/6/3, 2–5 zadataka po delu, 6–7 vrsta
- [ ] Ostalih 10 lekcija: isti obrazac (beleška → banka.yaml → kviz) posle provere pilota
