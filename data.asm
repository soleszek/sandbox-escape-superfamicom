.include "hdr.asm"

; Grafiki wygenerowane przez gfx4snes (pliki *_data.as tworzy make)
.section ".rodata_gfx1" superfree
.include "court_data.as"
.include "logo_data.as"
.include "sprites_data.as"
.ends

.section ".rodata_gfx2" superfree
.include "robot32_data.as"
.include "joybot32_data.as"
.include "icons_data.as"
.include "minicons_data.as"
.include "bar_data.as"
.include "blocks_data.as"
.include "dlg_data.as"
.ends

; Awatary trybu fabularnego
.section ".rodata_gfx3" superfree
.include "muggy48_data.as"
.include "muggy32_data.as"
.include "ruden48_data.as"
.include "ruden32_data.as"
.include "malten48_data.as"
.include "malten32_data.as"
.include "waller48_data.as"
.include "waller32_data.as"
.ends

.section ".rodata_gfx4" superfree
.include "doppler48_data.as"
.include "doppler32_data.as"
.include "changero48_data.as"
.include "changero32_data.as"
.include "chronos48_data.as"
.include "chronos32_data.as"
.ends

.section ".rodata_gfx5" superfree
.include "magneton48_data.as"
.include "magneton32_data.as"
.include "telementor48_data.as"
.include "telementor32_data.as"
.include "blinker48_data.as"
.include "blinker32_data.as"
.include "kimantero48_data.as"
.include "kimantero32_data.as"
.ends

; Burza w ostatniej walce: deszcz (BG3) i pioruny
.section ".rodata_storm" superfree
rain_til:
.incbin "rain.til"
rain_tilend:
rain_map:
.incbin "rain.map"
rain_mapend:
bolt_til:
.incbin "bolt.til"
bolt_tilend:
.ends

.section ".rodata_sfx_thunder" superfree
snd_thunder:
.incbin "thunder.brr"
snd_thunder_end:
.ends

; Dzwieki BRR. Kazdy bank ROM ma 32 KB, wiec dlugie dzwieki maja osobne sekcje.
.section ".rodata_sfx1" superfree
snd_tada:
.incbin "tada.brr"
snd_tada_end:
snd_tok1:
.incbin "tok1.brr"
snd_tok1_end:
snd_tok2:
.incbin "tok2.brr"
snd_tok2_end:
snd_tokwall:
.incbin "tokwall.brr"
snd_tokwall_end:
.ends

.section ".rodata_sfx2" superfree
snd_fanfare:
.incbin "fanfare.brr"
snd_fanfare_end:
.ends

.section ".rodata_sfx3" superfree
snd_sad:
.incbin "sad.brr"
snd_sad_end:
.ends

.section ".rodata_sfx4" superfree
snd_tick:
.incbin "tick.brr"
snd_tick_end:
snd_confirm:
.incbin "confirm.brr"
snd_confirm_end:
snd_ready:
.incbin "ready.brr"
snd_ready_end:
snd_arm:
.incbin "arm.brr"
snd_arm_end:
snd_super:
.incbin "super.brr"
snd_super_end:
snd_curve:
.incbin "curve.brr"
snd_curve_end:
snd_zigzag:
.incbin "zigzag.brr"
snd_zigzag_end:
snd_ghost:
.incbin "ghost.brr"
snd_ghost_end:
.ends

; ---------------------------------------------------------------------------
; Szybkie rysowanie paletki. Kod z kompilatora C zajmowal na to ok. 30 linii obrazu
; na kazda paletke; ta procedura robi to samo w ulamku tego czasu.
.ifdef FASTROM
.BASE $00   ; RAM: bez przesuniecia $80 (FastROM dotyczy tylko ROM)
.endif
.RAMSECTION ".pad_vars" BANK $7E SLOT 2
pad_n		DW
pad_yy		DW
pad_at		DW
svis		DSB 96		; 1 = sprite jest na ekranie (uzywane takze przez kod C)
.ENDS
.ifdef FASTROM
.BASE $80
.endif

.section ".pad_text" superfree
; void pad_asm(u16 id, u16 sx, s16 y, u16 h, u16 attr)
; argumenty (po php/phx/phy): id 9,s  sx 11,s  y 13,s  h 15,s  attr 17,s
pad_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	15,s		; n = (h + 7) / 8 segmentow
	clc
	adc	#7
	lsr	a
	lsr	a
	lsr	a
	sta.l	pad_n
	lda	9,s		; X = przesuniecie w OAM
	tax
	ldy	#0		; Y = numer segmentu
@seg:
	tya
	cmp.l	pad_n
	bcs	@hide		; segment nieuzywany
	lda	17,s
	sta.l	pad_at
	tya
	inc	a
	cmp.l	pad_n
	bne	@notlast
	lda	13,s		; ostatni segment: yy = y + h - 8, kafelek odbity w pionie
	clc
	adc	15,s
	sec
	sbc	#8
	sta.l	pad_yy
	lda.l	pad_at
	ora	#$0080
	sta.l	pad_at
	bra	@check
@notlast:
	tya			; yy = y + 8 * i
	asl	a
	asl	a
	asl	a
	clc
	adc	13,s
	sta.l	pad_yy
@check:
	lda.l	pad_yy		; poza boiskiem u gory (Changero za krawedzia)?
	sec
	sbc	#40
	beq	@hide
	bmi	@hide
	lda.l	pad_yy		; ...albo na dole?
	sec
	sbc	#200
	bpl	@hide
	lda.l	pad_yy		; slowo 0: x (mlodszy bajt), y (starszy)
	xba
	and	#$FF00
	ora	11,s
	sta.l	oamMemory,x
	lda.l	pad_at		; slowo 1: kafelek (mlodszy), atrybuty (starszy)
	xba
	and	#$FF00
	sta.l	pad_yy
	tya
	beq	@top
	inc	a
	cmp.l	pad_n
	beq	@top
	lda	#1		; srodkowy segment
	bra	@tile
@top:
	lda	#0		; gorny i dolny segment
@tile:
	ora.l	pad_yy
	sta.l	oamMemory+2,x
	bra	@next
@hide:
	sep	#$20
.ACCU 8
	lda	#240
	sta.l	oamMemory+1,x
	rep	#$20
.ACCU 16
@next:
	inx
	inx
	inx
	inx
	iny
	cpy	#10
	beq	@segdone
	jmp	@seg
@segdone:
	lda	9,s		; wszystkie 10 sprite'ow paletki oznaczone jako widoczne
	lsr	a
	lsr	a
	tax
	ldy	#10
	sep	#$20
.ACCU 8
	lda	#1
@vis:
	sta.l	svis,x
	inx
	dey
	bne	@vis
	rep	#$20
.ACCU 16
	ply
	plx
	plp
	rtl
.ends

; ---------------------------------------------------------------------------
; Dodatkowe pilki (SPLIT, do 3): ruch z odbiciem od band i rysowanie z ogonem.
; Kod z kompilatora C zajmowal na to ok. 40 linii obrazu na pilke.
.ifdef FASTROM
.BASE $00   ; RAM: bez przesuniecia $80 (FastROM dotyczy tylko ROM)
.endif
.RAMSECTION ".xb_vars" BANK $7E SLOT 2
xm_pbx		DW	; poprzednia pozycja (piksele) - dla kolizji w C
xm_pby		DW
xm_flags	DW	; bit 0 = odbicie od bandy, bit 1 = przewiniecie w lewo, bit 2 = w prawo
xm_old		DW
xm_k2		DW	; k * 2 (tablice slow)
xm_k16		DW	; k * 16 (historia)
xm_t		DW
xm_step		DW
xm_i		DW
xm_sb		DW
xm_st		DW
.ENDS
.ifdef FASTROM
.BASE $80
.endif

