# lesson-quiz — kviz po lekciji

Jedan `spec.yaml` → jedan samostalan `index.html` (radi i sa `file://`), na zajedničkoj hub školjci
(navigacija = zadaci po delovima lekcije · glavni deo = zadatak · fioka = pomoć / „Saznaj više”).
Render logika: `shared/python/lesson_quiz.py`. Primer: `tools/geografija/juzna-evropa-kviz/`.

## Mehanika — lestvica pomoći (ista za sve vrste)

1. Učenik odgovara. Posle **svake greške** u fioci (na telefonu ispod zadatka) stiže sledeći
   stepenik pomoći iz `pomoc:` — *usmeri* → *suzi* → *iz lekcije*.
2. Greška posle poslednjeg stepenika **otkriva** odgovor i objašnjenje.
3. Bodovi: bez greške 3 · jedna greška 2 · više 1 · otkriveno 0.
4. Posle odgovora fioka prelazi u **Saznaj više**: objašnjenje, pojmovi i druge lekcije u kojima se
   pojam javlja (iz privatnog grafa `tools/{predmet}/_source/pojmovi-{razred}/`, ako postoji).

Jedan kviz, bez režima. Instanca se izvlači iz banke; u rezultat ide **prvi odgovor** na svako pitanje
(tačno / netačno), a pomoć ostaje posle greške da bi se našao tačan odgovor, bez promene rezultata.

## Banka, težina i sastav

- **Banka:** svi zadaci lekcije — u `spec.yaml` (`delovi`) ili, za veliku banku, u posebnom fajlu
  (`banka: banka.yaml` sa `delovi` i `mesta`). Cilj: iscrpeti lekciju — svaka činjenica, broj, pojam,
  uzrok/posledica i mesto na karti bar jednom; svaka vrsta zadatka u sve tri težine.
- **Težina** (`tezina`, obavezno): `lako` — jedna istaknuta činjenica, očigledni pogrešni odgovori;
  `srednje` — detalji, brojevi, dve činjenice, uverljivi pogrešni odgovori; `tesko` — zaključivanje,
  poređenje, primena, dopuna bez banke reči, male države i mesta na karti. U listi zadataka oznake
  **L / S / T**, legenda sa brojem po težini.
- **Sastav:** instanca ima `sastav.pitanja` pitanja (podrazumevano 25) u odnosu `sastav.odnos`
  (podrazumevano 40/40/20), ravnomerno po delovima lekcije pa po vrstama. Banci se pri svakom izvlačenju
  pridružuju i zadaci generisani iz `baza.drzave` (`sastav.generisano`; težina dolazi od `tezina` države).
- **Nova instanca:** 10–25% pitanja dolazi iz prethodne instance, najpre netačno odgovorena (oko dve
  trećine), pa tačna (oznaka ↻). Ostalo su pitanja koja nisu bila u prethodnoj: prvo ona nikad postavljena,
  a kad ih nestane, ona postavljena najdavnije.

## Arhiva i istorija odgovora

- **Arhiva rezultata:** završena instanca (svako pitanje ima prvi odgovor) ostaje u arhivi kviza, levo u
  navigaciji: rezultat, **Pregled rada** i **CSV** za nastavnika.
- **Banka:** svaki odgovor se upisuje i po pitanju; stranica Banke pokazuje hronologiju (kada, tačno ili
  netačno, u kom kvizu i kojoj instanci, sa vezom na tu instancu u arhivi).
- Sve je u pregledaču (localStorage), bez naloga: javna i zaštićena kopija dele isti zapis, ali drugi uređaj
  ne vidi ove podatke.

## Vrste zadataka

| vrsta | šta | posebno |
|---|---|---|
| `izbor` | jedan ili više tačnih | pogrešni odgovori se precrtavaju |
| `tacno_netacno` | tačno / netačno | netačna tvrdnja traži i ispravku (`ispravke`); pogrešan izbor kod tačne tvrdnje je otkriva |
| `dopuni` | praznine `{{odgovor\|alternativa}}` | `ponudjene` = banka reči; tačne praznine se zaključaju |
| `povezi` | `parovi` levo ↔ desno | desna kolona se meša |
| `zakljuci` | rasuđivanje, jedan tačan | `pomoc` piši kao korake („Korak 1: …”) |
| `karta_klik` | klikni državu (`drzava: ISO3`) ili mesto (`mesto: slug`) | promašaj kaže koja je država / koliko km |
| `gde_sam` | `tragovi` jedan po jedan, klik na kartu | svaki pogrešan klik ili „Još jedan trag” = sledeći trag |
| `datum` | godina (`godina`) ili raspon (`od`/`do`) događaja `dogadjaj` | pogrešna godina kaže ranije/kasnije i koliko blizu; stavlja događaj na osu |
| `poredjaj` | poređaj `stavke` hronološki (u spec-u u tačnom redu, svaka sa `godina`) | tačne pozicije se zaključaju; sve stavke idu na osu |
| `lanac` | uzrok → posledica: `karike` sa jednom praznom (`praznina`) | biraš kariku iz `odgovori`; `pomoc` kao koraci rasuđivanja |
| `izvor` | odlomak `izvor: {autor, naslov, tekst, napomena}` + pitanje | odlomak sopstvenim rečima ili javno dobro, uz napomenu |
| `uporedi` | razvrstaj `tvrdnje` u `a` / `b` / oba / nijedan | svaka tvrdnja ima `odgovor` i `zasto` |
| `ko_sam` | ličnost iz `tragova` jedan po jedan, odgovor iz `odgovori` | svaki trag ili greška = manje bodova |
| `objasni` | učenik napiše odgovor, pa vidi `uzor` i štiklira `ideje` | samoprocena (sve ideje = tačno; neke → 1); nema ga u testu |

