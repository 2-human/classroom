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
