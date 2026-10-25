# Istorija 7 — kviz za razumevanje (predlog)

Datum: 2026-10-25 · Status: **predlog, čeka odluke operatera**

Izvor: udžbenik istorije za 7. razred (1780–1918), str. 10–38 → `tools/istorija/_source/lekcije-7/`
(4 lekcije: 1.1 Osnovne odlike perioda 1780–1918, 1.2 Istorijski izvori, 2.1 Industrijska
revolucija, 2.2 Doba prosvetiteljstva; 203 pojma, 37 slika). Nedostaju str. 15, 20–27, 33, 39
(rezimei i pitanja na kraju lekcija; možda i lekcija 1.3).

## Polazište: šta zadržavamo

| Iz | Šta |
|---|---|
| Istorija 6 (`timeline-mcq-quiz`) | datum → događaj se pojavi na vremenskoj osi → pitanja o njemu |
| Geografija 7 (`lesson-quiz`) | lestvica pomoći (usmeri → suzi → iz lekcije → otkrij), bodovi 3/2/1/0, banka L/S/T izvučena 40/40/20, Učenje / Test / Ispravka, svaki test zabeležen + CSV, fioka „Saznaj više” sa „Iz udžbenika” i grafom pojmova |

Slabost geografskih banaka za ovaj cilj: mnogo zadataka proverava zapamćen broj ili ime
(„površina 88.499 km²”). Za istoriju težište pomeramo na **zašto**, **šta je iz čega proisteklo**
i **kako to znamo**.

## Novo: razumevanje

1. **Svaki pogrešan odgovor objašnjava sebe** (`zasto` po ponuđenom odgovoru): kad učenik izabere
   „Petar I je dobio izlaz na Crno more”, ne dobija samo ✗ nego „Crno more je osvojila Katarina II
   ratujući protiv Osmanlija; Petar je pobedio Švedsku i dobio Baltik”. Greška postaje lekcija.
2. **Vremenska osa lekcije** (iz istorije 6, sada u lesson-quiz): kartica „Osa” u glavnom delu;
   svaki tačno rešen zadatak sa datumom stavlja svoj događaj na osu, pa osa raste kako učenik uči.
   Vrste: `datum` (upiši godinu / opseg) i `poredjaj` (poređaj 3–5 događaja hronološki).
3. **Uzrok → posledica** (`lanac`): lanac od 3–4 karike sa jednom praznom karikom
   („pobeda nad Švedskom → ? → osnivanje Sankt Peterburga”). Lestvica pomoći = koraci rasuđivanja.
4. **Istorijski izvor** (`izvor`): kratak odlomak (sopstvenim rečima ili javno dobro) → ko piše,
   kakav je stav, šta izvor dokazuje a šta ne. U udžbeniku: Volter vs. Ruso, Fridrih o Volteru,
   „vojska koja je zaposela državu”.
5. **Uporedi** (`uporedi`): tvrdnje se razvrstavaju u A / B / oba / nijedan
   (Marija Terezija – Josif II, Monteskje – Ruso, Petar I – Katarina II).
6. **Ko sam ja?** (`ko_sam`): ličnost se otkriva trag po trag (kao „Gde sam?” na karti);
   ranije pogođeno = više bodova.
7. **Objasni svojim rečima** (`objasni`): učenik napiše jednu-dve rečenice, zatim vidi uzorni
   odgovor i spisak ključnih ideja i sam štiklira koje je naveo. Bez AI i bez servera.

## Novo: učvršćivanje kroz vreme

8. **Moje znanje** (po pojmu, preko više dana): svaki pojam ima nivo savladanosti (kutije 0–4,
   Leitnerov princip). Tačno iz prve → pojam ide kutiju gore i vraća se kasnije; greška → nazad u
   kutiju 0, vraća se već u sledećoj sesiji. Nova sesija Učenja izvlači ~polovinu zadataka iz pojmova
   koji su „na redu”, ostatak iz banke 40/40/20. Pregled „Moje znanje” = pojmovi po lekciji sa
   nivoom.
9. **Isti pojam, drugi ugao**: kad se pojam vrati, dolazi kroz *drugu vrstu* zadatka nego prošli put
   (izbor → lanac → objasni), da učenik ne pamti odgovor nego razume pojam.
10. **Ponavljanje poglavlja**: test koji meša sve lekcije poglavlja (interleaving).

## Arhitektura

Proširiti `shared/python/lesson_quiz.py` (nove `vrsta`, kartica Osa, Moje znanje, `zasto`) —
ne praviti treći tip; geografija dobija sve automatski (CLAUDE.md: bez dupliranja render logike).
`STATE_VERSION` 3 → 4 (novi oblik stanja: savladanost pojmova).
Kvizovi: `tools/istorija/{lekcija}-kviz/` (spec.yaml + banka.yaml + make.py), `nivo: osnovna`,
`razred: 7`, `lekcije: [n]`; kurikulum `shared/kurikulum/osnovna/7/istorija.yaml`; zaštićene kopije
sa slikama preko `scripts/build_zasticeno.py`.

## Otvorena pitanja

- Opseg: 4 lekcije sada, ili prvo doslikati str. 15, 20–27, 33, 39?
- Koje od novih mehanika 1–10 ulaze u prvu verziju?
- `objasni`: samoprocena se boduje (npr. 0–2) ili samo beleži?
- Lekcija 1.3 (ako postoji na str. 20–27) → prenumerisanje 2.1/2.2.