.section ".xb_text" superfree
; void xb_move_asm(u16 k)
xb_move_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	9,s
	asl	a
	sta.l	xm_k2
	asl	a
	asl	a
	asl	a
	sta.l	xm_k16
	lda.l	xm_k2
	tax
	lda	#0
	sta.l	xm_flags
	lda.l	xb_x,x		; poprzednia pozycja w pikselach
	xba
	and	#$00FF
	sta.l	xm_pbx
	lda.l	xb_y,x
	xba
	and	#$00FF
	sta.l	xm_pby
	lda.l	xb_x,x		; x += vx
	sta.l	xm_old
	clc
	adc.l	xb_vx,x
	sta.l	xb_x,x
	lda.l	xb_vx,x
	beq	@xdone
	bmi	@xneg
	lda.l	xb_x,x		; vx > 0: przewiniecie przez krawedz, gdy nowe < stare
	cmp.l	xm_old
	bcs	@xdone
	lda	#4
	sta.l	xm_flags
	bra	@xdone
@xneg:
	lda.l	xm_old		; vx < 0: przewiniecie, gdy nowe > stare
	cmp.l	xb_x,x
	bcs	@xdone
	lda	#2
	sta.l	xm_flags
@xdone:
	lda.l	xb_y,x		; y += vy
	clc
	adc.l	xb_vy,x
	sta.l	xb_y,x
	xba
	and	#$00FF
	cmp	#48		; FIELD_TOP
	bcs	@nottop
	lda	#$3000		; FP(48)
	bra	@bounce
@nottop:
	cmp	#193		; ponizej FIELD_BOTTOM - BALL_SIZE (192)?
	bcc	@ydone
	lda	#$C000		; FP(192)
@bounce:
	sta.l	xb_y,x
	lda	#0
	sec
	sbc.l	xb_vy,x
	sta.l	xb_vy,x
	lda.l	xm_flags
	ora	#1
	sta.l	xm_flags
@ydone:
	lda.l	xb_x,x		; historia pozycji (ogon), indeks (hist_pos - 1) & 15
	xba
	and	#$00FF
	sta.l	xm_t
	lda.l	xb_y,x
	and	#$FF00
	ora.l	xm_t
	sta.l	xm_t		; mlodszy bajt x, starszy y
	lda.l	hist_pos
	and	#$00FF
	dec	a
	and	#$000F
	clc
	adc.l	xm_k16
	tax
	sep	#$20
.ACCU 8
	lda.l	xm_t
	sta.l	xh_x,x
	lda.l	xm_t+1
	sta.l	xh_y,x
	rep	#$20
.ACCU 16
	ply
	plx
	plp
	rtl