**Zašto (`zasto`):** svaki pogrešan ponuđeni odgovor (`odgovori`, `ispravke`, `uporedi.tvrdnje`) može da
objasni zašto nije tačan. Učenik to vidi u fioci čim ga izabere, a tekst odgovora se precrta.

**Vremenska osa:** u spec-u `osa: {od, do, trake: [{id, label, color}]}`. Zadaci sa datumom (`datum`,
stavke `poredjaj`, ili bilo koji zadatak sa `osa: {naziv, od, do?, traka?}`) posle odgovora stavljaju
događaj na učenikovu osu (pregled „Vremenska osa”). Isti `naziv` = jedna tačka, ma koji zadatak je
postavio; bledo = otkriven odgovor. Isti događaj u svim zadacima piši sa istim `naziv`/`od`/`do`.
Događaj koji knjiga datira samo delom veka dobija `oznaka: "kraj XVIII veka"` (reči knjige): na osi se
crta šrafirano, sa tom oznakom umesto godina (`od`/`do` ga samo približno smeštaju); `datum` ga ne sme tražiti.

**Moje znanje:** svaki pojam (`pojmovi`) ima nivo 0–4 (Leitner); tačno iz prve → nivo gore, vraća se
posle 1, 3, 7, 14 dana; greška → nazad na 0. Nova instanca izvlači do `sastav.ponavljanje`%
(podrazumevano 20) novih pitanja iz pojmova koji su na redu, po mogućstvu kroz drugu vrstu zadatka.

## Novi kviz

```bash
cp -r templates/lesson-quiz/ tools/{predmet}/{slug}/
cd tools/{predmet}/{slug}/ && mv spec.template.yaml spec.yaml   # popuni
python3 make.py
cd ../../.. && python3 scripts/regenerate_index.py
```

`load_spec` proverava: jedinstvene `id`, poznatu `vrsta`, bar jedan tačan odgovor (`zakljuci`
tačno jedan), ispravke za netačne tvrdnje, praznine u `dopuni`, ciljeve karte.
Bump `STATE_VERSION` u `lesson_quiz.py` kad se promeni oblik sačuvanog stanja (briše napredak).

## Slike iz udžbenika i zaštićena verzija

`iz_udzbenika.slika` pokazuje na isečak u privatnom `tools/{predmet}/_source/slike-{razred}/` (van
git-a). Javni kviz ga učitava lokalno; gde ga nema (GitHub Pages), umesto slike stoji link ka
zaštićenoj verziji. Zaštićena verzija (lozinka, šifrovano, slike ugrađene):

```bash
python3 scripts/build_zasticeno.py tools/{predmet}/{slug}    # → zasticeno/{predmet}/{slug}/
python3 scripts/regenerate_index.py                         # katalog dobija link
```

Lozinka je u macOS Keychain-u (`classroom-zasticeno`); pogledaj je sa
`security find-generic-password -s classroom-zasticeno -w`, promeni sa
`security add-generic-password -U -s classroom-zasticeno -a classroom -w 'NOVA'` pa ponovo pokreni skriptu.

Fioka „Iz udžbenika” vodi i na zaštićenu stranicu lekcije (`scripts/build_lekcije.py`): link na odeljak beleški
(`iz_udzbenika.odeljak`, inače po strani) i na stranu udžbenika; u zaštićenoj kopiji kviza fioka prikazuje i
beleške tog odeljka, a oba linka otvaraju taj deo lekcije (odeljak sa njegovim stranama, ili stranu) u
proširenoj fioci; „Otvori u lekciji” ga prikazuje u glavnoj koloni, gde je i cela lekcija (grupa „Lekcija” u
navigaciji). Stranice lekcija napravi pre zaštićenih kopija kvizova.

## Kviz iz banke pitanja

Svaki predmet ima banku po lekciji: `shared/banke/{nivo}/{razred}/{predmet}/{NN-slug}.yaml`
(`lekcija`, `naslov`, `pojmovi`, `delovi`, a geografija i `mesta`; id zadatka je jedinstven u predmetu, nove banke počinju sa `lNN-`). Proveri je sa
`python3 scripts/proveri_banku.py shared/banke/...`. Kviz je tada samo definicija: `spec.yaml` bez
`banka:`, sa `banka_lekcije: [3, 4, 5, 6, 10]`, `sastav` i `osa`. Svaki deo lekcije postaje deo kviza
(„3. Naslov”), instanca izvlači zadatke srazmerno veličini delova, a zaštićena kopija u navigaciji
ima grupu „Gradivo” sa svim izabranim lekcijama. Godine pre nove ere su negativni brojevi: učenik
upisuje broj i bira „pre n. e.” ili „n. e.”.

## Pitanje uz sliku ili kartu

Ako pitanje traži gledanje slike ili karte, zadatak dobija `slika_u_pitanju: true`, a slika je
`iz_udzbenika.slika`. Prikazuje se u glavnoj koloni ispod odgovora (potpis tek posle odgovora, da ne
otkrije rešenje); javna kopija umesto slike vodi na verziju sa slikama.
