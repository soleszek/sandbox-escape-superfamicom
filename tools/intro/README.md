# Intro (po wlaczeniu konsoli) - generatory

Wszystko, co widac i slychac w intro, powstaje z tych skryptow (Python 3, Pillow, numpy).
Gotowe wyniki leza juz w katalogu gry, wiec do zbudowania ROM-u wystarczy `make`.
Skrypty trzeba uruchomic tylko po zmianie intro. Polecenia wpisuj w katalogu gry:

```
python3 tools/intro/scene1.py all
python3 tools/intro/conv_all.py
python3 tools/intro/build_intro.py
python3 tools/make_intro_music.py music/intro.it $(cat tools/intro/work/music_bars.txt)
python3 tools/make_intro_sfx.py
make
```

1. `scene1.py all` - rysuje 11 klatek sceny 1 (mezczyzna przy laptopie) do `tools/intro/work/`.
2. `conv_all.py` - zamienia scene 1, cztery przebitki (z klatkami animacji) i ekran z logo MaiFlow
   na kafelki i palety SNES (kilka minut). Wynik: `tools/intro/work/conv.pkl`.
3. `build_intro.py` - sklada cale intro: os czasu klatka po klatce (zapisy grafiki w VBlank,
   przesuniecia warstw, dzwieki), okno czatu, napis z krzykiem. Wynik w katalogu gry:
   `intro_data.as` (dolaczany w `data.asm`) i `intro_0.bin` ... `intro_6.bin`.
   Zapisuje tez numer taktu muzyki, na ktory wypada "Enough!" (`work/music_bars.txt`).
4. `make_intro_music.py` - muzyka intro (`music/intro.it`) dopasowana do tego taktu oraz
   `intro_music.h` (miejsce w utworze, od ktorego gra ekran startowy).
5. `make_intro_sfx.py` - dzwieki intro (`ithud.wav`, `icrash.wav`, `ishout.wav`, `iboom.wav`).

Pliki:
- `logo.py` - ekran producenta (logo kanalu w kole z `maiflow_logo.png`, napis wlasna gruba
  czcionka 8x8), `scene1.py` - scena 1, `flashes.py` - przebitki, `chat.py` - wyglad okna czatu,
- `snesconv.py` - kafelki i palety dla obrazow (grupowanie kolorow), `exactconv.py` - dla obrazow
  o dokladnych kolorach (tekst, czat),
- `font/` - czcionki pikselowe (X11 misc fonts, przerobione na format Pillow).
- `work/` - pliki posrednie, generowane (nie trzeba ich trzymac w repozytorium).

Odtwarzanie w grze: `run_intro()` w `superfamipong.c` czyta strumien polecen `intro_cmd` - jedna
porcja na klatke, zapisy kanalem DMA 7 zaraz po poczatku VBlank. Najpierw logo (7 s, w ciszy,
bez pomijania), potem intro. WATCH INTRO w SETTINGS przewija logo przy wygaszonym ekranie
(znacznik konca logo w strumieniu) i zaczyna od sekundy czerni przed scena 1.