; void xb_draw_asm(u16 k, u16 sb, u16 st)  - pilka (sprite sb) i ogon (sprite'y st..st+16)
xb_draw_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	9,s
	asl	a
	sta.l	xm_k2
	asl	a
	asl	a
	asl	a
	sta.l	xm_k16
	lda	11,s
	sta.l	xm_sb
	lda	13,s
	sta.l	xm_st
	lda	9,s		; --- pilka ---
	tax
	lda.l	xb_on,x
	and	#$00FF
	beq	@ballhide
	lda.l	xm_k2
	tax
	lda.l	xb_x,x
	xba
	and	#$00FF
	jsr	_xb_clampx
	sta.l	xm_t
	lda.l	xb_y,x
	and	#$FF00
	ora.l	xm_t
	pha
	lda.l	xm_sb
	tax
	pla
	sta.l	oamMemory,x
	lda	#$3002		; kafelek TILE_BALL, atrybuty SPR_ATTR(0,0,0)
	sta.l	oamMemory+2,x
	txa
	lsr	a
	lsr	a
	tax
	sep	#$20
.ACCU 8
	lda	#1
	sta.l	svis,x
	rep	#$20
.ACCU 16
	bra	@tail
@ballhide:
	lda.l	xm_sb
	jsr	_xb_hideid
@tail:
	lda	#2		; ogon: zawsze pozycje co 2 klatki (jak przy glownej pilce)
	sta.l	xm_step
	lda	#0
	sta.l	xm_i
@tloop:
	lda	9,s		; segment i widoczny, gdy i < xtail[k]
	tax
	lda.l	xtail,x
	and	#$00FF
	cmp.l	xm_i
	beq	@thide
	bcc	@thide
	lda.l	xm_i		; h = (hist_pos - 1 - step * (i + 1)) & 15
	inc	a
	sta.l	xm_t
	lda.l	xm_step
	cmp	#1
	beq	@one
	lda.l	xm_t
	asl	a
	sta.l	xm_t
@one:
	lda.l	hist_pos
	and	#$00FF
	dec	a
	sec
	sbc.l	xm_t
	and	#$000F
	clc
	adc.l	xm_k16
	tax
	lda.l	xh_x,x
	and	#$00FF
	jsr	_xb_clampx
	sta.l	xm_t
	lda.l	xh_y,x
	xba
	and	#$FF00
	ora.l	xm_t
	pha
	lda.l	xm_i
	asl	a
	asl	a
	clc
	adc.l	xm_st
	tax
	pla
	sta.l	oamMemory,x
	lda.l	xm_i
	clc
	adc	#$3803		; kafelek TILE_TAIL + i, atrybuty SPR_ATTR(4,0,0)
	sta.l	oamMemory+2,x
	txa
	lsr	a
	lsr	a
	tax
	sep	#$20
.ACCU 8
	lda	#1
	sta.l	svis,x
	rep	#$20
.ACCU 16
	bra	@tnext
@thide:
	lda.l	xm_i
	asl	a
	asl	a
	clc
	adc.l	xm_st
	jsr	_xb_hideid
@tnext:
	lda.l	xm_i
	inc	a
	sta.l	xm_i
	cmp	#5		; TAIL_LEN
	beq	@tdone
	jmp	@tloop
@tdone:
	ply
	plx
	plp
	rtl

; void tail_draw_asm(void): ogon komety glownej pilki (sprite'y SPR_TAIL..+16) z hist_x/hist_y -
; to samo co petla w draw_sprites, ktora w C zajmowala ok. 25 linii obrazu
tail_draw_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#0
	sta.l	xm_i
@tl:
	lda.l	tail_len		; segment i widoczny, gdy i < tail_len
	and	#$00FF
	cmp.l	xm_i
	beq	@hj
	bcs	@vis
@hj:
	jmp	@th
@vis:
	lda.l	xm_i			; h = (hist_pos - 1 - 2 * (i + 1)) & 15
	inc	a
	asl	a
	sta.l	xm_t
	lda.l	hist_pos
	and	#$00FF
	dec	a
	sec
	sbc.l	xm_t
	and	#$000F
	tax
	lda.l	hist_x,x
	and	#$00FF
	jsr	_xb_clampx
	sta.l	xm_t
	lda.l	hist_y,x
	xba
	and	#$FF00
	ora.l	xm_t
	pha
	lda.l	xm_i
	asl	a
	asl	a
	clc
	adc	#92			; SPR_TAIL
	tax
	pla
	sta.l	oamMemory,x
	lda.l	xm_i
	clc
	adc	#$3803			; kafelek TILE_TAIL + i, atrybuty SPR_ATTR(4,0,0)
	sta.l	oamMemory+2,x
	txa
	lsr	a
	lsr	a
	tax
	sep	#$20
.ACCU 8
	lda	#1
	sta.l	svis,x
	rep	#$20
.ACCU 16
	bra	@tn
@th:
	lda.l	xm_i
	asl	a
	asl	a
	clc
	adc	#92
	jsr	_xb_hideid
@tn:
	lda.l	xm_i
	inc	a
	sta.l	xm_i
	cmp	#5			; TAIL_LEN
	bcs	@td
	jmp	@tl
@td:
	ply
	plx
	plp
	rtl

; A = x (0..255): dodaje przesuniecie trzesienia ekranu i przycina do 0..255
_xb_clampx:
	clc
	adc.l	spr_dx
	bpl	@pos
	lda	#0
	rts
@pos:
	cmp	#256
	bcc	@ok
	lda	#255
@ok:
	rts

; A = numer sprite'a w OAM: ukrywa go, jesli jest widoczny
_xb_hideid:
	sta.l	xm_t
	lsr	a
	lsr	a
	tax
	sep	#$20
.ACCU 8
	lda.l	svis,x
	beq	@hdone
	lda	#0
	sta.l	svis,x
	rep	#$20
.ACCU 16
	lda.l	xm_t
	tax
	sep	#$20
.ACCU 8
	lda	#240
	sta.l	oamMemory+1,x
@hdone:
	rep	#$20
.ACCU 16
	rts
.ends

; Tla aren: Ruden (kurz, ogry, gradient) i Malten (mgla, gradient)
.section ".rodata_arena1" superfree
ruden_dust_til:
.incbin "ruden_dust.til"
ruden_dust_tilend:
ruden_dust_map:
.incbin "ruden_dust.map"
ruden_crowd_til:
.incbin "ruden_crowd.til"
ruden_crowd_tilend:
ruden_crowd_map:
.incbin "ruden_crowd.map"
ruden_grad:
.incbin "ruden_grad.bin"
ruden_gradend:
.ends

.section ".rodata_arena2" superfree
malten_fog_til:
.incbin "malten_fog.til"
malten_fog_tilend:
malten_fog_map:
.incbin "malten_fog.map"
malten_grad:
.incbin "malten_grad.bin"
malten_gradend:
.ends

; ---------------------------------------------------------------------------
; Falowanie mgly Maltena (HDMA posrednie): 32 wartosci przesuniecia = dryf + fala.
; Tablice wskaznikow dla kazdej fazy sa gotowe od wczytania walki, wiec co klatke
; liczymy tylko te 32 wartosci.  void wave_vals_asm(u16 base)  - argument 9,s
.section ".wave_text" superfree
wave_vals_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	9,s
	sta.l	pad_n		; dryf mgly
	ldx	#0		; X = numer wartosci (0..31)
	ldy	#0		; Y = przesuniecie w tablicy slow (0..62)
@lp:
	lda.l	wave_sine,x
	and	#$00FF
	cmp	#$0080		; rozszerzenie znaku
	bcc	@pos
	ora	#$FF00
@pos:
	clc
	adc.l	pad_n
	phx
	tyx
	sta.l	wave_val,x
	plx
	iny
	iny
	inx
	cpx	#32
	bne	@lp
	ply
	plx
	plp
	rtl
wave_sine:
	.db 0, 1, 2, 2, 3, 3, 4, 4, 4, 4, 4, 3, 3, 2, 2, 1, 0, $FF, $FE, $FE, $FD, $FD, $FC, $FC, $FC, $FC, $FC, $FD, $FD, $FE, $FE, $FF
.ends

; Arena Wallera: mur, pochodnie, nietoperze, gradient nocnego nieba
.section ".rodata_arena3" superfree
waller_wall_til:
.incbin "waller_wall.til"
waller_wall_tilend:
waller_wall_map:
.incbin "waller_wall.map"
waller_torch_til:
.incbin "waller_torch.til"
waller_torch_tilend:
bat_til:
.incbin "bat.til"
bat_tilend:
waller_grad:
.incbin "waller_grad.bin"
waller_gradend:
.ends

; ---------------------------------------------------------------------------
; Nietoperze Wallera: ruch i sprite'y (kod C byl za wolny - ok. 36 linii obrazu).
; void bats_asm(void); wynik: bat_n = liczba aktywnych nietoperzy (takze czekajacych)
.section ".bats_text" superfree
bats_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#0
	sta.l	bat_n
	ldx	#0			; X = numer nietoperza
@lp:
	lda.l	bat_on,x
	and	#$00FF
	bne	@on
	jmp	@next
@on:
	lda.l	bat_n
	inc	a
	sta.l	bat_n
	lda.l	bat_del,x		; czeka na swoja kolej wylotu?
	and	#$00FF
	beq	@fly
	sep	#$20
.ACCU 8
	dec	a
	sta.l	bat_del,x
	rep	#$20
.ACCU 16
	jmp	@next
@fly:
	phx
	txa
	asl	a
	tax				; X = 2*i (tablice slow)
	lda.l	bat_age,x
	inc	a
	sta.l	bat_age,x
	sta.l	bt_age
	lda.l	bat_x,x
	clc
	adc.l	bat_vx,x
	sta.l	bat_x,x
	cmp	#$8000			; x >> 4 z zachowaniem znaku
	ror	a
	cmp	#$8000
	ror	a
	cmp	#$8000
	ror	a
	cmp	#$8000
	ror	a
	sta.l	bt_x
	lda.l	bat_spr,x
	sta.l	bt_id
	plx				; X = i
	lda.l	bt_x			; poza ekranem (x < -16 lub x > 255)?
	clc
	adc	#16
	cmp	#272
	bcc	@alive
	sep	#$20
.ACCU 8
	lda	#0
	sta.l	bat_on,x
	rep	#$20
.ACCU 16
	jsr	bt_hide2
	jmp	@next
@alive:
	lda.l	bt_age			; wznoszenie: r = min(1,5 * wiek, rise)
	lsr	a
	clc
	adc.l	bt_age
	sta.l	bt_r
	lda.l	bat_rise,x
	and	#$00FF
	cmp.l	bt_r
	bcs	@nocap
	sta.l	bt_r
@nocap:
	lda.l	bat_ph,x		; kolysanie: bob[((wiek >> 1) + faza) & 15]
	and	#$00FF
	sta.l	bt_t
	lda.l	bt_age
	lsr	a
	clc
	adc.l	bt_t
	and	#$000F
	phx
	tax
	lda.l	bat_bob,x
	and	#$00FF
	cmp	#$0080
	bcc	@bpos
	ora	#$FF00
@bpos:
	plx
	sta.l	bt_t
	lda.l	bat_sy			; y = sy - r + bob
	and	#$00FF
	sec
	sbc.l	bt_r
	clc
	adc.l	bt_t
	sta.l	bt_y
	lda.l	bt_x			; widoczny: 0 <= x <= 247 i 52 <= y < 224
	cmp	#248
	bcs	@hidev
	lda.l	bt_y
	cmp	#52
	bcc	@hidev
	cmp	#224
	bcs	@hidev
	lda.l	bat_fl,x		; klatka skrzydel: ((wiek + faza) >> 2) & 1
	and	#$00FF
	clc
	adc.l	bt_age
	lsr	a
	lsr	a
	and	#$0001
	clc
	adc	#32			; TILE_BAT
	sta.l	bt_t
	phx
	lda.l	bt_id
	tax
	sep	#$20
.ACCU 8
	lda.l	bt_x
	sta.l	oamMemory,x
	clc
	adc	#8
	sta.l	oamMemory+4,x
	lda.l	bt_y
	sta.l	oamMemory+1,x
	sta.l	oamMemory+5,x
	lda.l	bt_t
	sta.l	oamMemory+2,x
	sta.l	oamMemory+6,x
	lda	#$1E			; paleta 7, priorytet 1
	sta.l	oamMemory+3,x
	lda	#$5E			; to samo, odbicie poziome
	sta.l	oamMemory+7,x
	rep	#$20
.ACCU 16
	txa
	lsr	a
	lsr	a
	tax
	sep	#$20
.ACCU 8
	lda	#1
	sta.l	svis,x
	sta.l	svis+1,x
	rep	#$20
.ACCU 16
	plx
	bra	@next
@hidev:
	jsr	bt_hide2
@next:
	inx
	cpx	#5
	beq	@done
	jmp	@lp
@done:
	ply
	plx
	plp
	rtl

; schowanie obu sprite'ow nietoperza bt_id (tryb 16-bitowy, X zachowany)
bt_hide2:
	phx
	lda.l	bt_id
	tax
	sep	#$20
.ACCU 8
	lda	#240
	sta.l	oamMemory+1,x
	sta.l	oamMemory+5,x
	rep	#$20
.ACCU 16
	txa
	lsr	a
	lsr	a
	tax
	sep	#$20
.ACCU 8
	lda	#0
	sta.l	svis,x
	sta.l	svis+1,x
	rep	#$20
.ACCU 16
	plx
	rts
.ends

; Ekran tytulowy: blyskawice
.section ".rodata_title" superfree
title_bolt_til:
.incbin "title_bolt.til"
title_bolt_tilend:
title_bolt_map:
.incbin "title_bolt.map"
.ends

; ---------------------------------------------------------------------------
; Areny strażnikow 4-9 (tools/make_arena2.py)
.section ".rodata_arena4" superfree
doppler_code_til:
.incbin "doppler_code.til"
doppler_code_tilend:
doppler_code_map:
.incbin "doppler_code.map"
doppler_ca:
.incbin "doppler_ca.bin"
doppler_cb:
.incbin "doppler_cb.bin"
doppler_grad:
.incbin "doppler_grad.bin"
doppler_gradend:
.ends

.section ".rodata_arena5" superfree
changero_plasma_til:
.incbin "changero_plasma.til"
changero_plasma_tilend:
changero_plasma_map:
.incbin "changero_plasma.map"
changero_cols:
.incbin "changero_cols.bin"
.ends

; Falowanie Changero: 32 wartosci przesuniecia = dryf + fala o amplitudzie 0..8 px.
; void wave2_vals_asm(u16 base, u16 amp)  - argumenty 9,s i 11,s
.section ".wave2_text" superfree
wave2_vals_asm:
	php
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	9,s
	sta.l	pad_n		; dryf
	lda	11,s		; X = amp * 32 (wiersz tablicy sinusow)
	asl	a
	asl	a
	asl	a
	asl	a
	asl	a
	tax
	ldy	#0		; Y = przesuniecie w tablicy slow (0..62)
@lp:
	lda.l	changero_wave,x
	and	#$00FF
	cmp	#$0080		; rozszerzenie znaku
	bcc	@pos
	ora	#$FF00
@pos:
	clc
	adc.l	pad_n
	phx
	tyx
	sta.l	wave_val,x
	plx
	iny
	iny
	inx
	cpy	#64
	bne	@lp
	ply
	plx
	plp
	rtl
changero_wave:
.incbin "changero_wave.bin"
.ends

.section ".rodata_arena6" superfree
chronos_dial_til:
.incbin "chronos_dial.til"
chronos_dial_tilend:
chronos_dial_map:
.incbin "chronos_dial.map"
chronos_grad:
.incbin "chronos_grad.bin"
chronos_gradend:
chronos_hands_til:
.incbin "chronos_hands.til"
chronos_hands_tilend:
chronos_hm:
.incbin "chronos_hm.bin"
chronos_hh:
.incbin "chronos_hh.bin"
chronos_wave:
.incbin "chronos_wave.bin"
.ends

.section ".rodata_arena7" superfree
magneton_field_til:
.incbin "magneton_field.til"
magneton_field_tilend:
magneton_field_map:
.incbin "magneton_field.map"
magneton_cols:
.incbin "magneton_cols.bin"
magneton_grad:
.incbin "magneton_grad.bin"
magneton_gradend:
magneton_spark_til:
.incbin "magneton_spark.til"
magneton_spark_tilend:
magneton_sparks:
.incbin "magneton_sparks.bin"
.ends

.section ".rodata_arena8" superfree
telementor_sky_til:
.incbin "telementor_sky.til"
telementor_sky_tilend:
telementor_sky_map:
.incbin "telementor_sky.map"
telementor_cols:
.incbin "telementor_cols.bin"
telementor_grad:
.incbin "telementor_grad.bin"
telementor_gradend:
telementor_ufo_til:
.incbin "telementor_ufo.til"
telementor_ufo_tilend:
telementor_beam:
.incbin "telementor_beam.bin"
.ends

; 32 ukryte wpisy OAM (sprite'y aren 96-127)
.section ".rodata_arhid" superfree
ar_hidblk:
.rept 32
.db 0, 240, 0, 0
.endr
.ends

.section ".rodata_arena9" superfree
blinker_rainbow_til:
.incbin "blinker_rainbow.til"
blinker_rainbow_tilend:
blinker_rainbow_map:
.incbin "blinker_rainbow.map"
blinker_cols:
.incbin "blinker_cols.bin"
.ends

; Duch na arenie Maltena (4 sprite'y 16x16, 2 klatki)
.section ".rodata_ghost" superfree
malten_ghost_til:
.incbin "malten_ghost.til"
malten_ghost_tilend:
.ends

; ---------------------------------------------------------------------------
; Plansza Lucifero (Mode 7): podloga, kolory, tablice perspektywy (tools/make_lucifero_floor.py)
.section ".rodata_luc" superfree
luc_floor_til:
.incbin "luc_floor.til"
luc_floor_tilend:
luc_floor_map:
.incbin "luc_floor.map"
luc_floor_mapend:
luc_floor_pal:
.incbin "luc_floor.pal"
luc_m7:
.incbin "luc_m7.bin"
.ends

.section ".rodata_lucp" superfree
luc_py:
.incbin "luc_proj.bin" READ 256
luc_ps:
.incbin "luc_proj.bin" SKIP 256
.ends

; void luc_project(void): pozostale sprite'y boiska (pilki, ogony, iskry; bez paletek i kursorow)
; przeliczone na perspektywe: y' = luc_py[y], x' = 128 + (x - 128) * luc_ps[y'] / 256.
; Tylko sprite'y widoczne wedlug svis, w zakresach 0-2, 23-36 i 57-79; pomija y < 24 (nad boiskiem,
; takze rozszerzonym o 24 px) i sprite'y z ustawionym 9. bitem x. Zapamietuje (offset, x, y, kafelek, atrybuty)
; do przywrocenia przez luc_unproject. Paletki rysuje od razu w perspektywie draw_paddle (C).
.section ".luc_text" superfree
luc_project:
	php
	phb
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#0
	sep	#$20
.ACCU 8
	pha
	lda	#$7E
	pha
	plb
	pla
	ldx	#0
	lda	#3
	jsr	luc_prj_rng
	ldx	#23
	lda	#37
	jsr	luc_prj_rng
	ldx	#57
	lda	#80
	jsr	luc_prj_rng
	ply
	plx
	plb
	plp
	rtl

; X = pierwszy numer sprite'a, A = koniec zakresu (bez niego)
luc_prj_rng:
	sta.w	luc_e
	txa				; maska 9. bitu: bajt n/4, bit (n & 3) * 2
	lsr	a
	lsr	a
	sta.w	luc_hb
	txa
	and	#3
	phx
	tax
	lda.l	luc_xm,x
	plx
	sta.w	luc_hm
@lp:
	lda.w	svis,x			; schowany: od razu dalej
	bne	@vis
@next:
	lda.w	luc_hm
	asl	a
	asl	a
	bne	@m
	inc.w	luc_hb
	lda	#1
@m:
	sta.w	luc_hm
	inx
	txa
	cmp.w	luc_e
	bcc	@lp
	rts
@vis:
	rep	#$20
.ACCU 16
	txa
	asl	a
	asl	a
	tay				; Y = offset w OAM
	lda	#0
	sep	#$20
.ACCU 8
	lda.w	oamMemory+1,y
	cmp	#224
	bcs	@next
	cmp	#24			; rozszerzone boisko siega y = 24 (pilka nie moze trafic do paska)
	bcc	@next
	phx
	rep	#$20
.ACCU 16
	lda.w	luc_hb
	and	#$00FF
	tax
	lda	#0
	sep	#$20
.ACCU 8
	lda.w	oamMemory+512,x
	and.w	luc_hm
	beq	@ok
	plx
	bra	@next
@ok:
	ldx.w	luc_nb			; zapamietanie: offset, x, y, kafelek, atrybuty
	rep	#$20
.ACCU 16
	tya
	sta.w	luc_bak,x
	lda.w	oamMemory,y
	sta.w	luc_bak+2,x
	lda.w	oamMemory+2,y
	sta.w	luc_bak+4,x
	txa
	clc
	adc	#6
	sta.w	luc_nb
	lda	#0
	sep	#$20
.ACCU 8
	lda.w	oamMemory+1,y
	tax
	lda.l	luc_pyr,x		; y'
	sta.w	oamMemory+1,y
	tax
	lda.w	oamMemory,y
	sec
	sbc	#128
	bcc	@neg
	sta.l	$004202
	lda.l	luc_psr,x
	sta.l	$004203
	nop
	nop
	nop
	nop
	lda.l	$004217
	clc
	adc	#128
	sta.w	oamMemory,y
	plx
	jmp	@next
@neg:
	eor	#$FF
	inc	a
	sta.l	$004202
	lda.l	luc_psr,x
	sta.l	$004203
	nop
	nop
	nop
	nop
	lda	#128
	sec
	sbc.l	$004217
	sta.w	oamMemory,y
	plx
	jmp	@next

luc_unproject:
	php
	phb
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#0
	sep	#$20
.ACCU 8
	lda	#$7E
	pha
	plb
	ldx	#0
@lp:
	cpx.w	luc_nb
	bcs	@done
	rep	#$20
.ACCU 16
	lda.w	luc_bak,x		; offset sprite'a (0-316)
	tay
	sep	#$20
.ACCU 8
	lda.w	luc_bak+2,x
	sta.w	oamMemory,y
	lda.w	luc_bak+3,x
	sta.w	oamMemory+1,y
	lda.w	luc_bak+4,x
	sta.w	oamMemory+2,y
	lda.w	luc_bak+5,x
	sta.w	oamMemory+3,y
	inx
	inx
	inx
	inx
	inx
	inx
	bra	@lp
@done:
	ply
	plx
	plb
	plp
	rtl
.ends

.section ".rodata_lucx" superfree
luc_xm:
.db 1, 4, 16, 64			; maska 9. bitu x w bajcie tablicy wysokiej
.ends

; ---------------------------------------------------------------------------
; Plansza Lucifero: skosne, wygladzone paletki (tools/make_lucifero_pads.py)
.section ".rodata_lpad0a" superfree
luc_pad0_a:
.incbin "luc_pad0_a.bin"
.ends
.section ".rodata_lpad0b" superfree
luc_pad0_b:
.incbin "luc_pad0_b.bin"
.ends
.section ".rodata_lpad1a" superfree
luc_pad1_a:
.incbin "luc_pad1_a.bin"
.ends
.section ".rodata_lpad1b" superfree
luc_pad1_b:
.incbin "luc_pad1_b.bin"
.ends
.section ".rodata_lpadx" superfree
luc_padx:
.incbin "luc_padx.bin"
.ends

; numery kafelkow (tablica nazw 1 sprite'ow) pasow paletek: 0-19 pelne pasy, 20-27 przyciete konce
.section ".rodata_lptl" superfree
luc_tiles:
.db 96, 98, 100, 102, 104, 106, 108, 110, 128, 130, 132, 134, 136, 138, 140, 142
.db 160, 162, 164, 166, 168, 170, 172, 174, 192, 194, 196, 198
.ends

; void luc_pad_asm(u16 id, u16 sx, s16 y, u16 h, u16 attr): paletka na planszy Lucifero (skosna,
; wygladzona) z gotowych pasow 16x16; zmieniony przyciety koniec dostaje zrodlo w ROM (luc_cs, luc_cb)
; i znacznik luc_cd - wysyla go luc_flush_asm zaraz po VBlank. Argumenty (po php/phb/phx/phy):
; id 10,s  sx 12,s  y 14,s  h 16,s  attr 18,s
.section ".lpad_text" superfree
luc_pad_asm:
	php
	phb
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#$0000
	sep	#$20
.ACCU 8
	lda	#$7E
	pha
	plb
	rep	#$20
.ACCU 16
	lda	12,s			; strona i przesuniecie od toru (trzesienie ekranu, blizniaki)
	cmp	#128
	bcs	@right
	sec
	sbc	#16
	ldx	#0
	bra	@sd
@right:
	sec
	sbc	#232
	ldx	#1
@sd:
	sep	#$20
.ACCU 8
	sta.w	lp_dx
	txa
	sta.w	lp_side
	rep	#$20
.ACCU 16
	lda	10,s			; numer paletki (pamiec przycietych koncow)
	ldx	#0
	cmp	#12
	beq	@pi
	inx
	cmp	#52
	beq	@pi
	inx
	cmp	#148
	beq	@pi
	inx
@pi:
	sep	#$20
.ACCU 8
	txa
	asl	a
	sta.w	lp_pi2			; pi * 2
	rep	#$20
.ACCU 16
	lda	10,s
	sta.w	lp_off			; offset w OAM
	lsr	a
	lsr	a
	sta.w	lp_svi			; numer sprite'a (svis)
	lda	14,s			; y (s16) -> 0..223
	bpl	@yp
	lda	#0
@yp:
	cmp	#224
	bcc	@y1
	lda	#223
@y1:
	tax
	clc
	adc	16,s			; y + h -> najwyzej 223
	cmp	#224
	bcc	@y2
	lda	#223
@y2:
	pha
	lda	#0
	sep	#$20
.ACCU 8
	lda.l	luc_pyr,x
	cmp	#64
	bcs	@lt1
	lda	#64
@lt1:
	sta.w	lp_lt
	rep	#$20
.ACCU 16
	plx
	lda	#0
	sep	#$20
.ACCU 8
	lda.l	luc_pyr,x
	cmp.w	lp_lt
	beq	@lbfix
	bcs	@lb1
@lbfix:
	lda.w	lp_lt
	inc	a
@lb1:
	sta.w	lp_lb
	lda.w	lp_lt			; pierwszy i ostatni pas
	sec
	sbc	#64
	lsr	a
	lsr	a
	lsr	a
	lsr	a
	sta.w	lp_b
	lda.w	lp_lb
	sec
	sbc	#65
	lsr	a
	lsr	a
	lsr	a
	lsr	a
	cmp	#10
	bcc	@bb1
	lda	#9
@bb1:
	sta.w	lp_bb
	lda.w	lp_b
	sta.w	lp_bt
	stz.w	lp_n
	lda	18,s			; atrybuty: paleta, priorytet + druga tablica nazw
	ora	#$01
	sta.w	lp_at
@band:
	stz.w	lp_sh			; przesuniecie sprite'a w dol (tylko pas z oboma koncami)
	lda.w	lp_b			; rs = 64 + 16 * b
	asl	a
	asl	a
	asl	a
	asl	a
	clc
	adc	#64
	sta.w	lp_rs
	lda.w	lp_lt			; pelny pas, jesli lt <= rs i lb >= rs + 16
	cmp.w	lp_rs
	beq	@chk2
	bcs	@part
@chk2:
	lda.w	lp_rs
	clc
	adc	#16
	bcs	@part
	cmp.w	lp_lb
	beq	@full
	bcs	@part
@full:
	lda.w	lp_b			; koniec paletki rowno z granica pasa: wariant z zaokraglonym koncem
	cmp.w	lp_bt
	bne	@fb
	lda	#31			; gorny koniec rowno z poczatkiem pasa (v = 31)...
	sta.w	lp_v
	lda.w	lp_b
	cmp.w	lp_bb
	bne	@fv0
	lda	#48			; ...i dolny rowno z jego koncem (oba konce: v = 48)
	sta.w	lp_v
@fv0:
	stz.w	lp_slot
	jmp	@pv
@fb:
	lda.w	lp_b
	cmp.w	lp_bb
	bne	@fsh
	lda	#32			; dolny koniec rowno z koncem pasa (v = 32)
	sta.w	lp_v
	lda	#1
	sta.w	lp_slot
	jmp	@pv
@fsh:
	lda.w	lp_side			; k = side * 10 + b
	beq	@f0
	lda	#10
@f0:
	clc
	adc.w	lp_b
	jmp	@tile
@part:
	lda.w	lp_b			; miejsce: 0 = gorny koniec, 1 = dolny
	cmp.w	lp_bt
	bne	@bot
	lda.w	lp_lt
	cmp.w	lp_rs
	beq	@bot
	bcc	@bot
	lda.w	lp_rs			; paletka konczy sie w tym samym pasie (lb < rs + 16)?
	clc
	adc	#16
	cmp.w	lp_lb
	beq	@both			; dolny koniec rowno z koncem pasa: tez oba konce w tym pasie
	bcc	@top
@both:
	lda.w	lp_lt			; tak: wariant z oboma koncami o dlugosci lb - lt, sprite nizej o lt - rs
	sec
	sbc.w	lp_rs
	sta.w	lp_sh
	lda.w	lp_lb
	sec
	sbc.w	lp_lt
	clc
	adc	#32
	sta.w	lp_v
	stz.w	lp_slot
	bra	@pv
@top:
	lda.w	lp_lt			; wariant gorny: v = lt - rs, miejsce 0
	sec
	sbc.w	lp_rs
	sta.w	lp_v
	stz.w	lp_slot
	bra	@pv
@bot:
	lda.w	lp_b
	cmp.w	lp_bt
	bne	@s1
	stz.w	lp_slot			; pierwszy pas zaczyna sie rowno z paletka i ona w nim konczy:
	lda.w	lp_lb			; oba konce, v = 32 + (lb - rs)
	sec
	sbc.w	lp_rs
	clc
	adc	#32
	sta.w	lp_v
	bra	@pv
@s1:
	lda	#1
	sta.w	lp_slot
@sv:
	lda.w	lp_lb			; wariant dolny: v = 15 + (lb - rs)
	sec
	sbc.w	lp_rs
	clc
	adc	#15
	sta.w	lp_v
@pv:
	lda.w	lp_pi2			; k = pi * 2 + miejsce (0-7; kafelki: luc_tiles[20 + k])
	clc
	adc.w	lp_slot
	sta.w	lp_k
	rep	#$20
.ACCU 16
	and	#$00FF
	asl	a
	tax				; X = indeks pamieci wariantu (u16)
	lda.w	lp_b
	and	#$00FF
	xba
	lsr	a
	lsr	a			; b * 64 (warianty 0-48)
	sta.w	lp_code
	lda.w	lp_v
	and	#$00FF
	ora.w	lp_code
	cmp.w	luc_pv16,x
	beq	@same
	sta.w	luc_pv16,x		; nowy wariant: zastepuje niewyslany poprzedni (bez kolejki)
	lda	#0
	sep	#$20
.ACCU 8
	jsr	luc_src
	rep	#$20
.ACCU 16
	lda.w	lp_src
	sta.w	luc_cs,x
	lda.w	lp_k
	and	#$00FF
	tax
	lda	#0
	sep	#$20
.ACCU 8
	lda.w	lp_bk
	sta.w	luc_cb,x
	lda	#1
	sta.w	luc_cd,x
	bra	@same8
@same:
.ACCU 16
	lda	#0			; (tu procesor jest w trybie 16-bitowym)
	sep	#$20
.ACCU 8
@same8:
	lda.w	lp_k
	clc
	adc	#20
@tile:
	rep	#$20
.ACCU 16
	and	#$00FF
	tax
	lda	#0
	sep	#$20
.ACCU 8
	lda.l	luc_tiles,x
	sta.w	lp_t
	lda.w	lp_side			; x = X0[side * 10 + b] + dx
	beq	@x0
	lda	#10
@x0:
	clc
	adc.w	lp_b
	rep	#$20
.ACCU 16
	and	#$00FF
	tax
	lda	#0
	sep	#$20
.ACCU 8
	lda.l	luc_padxr,x
	clc
	adc.w	lp_dx
	ldy.w	lp_off
	sta.w	oamMemory,y
	lda.w	lp_sh			; pas z oboma koncami: x poprawione o skos toru
	beq	@ns
	rep	#$20
.ACCU 16
	and	#$00FF
	tax
	lda	#0
	sep	#$20
.ACCU 8
	lda.w	lp_side
	bne	@shr
	lda.w	oamMemory,y		; lewy tor: nizej znaczy bardziej w lewo
	sec
	sbc.l	luc_shx,x
	sta.w	oamMemory,y
	bra	@ns
@shr:
	lda.w	oamMemory,y
	clc
	adc.l	luc_shx,x
	sta.w	oamMemory,y
@ns:
	lda.w	lp_rs
	dec	a
	clc
	adc.w	lp_sh
	sta.w	oamMemory+1,y
	lda.w	lp_t
	sta.w	oamMemory+2,y
	lda.w	lp_at
	sta.w	oamMemory+3,y
	ldx.w	lp_svi
	lda	#1
	sta.l	svis,x
	inx
	stx.w	lp_svi
	rep	#$20
.ACCU 16
	tya
	clc
	adc	#4
	sta.w	lp_off
	lda	#0
	sep	#$20
.ACCU 8
	inc.w	lp_n
	lda.w	lp_n
	cmp	#10
	bcs	@done
	lda.w	lp_b
	cmp.w	lp_bb
	bcs	@hide
	inc.w	lp_b
	jmp	@band
@hide:					; pozostale sprite'y paletki: schowane
	lda.w	lp_n
	cmp	#10
	bcs	@done
	ldx.w	lp_svi
	lda.l	svis,x
	beq	@hn
	lda	#0
	sta.l	svis,x
	ldy.w	lp_off
	lda	#240
	sta.w	oamMemory+1,y
@hn:
	inx
	stx.w	lp_svi
	rep	#$20
.ACCU 16
	lda.w	lp_off
	clc
	adc	#4
	sta.w	lp_off
	lda	#0
	sep	#$20
.ACCU 8
	inc.w	lp_n
	bra	@hide
@done:
	ply
	plx
	plb
	plp
	rtl

; void luc_flush_asm(void): zaraz po VBlank - zmienione konce paletek (luc_cd), potem pelne pasy nowego
; zestawu (luc_breload 1-20). Kazdy pas tylko, gdy VBlank jeszcze trwa; reszta czeka do nastepnej klatki.
.ACCU 8
.INDEX 16
luc_flush_asm:
	php
	phb
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#$0000
	sep	#$20
.ACCU 8
	lda	#$7E
	pha
	plb
	lda	#$80			; VRAM: przyrost adresu po zapisie $2119
	sta.l	$002115
	lda	#$01			; DMA 0: dwa rejestry $2118/$2119
	sta.l	$004300
	lda	#$18
	sta.l	$004301
	ldx	#0
@cap:
	lda.w	luc_cd,x
	beq	@cnext
	jsr	luc_vbok
	bcc	@c1
	jmp	@done
@c1:
	stz.w	luc_cd,x
	lda.w	luc_cb,x
	sta.w	lp_bk
	rep	#$20
.ACCU 16
	txa
	asl	a
	tay
	lda.w	luc_cs,y
	sta.w	lp_src
	phx
	tyx
	lda.l	luc_sva+40,x		; kafelki koncow: sloty 20-27
	plx
	sta.w	lp_va
	lda	#0
	sep	#$20
.ACCU 8
	jsr	luc_up128
@cnext:
	inx
	cpx	#8
	bcc	@cap
@full:
	lda.w	luc_breload
	beq	@done
	cmp	#21
	bcs	@fend
	jsr	luc_vbok
	bcs	@done
	lda.w	luc_breload		; k = breload - 1: strona k / 10, pas k % 10, wariant pelny
	dec	a
	stz.w	lp_side
	cmp	#10
	bcc	@f0
	sec
	sbc	#10
	inc.w	lp_side
@f0:
	sta.w	lp_b
	stz.w	lp_v
	jsr	luc_src
	rep	#$20
.ACCU 16
	lda.w	luc_breload
	and	#$00FF
	dec	a
	asl	a
	tax
	lda.l	luc_sva,x
	sta.w	lp_va
	lda	#0
	sep	#$20
.ACCU 8
	jsr	luc_up128
	inc.w	luc_breload
	bra	@full
@fend:
	stz.w	luc_breload
@done:
	ply
	plx
	plb
	plp
	rtl

; Zrodlo obrazu pasa w ROM. Wejscie: lp_side, lp_b, lp_v i luc_pset; wyjscie: lp_src (adres), lp_bk (bank).
; Plik pasow: 5 pasow po 31 wariantow po 128 B (pasy 0-4 w czesci a, 5-9 w b). A 8-bit; X zachowany.
.ACCU 8
.INDEX 16
luc_src:
	phx
	stz.w	lp_idx
	lda.w	lp_b
	cmp	#5
	bcc	@a
	sec
	sbc	#5
	inc.w	lp_idx			; czesc b
@a:
	sta.w	lp_bm			; pas w czesci (b % 5)
	lda.w	lp_side
	beq	@s0
	lda.w	lp_idx
	ora	#2
	sta.w	lp_idx
@s0:
	lda.w	luc_pset		; pasy dla odsunietej kamery
	beq	@p0
	lda.w	lp_idx
	ora	#4
	sta.w	lp_idx
@p0:
	rep	#$20
.ACCU 16
	lda.w	lp_idx
	and	#$00FF
	tax
	lda	#0
	sep	#$20
.ACCU 8
	lda.l	luc_pbank,x
	sta.w	lp_bk
	rep	#$20
.ACCU 16
	txa
	asl	a
	tax
	lda.l	luc_pbase,x
	sta.w	lp_src
	lda.w	lp_bm
	and	#$00FF
	asl	a
	tax
	lda.l	luc_boff,x		; + (b % 5) * 49 * 128
	clc
	adc.w	lp_src
	sta.w	lp_src
	lda.w	lp_v			; + v * 128
	and	#$00FF
	xba
	lsr	a
	clc
	adc.w	lp_src
	sta.w	lp_src
	lda	#0
	sep	#$20
.ACCU 8
	plx
	rts

; carry 0 = trwa VBlank i zostal zapas czasu (linie 225-254, jak vb_ok w C). A 8-bit
.ACCU 8
.INDEX 16
luc_vbok:
	lda.l	$00213F			; kasuje przerzutnik odczytu licznika
	lda.l	$002137			; zatrzaskuje licznik linii
	lda.l	$00213D
	sta.w	lp_vl
	lda.l	$00213D
	and	#$01
	bne	@no			; linia 256 i dalej
	lda.w	lp_vl
	cmp	#225
	bcc	@no
	cmp	#255
	bcs	@no
	clc
	rts
@no:
	sec
	rts

; 128 B pasa (dwa wiersze kafelkow 16x16) z lp_bk:lp_src do VRAM lp_va i lp_va + 256 (DMA 0). A 8-bit
.ACCU 8
.INDEX 16
luc_up128:
	rep	#$20
.ACCU 16
	lda.w	lp_va
	sta.l	$002116
	lda.w	lp_src
	sta.l	$004302
	lda	#64
	sta.l	$004305
	sep	#$20
.ACCU 8
	lda.w	lp_bk
	sta.l	$004304
	lda	#$01
	sta.l	$00420B
	rep	#$20
.ACCU 16
	lda.w	lp_va
	clc
	adc	#256
	sta.l	$002116
	lda.w	lp_src
	clc
	adc	#64
	sta.l	$004302
	lda	#64
	sta.l	$004305
	sep	#$20
.ACCU 8
	lda.w	lp_bk
	sta.l	$004304
	lda	#$01
	sta.l	$00420B
	rts
.ends

; zrodla pasow paletek (luc_src) i adresy VRAM ich kafelkow (luc_flush_asm)
.section ".rodata_lsrc" superfree
luc_pbase:				; indeks: pset * 4 + strona * 2 + czesc
.dw luc_pad0_a, luc_pad0_b, luc_pad1_a, luc_pad1_b, luc_wpad0_a, luc_wpad0_b, luc_wpad1_a, luc_wpad1_b
luc_pbank:
.db :luc_pad0_a, :luc_pad0_b, :luc_pad1_a, :luc_pad1_b, :luc_wpad0_a, :luc_wpad0_b, :luc_wpad1_a, :luc_wpad1_b
luc_boff:				; (b % 5) * 49 wariantow * 128 B
.dw 0, 6272, 12544, 18816, 25088
luc_sva:				; slowo VRAM pasu k: $5000 + 16 * luc_tiles[k] (0-19 pelne, 20-27 konce)
.dw $5600, $5620, $5640, $5660, $5680, $56A0, $56C0, $56E0
.dw $5800, $5820, $5840, $5860, $5880, $58A0, $58C0, $58E0
.dw $5A00, $5A20, $5A40, $5A60, $5A80, $5AA0, $5AC0, $5AE0
.dw $5C00, $5C20, $5C40, $5C60
luc_shx:				; pas z oboma koncami: przesuniecie x dla d = lt - rs (ok. 0,19 px na linie)
.db 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3
.ends

; ---------------------------------------------------------------------------
; Plansza Lucifero: popiol (30 platkow, sprite'y 98-127, bez perspektywy)
.section ".rodata_lash" superfree
luc_sway:
.dw 0, 5, 10, 15, 20, 24, 28, 32, 36, 40, 43, 45, 47, 49, 50, 51
.dw 51, 51, 50, 49, 47, 45, 43, 40, 36, 32, 28, 24, 20, 15, 10, 5
.dw 0, 65531, 65526, 65521, 65516, 65512, 65508, 65504, 65500, 65496, 65493, 65491, 65489, 65487, 65486, 65485
.dw 65485, 65485, 65486, 65487, 65489, 65491, 65493, 65496, 65500, 65504, 65508, 65512, 65516, 65521, 65526, 65531
.dw 0, 8, 16, 25, 32, 40, 47, 54, 60, 65, 70, 75, 78, 81, 83, 84
.dw 84, 84, 83, 81, 78, 75, 70, 65, 60, 54, 47, 40, 32, 25, 16, 8
.dw 0, 65528, 65520, 65511, 65504, 65496, 65489, 65482, 65476, 65471, 65466, 65461, 65458, 65455, 65453, 65452
.dw 65452, 65452, 65453, 65455, 65458, 65461, 65466, 65471, 65476, 65482, 65489, 65496, 65504, 65511, 65520, 65528
.dw 0, 12, 23, 34, 45, 56, 65, 75, 83, 91, 98, 104, 109, 113, 115, 117
.dw 118, 117, 115, 113, 109, 104, 98, 91, 83, 75, 65, 56, 45, 34, 23, 12
.dw 0, 65524, 65513, 65502, 65491, 65480, 65471, 65461, 65453, 65445, 65438, 65432, 65427, 65423, 65421, 65419
.dw 65418, 65419, 65421, 65423, 65427, 65432, 65438, 65445, 65453, 65461, 65471, 65480, 65491, 65502, 65513, 65524
.dw 0, 15, 30, 45, 59, 72, 85, 97, 109, 119, 128, 135, 142, 147, 151, 153
.dw 154, 153, 151, 147, 142, 135, 128, 119, 109, 97, 85, 72, 59, 45, 30, 15
.dw 0, 65521, 65506, 65491, 65477, 65464, 65451, 65439, 65427, 65417, 65408, 65401, 65394, 65389, 65385, 65383
.dw 65382, 65383, 65385, 65389, 65394, 65401, 65408, 65417, 65427, 65439, 65451, 65464, 65477, 65491, 65506, 65521
luc_gust:
.dw 0, 0, 2, 5, 11, 21, 35, 52, 72, 95, 118, 140, 162, 179, 193, 202
.dw 205, 202, 193, 179, 162, 140, 118, 95, 72, 52, 35, 21, 11, 5, 2, 0
.dw 0, 0, 65534, 65531, 65525, 65515, 65501, 65484, 65464, 65441, 65418, 65396, 65374, 65357, 65343, 65334
.dw 65331, 65334, 65343, 65357, 65374, 65396, 65418, 65441, 65464, 65484, 65501, 65515, 65525, 65531, 65534, 0
.ends

; void luc_ash(void): ruch platkow popiolu i ich sprite'y. Kazdy platek opada (ash_vy w 1/256 px
; na klatke), kolysze sie (tablica luc_sway, faza i amplituda platka) i niesie go podmuch (luc_gust);
; po wypadnieciu dolem wraca u gory w losowym miejscu.
.section ".lash_text" superfree
luc_ash:
	php
	phb
	phx
	phy
	rep	#$30
.ACCU 16
.INDEX 16
	lda	#$0000
	sep	#$20
.ACCU 8
	lda	#$7E
	pha
	plb
	inc.w	ash_f
	rep	#$20
.ACCU 16
	lda.w	ash_f			; podmuch: wspolny dla wszystkich platkow
	lsr	a
	lsr	a
	and	#$003F
	asl	a
	tax
	lda.l	luc_gust,x
	sta.w	ash_g
	ldx	#0			; X = numer platka * 2
	ldy	#392			; Y = offset sprite'a 98 w OAM
@lp:
	lda.w	ash_up			; przemiana: iskry unosza sie w gore i wracaja od dolu
	beq	@down
	lda.w	ash_y,x
	sec
	sbc.w	ash_vy,x
	cmp	#48 * 256
	bcs	@nores
	lda.w	ash_rng
	lsr	a
	bcc	@r2
	eor	#$B400
@r2:
	sta.w	ash_rng
	and	#$FF00
	sta.w	ash_x,x
	lda	#223 * 256
	bra	@nores
@down:
	lda.w	ash_y,x			; opadanie
	clc
	adc.w	ash_vy,x
	cmp	#224 * 256
	bcc	@nores
	lda.w	ash_rng			; wypadl dolem: nowy u gory, w losowym miejscu
	lsr	a
	bcc	@r1
	eor	#$B400
@r1:
	sta.w	ash_rng
	and	#$FF00
	sta.w	ash_x,x
	lda	#48 * 256
@nores:
	sta.w	ash_y,x
	phy				; kolysanie: luc_sway[poziom * 64 + ((f / 2 + faza) & 63)]
	lda.w	ash_f
	lsr	a
	clc
	adc.w	ash_ph,x
	and	#$003F
	clc
	adc.w	ash_lv,x		; poziom * 64
	asl	a
	phx
	tax
	lda.l	luc_sway,x
	plx
	clc
	adc.w	ash_g
	clc
	adc.w	ash_x,x
	sta.w	ash_x,x
	ply
	lda	#0
	sep	#$20
.ACCU 8
	lda.w	ash_x+1,x		; sprite: x, y, kafelek, atrybuty (paleta 3, priorytet 3)
	sta.w	oamMemory,y
	lda.w	ash_y+1,x
	dec	a
	sta.w	oamMemory+1,y
	lda.w	ash_t,x
	sta.w	oamMemory+2,y
	lda	#$36
	sta.w	oamMemory+3,y
	rep	#$20
.ACCU 16
	iny
	iny
	iny
	iny
	inx
	inx
	cpx	#60
	bcs	@done
	jmp	@lp
@done:
	sep	#$20
.ACCU 8
	ply
	plx
	plb
	plp
	rtl
.ends

; kafelki platkow popiolu (sprite'y 160-163): 2x2 i 1x1 w kolorze 2 (jasny) oraz 3 (ciemniejszy)
.section ".rodata_lashtil" superfree
luc_ash_til:
.db $00,$C0, $00,$C0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0,  0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
.db $00,$80, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0,  0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
.db $C0,$C0, $C0,$C0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0,  0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
.db $80,$80, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0,  0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
.ends

; twarz zjawy (96x96: 12 x 12 kafelkow, wiersz po wierszu) i jej paleta
.section ".rodata_lface" superfree
luc_face_til:
.incbin "luc_face.til"
luc_face_pal:
.incbin "luc_face.pal"
.ends

; rozszerzenie boiska Lucifero: kamera (16 krokow), podloga rozszerzona, pasy paletek dla kamery C1
.section ".rodata_lcamh" superfree
luc_cam_hdma:
.incbin "luc_cam_hdma.bin"
.ends
.section ".rodata_lcamp" superfree
luc_cam_proj:
.incbin "luc_cam_proj.bin"
.ends
.section ".rodata_lwide" superfree
luc_wide_map:
.incbin "luc_wide.map"
luc_wide_lo:
.incbin "luc_wide_lo.til"
luc_wide_hi:
.incbin "luc_wide_hi.til"
luc_wpadx:
.incbin "luc_wpadx.bin"
.ends
.section ".rodata_luc_wpad0_a" superfree
luc_wpad0_a:
.incbin "luc_wpad0_a.bin"
.ends
.section ".rodata_luc_wpad0_b" superfree
luc_wpad0_b:
.incbin "luc_wpad0_b.bin"
.ends
.section ".rodata_luc_wpad1_a" superfree
luc_wpad1_a:
.incbin "luc_wpad1_a.bin"
.ends
.section ".rodata_luc_wpad1_b" superfree
luc_wpad1_b:
.incbin "luc_wpad1_b.bin"
.ends

; void luc_cam_hdma_asm(u16 step): kanaly HDMA 4 (M7A) i 5 (przesuniecie pionowe) czytaja tablice kroku
; kamery prosto z ROM (luc_cam_hdma: 16 krokow po 358 + 358 B), bez kopiowania do RAM. Tylko w VBlank.
; Argument (po php/phx): step 7,s
.section ".lcamh_text" superfree
luc_cam_hdma_asm:
	php
	phx
	rep	#$30
.ACCU 16
.INDEX 16
	lda	7,s
	and	#$000F
	asl	a
	tax
	lda.l	luc_camofs,x
	clc
	adc.w	#luc_cam_hdma
	sta.l	$004342
	clc
	adc	#358
	sta.l	$004352
	sep	#$20
.ACCU 8
	lda.b	#:luc_cam_hdma
	sta.l	$004344
	sta.l	$004354
	plx
	plp
	rtl
luc_camofs:				; krok * 716
.dw 0, 716, 1432, 2148, 2864, 3580, 4296, 5012, 5728, 6444, 7160, 7876, 8592, 9308, 10024, 10740
.ends
