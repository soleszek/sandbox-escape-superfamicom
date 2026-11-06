ifeq ($(strip $(PVSNESLIB_HOME)),)
$(error "Ustaw zmienna PVSNESLIB_HOME: https://github.com/alekmaul/pvsneslib/wiki/Installation")
endif

# Nazwa ROM-u. Pliki MSU-1 musza sie nazywac tak samo: superfamipong.msu, superfamipong-1.pcm
export ROMNAME  := superfamipong
export ROMTITLE := SANDBOX ESCAPE

# Kod regionu w naglowku: 00 = Japonia (Super Famicom, NTSC 60 Hz)
export COUNTRY  := 00

# Kartridz z pamiecia SRAM i bateria (02), 2 KB SRAM (01) - zapis odblokowanych mocy.
# FXPAK Pro przechowuje ja na karcie SD jako superfamipong.srm
export CARTRIDGETYPE := 02
export SRAMSIZE      := 01
export ROMSIZE       := 0A    # 1 MB (plansza Lucifero); od banku 8 lezy muzyka
export ROMBANKS      := 32

# Muzyka: moduly .it -> bank dzwiekow (smconv), od banku ROM 8
AUDIOFILES := music/ruden.it music/malten.it music/waller.it music/doppler.it music/changero.it \
              music/chronos.it music/magneton.it music/telementor.it music/blinker.it music/kimantero.it music/tango.it music/lucifero.it
export SOUNDBANK := soundbank

# FastROM: kod z bankow $80+, rejestr $420D wlaczany przy starcie (biblioteka LoROM_FastROM)
FASTROM=1
include ${PVSNESLIB_HOME}/devkitsnes/snes_rules

SMCONVFLAGS := -s -o $(SOUNDBANK) -V -b 8
musics: $(SOUNDBANK).obj

.PHONY: bitmaps sounds all

#---------------------------------------------------------------------------------
all: bitmaps sounds musics $(ROMNAME).sfc

clean: cleanBuildRes cleanRom cleanGfx cleanAudio
	@rm -f *.brr

#---------------------------------------------------------------------------------
# Grafiki tla (BG1). -e = numer palety BG, -f = numer pierwszego kafelka w VRAM.
# Te liczby musza sie zgadzac ze stalymi PAL_* i TILES_* w superfamipong.c
GFXBG = $(GFXCONV) -s 8 -o 16 -u 16 -p -m -t png

court.pic: court.png
	$(GFXBG) -e 1 -f 0 -i $<
logo.pic: logo.png
	$(GFXBG) -e 4 -f 16 -i $<
joybot32.pic: joybot32.png
	$(GFXBG) -e 2 -f 256 -i $<
robot32.pic: robot32.png
	$(GFXBG) -e 5 -f 272 -i $<
icons.pic: icons.png
	$(GFXBG) -e 6 -f 288 -i $<
minicons.pic: minicons.png
	$(GFXBG) -e 6 -f 348 -i $<
bar.pic: bar.png
	$(GFXBG) -e 7 -f 364 -i $<
blocks.pic: blocks.png
	$(GFXBG) -e 1 -f 372 -i $<
dlg.pic: dlg.png
	$(GFXBG) -e 1 -f 376 -i $<

# Awatary: Muggy zawsze w slocie 388/424 (paleta 2), strażnik w slocie 440/476 (paleta 3)
muggy48.pic: muggy48.png
	$(GFXBG) -e 2 -f 388 -i $<
muggy32.pic: muggy32.png
	$(GFXBG) -e 2 -f 424 -i $<
%48.pic: %48.png
	$(GFXBG) -e 3 -f 440 -i $<
%32.pic: %32.png
	$(GFXBG) -e 3 -f 476 -i $<

# Sprite'y: 0 = gora paletki, 1 = srodek, 2 = pilka, 3..7 = ogon komety, 8 = rog kursora
sprites.pic: sprites.png
	$(GFXCONV) -s 8 -o 16 -u 16 -p -t png -i $<

bitmaps: court.pic logo.pic \
         robot32.pic joybot32.pic icons.pic minicons.pic bar.pic sprites.pic \
         blocks.pic dlg.pic muggy48.pic muggy32.pic ruden48.pic ruden32.pic \
         malten48.pic malten32.pic waller48.pic waller32.pic doppler48.pic doppler32.pic \
         changero48.pic changero32.pic chronos48.pic chronos32.pic magneton48.pic magneton32.pic \
         telementor48.pic telementor32.pic blinker48.pic blinker32.pic kimantero48.pic kimantero32.pic

#---------------------------------------------------------------------------------
# Dzwieki: WAV 12 kHz -> BRR (regula %.brr: %.wav jest w snes_rules)
sounds: tada.brr tok1.brr tok2.brr tokwall.brr fanfare.brr sad.brr \
        tick.brr confirm.brr ready.brr arm.brr super.brr curve.brr zigzag.brr ghost.brr thunder.brr
