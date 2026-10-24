# Kviz 2.0 — proširena mehanika (predlog)

Datum: 2026-10-24 · Status: **pilot urađen** (2026-10-24): jezgro + A, B, C, D, K, H, I — `tools/geografija/juzna-evropa-kviz/`; ostalo (E, F, G, J, L, M, N) sledeće

Polazište: dva postojeća tipa (`labeled-location-quiz` — karta + hintovi + test pitanja,
`timeline-mcq-quiz` — datumi + MCQ) i ono što operater želi da zadrži: **fioka desno koja posle
svake greške daje sve više informacija**, dok učenik sam ne dođe do odgovora.

## 1. Jedno jezgro: zadatak + lestvica pomoći

Svaki zadatak (bilo kog tipa) ima isti životni ciklus:

```
pitanje → pokušaj → greška → stepenik pomoći 1 (fioka) → pokušaj → greška → stepenik 2 → …
       → tačno  (bodovi po broju iskorišćenih stepenika)      → poslednji stepenik = otkriven odgovor + objašnjenje
```

- **Lestvica pomoći** (generalizacija današnjih hintova), od najblažeg ka najkonkretnijem:
  1. *usmeri* — na šta da obrati pažnju (bez imenovanja odgovora)
  2. *suzi* — isključi deo ponuđenog / precizira region
  3. *iz lekcije* — kratak isečak beleške lekcije (sopstvenim rečima) + link na pojam u grafu
  4. *otkrij* — tačan odgovor + objašnjenje „zašto”
- **Bodovi:** samostalno 3 · uz 1 pomoć 2 · uz 2 pomoći 1 · otkriveno 0. Isto za sve tipove,
  pa je zbir uporediv između lekcija.
- **Režimi** ostaju: *Učenje* (lestvica uključena), *Test* (bez pomoći; na kraju **Ispravka** —
  samo pogrešni zadaci ponovo, sa lestvicom). *Ponavljanje*: zadaci koji su otkriveni vraćaju se
  kasnije u istoj sesiji (razmaknuto ponavljanje).
- **Posle tačnog** fioka prelazi u *Saznaj više*: pojam iz grafa (sažetak, ključne činjenice),
  „Pojavljuje se i u lekcijama: …” (veze grafa), slika iz lekcije ako postoji.

Raspored (hub školjka): **navigacija** = zadaci kviza grupisani po delu lekcije, sa statusom
(○ ◐ ✓ ✗ i bodovima) · **glavni deo** = trenutni zadatak · **fioka** = lestvica / saznaj više.

## 2. Vrste zadataka

| # | Vrsta | Proverava | Izvor u udžbeniku |
|---|---|---|---|
| A | Izbor (jedan / više tačnih) | činjenice | „Proveri”, pitanja na kraju |
| B | Tačno / netačno **+ ispravi** — za netačnu tvrdnju bira se ispravka | činjenice + razumevanje | T/N zadaci (Crna Gora) |
| C | Dopuni rečenicu (upis ili ponuđene reči) | pojmove | „Dopuni rečenice” (Hrvatska) |
| D | Poveži parove (država–glavni grad, reka–ušće, pojam–opis) | veze | „Poveži” |
| E | Popuni tabelu (država · glavni grad · površina · jezik…) | sistematizaciju | tabela Južne Evrope |
| F | Ukrštenica | pojmove | „Ponovi” (Španija) |
| G | Na karti: prevuci pojam (postojeći kviz) | snalaženje | „Upiši na nemoj karti” |
| H | Na karti: klikni državu / region / grad | snalaženje | karte država |
| I | **Gde sam?** — opis se otkriva rečenicu po rečenicu, učenik klikne mesto na karti; ranije = više bodova | snalaženje + zaključivanje | — (novo) |
| J | Poređaj (po broju stanovnika, površini, dužini reke, od severa ka jugu) | odnose veličina | — (novo) |
| K | **Zaključi** — situacija → izbor, a lestvica pomoći su *koraci rasuđivanja* („Gde leži? → Kakva je tada klima? → Šta uspeva u takvoj klimi?”) | razmišljanje | „Pitanja za razmišljanje”, zadaci „objasni” |
| L | Uzrok → posledica (poveži) | razmišljanje | delovi „zbog toga…” u tekstu |
| M | Uporedi dve države („tačno za A, ali ne za B”) | razmišljanje | — (novo) |
| N | Prepoznaj sa slike (pejzaž → tip klime / privreda / država) | zaključivanje | fotografije lekcija |

Napomena za N: isečene slike iz udžbenika ostaju **privatne** (`_source/`). Javni kviz koristi
slike slobodne licence (npr. Wikimedia Commons) ili radi samo u lokalnoj verziji.

### Šta smo našli u udžbeniku (11 lekcija)
Formati zadataka: upiši na nemu kartu (brojevima / bojama / slovima), popuni tabelu, tačno/netačno
(zaokruži T ili N), poveži (slova na linije), dopuni rečenice, ukrštenica sa rešenjem u osenčenoj koloni,
prepoznaj grad / zastavu sa fotografije, zaključi sa tematske karte, pitanja „objasni / razmisli” u
tekstu, rad sa atlasom. Svaka beleška već ima: „Na karti” (mesta sa koordinatama — osnova za G/H/I),
„Zadaci iz udžbenika” (sa očekivanim odgovorima) i „Pitanja za razmišljanje” (osnova za K).

## 3. Podaci

- `shared/kurikulum/osnovna/7/geografija.yaml` — lekcije (iz beleški).
- `shared/znanje/{slug}/` — pojmovi (države, regioni, reke, planine…) sa vezama; izvor
  `izvori/udzbenik-geografija-7.md` (sopstvenim rečima). Lekcije ↔ pojmovi preko `pojmovi:`.
- Zadaci: `tools/geografija/{lekcija}-kviz/spec.yaml` (novi tip `lesson-quiz`, šablon u
  `templates/lesson-quiz/`), svaki zadatak: `vrsta`, `pojmovi`, `pitanje`, rešenje, `pomoc:
  [usmeri, suzi, iz_lekcije]`, `objasnjenje`. Generator: `shared/python/lesson_quiz.py`.
- Karta: ista projekcija i `countries.geojson` kao Evropa kviz (države kao klikabilne površine).

## 4. Redosled izrade (predlog)

1. Jezgro (lestvica, bodovi, režimi, fioka) + vrste A, B, C, D, K — jedna lekcija kao pilot (Južna Evropa).
2. Karta: H, I (+ G iz postojećeg kviza).
3. E, F, J, L, M; pa N.
4. Kvizovi za sve lekcije + pregledni test kroz sve lekcije.
