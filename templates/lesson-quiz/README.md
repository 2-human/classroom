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

Režimi: **Učenje** (pomoć) · **Test** (bez pomoći, isto bodovanje) · **Ispravka** (posle testa:
zadaci koji nisu rešeni iz prve, sa pomoći; rezultat testa se ne menja). U Učenju meni ⋯ ima
„Ponovi otkrivene”.

## Banka, težina i sastav

- **Banka:** svi zadaci lekcije — u `spec.yaml` (`delovi`) ili, za veliku banku, u posebnom fajlu
  (`banka: banka.yaml` sa `delovi` i `mesta`). Cilj: iscrpeti lekciju — svaka činjenica, broj, pojam,
  uzrok/posledica i mesto na karti bar jednom; svaka vrsta zadatka u sve tri težine.
- **Težina** (`tezina`, obavezno): `lako` — jedna istaknuta činjenica, očigledni pogrešni odgovori;
  `srednje` — detalji, brojevi, dve činjenice, uverljivi pogrešni odgovori; `tesko` — zaključivanje,
  poređenje, primena, dopuna bez banke reči, male države i mesta na karti. U listi zadataka oznake
  **L / S / T**, legenda sa brojem po težini.
- **Sastav:** i sesija Učenja i svaki test se izvlače nanovo iz banke: `sastav.ucenje` / `sastav.test`
  zadataka u odnosu `sastav.odnos` (podrazumevano 40/40/20), ravnomerno po delovima lekcije pa po
  vrstama. Banci se pri svakom izvlačenju pridružuju i zadaci generisani iz `baza.drzave`
  (`sastav.generisano`; njihova težina dolazi od `tezina` države). „Počni učenje ispočetka” = nova sesija.

## Test: svaki zabeležen

- **Beleženje:** svaki pokušaj (zadaci, svaki odgovor učenika po zadatku, bodovi, Ispravka, ime ako
  ga upiše) čuva se u pregledaču (localStorage). „Moji testovi” u navigaciji → **Pregled rada**
  (svaki zadatak: odgovori učenika ✓/✗ i tačan odgovor) i **Preuzmi (CSV)** za nastavnika (jedan red po
  zadatku; „Preuzmi sve testove” na ekranu Novi test). Bez servera i naloga — rezultati su na uređaju
  na kome je test rađen.

## Vrste zadataka

| vrsta | šta | posebno |
|---|---|---|
| `izbor` | jedan ili više tačnih | pogrešni odgovori se precrtavaju |
| `tacno_netacno` | tačno / netačno | netačna tvrdnja traži i ispravku (`ispravke`); pogrešan izbor kod tačne tvrdnje je otkriva |
| `dopuni` | praznine `{{odgovor\|alternativa}}` | `ponudjene` = banka reči; tačne praznine se zaključaju |
| `povezi` | `parovi` levo ↔ desno | desna kolona se meša |
| `zakljuci` | rasuđivanje, jedan tačan | `pomoc` piši kao korake („Korak 1: …”) |
| `karta_klik` | klikni državu (`drzava: ISO3`) ili mesto (`mesto: slug`) | u Učenju promašaj kaže koja je država / koliko km |
| `gde_sam` | `tragovi` jedan po jedan, klik na kartu | svaki pogrešan klik ili „Još jedan trag” = sledeći trag |
| `datum` | godina (`godina`) ili raspon (`od`/`do`) događaja `dogadjaj` | pogrešna godina kaže ranije/kasnije i koliko blizu; stavlja događaj na osu |
| `poredjaj` | poređaj `stavke` hronološki (u spec-u u tačnom redu, svaka sa `godina`) | tačne pozicije se zaključaju; sve stavke idu na osu |
| `lanac` | uzrok → posledica: `karike` sa jednom praznom (`praznina`) | biraš kariku iz `odgovori`; `pomoc` kao koraci rasuđivanja |
| `izvor` | odlomak `izvor: {autor, naslov, tekst, napomena}` + pitanje | odlomak sopstvenim rečima ili javno dobro, uz napomenu |
| `uporedi` | razvrstaj `tvrdnje` u `a` / `b` / oba / nijedan | svaka tvrdnja ima `odgovor` i `zasto` |
| `ko_sam` | ličnost iz `tragova` jedan po jedan, odgovor iz `odgovori` | svaki trag ili greška = manje bodova |
| `objasni` | učenik napiše odgovor, pa vidi `uzor` i štiklira `ideje` | samoprocena (sve → 3, bar pola → 2, neke → 1); nema ga u testu |

**Zašto (`zasto`):** svaki pogrešan ponuđeni odgovor (`odgovori`, `ispravke`, `uporedi.tvrdnje`) može da
objasni zašto nije tačan. Učenik to vidi u fioci čim ga izabere, a tekst odgovora se precrta.

**Vremenska osa:** u spec-u `osa: {od, do, trake: [{id, label, color}]}`. Zadaci sa datumom (`datum`,
stavke `poredjaj`, ili bilo koji zadatak sa `osa: {naziv, od, do?, traka?}`) posle odgovora stavljaju
događaj na učenikovu osu (pregled „Vremenska osa”). Isti `naziv` = jedna tačka, ma koji zadatak je
postavio; bledo = otkriven odgovor. Isti događaj u svim zadacima piši sa istim `naziv`/`od`/`do`.

**Moje znanje:** svaki pojam (`pojmovi`) ima nivo 0–4 (Leitner); tačno iz prve → nivo gore, vraća se
posle 1, 3, 7, 14 dana; greška → nazad na 0. Nova sesija Učenja izvlači `sastav.ponavljanje`%
(podrazumevano 50) zadataka iz pojmova koji su na redu, po mogućstvu kroz drugu vrstu zadatka nego
prošli put (oznaka ↻). Ispravka ne menja nivo.

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
