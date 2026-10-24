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
