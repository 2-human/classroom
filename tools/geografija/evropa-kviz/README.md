# Evropa — geografski kviz

42 geografska pojma na karti Evrope: mora, moreuzi, planinski venci, reke, ostrva, poluostrva. Učenik upisuje broj pojma sa spiska u kvadrat na pravoj lokaciji na karti. Sistem broji greške i traži ponovan unos dok ne bude tačno.

## Kako koristiti

**U browseru (najlakše):** otvori `index.html` duplim klikom — radi i bez interneta.

**Na GitHub Pages:** [classroom.tnosugar.github.io/tools/geografija/evropa-kviz/](https://classroom.tnosugar.github.io/tools/geografija/evropa-kviz/) *(dostupno kad postane public)*

**Za štampu:**
- `radna.pdf` — verzija za učenika, prazni krugovi
- `resenja.pdf` — verzija sa odgovorima, krugovi sa upisanim brojevima

## Funkcionalnost

- Klik u kvadrat, upiši broj pojma, Enter ili klik van polja → provera.
- Tačno → polje pozeleni, zaključa se.
- Pogrešno → polje crveno, zatrese se, traži ponovan unos. Broj grešaka po polju se prikazuje u uglu.
- Ukupno tačnih i ukupno grešaka na vrhu.
- Zumiranje: dugmad +/− gore desno, točkić miša, dvoklik, prevuci za pomeranje. Pinch na tabletu/telefonu.
- **Raspored (hub, tri panela):** levo spisak pojmova sa pretragom i brojačem, u sredini karta, desno fioka sa opisom (Učenje) ili pitanjima (Test) koja se otvara po potrebi. Gore putanja `classroom › Geografija › Evropa` vodi nazad na katalog.
- Reset: "Počni ispočetka" u meniju ⋯.
- **Mod izbora pitanja:** Selektor u meniju ⋯ ("Pitanja: Sve (42) / 20 nasumičnih / 10 nasumičnih / 5 nasumičnih") dozvoljava kraći kviz sa nasumično odabranim podskupom termina. Default je "Sve (42)", pa se ponašanje ne menja ako nastavnik ništa ne pipa.
- **Sačuvan progres:** Stanje (uneseni odgovori, broj grešaka, izabrani mod) se automatski čuva u browser-u (localStorage). Ako učenik slučajno osveži stranicu, sve se vrati gde je bilo, sa žutim banerom "Nastavak prethodne sesije". "Počni ispočetka" briše sačuvano stanje.
- **Rezultati (Test):** kartica "Rezultati" iznad karte — tabela po pojmu (lociranje, greške, pitanja, bonus). AI analiza (nastavnikov Claude API ključ) se vidi samo kad se stranica otvori sa `?nastavnik` (ili `#nastavnik`) na kraju adrese.
- **CSV export:** Po završetku kviza u kartici "Rezultati" pojavi se dugme "Preuzmi rezultate (CSV)" — preuzme se fajl `rezultati-YYYY-MM-DD.csv` sa kolonama `id, name, correct, miss_count`. Korisno ako nastavnik želi izveštaj po učeniku.
- **Štampa iz browser-a:** Ctrl+P / Cmd+P daje čistu print verziju (bez dugmadi, bez zoom kontrola, statički layout). PDF generator je i dalje dostupan ako je potreban (`radna.pdf` + `resenja.pdf` u istom folderu).

## Kako se regeneriše

Ako menjaš `spec.yaml` (dodaješ termin, menjaš koordinatu, prepravljaš tekst), rebuild komandom:

```bash
python3 make.py
```

Generišu se tri fajla u istom folderu (overwrite svaki put):
- `index.html` — interaktivan kviz
- `radna.pdf` — printable
- `resenja.pdf` — printable

Zavisnosti: `pip install pyyaml matplotlib numpy`.

## Struktura

| Fajl | Tip | Opis |
|---|---|---|
| `spec.yaml` | source | 42 termina + koordinate + geometrija planina/reka + UI tekstovi |
| `make.py` | source | thin orchestrator — čita spec.yaml, poziva shared/python/labeled_location_quiz |
| `index.html` | generated | interaktivan kviz |
| `radna.pdf` | generated | PDF za učenika |
| `resenja.pdf` | generated | PDF za nastavnika (ključ) |

Render logika živi u `../../../shared/python/labeled_location_quiz.py`. Ovaj alat je referentna instanca šablona `labeled-location-quiz`; vidi `../../../templates/labeled-location-quiz/README.md` za pravljenje sličnih kvizova.

## Vidi takođe

- `../../../README.md` — pregled celog repo-a.
- `../../../templates/labeled-location-quiz/README.md` — kako napraviti sledeći ovakav kviz (Azija, Afrika, Srbija po opštinama, itd.).
