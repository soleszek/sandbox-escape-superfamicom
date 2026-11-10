/*---------------------------------------------------------------------------------
    Uwaga: 816-tcc zle kompiluje przypisania lancuchowe (a = b = c) i bywa, ze zlozone
    warunki z || i !; w krytycznych miejscach uzywamy prostych, osobnych if-ow.

    SANDBOX ESCAPE: A PADDLE ODYSSEY dla Super Famicom / SNES (PVSnesLib)

    Warstwy (Mode 1):
      BG0  - tekst (imiona, wynik, komunikaty), domyslna czcionka PVSnesLib
      BG1  - ekran tytulowy / ekran wyboru mocy / boisko z paskiem nad nim
      OBJ  - pilka, paletki, ogon komety, ramki kursorow (sprite'y 8x8)

    Mapa VRAM (adresy w slowach):
      $0000  kafelki BG1   $3000  czcionka   $4000  sprite'y
      $6000  mapa BG1      $6800  mapa tekstu

    Palety BG: 0 czcionka, 1 boisko, 2-3 awatary, 4 logo, 5 AI Agent,
               6 ikony mocy, 7 pasek mocy
    Palety sprite'ow: 0 gracz 1 (+ biala pilka), 1 gracz 2, 2 pilka podczas mocy,
               4 ogon komety (palety 4-7 biora udzial w mieszaniu kolorow)

    Dzwiek: efekty BRR na SPC700, muzyka przez MSU-1 (FXPAK Pro).
---------------------------------------------------------------------------------*/
#include <snes.h>
#include <string.h>
// Na planszy Lucifero (Mode 7) czekanie na VBlank przelicza sprite'y boiska na perspektywe
// i dorysowuje napisy z warstwy tekstu sprite'ami (patrz luc_wait_vb).
void luc_wait_vb(void);
#define WaitForVBlank() luc_wait_vb()

#include "court.inc"
#include "logo.inc"
#include "robot32.inc"   // AI Agent (przeciwnik komputerowy)
#include "joybot32.inc"   // Robocik-dzojstik
#include "icons.inc"
#include "minicons.inc"
#include "bar.inc"
#include "sprites.inc"
#include "blocks.inc"
#include "dlg.inc"
#include "muggy48.inc"
#include "muggy32.inc"
#include "ruden48.inc"
#include "ruden32.inc"
#include "malten48.inc"
#include "malten32.inc"
#include "waller48.inc"
#include "waller32.inc"
#include "doppler48.inc"
#include "doppler32.inc"
#include "changero48.inc"
#include "changero32.inc"
#include "chronos48.inc"
#include "chronos32.inc"
#include "magneton48.inc"
#include "magneton32.inc"
#include "telementor48.inc"
#include "telementor32.inc"
#include "blinker48.inc"
#include "blinker32.inc"
#include "kimantero48.inc"
#include "kimantero32.inc"
#include "story.h"

extern char snd_tada, snd_tada_end, snd_tok1, snd_tok1_end, snd_tok2, snd_tok2_end;
extern char snd_thunder, snd_thunder_end;
#include "soundbank.h"   // muzyka: numery modulow MOD_... (bank dzwiekow z plikow music/*.it)
extern char SOUNDBANK__0, SOUNDBANK__1, SOUNDBANK__2, SOUNDBANK__3, SOUNDBANK__4, SOUNDBANK__5;
extern char rain_til, rain_tilend, rain_map, rain_mapend, bolt_til, bolt_tilend;
extern char ruden_dust_til, ruden_dust_tilend, ruden_dust_map, ruden_crowd_til, ruden_crowd_tilend, ruden_crowd_map;
extern char ruden_grad, ruden_gradend, malten_fog_til, malten_fog_tilend, malten_fog_map, malten_grad, malten_gradend;
extern char waller_wall_til, waller_wall_tilend, waller_wall_map, waller_torch_til, waller_torch_tilend, bat_til, bat_tilend, waller_grad, waller_gradend;
extern char snd_tokwall, snd_tokwall_end, snd_fanfare, snd_fanfare_end, snd_sad, snd_sad_end;
extern char snd_tick, snd_tick_end, snd_confirm, snd_confirm_end, snd_ready, snd_ready_end;
extern char snd_arm, snd_arm_end, snd_super, snd_super_end, snd_curve, snd_curve_end;
extern char snd_zigzag, snd_zigzag_end, snd_ghost, snd_ghost_end;

//---------------------------------------------------------------------------------
// Imiona (czcionka ma tylko wielkie litery bez polskich znakow)

// Wymiary boiska i obiektow (w pikselach)
#define FIELD_TOP     48
#define FIELD_BOTTOM  200
#define BALL_SIZE     8
#define PADDLE_W      8
#define PADDLE_H      32
#define P1_X          16
#define P2_X          232

// Rozgrywka - te liczby warto stroic
#define PADDLE_SPEED  3       // px na klatke (gracz)
#define CPU_SPEED     0x0140  // 8.8: 1.25 px na klatke (komputer)
#define CPU_REACT_X   128     // komputer reaguje, gdy pilka minie te kolumne
#define SERVE_SPEED   0x0180  // 8.8: 1.5 px na klatke
#define MAX_SPEED     0x0300  // 8.8: 3 px na klatke
#define SPEED_STEP    0x0010  // przyspieszenie po kazdym odbiciu
#define SPIN          16      // predkosc pionowa za kazdy px od srodka paletki
#define WIN_SCORE     7

// Moce specjalne
#define BAR_MAX       8       // pojemnosc paska mocy
#define EDGE_ZONE     4       // odbicie krawedzia: skrajne 4 px paletki (przy 32 px: >= 12 px od srodka)
#define SUPER_MULT    4       // Superstrzal: 4x predkosc zwyklego odbicia...
#define SUPER_MAX     0x0C00  // ...ale najwyzej 12 px na klatke
#define CURVE_START   0x0180  // Podkrecona: start 1.5 px na klatke w strone przeciwna do luku
#define CURVE_ACC     12      // Podkrecona: zmiana predkosci pionowej na klatke (1/256 px)
#define CURVE_MAX     0x0300  // Podkrecona: najwyzej 3 px na klatke w pionie
#define ZIG_MIN    6     // ZIGZAG: odcinki 6..28 klatek
#define ZIG_MAX    28
#define ZIG_VMIN      0x00C0  // Zygzak: losowa predkosc pionowa 0.75..2 px na klatke
#define ZIG_VMAX   0x0280   // ...i predkosc pionowa do 2.5 px na klatke
#define ZIG_SEGMENTS  6       // Zygzak: najwyzej 6 losowych odcinkow
#define GHOST_X1   70    // GHOST: pilka niewidoczna miedzy x = 70..186 (strefa o 20% dluzsza)
#define GHOST_X2   186
#define GHOST_SHIFT   30      // Duch: w ukryciu tor zmienia sie tak, by pilka pojawila sie
                              // ok. 30 px (20% wysokosci boiska) wyzej albo nizej
#define TAIL_SPEED    0x0280  // ogon komety od 2.5 px na klatke
#define TAIL_LEN      5
#define CPU_DELAY     12      // opoznienie reakcji komputera na Podkrecona i Zygzak
#define CPU_GHOST_ERR 12      // blad zgadywania komputera przy Duchu (+-px)

enum { PWR_SUPER, PWR_CURVE, PWR_ZIGZAG, PWR_GHOST, PWR_GROW, PWR_SPLIT, PWR_FORTRESS, PWR_TWIN, PWR_SWAP, PWR_SLOW,
       PWR_CATCH, PWR_BLINK, PWR_CAMO, PWR_CHAOS };
#define PWR_DRAWN    14   // moce z gotowymi ikonami (reszta: ikona zablokowanej)
#define PWR_ALL      14   // 4 podstawowe + 10 mocy strażnikow
#define PWR_HELL     14   // moc Lucifero: przemiana swiata (rdza, muzyka przemiany, iskry) + jedno z dzialan
#define NUM_GUARD    11     // strażnicy razem z Lucifero (w fabule: po pracach nad jego plansza)
#define G_LUCIFERO   10
#define ARENA_LUC    11   // pochylone boisko Lucifero (Mode 7)
#define ICON_LOCK    14   // ikona zablokowanej mocy
#define ICON_STRIDE  30   // szerokosc mapy ikon: 15 ikon po 2 kafelki
enum { SP_NONE, SP_SUPER, SP_CURVE, SP_ZIGZAG, SP_GHOST };   // SP_x = PWR_x + 1

// Glosnosc muzyki MSU-1 (0..255). Zmniejsz, jesli muzyka zaglusza efekty.
#define MUSIC_VOLUME  0xC0

#define FP(px) ((u16)(px) << 8)   // piksel -> format 8.8
#define REG_CGADD_ (*(vuint8 *)0x2121)   // adres palety (odczyt palety czcionki)
#define REG_CGREAD (*(vuint8 *)0x213B)

// VRAM
#define VRAM_BG1_GFX  0x0000
#define VRAM_FONT     0x3000
#define VRAM_SPR      0x4000
#define VRAM_BG1_MAP  0x6000
#define VRAM_TXT_MAP  0x6800
#define VRAM_RAIN_GFX 0x5000   // BG3: kafelki deszczu (2 bity na piksel)
#define VRAM_RAIN_MAP 0x7000   // BG3: mapa deszczu
#define TILES_BOLT    544      // pioruny w kafelkach boiska (w meczu ten obszar jest wolny)

// Palety BG i pierwsze kafelki grafik - musza sie zgadzac z -e i -f w Makefile
#define PAL_FONT   0
#define PAL_COURT  1
#define PAL_LOGO   4
#define PAL_ROBOT  5
#define PAL_ICONS  6
#define PAL_BAR    7
#define TILES_LOGO   16
#define TILES_JOY    256   // Robocik-dzojstik 32x32 (logo zajmuje 16-255)
#define TILES_ROBOT  272
#define TILES_ICONS  288
#define TILES_MINI   348
#define TILES_BAR    364
#define TILES_BLOCK  372
#define TILES_DLG    376
#define TILES_MUG48  388
#define TILES_MUG32  424
#define TILES_GRD48  440
#define TILES_GRD32  476
#define PAL_DLG    1   // w scenach dialogowych paleta boiska jest zastepowana
#define PAL_AV1    2   // awatar Muggy'ego (w trybie fabularnym)
#define PAL_AV2    3   // awatar strażnika

// Sprite'y w OAM (PVSnesLib wymaga wielokrotnosci 4)
#define SPR_BALL  0
#define SPR_BALL2 4    // druga pilka (SPLIT)
#define SPR_FAKE  8    // falszywa pilka Maltena
#define SPR_P1    12   // do 10 sprite'ow (paletka do 80 px)
#define SPR_P2    52   // do 10 sprite'ow
#define SPR_TAIL  92   // 5 sprite'ow ogona
#define SPR_CUR1  112  // 4 rogi ramki kursora gracza 1
#define SPR_CUR2  128  // 4 rogi ramki kursora gracza 2 / AI Agenta
#define SPR_FAKE2 144  // druga falszywa pilka Maltena
#define SPR_TWIN0 148  // bliźniak paletki gracza 1 (TWIN), do 10 sprite'ow
#define SPR_TWIN1 188  // bliźniak / przewinieta czesc paletki gracza 2
#define SPR_SPARK 228  // 6 iskier Kimantero
#define SPR_TAIL2 252  // 5 sprite'ow ogona drugiej pilki (SPLIT)
#define SPR_BALL3 272  // trzecia i czwarta pilka (podwojny SPLIT)
#define SPR_BALL4 276
#define SPR_TAIL3 280  // ich ogony (po 5 sprite'ow)
#define SPR_TAIL4 300
#define TEST_UNLOCK 0   // Lucifero w QUICK MATCH dopiero po pokonaniu go w trybie fabularnym
#define SPR_COUNT 80
#define CATCH_TIME 45    // CATCH (komputer): pilka przyklejona przez 45 klatek
#define CATCH_TIME_HUMAN 480   // CATCH (gracz): strzal przyciskiem A, samoczynnie po 8 s
#define CAMO_TIME  360   // CAMO: 6 s
#define BLINK_RET  16    // BLINK STRIKE: powrot na miejsce w 16 klatek
#define NO_Y      (-999)
#define FIELD_H   (FIELD_BOTTOM - FIELD_TOP)
#define TWIN_TIME  528   // TWIN: 8.8 s
#define SWAP_TIME 360    // SWAP: 6 s
#define SLOW_TIME  360   // SLOW: 6 s
#define PAD_MAX_SPR 10
#define TILE_PAD_TOP  0   // dol paletki to ten sam kafelek odbity w pionie
#define TILE_PAD_MID  1
#define TILE_BALL     2
#define TILE_TAIL     3   // 3..7
#define TILE_CORNER   8

// Dzwieki: numer = indeks w tablicy sounds[] (patrz init_sound)
#define SND_TADA     0
#define SND_TOK1     1
#define SND_TOK2     2
#define SND_WALL     3
#define SND_FANFARE  4
#define SND_SAD      5
#define SND_TICK     6
#define SND_CONFIRM  7
#define SND_READY    8
#define SND_ARM      9
#define SND_SUPER    10   // SND_SUPER + PWR_x = dzwiek danej mocy
#define SND_CURVE    11
#define SND_ZIGZAG   12
#define SND_GHOST    13
#define SND_THUNDER  14   // grzmot (burza w ostatniej walce)
#define SND_COUNT    15
#define SND_PITCH    6    // 6 * 2000 Hz = 12 kHz, tak jak w plikach WAV
#define SND_REGION   66   // pamiec SPC na najdluzszy dzwiek: 66 * 256 B

// MSU-1: rejestry pod $2000-$2007
#define MSU_STATUS   (*(vuint8 *)0x2000)
#define MSU_TRACK_LO (*(vuint8 *)0x2004)
#define MSU_TRACK_HI (*(vuint8 *)0x2005)
#define MSU_VOLUME   (*(vuint8 *)0x2006)
#define MSU_CONTROL  (*(vuint8 *)0x2007)
#define MSU_BUSY     0x40
#define MSU_ERROR    0x08
#define MSU_PLAY_LOOP 0x03

// Mieszanie kolorow: normalnie polprzezroczyste sprite'y z palet 4-7 (ogon),
// przez 2 klatki po uderzeniu specjalnym bialy blysk calego ekranu
#define CM_NORMAL_WSEL  0x02   // zrodlo: podekran (na nim BG1 = boisko)
#define CM_NORMAL_ADSUB 0x50   // dodawanie z polowa jasnosci, tylko sprite'y
#define CM_FLASH_WSEL   0x00   // zrodlo: staly kolor
#define CM_FLASH_ADSUB  0x3F   // dodawanie do wszystkich warstw i tla
#define CM_FLASH_LEVEL  12     // jasnosc blysku (0..31)

enum { ST_TITLE, ST_SELECT, ST_SERVE, ST_PLAY, ST_PAUSE, ST_OVER, ST_DIALOG, ST_SSELECT, ST_RESULT, ST_THEEND, ST_CHARS, ST_POINTS, ST_NAME, ST_HISCORE, ST_DIFF };
enum { AFT_SELECT, AFT_MATCH, AFT_THEEND, AFT_G1 };
enum { MUS_OFF, MUS_LOADING, MUS_READY, MUS_PLAYING };

// Kolory zmieniane w trakcie gry (indeksy CGRAM i wartosci)
#define CGI_P1    0
#define CGI_P2    1
#define CGI_BAR1  2
#define CGI_BAR2  3
#define CGI_BALL  4
#define CGI_BACK  5   // tlo ekranu (Blinker, CAMO)
#define CGI_P1E   6   // krawedz paletki gracza 1 (CAMO)
#define CGI_P2E   7   // krawedz paletki gracza 2 (CAMO, teczowa krawedz Kimantero)
#define CG_COUNT  8
const u8 cg_index[CG_COUNT] = {128 + 1, 144 + 1, PAL_BAR * 16 + 2, PAL_BAR * 16 + 3, 160 + 3, 0, 128 + 2, 144 + 2};
#define COL_P1       RGB8(150, 20, 50)
#define COL_P1_LIT   RGB8(240, 110, 140)
#define COL_P2       RGB8(24, 88, 200)
#define COL_P2_LIT   RGB8(130, 190, 255)
#define COL_BAR1     RGB8(205, 60, 90)
#define COL_BAR1_LIT RGB8(255, 210, 220)
#define COL_BAR2     RGB8(80, 140, 240)
#define COL_BAR2_LIT RGB8(210, 235, 255)
#define COL_WHITE    RGB8(255, 255, 255)
#define COL_MUG      RGB8(0, 160, 170)     // turkusowa paletka Muggy'ego
#define COL_MUG_LIT  RGB8(120, 240, 240)
#define COL_MUG_EDGE RGB8(110, 224, 224)
const u16 ball_col[4] = {RGB8(255, 140, 0), RGB8(64, 224, 88), RGB8(255, 232, 48), RGB8(176, 216, 255)};

// Palety sprite'ow ustawiane w kodzie
const u16 pal_p2[4] = {0, COL_P2, RGB8(110, 170, 255), COL_WHITE};
const u16 pal_ballsp[4] = {0, 0, 0, COL_WHITE};
const u16 pal_tail[6] = {0, RGB8(255, 255, 255), RGB8(255, 232, 96), RGB8(255, 150, 40),
                         RGB8(224, 56, 40), RGB8(136, 24, 24)};

// Ekran wyboru mocy: ikony w siatce 2 x 2
const u8 icon_col[4] = {4, 18, 4, 18};
const u8 icon_row[4] = {11, 11, 17, 17};
const char *pwr_name[PWR_ALL + 1] = {"SUPER SHOT", "CURVE", "ZIGZAG", "GHOST", "GROW", "SPLIT", "FORTRESS",
                                 "TWIN", "SWAP", "SLOW", "CATCH", "BLINK STRIKE", "CAMO", "CHAOS", "HELL"};
const char *pwr_desc[PWR_ALL + 1] = {"4X SPEED + COMET TAIL     ", "BALL FLIES IN AN ARC      ",
                           "BALL ZIGZAGS UP AND DOWN  ", "BALL VANISHES MIDCOURT    ",
                           "PADDLE GROWS TO 80 PX     ", "BALL SPLITS INTO TWO      ",
                           "3-GAP WALL BEHIND YOU     ", "MIRROR TWIN PADDLE        ",
                           "INVERTS OPPONENT CONTROLS ", "SLOWS OPPONENT PADDLE     ",
                           "CATCH THE BALL, AIM, SHOOT", "TELEPORT AND STRIKE CLOSE ",
                           "HIDES OPPONENT PADDLE     ", "RANDOM GUARDIAN POWER     ",
                           "THE WORLD TURNS TO RUST   "};
const char *lock_desc[NUM_GUARD] = {"DEFEAT RUDEN TO UNLOCK    ", "DEFEAT MALTEN TO UNLOCK   ",
                            "DEFEAT WALLER TO UNLOCK   ", "DEFEAT CYBER-DOPPLER      ",
                            "DEFEAT CHANGERO TO UNLOCK ", "DEFEAT CHRONOS TO UNLOCK  ",
                            "DEFEAT MAGNETON TO UNLOCK ", "DEFEAT TELEMENTOR         ",
                            "DEFEAT BLINKER TO UNLOCK  ", "DEFEAT KIMANTERO          ",
                            "DEFEAT LUCIFERO           "};
const char blank28[] = "                            ";

// Strażnicy trybu fabularnego (etap 2: pierwsi trzej)
#define STORY_STAGES 11   // 11. etap (Lucifero) pojawia sie dopiero po przemianie Kimantero
#define GROW_H       80     // GROW: paletka 80 px...
#define GROW_TIME    540    // ...przez 9 s
#define FORT_TIME    480    // FORTRESS: 8 s
#define SPLIT_VY     0x00C0 // SPLIT: pilki rozchodza sie o +-0.75 px na klatke
#define SPLIT_SLOW   7      // SPLIT: druga pilka leci z predkoscia 7/10 (30% wolniej)
#define WALL_HP      8      // Waller: stale mury znikaja po 8 uderzeniach pilki-komety
#define EDGE_TOL     2      // tolerancja kolizji na rogach paletki (px)
const char *g_name[NUM_GUARD] = {"RUDEN", "MALTEN", "WALLER", "CYBER-DOPPLER", "CHANGERO", "CHRONOS",
                                    "MAGNETON", "TELEMENTOR", "BLINKER", "KIMANTERO", "LUCIFERO"};
const u8 g_height[NUM_GUARD] = {50, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32};
const u16 g_speed[NUM_GUARD] = {0x0100, 0x0140, 0x0100, 0x0140, 0x0180, 0x0140, 0x0180, 0x0140, 0x01C0, 0x0340, 0x0200};
const u8 g_points[NUM_GUARD] = {5, 5, 5, 5, 5, 6, 7, 8, 9, 10, 10};
const u8 g_power[NUM_GUARD] = {PWR_GROW, PWR_SPLIT, PWR_FORTRESS, PWR_TWIN, PWR_SWAP, PWR_SLOW,
                                  PWR_CATCH, PWR_BLINK, PWR_CAMO, PWR_CHAOS, PWR_HELL};
const u8 story_mod[NUM_GUARD] = {MOD_RUDEN, MOD_MALTEN, MOD_WALLER, MOD_DOPPLER, MOD_CHANGERO,
                                    MOD_CHRONOS, MOD_MAGNETON, MOD_TELEMENTOR, MOD_BLINKER, MOD_KIMANTERO,
                                    MOD_LUCIFERO};   // Lucifero: mgla (pozycje 0-3), przemiana (od pozycji 4)
const u16 g_fill[NUM_GUARD] = {RGB8(168, 72, 40), RGB8(112, 48, 152), RGB8(120, 120, 132),
                                  RGB8(176, 184, 200), RGB8(240, 140, 40), RGB8(184, 140, 60),
                                  RGB8(90, 120, 170), RGB8(110, 50, 170), RGB8(240, 220, 140), RGB8(40, 36, 56),
                                  RGB8(110, 14, 14)};
const u16 g_lit[NUM_GUARD] = {RGB8(240, 140, 100), RGB8(190, 120, 230), RGB8(200, 200, 214),
                                 RGB8(236, 240, 250), RGB8(255, 200, 120), RGB8(240, 210, 120),
                                 RGB8(160, 190, 240), RGB8(190, 130, 240), RGB8(255, 250, 220), RGB8(120, 110, 150),
                                 RGB8(200, 40, 30)};
const u16 g_edge[NUM_GUARD] = {RGB8(224, 124, 80), RGB8(128, 255, 80), RGB8(80, 184, 255),
                                  RGB8(255, 64, 64), RGB8(40, 200, 230), RGB8(255, 240, 200),
                                  RGB8(230, 48, 48), RGB8(230, 120, 255), RGB8(255, 176, 32), RGB8(255, 200, 40),
                                  RGB8(255, 96, 32)};
const u8 power_snd[PWR_ALL + 1] = {10, 11, 12, 13, 10, 12, 3, 13, 12, 11, 9, 13, 13, 10, SND_THUNDER};
// Blinker: kolory tla (nasycone, ale srednio jasne, zeby biala pilka byla czytelna)
const u16 back_cols[6] = {RGB8(150, 36, 36), RGB8(36, 128, 56), RGB8(40, 64, 176), RGB8(112, 44, 150),
                          RGB8(176, 92, 16), RGB8(20, 120, 128)};
const u16 rainbow[6] = {RGB8(255, 64, 64), RGB8(255, 200, 40), RGB8(64, 220, 120), RGB8(64, 140, 255),
                        RGB8(200, 96, 255), RGB8(255, 255, 255)};
const u8 chaos_set[8] = {PWR_GROW, PWR_SPLIT, PWR_FORTRESS, PWR_TWIN, PWR_SWAP, PWR_SLOW, PWR_CATCH, PWR_CAMO};   // dzwiek uderzenia dla kazdej mocy

// Bezposredni zapis do VRAM (kolumny blokow Wallera i FORTRESS)
#define VPORT_MAIN  (*(vuint8 *)0x2115)
#define VPORT_ADDL  (*(vuint8 *)0x2116)
#define VPORT_ADDH  (*(vuint8 *)0x2117)
#define VPORT_DATAL (*(vuint8 *)0x2118)
#define VPORT_DATAH (*(vuint8 *)0x2119)
// Kanal DMA 1 do kopiowania kolumny mapy (VRAM z przeskokiem o 32 slowa)
#define DMA1_P   (*(vuint8 *)0x4310)
#define DMA1_B   (*(vuint8 *)0x4311)
#define DMA1_AL  (*(vuint8 *)0x4312)
#define DMA1_AH  (*(vuint8 *)0x4313)
#define DMA1_AB  (*(vuint8 *)0x4314)
#define DMA1_SL  (*(vuint8 *)0x4315)
#define DMA1_SH  (*(vuint8 *)0x4316)
#define DMA_EN   (*(vuint8 *)0x420B)
const u8 think_delay[12] = {3, 3, 4, 4, 5, 5, 6, 7, 8, 10, 13, 16};

//---------------------------------------------------------------------------------
u16 ball_x, ball_y;  // 8.8
s16 vel_x, vel_y;    // 8.8, ze znakiem
s16 p1_y, p2_y;      // gorna krawedz paletek
s16 cpu_error;       // celowy blad komputera, losowany po kazdym odbiciu
u16 cpu_acc;         // akumulator ulamkowej predkosci komputera
u16 score1, score2;  // u16, bo printf w PVSnesLib czyta argumenty jako 16-bitowe
u8 two_players;
u8 serve_right;
u8 state;
u16 timer, frame;
u16 pad0, pad1, pad0_new, pad1_new;
u16 bgmap[32 * 32];  // mapa BG1 skladana w RAM i kopiowana do VRAM
brrsamples sounds[SND_COUNT];
u8 msu_present, music_state, music_want;

// moce
u8 power[2], last_power[2];
u8 bar[2], armed[2];
u8 cpu_arm_wait;
u8 sp_type, sp_owner;      // aktywne uderzenie specjalne i kto je wykonal
s16 sp_saved;              // predkosc sprzed Superstrzalu
s16 curve_acc;
u8 zig_timer, zig_flips;
u8 ghost_hidden, ghost_blink, cpu_ghost_mode, ghost_lag;
s16 cpu_ghost_target;

// ekran wyboru
u8 sel_idx[2], sel_done[2], cpu_think, cpu_delay, ready_timer, desc_dirty;

// historia pozycji pilki (ogon komety i opozniona reakcja komputera)
u8 hist_x[16], hist_y[16], hist_pos;
// Dodatkowe pilki (SPLIT): do 3, czyli razem z glowna do 4 na boisku
#define XB 3
u8 xh_x[XB][16], xh_y[XB][16], xtail[XB];   // historia pozycji (ogon) i dlugosc ogona
u8 xb_on[XB], cpu_tgt, xk;
u16 xb_x[XB], xb_y[XB];
s16 xb_vx[XB], xb_vy[XB];
const u16 xb_spr[XB] = {SPR_BALL2, SPR_BALL3, SPR_BALL4};
const u16 xt_spr[XB] = {SPR_TAIL2, SPR_TAIL3, SPR_TAIL4};
s16 pull_step;
u8 xb_cs[XB];            // dodatkowa pilka spowolniona przez Chronosa
s16 xb_csv[XB];          // ...i jej predkosc sprzed spowolnienia
u16 xb_pull[XB];         // przyciaganie Magnetona tej pilki
void clear_xballs(void);
void xb_move_asm(u16 k);                  // procedury w data.asm
void xb_draw_asm(u16 k, u16 sb, u16 st);
void tail_draw_asm(void);
extern u16 xm_pbx, xm_pby, xm_flags;
u8 tail_len;

// efekty obslugiwane w VBlank
u8 shake_t, flash_t, sfx_lock, scroll_dirty, cm_dirty, hud_dirty;
extern u8 digi_active;     // zmienne biblioteki dzwieku (snesmod)
extern u16 digi_remain;
extern u16 lag_frame_counter;
u8 snd_dead;              // procesor dzwieku nie odpowiada: efekty wyciszone do konca sesji
u8 music_on;              // ustawienie MUSIC ON/OFF (zapisywane na karcie)
u8 spc_mus;               // modul muzyki: 0 brak, 1 wczytany, 2 gra
u8 qm_track;              // QUICK MATCH / FAST & FURIOUS: 0 = tango, 1..10 = utwor strażnika
#define MUSIC_VOL 200     // glosnosc muzyki (efekty zostaja wyrazne)
u16 spc_err;

s16 shake_x, spr_dx;
u8 cm_wsel, cm_adsub, cm_data;
u16 cg_want[CG_COUNT], cg_cur[CG_COUNT];

// paletki o zmiennej wysokosci (Ruden, GROW)
u8 pad_h[2], pad_target[2], pad_base[2];
u16 grow_timer[2], fort_timer[2];
// bloki za paletkami: wiersze mapy 6..24, kolumna 0 (gracz 1) i 31 (gracz 2)
u8 blk[2][32];
u8 blk_dirty, court_shown;
u16 colbuf[2][19];   // gotowe kolumny blokow (wiersze 6..24) do wyslania przez DMA
// druga pilka (SPLIT) i falszywa pilka Maltena
u8 split_active;   // liczba dodatkowych pilek na boisku (0..3)
u8 fake_active[2], fake_life[2];
u16 fake_x[2], fake_y[2], fake_timer;
s16 fake_vx[2], fake_vy[2];
// Waller: wytrzymalosc stalych murow (0 = gorny, 1 = dolny)
u8 wall_hp[4];   // [strona * 2 + 0/1]: gorny i dolny mur Wallera
// Muggy: moce zebrane w biezacym podejsciu (przelaczane L/R)
u8 run_pw[16], run_n, run_cur;
// parametry meczu
u16 cpu_speed, win_score;
// Poziom trudnosci (gra z komputerem): 0 EASY (jak dotad), 1 NORMAL, 2 HARD.
// Wyzszy poziom = lepsza gra przeciwnika (reakcja, celnosc, predkosc, przewidywanie, odbicie
// krawedzia paletki) i uzycie mocy zaraz po zapelnieniu paska. Zdolnosci strażnikow bez zmian.
u8 difficulty, diff_next, diff_idx;
u8 cpu_react, cpu_delay_d, pred_ok, pred_ball, cpu_err_r, cpu_pw, cpu_aim_k, pred_cool;
s16 pred_y, pred_vx, pred_vy;
// Wartosci dobrane pomiarem: na tych samych trudnych uderzeniach (na NORMAL i HARD szybszych,
// jak cala gra) komputer przepuszcza EASY 12,6%, NORMAL ok. 6% (2x trudniej), HARD ok. 4% (3x) pilek.
const u8 diff_react[3] = {128, 118, 114};  // komputer zaczyna gonic pilke po minieciu tej kolumny
const u8 diff_delay[3] = {12, 10, 9};     // opoznienie reakcji na podkrecona i zygzak (klatki)
const u8 diff_err[3] = {10, 8, 7};         // blad celowania +-px
const u8 diff_spd[3] = {16, 18, 20};       // predkosc paletki x n/16
const u8 diff_aim[3] = {0, 1, 2};          // odbicie krawedzia paletki: n/8 jej wysokosci, w strone dalsza od gracza
const u8 diff_ball[3] = {64, 68, 72};      // predkosc pilki x n/64: start, przyrost po odbiciu i limit (+6,25% / +12,5%)
u16 serve_spd, spd_step, max_spd;
const u8 diff_pw[3] = {0, 1, 1};           // waga przewidywania: n/4 (reszta: biezaca wysokosc pilki)
void show_difficulty(u8 next);
void show_points(u8 players2);
void show_story_select(void);
u16 col_p1, col_p1_lit, col_p2, col_p2_lit;
// tryb fabularny
u8 story, stage, story_power, result_win;
u16 luc_carry;   // punkty, ktore Muggy stracil z Kimantero - licza sie dalej w walce z Lucifero
u8 luc_phase;    // scena przemiany: 0 = jeszcze Kimantero (okienka 1-6), 1 = Lucifero
u16 unlock_mask, result_timer;
u8 menu_idx, erase_ask;
u8 luc_test;   // na czas prac: walka z Lucifero wprost z menu tytulowego (STAGE 11: LUCIFERO)
// Tryby QUICK MATCH (game_mode 0) i FAST & FURIOUS (game_mode 1)
u8 title_sub;      // 1 = podmenu 1 PLAYER / 2 PLAYERS po wybraniu trybu
u8 game_mode, ff_mode, ff_level, pts_idx, pts_players;
const u8 pts_val[6] = {3, 5, 7, 10, 15, 21};   // do ilu punktow trwa mecz
#define FF_MAX 0x2000   // FAST & FURIOUS: techniczny limit 32 px na klatke

// FAST & FURIOUS: moc przyspieszajaca pilke nigdy jej nie spowalnia. Jesli jej predkosc
// nie jest co najmniej o 5% wyzsza od biezacej, pilka dostaje biezaca predkosc + 6.25%.
// Poza tym trybem zwraca predkosc mocy bez zmian.
s16 ff_boost(s16 v, s16 cur)
{
    if (!ff_mode)
        return v;
    if (v < cur + cur / 20)        // mniej niz +5%
        v = cur + cur / 16;        // biezaca + 6.25%
    if (v > FF_MAX)
        v = FF_MAX;
    return v;
}
u8 box_i, box_end, typing, tcol, trow, tick_n, speaker, after_scene;
u8 scene_now;   // numer wyswietlanej sceny
const char *tptr;
char chbuf[2];
u16 avpal[3][16], avbuf[16], avbuf3[3][16];   // awatary: Muggy, strażnik, drugi bliźniak Cyber-dopplera
u8 av_dim[3], avpal_dirty;
u8 luc_on;   // plansza Lucifero (Mode 7) aktywna
u16 luc_nb;   // (data.asm) liczba zapamietanych bajtow przeliczonych sprite'ow
// moce strażnikow 4-6 i ich zdolnosci stale
u16 twin_timer[2], swap_timer[2], slow_timer[2];
u8 cpu_inv, cpu_inv_t, status_dirty;
u8 zig_final_t;   // klatki od ostatniego skretu zygzaka (komputer widzi wtedy prawdziwy kierunek)
u8 zig_track;     // komputer sledzi pas, w ktorym wije sie zygzak
s16 zig_ymin, zig_ymax;
u8 ghost_on[2], wrap[2];   // widmowy blizniak Cyber-dopplera, przechodzenie Changero przez krawedz
u16 ghost_t[2];
// Postacie: kazda strona boiska gra jakas postacia (w trybie fabularnym: Muggy i strażnik)
#define CH_JOY    0    // Robocik-dzojstik (JOYBOT)
#define CH_SFC    2
#define CH_MUGGY  3
#define CH_G0     4    // strażnicy: CH_G0 + numer strażnika (0..9)
u8 char_of[2];
u8 tele0_done, tele0_cool, tele0_flash;   // Telementor po lewej stronie (gracz)
// Burza (ostatnia walka; w trybach 1/2 PLAYER, gdy Kimantero gra po lewej)
u8 storm_on, bolt_t, bolt_row, bolt_col, bolt_dirty, thunder_t, bright_max, cm_norm_adsub;
u16 rain_x, rain_y, storm_t, storm_flash;
u16 bolt_save[16], bolt_new[16];
u8 storm_bri;   // zadana jasnosc (ustawiana w VBlank); 0 = bez zmiany
u16 font_pal[16];   // kopia palety czcionki
void bolt_upload(void);
// Areny strażnikow (tla walk): 0 brak, 1 Ruden (gradient, kurz, ogry), 2 Malten (gradient, mgla)
u8 arena, arena_hidden, arena_apply, hdma_mask, hdma_start, wave_buf, wave_ready, wave_phase;
u8 crowd_frame, crowd_step, crowd_t, crowd_dirty, cheer_t;
u8 eye_i, eye_dir, eye_t, eye_dirty;   // swiecace oczy ogrow: puls kolorow 7 (oczy) i 8 (poswiata)
const u16 eye_glow[16] = {RGB8(150, 20, 10), RGB8(157, 26, 12), RGB8(164, 32, 15), RGB8(171, 38, 17), RGB8(178, 44, 20), RGB8(185, 50, 22), RGB8(192, 56, 25), RGB8(199, 62, 27),
                          RGB8(206, 68, 30), RGB8(213, 74, 32), RGB8(220, 80, 35), RGB8(227, 86, 37), RGB8(234, 92, 40), RGB8(241, 98, 42), RGB8(248, 104, 45), RGB8(255, 110, 50)};
const u16 eye_halo[16] = {RGB8(40, 10, 6), RGB8(44, 11, 6), RGB8(49, 12, 6), RGB8(54, 13, 7), RGB8(58, 14, 7), RGB8(63, 15, 7), RGB8(68, 16, 8), RGB8(72, 17, 8),
                          RGB8(77, 18, 8), RGB8(82, 19, 8), RGB8(86, 20, 9), RGB8(91, 21, 9), RGB8(96, 22, 9), RGB8(100, 23, 10), RGB8(105, 24, 10), RGB8(110, 24, 10)};
const u8 crowd_seq[4] = {0, 1, 2, 1};   // ogry: dol, srodek, gora, srodek (pary w przeciwfazie)
// Arena Wallera: pochodnie (kolumny mapy), migotanie swiatla, nietoperze
#define TORCHES 4
#define BATS 5
#define SPR_BAT 320    // sprite'y 80-89 (po 2 na nietoperza)
#define TILE_BAT 32    // 2 kafelki sprite'ow: polowa nietoperza w 2 klatkach skrzydel
const u8 torch_col[TORCHES] = {7, 13, 19, 25};
u8 tor_f[TORCHES], tor_t[TORCHES], torch_dirty, glow_lv, glow_cur, glow_t;
const u16 glow_col[5] = {RGB8(104, 58, 24), RGB8(120, 68, 28), RGB8(134, 76, 32), RGB8(146, 84, 34), RGB8(158, 92, 38)};
s16 bat_x[BATS], bat_y[BATS], bat_vx[BATS];   // pozycja i predkosc w 1/16 piksela
u8 bat_on[BATS], bat_del[BATS], bat_rise[BATS], bat_sy;
u16 bat_age[BATS], bat_timer;
const s8 bat_bob[16] = {0, 1, 2, 2, 3, 2, 2, 1, 0, -1, -2, -2, -3, -2, -2, -1};
const u16 bat_spr[BATS] = {SPR_BAT, SPR_BAT + 8, SPR_BAT + 16, SPR_BAT + 24, SPR_BAT + 32};   // bez mnozenia
const u8 bat_ph[BATS] = {0, 5, 10, 15, 4};    // przesuniecie fazy kolysania
const u8 bat_fl[BATS] = {0, 3, 6, 9, 12};     // przesuniecie fazy skrzydel
const u8 bat_dl[BATS] = {0, 9, 18, 27, 36};   // kolejnosc wylotu
u8 arn_rng;   // szybki generator losowy dla efektow aren (ustawiany w main)
u16 bt_age, bt_x, bt_y, bt_r, bt_t, bt_id, bat_n;   // robocze zmienne procedury bats_asm
void bats_asm(void);   // data.asm
u8 arn_rand(void)
{
    u8 r = arn_rng;
    r ^= r << 3;
    r ^= r >> 5;
    r ^= r << 1;
    if (!r)
        r = 0x5A;
    arn_rng = r;
    return r;
}
void hide_bats(void);
void vblank_arena2(void);   // areny 4-9 (Cyber-doppler ... Blinker)
void arena2_reset(void);
u8 mag_glow;                // Magneton przyciaga pilke: linie pola rozblyskuja (klatki)
// Ekran tytulowy (blyskawice) i pokaz po bezczynnosci
u8 demo, demo_prev, demo_over, tfl_k, tfl_side, tcol_dirty;
s8 demo_err;
u16 title_idle, tfl_t, demo_t, tfl_col[4];

u16 arena_x, last_owner_score;
u8 hdma_grad[256];         // HDMA: kolor tla co 4 linie (gradient nieba); tablica ma 201 bajtow z koncem
u8 wave_ind[32][236];      // HDMA posrednie: dla kazdej fazy fali wskazniki pasow 2-liniowych
u16 wave_val[32];          // 32 wartosci przesuniecia mgly (dryf + fala), liczone co klatke
u16 wave_zero;             // przesuniecie 0 (pasek u gory i dol ekranu)
u16 crowd_rows[5][256];    // 5 klatek tlumu ogrow: wiersze 17-24 mapy boiska (4 = wiwat w podskoku)
#define HDMAEN_REG (*(vuint8 *)0x420C)
#define DMA_REG(ch, r) (*(vuint8 *)(0x4300 + (ch) * 16 + (r)))
#define CM_STORM_ADSUB 0x54   // jak zwykle + polprzezroczysty deszcz (BG3)
#define STORM_BRIGHT   11     // przyciemniona scena w trakcie burzy
#define SFP_BGMODE (*(vuint8 *)0x2105)
// wybor postaci w trybach 1/2 PLAYER
#define TILES_GRD32B 528   // drugi slot malego awatara strażnika (strona prawa)
#define TILES_CHARS  544   // ekran wyboru postaci: male awatary wszystkich strażnikow (10 x 16)
#define NO_SLOT      0xFFFF
#define CHAR_N 14
const u8 list_char[CHAR_N] = {CH_MUGGY, CH_JOY, CH_SFC, CH_G0, CH_G0 + 1, CH_G0 + 2, CH_G0 + 3, CH_G0 + 4,
                              CH_G0 + 5, CH_G0 + 6, CH_G0 + 7, CH_G0 + 8, CH_G0 + 9, CH_G0 + 10};
u8 csel[2], cdone[2], cphase, ctimer, prev_dirty, prev_wait;
u16 prev_pal[2][16];   // palety podgladow przygotowane poza VBlank
u8 prev_slot[2];
u16 *gi_map32;
u8 *gi_pal;
u16 cf, cl, ce;   // kolory paletki postaci (wypelnienie, rozjasnienie, krawedz)
// strażnicy 7-10
u8 pad_x[2];                        // x paletek (BLINK STRIKE przenosi je na srodek)
u8 catch_side, tele_done, tele_flash, blink_side, blink_ret, force_tail, chaos_last, back_idx;
u16 catch_timer;   // CATCH: klatki do samoczynnego wystrzalu
u8 blink_left[2];  // BLINK STRIKE: pozostale teleporty z jednej aktywacji
u16 camo_timer[2], back_t, pull_total, back_col, col_p1_edge, col_p2_edge;
u8 chaos_icon_t[2];
s16 spk_x[6], spk_y[6], spk_vx[6], spk_vy[6];
// TWIN: samodzielny, wysuniety do przodu blizniak; Chronos; Kimantero; Telementor; dialogi
u8 twin_x[2];
s16 twin_y[2];
u16 twin_acc[2];
s16 hit_fx;                 // x krawedzi paletki przy odbiciu (blizniak); NO_Y = zwykla paletka
u8 chron_slowed, kim_level, tele_cool;
s16 chron_saved;
u16 txt_base, chq_addr, chq_val;
u8 chq_pending;
u8 spk_life[6];
u8 spk_on;   // iskry zyja albo sa jeszcze na ekranie
s16 extra_y(u8 p);

// Czy strona p gra strażnikiem nr g
u8 is_g(u8 p, u8 g)
{
    return char_of[p] == CH_G0 + g;
}

u8 any_g(u8 g)
{
    return char_of[0] == CH_G0 + g || char_of[1] == CH_G0 + g;
}
u16 *g48_map, *g32_map;
u8 save_buf[136];   // 0-15: postepy i ustawienia, 16-128: tabela najlepszych wynikow
// Imie gracza (tryb fabularny) i najlepsze wyniki
#define NAME_MAX 9
#define HS_N 10
#define HS_EMPTY ((s16)0x8000)
char player_name[NAME_MAX + 1];
char hs_name[HS_N][NAME_MAX + 1];
s16 hs_score[HS_N];
s16 run_score;   // podejscie w trybie fabularnym: punkty zdobyte - punkty stracone
u8 hs_new, name_pos, name_rep, hs_blink;
char name_ed[NAME_MAX + 1];
char dlg_buf[200], dlg_tmp[200];
const char name_chars[] = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.";

//---------------------------------------------------------------------------------
// MUZYKA (MSU-1)
//---------------------------------------------------------------------------------
u8 msu_detect(void)
{
    // MSU-1 przedstawia sie napisem "S-MSU1" pod $2002-$2007
    const char *sig = "S-MSU1";
    vuint8 *id = (vuint8 *)0x2002;
    u8 i;
    for (i = 0; i < 6; i++)
    {
        if (id[i] != sig[i])
            return 0;
    }
    return 1;
}

void music_off(void)
{
    music_want = 0;
    if (msu_present)
        MSU_CONTROL = 0;
    music_state = MUS_OFF;
}

void music_load(u8 track)
{
    music_want = 0;
    if (!msu_present)
        return;
    MSU_TRACK_LO = track;   // plik superfamipong-<track>.pcm
    MSU_TRACK_HI = 0;   // zapis starszego bajtu uruchamia ladowanie (od poczatku utworu)
    music_state = MUS_LOADING;
}

// Wywolywane co klatke: nie blokuje gry, gdy karta SD jeszcze laduje utwor
void music_update(void)
{
    if (music_state == MUS_LOADING && !(MSU_STATUS & MSU_BUSY))
    {
        if (MSU_STATUS & MSU_ERROR)
        {
            music_state = MUS_OFF;   // brak pliku .pcm - gramy bez muzyki
        }
        else
        {
            MSU_VOLUME = MUSIC_VOLUME;
            music_state = MUS_READY;
        }
    }
    if (music_state == MUS_READY && music_want)
    {
        MSU_CONTROL = MSU_PLAY_LOOP;
        music_state = MUS_PLAYING;
    }
    else if (music_state == MUS_PLAYING && !music_want)
    {
        MSU_CONTROL = 0;   // pauza: pozycja w utworze zostaje zapamietana
        music_state = MUS_READY;
    }
}

//---------------------------------------------------------------------------------
// DZWIEKI (SPC700)
//
// Na prawdziwej konsoli sterownik SPC700 nie lubi polecen wysylanych zbyt gesto
// (np. dwa dzwieki w jednej klatce): potrafi sie zawiesic na zapetlonej probce.
// Dlatego dzwieki ida przez kolejke: najwyzej jeden co 2 klatki, a dzwiek o nizszym
// priorytecie nie przerywa grajacego dzwieku o wyzszym.
//---------------------------------------------------------------------------------
#define SND_NONE 0xFF
const u8 snd_prio[SND_COUNT] = {9, 4, 4, 3, 10, 10, 1, 5, 6, 7, 8, 8, 8, 8, 4};   // grzmot jak odbicie: nie blokuje tokow
const u8 snd_len[SND_COUNT] = {57, 6, 6, 5, 122, 148, 2, 10, 27, 15, 24, 24, 21, 30};   // w klatkach
u8 snd_req, snd_gap, snd_cur_prio, snd_left;

void play_sound(u8 i)
{
    if (snd_req == SND_NONE || snd_prio[i] >= snd_prio[snd_req])
        snd_req = i;
}

// Pauza muzyki: sterownik SPC700 zawieszal sie czasem na zapetlonej nucie, gdy polecenie
// pauzy trafilo w chwili innego polecenia albo przesylania probki efektu. Pauze i wznowienie
// wysylamy wiec dopiero w spokojnej chwili: z odstepem od poprzedniego polecenia, nie w tej
// samej klatce co efekt i po zakonczeniu przesylania probki.
u8 pause_cmd;   // 0 brak, 1 pauza czeka, 2 wznowienie czeka, 3 zatrzymanie czeka
u8 mus_pos;     // moc Lucifero: pozycja utworu + 1 do wlaczenia (0 = brak)
extern u8 spc_fread, spc_fwrite;   // kolejka wiadomosci biblioteki dzwieku (odczyt / zapis)
void spc_flush_safe(void);
// Po spcPlay SPC700 przez kilkanascie klatek ustawia echo modulu i nie odbiera strumieni efektow
// (zadanie strumienia konczylo sie porzuceniem efektu). Czekamy, az zglosi granie (port 2, bit 5).
#define REG_APUIO2 (*(vuint8 *)0x2142)
u8 play_wait;

void sound_tick(void)
{
    if (snd_dead)
        return;
    if (snd_left)
        snd_left--;
    if (play_wait)
    {
        play_wait--;
        if (play_wait < 88 && (REG_APUIO2 & 0x20))   // po 2 klatkach polecenie PLAY juz dotarlo
            play_wait = 0;
        else
            return;
    }
    if (snd_gap)
    {
        snd_gap--;
        return;
    }
    if (pause_cmd)   // polecenie muzyki czeka: najpierw koniec przesylania probki, bez nowych efektow
    {
        if (digi_active)
            return;
        // Pauza: utwor gra dalej bez dzwieku (glosnosc 0), wznowienie przywraca glosnosc.
        // Biblioteczne spcPauseMusic wylaczalo wszystkie brzmiace dzwieki, a spcResumeMusic ich
        // nie przywracalo - dlugi dzwiek w tle (Lucifero) wracal dopiero po kilkunastu sekundach.
        if (pause_cmd == 1)
            spcSetModuleVolume(0);
        else if (pause_cmd == 2)
            spcSetModuleVolume(MUSIC_VOL);
        else
        {
            spcStop();   // 3: zatrzymanie muzyki (koniec meczu)
            spc_mus = 0;
            mus_pos = 0;
        }
        // Polecenia muzyki biblioteka tylko wstawia do kolejki; dostarcza je spcProcess, ktory
        // dzieli porty z przesylaniem probek. Gdy zaraz potem ruszal efekt (np. fanfara),
        // polecenie potrafilo przepasc i muzyka grala dalej / wyla. Czekamy na dostarczenie.
        spc_flush_safe();
        pause_cmd = 0;
        snd_gap = 3;   // nastepne polecenie najwczesniej za 3 klatki
        return;
    }
    // Inna czesc utworu (moc Lucifero): bez spc_flush_safe, ktore przy PLAY zatrzymywalo gre na
    // kilka klatek. Polecenie dostarcza zwykle snd_process; efekty czekaja, az dotrze i modul zagra.
    if (mus_pos && music_want && spc_mus == 2 && !digi_active)
    {
        spcPlay(mus_pos - 1);
        mus_pos = 0;
        snd_gap = 3;
        play_wait = 90;
        return;
    }
    if (snd_req == SND_NONE)
        return;
    if (spc_fread != spc_fwrite)   // polecenie muzyki jeszcze w kolejce: efekt poczeka
        return;
    if (snd_left && snd_prio[snd_req] < snd_cur_prio)
    {
        snd_req = SND_NONE;   // nie przerywamy waznieszego dzwieku drobnym
        return;
    }
    *(vuint8 *)0x420D = 0;
    spcPlaySound(snd_req);
    *(vuint8 *)0x420D = 1;
    snd_cur_prio = snd_prio[snd_req];
    snd_left = snd_len[snd_req];
    snd_req = SND_NONE;
    snd_gap = 2;
}
void set_sound(u8 i, u8 vol, u8 pan, char *start, char *end)
{
    spcSetSoundEntry(vol, pan, SND_PITCH, end - start, (u8 *)start, &sounds[i]);
}

void init_sound(void)
{
    spcAllocateSoundRegion(SND_REGION);
    // play_sound(i) czyta wpis i, liczac od OSTATNIO ustawionego wpisu w gore pamieci.
    // Dlatego ustawiamy tablice od konca: sounds[0] na samym koncu.
    set_sound(SND_THUNDER, 15, 8, &snd_thunder, &snd_thunder_end);   // (kolejnosc malejaca - patrz wyzej)
    set_sound(SND_GHOST, 15, 8, &snd_ghost, &snd_ghost_end);
    set_sound(SND_ZIGZAG, 15, 8, &snd_zigzag, &snd_zigzag_end);
    set_sound(SND_CURVE, 15, 8, &snd_curve, &snd_curve_end);
    set_sound(SND_SUPER, 15, 8, &snd_super, &snd_super_end);
    set_sound(SND_ARM, 13, 8, &snd_arm, &snd_arm_end);
    set_sound(SND_READY, 14, 8, &snd_ready, &snd_ready_end);
    set_sound(SND_CONFIRM, 13, 8, &snd_confirm, &snd_confirm_end);
    set_sound(SND_TICK, 10, 8, &snd_tick, &snd_tick_end);
    set_sound(SND_SAD, 15, 8, &snd_sad, &snd_sad_end);
    set_sound(SND_FANFARE, 15, 8, &snd_fanfare, &snd_fanfare_end);
    set_sound(SND_WALL, 12, 8, &snd_tokwall, &snd_tokwall_end);
    set_sound(SND_TOK2, 15, 10, &snd_tok2, &snd_tok2_end);
    set_sound(SND_TOK1, 15, 5, &snd_tok1, &snd_tok1_end);
    set_sound(SND_TADA, 15, 8, &snd_tada, &snd_tada_end);
}

//---------------------------------------------------------------------------------
// GRAFIKA
//---------------------------------------------------------------------------------
void load_graphics(void)
{
    u8 i;

    // BG0: tekst
    consoleInitDefaultText(PAL_FONT);
    for (i = 0; i < 16; i++)   // paleta czcionki (do samonaprawy): biala czcionka, reszta czarna
        font_pal[i] = 0;
    font_pal[1] = 0x7FFF;
    bgSetGfxPtr(0, VRAM_FONT);
    bgSetMapPtr(0, VRAM_TXT_MAP, SC_32x32);

    // BG1: wszystkie kafelki naraz, kazda grafika od swojego numeru kafelka
    bgInitTileSet(1, &court_til, &court_pal, PAL_COURT, (&court_tilend - &court_til),
                  32, BG_16COLORS, VRAM_BG1_GFX);
    bgSetMapPtr(1, VRAM_BG1_MAP, SC_32x32);
    dmaCopyVram(&logo_til, VRAM_BG1_GFX + TILES_LOGO * 16, (&logo_tilend - &logo_til));
    dmaCopyVram(&joybot32_til, VRAM_BG1_GFX + TILES_JOY * 16, (&joybot32_tilend - &joybot32_til));
    dmaCopyVram(&robot32_til, VRAM_BG1_GFX + TILES_ROBOT * 16, (&robot32_tilend - &robot32_til));
    dmaCopyVram(&icons_til, VRAM_BG1_GFX + TILES_ICONS * 16, (&icons_tilend - &icons_til));
    dmaCopyVram(&minicons_til, VRAM_BG1_GFX + TILES_MINI * 16, (&minicons_tilend - &minicons_til));
    dmaCopyVram(&bar_til, VRAM_BG1_GFX + TILES_BAR * 16, (&bar_tilend - &bar_til));
    dmaCopyVram(&blocks_til, VRAM_BG1_GFX + TILES_BLOCK * 16, (&blocks_tilend - &blocks_til));
    dmaCopyVram(&dlg_til, VRAM_BG1_GFX + TILES_DLG * 16, (&dlg_tilend - &dlg_til));
    dmaCopyVram(&muggy48_til, VRAM_BG1_GFX + TILES_MUG48 * 16, (&muggy48_tilend - &muggy48_til));
    dmaCopyVram(&muggy32_til, VRAM_BG1_GFX + TILES_MUG32 * 16, (&muggy32_tilend - &muggy32_til));
    dmaCopyCGram(&logo_pal, PAL_LOGO * 16, 32);
    dmaCopyCGram(&robot32_pal, PAL_ROBOT * 16, 32);
    dmaCopyCGram(&icons_pal, PAL_ICONS * 16, 32);
    dmaCopyCGram(&bar_pal, PAL_BAR * 16, 32);

    // Sprite'y 8x8: paleta 0 z pliku PNG, pozostale z kodu
    oamInitGfxSet(&sprites_til, (&sprites_tilend - &sprites_til),
                  &sprites_pal, (&sprites_palend - &sprites_pal),
                  0, VRAM_SPR, OBJ_SIZE8_L16);
    dmaCopyCGram((u8 *)pal_p2, 128 + 16, 8);
    dmaCopyCGram((u8 *)pal_ballsp, 128 + 32, 8);
    dmaCopyCGram((u8 *)pal_tail, 128 + 64, 12);

    setMode(BG_MODE1, 0);
    bgSetDisable(2);
    bgSetGfxPtr(2, VRAM_RAIN_GFX);   // BG3: deszcz, wlaczany tylko w trakcie burzy
    bgSetMapPtr(2, VRAM_RAIN_MAP, SC_32x32);
    dmaCopyVram(&rain_til, VRAM_RAIN_GFX, (&rain_tilend - &rain_til));
    dmaCopyVram(&rain_map, VRAM_RAIN_MAP, (&rain_mapend - &rain_map));

    // Mieszanie kolorow: boisko (BG1) rowniez na podekranie, polprzezroczysty ogon
    REG_TS = 0x02;
    cm_wsel = CM_NORMAL_WSEL;
    cm_adsub = CM_NORMAL_ADSUB;
    cm_data = 0xE0;
    REG_CGWSEL = cm_wsel;
    REG_CGADSUB = cm_adsub;
    REG_COLDATA = cm_data;

    // kolory zmieniane w trakcie gry: stan poczatkowy zgodny z zaladowanymi paletami
    cg_cur[CGI_P1] = COL_P1;
    cg_cur[CGI_P2] = COL_P2;
    cg_cur[CGI_BAR1] = COL_BAR1;
    cg_cur[CGI_BAR2] = COL_BAR2;
    cg_cur[CGI_BALL] = COL_WHITE;
    cg_cur[CGI_BACK] = 0;
    cg_cur[CGI_P1E] = RGB8(225, 100, 125);
    cg_cur[CGI_P2E] = RGB8(110, 170, 255);
    for (i = 0; i < CG_COUNT; i++)
        cg_want[i] = cg_cur[i];
}

void map_put_stride(u16 *src, u8 w, u8 h, u8 stride, u8 col, u8 row)
{
    u8 x, y;
    u16 *dst;
    for (y = 0; y < h; y++)
    {
        dst = bgmap + (row + y) * 32 + col;
        for (x = 0; x < w; x++)
            dst[x] = src[y * stride + x];
    }
}

void map_put(u16 *src, u8 w, u8 h, u8 col, u8 row)
{
    map_put_stride(src, w, h, w, col, row);
}

// Palety awatarow: mowiaca postac w pelnych kolorach, druga przygaszona o polowe
u16 luc_pal[16];   // zastepczy awatar Lucifero (etap 1)
// Paleta awatara (zatwierdzona): kolory Kimantero (teczowy kontur) zamienione na krew, szkarlat i zar.
// 1 kontur, 2 wnetrze, 3 prawy gorny brzeg, 4 prawy dolny brzeg i usta, 5 lewy dolny brzeg i oko,
// 6 lewy gorny brzeg, 7 drugie oko, 8 blask
const u16 luc_av_pal[16] = {0, RGB8(8, 4, 4), RGB8(56, 8, 8), RGB8(208, 28, 16), RGB8(255, 156, 32),
                            RGB8(232, 72, 16), RGB8(92, 10, 18), RGB8(244, 92, 24), RGB8(255, 232, 176),
                            0, 0, 0, 0, 0, 0, 0};
void set_avatar_pal(u8 slot, u8 *pal)
{
    memcpy(avpal[slot], pal, 32);   // wysylane jawnie przez flush_avatar_pals / avpal_dirty
}

// Przyciemnione palety liczymy w zwyklej logice; w VBlank zostaje samo DMA.
// (Liczenie w VBlank razem z kopia tekstu nie miescilo sie w czasie i na konsoli
// spoznione zapisy psuly palete tla dialogu.)
void prep_avatar_pals(void)
{
    u8 s2, i;
    for (s2 = 0; s2 < 3; s2++)
        for (i = 0; i < 16; i++)
            avbuf3[s2][i] = av_dim[s2] ? ((avpal[s2][i] >> 1) & 0x3DEF) : avpal[s2][i];
}

void send_avatar_pals(void)
{
    dmaCopyCGram((u8 *)avbuf3[0], PAL_AV1 * 16, 32);
    dmaCopyCGram((u8 *)avbuf3[1], (PAL_AV1 + 1) * 16, 32);
    if (!luc_on)   // na planszy Lucifero paleta 4 to kolory podlogi (drugiego bliźniaka tam nie ma)
        dmaCopyCGram((u8 *)avbuf3[2], PAL_LOGO * 16, 32);
}

void flush_avatar_pals(void)   // przy wygaszonym ekranie: od razu
{
    prep_avatar_pals();
    send_avatar_pals();
    avpal_dirty = 0;
}

void load_guardian(u8 g, u16 slot32, u8 full)
{
    u8 *t48, *t32, *pal;
    u16 n48, n32;
    u8 i;
    if (g == 0)
    {
        t48 = &ruden48_til; n48 = &ruden48_tilend - &ruden48_til;
        t32 = &ruden32_til; n32 = &ruden32_tilend - &ruden32_til;
        pal = &ruden48_pal; g48_map = (u16 *)&ruden48_map; g32_map = (u16 *)&ruden32_map;
    }
    else if (g == 1)
    {
        t48 = &malten48_til; n48 = &malten48_tilend - &malten48_til;
        t32 = &malten32_til; n32 = &malten32_tilend - &malten32_til;
        pal = &malten48_pal; g48_map = (u16 *)&malten48_map; g32_map = (u16 *)&malten32_map;
    }
    else if (g == 2)
    {
        t48 = &waller48_til; n48 = &waller48_tilend - &waller48_til;
        t32 = &waller32_til; n32 = &waller32_tilend - &waller32_til;
        pal = &waller48_pal; g48_map = (u16 *)&waller48_map; g32_map = (u16 *)&waller32_map;
    }
    else if (g == 3)
    {
        t48 = &doppler48_til; n48 = &doppler48_tilend - &doppler48_til;
        t32 = &doppler32_til; n32 = &doppler32_tilend - &doppler32_til;
        pal = &doppler48_pal; g48_map = (u16 *)&doppler48_map; g32_map = (u16 *)&doppler32_map;
    }
    else if (g == 4)
    {
        t48 = &changero48_til; n48 = &changero48_tilend - &changero48_til;
        t32 = &changero32_til; n32 = &changero32_tilend - &changero32_til;
        pal = &changero48_pal; g48_map = (u16 *)&changero48_map; g32_map = (u16 *)&changero32_map;
    }
    else if (g == 5)
    {
        t48 = &chronos48_til; n48 = &chronos48_tilend - &chronos48_til;
        t32 = &chronos32_til; n32 = &chronos32_tilend - &chronos32_til;
        pal = &chronos48_pal; g48_map = (u16 *)&chronos48_map; g32_map = (u16 *)&chronos32_map;
    }
    else if (g == 6)
    {
        t48 = &magneton48_til; n48 = &magneton48_tilend - &magneton48_til;
        t32 = &magneton32_til; n32 = &magneton32_tilend - &magneton32_til;
        pal = &magneton48_pal; g48_map = (u16 *)&magneton48_map; g32_map = (u16 *)&magneton32_map;
    }
    else if (g == 7)
    {
        t48 = &telementor48_til; n48 = &telementor48_tilend - &telementor48_til;
        t32 = &telementor32_til; n32 = &telementor32_tilend - &telementor32_til;
        pal = &telementor48_pal; g48_map = (u16 *)&telementor48_map; g32_map = (u16 *)&telementor32_map;
    }
    else if (g == 8)
    {
        t48 = &blinker48_til; n48 = &blinker48_tilend - &blinker48_til;
        t32 = &blinker32_til; n32 = &blinker32_tilend - &blinker32_til;
        pal = &blinker48_pal; g48_map = (u16 *)&blinker48_map; g32_map = (u16 *)&blinker32_map;
    }
    else
    {
        t48 = &kimantero48_til; n48 = &kimantero48_tilend - &kimantero48_til;
        t32 = &kimantero32_til; n32 = &kimantero32_tilend - &kimantero32_til;
        pal = &kimantero48_pal; g48_map = (u16 *)&kimantero48_map; g32_map = (u16 *)&kimantero32_map;
    }
    if (g == G_LUCIFERO)   // zastepczy ksztalt (Kimantero), ale wlasna, piekielna paleta
    {
        for (i = 0; i < 16; i++)
            luc_pal[i] = luc_av_pal[i];
        pal = (u8 *)luc_pal;
    }
    gi_map32 = g32_map;
    gi_pal = pal;
    if (slot32 != NO_SLOT)
        dmaCopyVram(t32, VRAM_BG1_GFX + (TILES_GRD32 + slot32) * 16, n32);
    if (!full)
        return;
    dmaCopyVram(t48, VRAM_BG1_GFX + TILES_GRD48 * 16, n48);
    set_avatar_pal(1, pal);
    set_avatar_pal(2, pal);
    if (g == 3)   // drugi bliźniak: ta sama grafika z niebieskim wizjerem
    {
        avpal[2][6] = RGB8(64, 144, 255);
        avpal[2][7] = RGB8(176, 212, 255);
    }
}

void load_guardian_gfx(void)
{
    load_guardian(stage, 0, 1);
}

// Fragment mapy z przesunieciem numerow kafelkow i wlasna paleta
void map_put_pal(u16 *src, u8 w, u8 h, u8 col, u8 row, u8 pal, u16 dt)
{
    u8 x, y;
    u16 e;
    for (y = 0; y < h; y++)
    {
        for (x = 0; x < w; x++)
        {
            e = src[y * w + x];
            bgmap[(row + y) * 32 + col + x] = (((e & 0x03FF) + dt) & 0x03FF) | (e & 0xE000) | (pal << 10);
        }
    }
}

// Maly portret postaci strony p (paleta 2 + p; strażnik: kafelki w slocie strony)
void hud_char(u8 p, u8 col, u8 row)
{
    u8 c = char_of[p], pal = PAL_AV1 + p;
    if (c == CH_JOY)
    {
        dmaCopyCGram(&joybot32_pal, pal * 16, 32);
        map_put_pal((u16 *)&joybot32_map, 4, 4, col, row, pal, 0);
    }
    else if (c == CH_SFC)
        map_put((u16 *)&robot32_map, 4, 4, col, row);
    else if (c == CH_MUGGY)
    {
        dmaCopyCGram(&muggy48_pal, pal * 16, 32);
        map_put_pal((u16 *)&muggy32_map, 4, 4, col, row, pal, 0);
    }
    else
    {
        if (p)
        {
            load_guardian(c - CH_G0, TILES_GRD32B - TILES_GRD32, 0);
            dmaCopyCGram(gi_pal, pal * 16, 32);
            map_put_pal(gi_map32, 4, 4, col, row, pal, TILES_GRD32B - TILES_GRD32);
        }
        else
        {
            load_guardian(c - CH_G0, 0, 0);
            dmaCopyCGram(gi_pal, pal * 16, 32);
            map_put_pal(gi_map32, 4, 4, col, row, pal, 0);
        }
    }
}

char *char_name(u8 c)
{
    if (c == CH_JOY)
        return "JOYBOT";
    if (c == CH_SFC)
        return "AI AGENT";
    if (c == CH_MUGGY)
    {
        if (story)
            return player_name;   // tryb fabularny: imie wpisane przez gracza
        return "MUGGY";
    }
    return (char *)g_name[c - CH_G0];
}

// Podglad postaci na ekranie wyboru. Cala praca (wybor grafiki, mapa, paleta do bufora)
// dzieje sie w zwyklej logice; w VBlank zostaja tylko dwa krotkie transfery DMA.
// Kafelki strażnikow sa juz w VRAM (TILES_CHARS), wczytane przy wejsciu na ekran.
void preview_prepare(u8 p)
{
    u8 c = char_of[p], col = 2, pal = PAL_AV1 + p;
    if (p)
        col = 26;
    prev_slot[p] = pal;
    if (c == CH_JOY)
    {
        memcpy(prev_pal[p], &joybot32_pal, 32);
        map_put_pal((u16 *)&joybot32_map, 4, 4, col, 8, pal, 0);
    }
    else if (c == CH_MUGGY)
    {
        memcpy(prev_pal[p], &muggy48_pal, 32);
        map_put_pal((u16 *)&muggy32_map, 4, 4, col, 8, pal, 0);
    }
    else if (c == CH_SFC)
    {
        prev_slot[p] = 0xFF;   // robot ma stala palete nr 5
        map_put((u16 *)&robot32_map, 4, 4, col, 8);
    }
    else
    {
        load_guardian(c - CH_G0, NO_SLOT, 0);
        memcpy(prev_pal[p], gi_pal, 32);
        map_put_pal(gi_map32, 4, 4, col, 8, pal, TILES_CHARS + 16 * (c - CH_G0) - TILES_GRD32);
    }
}

void preview_send(u8 p)   // tylko DMA: paleta i wiersze 8-11 mapy
{
    if (prev_slot[p] != 0xFF)
        dmaCopyCGram((u8 *)prev_pal[p], prev_slot[p] * 16, 32);
}

void char_cols(u8 c)
{
    if (c == CH_JOY)   // Robocik-dzojstik: czerwony jak jego kulka
    {
        cf = RGB8(220, 56, 56);
        cl = RGB8(255, 140, 130);
        ce = RGB8(255, 96, 90);
    }
    else if (c == CH_SFC)
    {
        cf = COL_P2;
        cl = COL_P2_LIT;
        ce = RGB8(110, 170, 255);
    }
    else if (c == CH_MUGGY)
    {
        cf = COL_MUG;
        cl = COL_MUG_LIT;
        ce = COL_MUG_EDGE;
    }
    else
    {
        cf = g_fill[c - CH_G0];
        cl = g_lit[c - CH_G0];
        ce = g_edge[c - CH_G0];
    }
}

// Imiona nad boiskiem: lewa postac od kolumny 6, prawa wyrownana do kolumny 25
void hud_names2(void)
{
    char *nm;
    u8 len;
    consoleDrawText(6, 1, char_name(char_of[0]));
    nm = char_name(char_of[1]);
    len = strlen(nm);
    consoleDrawText(26 - len, 1, nm);
}

// Kolory paletek: wypelnienie, rozjasnienie (pulsowanie), krawedz
void set_paddle_colors(u16 f1, u16 l1, u16 e1, u16 f2, u16 l2, u16 e2)
{
    col_p1 = f1;
    col_p1_lit = l1;
    col_p2 = f2;
    col_p2_lit = l2;
    setPaletteColor(129, f1);
    setPaletteColor(130, e1);
    setPaletteColor(145, f2);
    setPaletteColor(146, e2);
    col_p1_edge = e1;
    col_p2_edge = e2;
    cg_want[CGI_P1E] = e1;
    cg_cur[CGI_P1E] = e1;
    cg_want[CGI_P2E] = e2;
    cg_cur[CGI_P2E] = e2;
    cg_want[CGI_P1] = f1;
    cg_cur[CGI_P1] = f1;
    cg_want[CGI_P2] = f2;
    cg_cur[CGI_P2] = f2;
}

// Bloki: ustawiamy wpisy kolumny w bgmap; vblank_tasks przepisuje je do VRAM
void blocks_to_map(u8 side)
{
    u8 r, col = side ? 31 : 0;
    u16 *cm = (u16 *)&court_map;
    for (r = 6; r <= 24; r++)
    {
        // blk: 0 brak, 1 caly blok, 2-4 popekany (kafelek TILES_BLOCK + blk - 1)
        bgmap[r * 32 + col] = blk[side][r] ? ((TILES_BLOCK + blk[side][r] - 1) | (PAL_COURT << 10)) : cm[r * 32 + col];
        colbuf[side][r - 6] = bgmap[r * 32 + col];
    }
    blk_dirty |= side ? 2 : 1;
}

// Wyglad muru wg wytrzymalosci: 7-8 caly, 5-6 i 3-4 pekniety, 1-2 prawie rozbity
u8 wall_look(u8 hp)
{
    if (hp >= 7)
        return 1;
    if (hp >= 5)
        return 2;
    if (hp >= 3)
        return 3;
    return 4;
}

// Stale bloki Wallera za jego paletka: gorny mur (wiersze 6-8) i dolny (22-24)
void passive_walls(u8 side)
{
    u8 r, a = 0, b = 0;
    if (wall_hp[side * 2])
        a = wall_look(wall_hp[side * 2]);
    if (wall_hp[side * 2 + 1])
        b = wall_look(wall_hp[side * 2 + 1]);
    for (r = 6; r <= 8; r++)
        blk[side][r] = a;
    for (r = 22; r <= 24; r++)
        blk[side][r] = b;
}

void passive_blocks(u8 side)
{
    u8 r;
    for (r = 0; r < 32; r++)
        blk[side][r] = 0;
    if (is_g(side, 2))
        passive_walls(side);
    blocks_to_map(side);
}

// Uderzenie piłki-komety w staly mur Wallera: mur peka, po WALL_HP uderzeniach znika
void damage_wall(u8 side, s16 y)
{
    u8 w;
    if (!is_g(side, 2))
        return;
    if ((y >> 3) <= 8)
        w = 0;
    else if (((y + BALL_SIZE - 1) >> 3) >= 22)
        w = 1;
    else
        return;   // trafienie w mur FORTRESS - te sie nie kruszą
    w += side * 2;
    if (!wall_hp[w])
        return;
    wall_hp[w]--;
    passive_walls(side);
    blocks_to_map(side);
    if (!wall_hp[w])
        play_sound(SND_SUPER);   // mur rozpada sie z hukiem
}

// FORTRESS: mury w srodkowej czesci linii (miedzy stalymi murami, wiersze 9-21)
// z 3 szczelinami po 16 px; tam, gdzie stalego muru juz nie ma, nic sie nie pojawia
void fortress(u8 side)
{
    u8 r, b, st;
    for (r = 9; r <= 21; r++)
        blk[side][r] = 1;
    for (b = 0; b < 3; b++)
    {
        st = 9 + b * 4 + rand() % 3;
        blk[side][st] = 0;
        blk[side][st + 1] = 0;
    }
    fort_timer[side] = FORT_TIME;
    blocks_to_map(side);
}

u8 blocked(u8 side, s16 y)
{
    s16 r0 = y >> 3, r1 = (y + BALL_SIZE - 1) >> 3;
    if (r0 < 0)
        r0 = 0;
    if (r1 > 31)
        r1 = 31;
    return blk[side][r0] | blk[side][r1];
}

// Kolumna 19 wpisow mapy jednym transferem DMA (pojedyncze zapisy nie mieszcza sie w VBlank)
void dma_column(u8 side)
{
    u16 a = VRAM_BG1_MAP + 6 * 32 + (side ? 31 : 0);
    u16 src = (u16)colbuf[side];
    VPORT_MAIN = 0x81;   // po kazdym slowie adres VRAM +32, czyli wiersz nizej
    VPORT_ADDL = a & 0xFF;
    VPORT_ADDH = a >> 8;
    DMA1_P = 0x01;       // zapis do dwoch rejestrow: $2118, $2119
    DMA1_B = 0x18;
    DMA1_AL = src & 0xFF;
    DMA1_AH = src >> 8;
    DMA1_AB = 0x7E;      // zmienne globalne leza w banku $7E
    DMA1_SL = 38;
    DMA1_SH = 0;
    DMA_EN = 0x02;
    VPORT_MAIN = 0x80;
}

// Zadania wykonywane zaraz po WaitForVBlank: rejestry, kolory, fragment mapy
#define REG_VBLANK (*(vuint8 *)0x4212)   // bit 7 = trwa VBlank
#define REG_NMI    (*(vuint8 *)0x4200)   // 0x81 = przerwanie VBlank + automatyczny odczyt padow
#define NMI_ON     0x81
#define NMI_OFF    0x01
#define REG_RDNMI  (*(vuint8 *)0x4210)   // odczyt kasuje flage przerwania VBlank
u8 nmi_shadow;   // czy przerwanie VBlank jest wlaczone (rejestru nie da sie odczytac)
extern u8 spc_fread, spc_fwrite;   // kolejka wiadomosci biblioteki dzwieku (odczyt / zapis)
void spc_flush_safe(void);
#define REG_LATCH  (*(vuint8 *)0x2137)
#define REG_VCOUNT (*(vuint8 *)0x213D)
#define REG_STAT   (*(vuint8 *)0x213F)
u16 dbg_vline, dbg_vmax;   // diagnostyka: w ktorej linii obrazu konczy sie logika gry

// Czy trwa VBlank i zostalo dosc czasu na zapis palety (linie 225-254 z 262; zapas 7 linii)
u8 vb_ok(void)
{
    u16 v;
    u8 t;
    t = REG_STAT;    // kasuje przerzutnik odczytu licznika
    t = REG_LATCH;   // zatrzaskuje liczniki
    v = REG_VCOUNT;
    v |= (REG_VCOUNT & 1) << 8;
    return v >= 225 && v < 255;
}

void vblank_tasks(void)
{
    u8 i;
    // Gdy logika sie spozni i VBlank juz minal, zapisy kolorow trafilyby w trakcie
    // rysowania obrazu (prawdziwa konsola psuje wtedy palete). Czekamy do nastepnej klatki.
    if (!(REG_VBLANK & 0x80))
        return;
    // Kolory zapisujemy NAJPIERW i tylko z zapasem czasu: zapis palety po koncu VBlank
    // trafia na prawdziwej konsoli pod przypadkowy adres (tak psula sie czcionka).
    for (i = 0; i < CG_COUNT; i++)
    {
        if (cg_want[i] != cg_cur[i])
        {
            if (!vb_ok())   // za malo czasu: reszta w nastepnej klatce
                break;
            setPaletteColor(cg_index[i], cg_want[i]);
            cg_cur[i] = cg_want[i];
        }
    }
    // Nastepna klatka ogrow: jeden transfer 8 calych wierszy (17-24), zaraz po kolorach i tylko
    // z zapasem czasu VBlank. Poza VBlank konsola ignoruje zapisy - 8 osobnych transferow konczylo
    // sie w linii 9 nastepnej klatki i zostawaly postacie sklejone z dwoch klatek animacji.
    // Wiersz 3 mapy BG1 (paski mocy i ikony mocy) zaraz po kolorach: to tylko 64 bajty. Na koncu
    // listy (po burzy, deszczu, CAMO) na konsoli czesto brakowalo juz czasu VBlank i pasek na
    // ekranie potrafil stac nawet kilkanascie sekund, choc gra liczyla go poprawnie.
    if (hud_dirty && vb_ok())
    {
        dmaCopyVram((u8 *)(bgmap + 96), VRAM_BG1_MAP + 96, 64);
        hud_dirty = 0;
    }
    if (arena == 1 && crowd_dirty && vb_ok())
    {
        dmaCopyVram((u8 *)crowd_rows[crowd_frame], VRAM_BG1_MAP + 17 * 32, 512);
        crowd_dirty = 0;
    }
    if (arena == 3 && torch_dirty && vb_ok())   // plomienie pochodni: jeden transfer wierszy 14-15
    {                                          // (osobne transfery wypadaly poza VBlank)
        dmaCopyVram((u8 *)(bgmap + 14 * 32), VRAM_BG1_MAP + 14 * 32, 128);
        torch_dirty = 0;
    }
    if (bolt_dirty)   // piorun w mapie boiska: zaraz po kolorach, tylko z zapasem czasu VBlank
        bolt_upload();
    if (arena == 1 && eye_dirty && vb_ok())   // swiecace oczy ogrow
    {
        setPaletteColor(PAL_COURT * 16 + 7, eye_glow[eye_i]);
        setPaletteColor(PAL_COURT * 16 + 8, eye_halo[eye_i]);
        eye_dirty = 0;
    }
    if (state == ST_TITLE && tcol_dirty && vb_ok())   // kolory piorunow (BG3, palety 1 i 2)
    {
        setPaletteColor(5, tfl_col[0]);
        setPaletteColor(6, tfl_col[1]);
        setPaletteColor(9, tfl_col[2]);
        setPaletteColor(10, tfl_col[3]);
        tcol_dirty = 0;
    }
    if (storm_on)   // deszcz: przewiniecie warstwy BG3 (w VBlank - bez rozdarcia obrazu)
        bgSetScroll(2, rain_x, rain_y);
    if (arena)
    {
        if (arena == 1 && !arena_hidden)
            bgSetScroll(2, arena_x, 0);   // kurz
        if (hdma_start)   // pierwszy VBlank po wczytaniu sceny: wlaczamy HDMA
        {
            if (!arena_hidden)
                HDMAEN_REG = hdma_mask;
            hdma_start = 0;
        }
        if (arena_apply)   // CAMO: chowamy gradient i warstwe tla areny
        {
            if (arena == ARENA_LUC)   // Mode 7 musi dzialac (CAMO chowa tylko paletke)
                ;
            else if (arena_hidden)
            {
                HDMAEN_REG = 0;
                bgSetDisable(2);
            }
            else
            {
                HDMAEN_REG = hdma_mask;
                bgSetEnable(2);
            }
            cg_cur[CGI_BACK] = 0xFFFF;   // kolor tla trzeba wpisac na nowo
            arena_apply = 0;
        }
        if (wave_ready)   // nastepna faza falowania mgly: tylko wskaznik tablicy
        {
            DMA_REG(5, 2) = (u16)wave_ind[wave_phase] & 0xFF;
            DMA_REG(5, 3) = (u16)wave_ind[wave_phase] >> 8;
            wave_ready = 0;
        }
        if (glow_cur != glow_lv && arena == 3 && !arena_hidden && vb_ok())   // migotanie swiatla pochodni
        {
            setPaletteColor(27, glow_col[glow_lv]);
            glow_cur = glow_lv;
        }
        if (arena >= 4 && arena != ARENA_LUC)
            vblank_arena2();
    }
    if (storm_bri)
    {
        setBrightness(storm_bri);
        storm_bri = 0;
    }
    if (prev_wait)
        prev_wait = 0;
    else if (prev_dirty && vb_ok())   // ekran wyboru postaci: nowy portret (palety i wiersze mapy)
    {
        if (prev_dirty & 1)
            preview_send(0);
        if (prev_dirty & 2)
            preview_send(1);
        dmaCopyVram((u8 *)(bgmap + 8 * 32), VRAM_BG1_MAP + 8 * 32, 4 * 64);
        prev_dirty = 0;
    }
    if (chq_pending && (REG_VBLANK & 0x80))   // jeden pisany znak dialogu
    {
        VPORT_MAIN = 0x80;
        VPORT_ADDL = chq_addr & 0xFF;
        VPORT_ADDH = chq_addr >> 8;
        VPORT_DATAL = chq_val & 0xFF;
        VPORT_DATAH = chq_val >> 8;
        chq_pending = 0;
    }
    if (avpal_dirty == 2)
        avpal_dirty = 1;
    else if (avpal_dirty && vb_ok())
    {
        send_avatar_pals();
        avpal_dirty = 0;
    }
    if (!(REG_VBLANK & 0x80))
        return;
    if (blk_dirty && court_shown)
    {
        if (blk_dirty & 1)
            dma_column(0);
        if (blk_dirty & 2)
            dma_column(1);
    }
    blk_dirty = 0;
    if (scroll_dirty)
    {
        bgSetScroll(0, shake_x, 0);
        bgSetScroll(1, shake_x, 0);
        scroll_dirty = 0;
    }
    if (cm_dirty)
    {
        REG_CGWSEL = cm_wsel;
        REG_CGADSUB = cm_adsub;
        REG_COLDATA = cm_data;
        cm_dirty = 0;
    }
}

// Plynne sciemnianie/rozjasnianie ekranu (16 klatek), dzwiek gra dalej

// spcProcess z wykrywaniem awarii: gdy biblioteka porzuci strumien efektu, bo procesor
// dzwieku nie odpowiedzial (digi_active = 0, a dane jeszcze zostaly), liczymy blad.
// Po 3 bledach przestajemy go pytac - kazde pytanie zatrzymywalo gre na ok. 0.4 s.
// Strumien probki trwa do ok. 70 linii obrazu. Jesli przerwanie VBlank wypadnie miedzy jego
// koncem a przywroceniem portow, SPC700 bierze dane probki za polecenie i sie zawiesza
// (cisza albo wycie zapetlonej probki). Dlatego strumien ruszamy tylko daleko od VBlank.
// Przesylanie probek do SPC700 ma rytm dopasowany do wolnego odczytu ROM: przy FastROM procesor
// wysylal je za szybko i czasem sterownik dzwieku sie gubil ("wycie"). Na czas rozmowy
// z SPC700 wlaczamy wolny odczyt (rejestr $420D), potem z powrotem szybki.
void spc_slow_process(void)
{
    *(vuint8 *)0x420D = 0;
    spcProcess();
    *(vuint8 *)0x420D = 1;
}
// spcProcess bez przerwania VBlank w trakcie (patrz snd_process)
void spc_proc_nmi(void)
{
    u8 t;
    if (nmi_shadow == NMI_ON)
    {
        REG_NMI = NMI_OFF;
        spc_slow_process();
        t = REG_RDNMI;
        REG_NMI = NMI_ON;
    }
    else
        spc_slow_process();
}

// Dostarczenie zaleglych polecen muzyki do SPC700. Biblioteczny spcFlush czeka bez limitu
// i przy starcie gry zawieszal ja na zawsze - tu najwyzej 1000 prob, potem gra idzie dalej.
// (Petla konczy sie, gdy kolejka jest pusta; po przejsciu na FastROM 60 prob mijalo za szybko
// i zatrzymanie muzyki czasem nie docieralo - wracalo "wycie".)
void spc_flush_safe(void)
{
    u16 n;
    for (n = 0; n < 1000 && spc_fread != spc_fwrite; n++)
        spc_proc_nmi();
}

void snd_process(void)
{
    u8 was = digi_active, t;
    u16 v;
    if (snd_dead)
        return;
    if (was)
    {
        t = REG_STAT;
        t = REG_LATCH;
        v = REG_VCOUNT;
        v |= (REG_VCOUNT & 1) << 8;
        if (v >= 120 && v < 225)   // za blisko VBlank: dokonczymy w nastepnej klatce
            return;
    }
    // Przesylanie porcji probki bez przerwania VBlank: przerwanie w trakcie przesylania zawieszalo
    // SPC700 na zapetlonym kawalku probki (np. staly ton po fanfarze). Gdy VBlank zacznie sie
    // w trakcie, kasujemy jego flage - ta klatka bedzie spozniona, ale dzwiek sie nie zawiesi.
    if (nmi_shadow == NMI_ON)
    {
        REG_NMI = NMI_OFF;
        spc_slow_process();
        t = REG_RDNMI;
        REG_NMI = NMI_ON;
    }
    else
        spc_slow_process();
    if (was && !digi_active)
    {
        if (!digi_remain)
            spc_err = 0;   // liczymy tylko bledy pod rzad
        else
        {
            spc_err++;
            if (spc_err >= 3)
                snd_dead = 1;
        }
    }
}

// Muzyka z wbudowanego ukladu dzwiekowego (moduly snesmod). Wczytywanie tylko przy
// zgaszonym ekranie, gdy nie gra efekt (fade czeka na jego koniec).
void spc_music_stop(void)   // bezposrednio: tylko przy zgaszonym ekranie (fade czeka na koniec probki)
{
    pause_cmd = 0;   // zalegla pauza, wznowienie albo zatrzymanie nie ma juz znaczenia
    mus_pos = 0;
    if (!snd_dead)
    {
        spcStop();   // zawsze, takze gdy muzyka "juz stoi": gdyby poprzednie zatrzymanie nie dotarlo
        spc_flush_safe();   // do sterownika, nuta wylaby dalej (np. w dialogu po walce)
        snd_gap = 3;
    }
    spc_mus = 0;
}

// W trakcie gry: zatrzymanie przez kolejke dzwieku (nie w chwili przesylania probki efektu)
void music_stop_safe(void)
{
    if (spc_mus)
        pause_cmd = 3;
}

void spc_music_load(u8 mod)
{
    spc_music_stop();
    if (!music_on || snd_dead)
        return;
    digi_active = 0;   // niedokonczony efekt przepada: wczytanie modulu i tak wycisza SPC700
    digi_remain = 0;
    *(vuint8 *)0x420D = 0;   // (wolny odczyt na czas przesylania - patrz spc_slow_process)
    spcLoad(mod);   // (obszar na efekty jest zarezerwowany raz, przy starcie - przed modulami)
    *(vuint8 *)0x420D = 1;
    spcSetModuleVolume(MUSIC_VOL);
    spc_mus = 1;
}

void spc_music_play(void)
{
    if (spc_mus == 1)
    {
        spcPlay(0);
        spc_mus = 2;
        play_wait = 90;   // najwyzej 1.5 s
    }
}

void fade(u8 fade_in)
{
    u8 i, t;
    REG_NMI = NMI_ON;   // rozjasnianie i wygaszanie zawsze z wlaczonym przerwaniem VBlank
    nmi_shadow = NMI_ON;
    for (i = 0; i < 16; i++)
    {
        WaitForVBlank();
        vblank_tasks();
        t = fade_in ? i : 15 - i;
        if (t > bright_max)   // w trakcie burzy scena jest przyciemniona
            t = bright_max;
        setBrightness(t);   // jasnosc 0 = ekran wylaczony
        sound_tick();       // dzwiek zaraz po VBlank (patrz snd_process)
        snd_process();
        music_update();
    }
    // Przed wczytywaniem nowego ekranu dajemy grajacemu efektowi dokonczyc sie (najwyzej
    // 3/4 s): wczytywanie trwa kilka klatek bez obslugi dzwieku i urwany strumien mogl
    // pogubic procesor dzwieku.
    for (i = 0; !fade_in && digi_active && !snd_dead && i < 90; i++)   // do 1.5 s
    {
        WaitForVBlank();
        snd_process();
    }
    // Ekran zgaszony: teraz wczytywanie nowej sceny. Na ten czas wylaczamy przerwanie VBlank,
    // bo biblioteka kopiuje w nim tekst przez ten sam kanal DMA, ktorego uzywamy do
    // wczytywania grafik i palet. Przerwanie w srodku naszego transferu psulo pamiec obrazu.
    // fade(1) i glowna petla wlaczaja je z powrotem.
    if (!fade_in)
    {
        REG_NMI = NMI_OFF;
        nmi_shadow = NMI_OFF;
        // HDMA tla aren dziala w kazdej linii obrazu, takze przy zgaszonym ekranie, i ustawia
        // adres palety. Podczas wczytywania (kopiowanie palet) przestawialo ten adres w srodku
        // transferu - kolory awatara trafialy w palete czcionki. Wylaczamy je przed wczytywaniem.
        HDMAEN_REG = 0;
    }
}

void clear_text(void)
{
    memset(scr_txt_font_map, 0, 0x800);
    scr_txt_dirty = 1;   // NMI skopiuje bufor tekstu do VRAM
}

//---------------------------------------------------------------------------------
// SPRITE'Y
//---------------------------------------------------------------------------------
// Sprite'y w trakcie gry wpisujemy prosto do bufora OAM (4 bajty: x, y, kafelek, atrybuty);
// wywolanie oamSet z C kosztowalo tyle, ze rysowanie zajmowalo ok. 80 z 262 linii klatki.
// Atrybuty: vhoopppN - odbicie pionowe/poziome, priorytet 3, numer palety.
#define SPR_ATTR(pal, h, v) (((v) << 7) | ((h) << 6) | 0x30 | ((pal) << 1))
// svis[n] = 1, gdy sprite n jest teraz na ekranie. Ukrywamy tylko widoczne sprite'y,
// zamiast co klatke na nowo zapisywac kilkadziesiat nieuzywanych (to bylo bardzo kosztowne).
extern u8 svis[];   // tablica w data.asm (wspolna z procedura pad_asm)
void pad_asm(u16 id, u16 sx, s16 y, u16 h, u16 attr);
#define SPR(id, x, y, tile, attr) { u8 *o_ = oamMemory + (id); o_[0] = (x); o_[1] = (y); o_[2] = (tile); o_[3] = (attr); svis[(id) >> 2] = 1; }
#define HIDE(id) { if (svis[(id) >> 2]) { oamMemory[(id) + 1] = 240; svis[(id) >> 2] = 0; } }

void hide_sprite(u16 id)
{
    HIDE(id)   // y=240 jest poza ekranem
}

u8 spr_x(s16 x)   // pozycja z przesunieciem trzesienia ekranu, bez wyjscia poza 0..255
{
    x += spr_dx;
    if (x < 0)
        return 0;
    if (x > 255)
        return 255;
    return x;
}

void hide_sprites(void)
{
    u8 i;
    for (i = 0; i < SPR_COUNT; i++)
    {
        oamMemory[i * 4 + 1] = 240;
        svis[i] = 0;
    }
}

extern u8 luc_py[], luc_ps[];   // data.asm: y pola -> linia ekranu, skala linii (plansza Lucifero)
// Plansza Lucifero: paletki skosne i wygladzone, rownolegle do krawedzi boiska. Paletka jezdzi po
// stalym torze, wiec obraz kazdego pasa 16 linii toru jest gotowy w ROM (tools/make_lucifero_pads.py):
// pelne pasy leza w VRAM caly czas, a przyciete konce paletki (gorny i dolny pas) sa wysylane po VBlank.
extern char luc_pad0_a, luc_pad0_b, luc_pad1_a, luc_pad1_b, luc_padx;
u16 luc_pf[2];
// (dla data.asm: luc_pad_asm, luc_flush_asm) zmienne robocze, pamiec przycietych koncow i ich zrodla
u8 lp_dx, lp_side, lp_pi2, lp_lt, lp_lb, lp_b, lp_bb, lp_bt, lp_n, lp_at, lp_rs, lp_v, lp_slot, lp_k, lp_t;
u8 lp_sh, lp_bk, lp_bm, lp_idx, lp_vl;
u16 lp_off, lp_svi, lp_code, lp_src, lp_va;
u16 luc_pv16[8];
u16 luc_cs[8];       // konce paletek (4 paletki x gora/dol): adres obrazu w ROM,
u8 luc_cb[8], luc_cd[8];   // jego bank i znacznik "do wyslania" (zawsze tylko najnowszy wariant)
void luc_pad_asm(u16 id, u16 sx, s16 y, u16 h, u16 attr);
void luc_flush_asm(void);   // data.asm: wysylka koncow i pelnych pasow zaraz po VBlank
extern u8 luc_pset;   // (zestaw pasow: 0 zwykla kamera, 1 odsunieta)
extern char luc_wpad0_a, luc_wpad0_b, luc_wpad1_a, luc_wpad1_b;
u8 *luc_pimg(u8 side, u8 b, u8 v)   // obraz pasa b toru side w wariancie v (128 B)
{
    u8 *base;
    if (luc_pset)   // kamera odsunieta (rozszerzone boisko)
    {
        if (side)
            base = (b < 5) ? (u8 *)&luc_wpad1_a : (u8 *)&luc_wpad1_b;
        else
            base = (b < 5) ? (u8 *)&luc_wpad0_a : (u8 *)&luc_wpad0_b;
    }
    else if (side)
        base = (b < 5) ? (u8 *)&luc_pad1_a : (u8 *)&luc_pad1_b;
    else
        base = (b < 5) ? (u8 *)&luc_pad0_a : (u8 *)&luc_pad0_b;
    return base + ((u16)(b % 5) * 31 + v) * 128;
}
u16 luc_slot_tile(u8 k)   // tablica nazw 1 sprite'ow: 0-19 pelne pasy, 20-27 przyciete konce paletek
{
    return 96 + 32 * (k >> 3) + 2 * (k & 7);
}
void luc_band_upload(u8 *src, u16 tile)
{
    dmaCopyVram(src, 0x5000 + tile * 16, 64);
    dmaCopyVram(src + 64, 0x5000 + (tile + 16) * 16, 64);
}
// Kolory paletek w czasie walki: liczone PRZED VBlank (luc_pcol_prep), a zaraz po jego poczatku
// tylko wpisywane (luc_pcol_send). Liczenie w VBlank (mnozenia) spychalo ostatnie zapisy palety
// poza VBlank - na konsoli trafialy wtedy w zle kolory (tlo, awatary w HUD); emulator tego nie pokazuje.
u16 luc_pc_buf[8];   // paletka 0: 0-3, paletka 1: 4-7 (kolory 12-15 palet sprite'ow 0 i 1)
u8 luc_pc_pend;      // bit p: kolory paletki p czekaja na wpisanie
void luc_pcol_prep(u8 p, u16 c)
{
    u8 r = c & 31, g = (c >> 5) & 31, bl = (c >> 10) & 31, k, o = p << 2;
    if (camo_timer[p])   // CAMO: cala paletka (pas i brzegi) w kolorze posadzki
    {
        for (k = 0; k < 4; k++)
            luc_pc_buf[o + k] = c;
    }
    else
    {
        luc_pc_buf[o] = ((r + 31) >> 1) | (((g + 31) >> 1) << 5) | (((bl + 31) >> 1) << 10);
        for (k = 1; k <= 3; k++)   // 13: 75%, 14: 50%, 15: 25% koloru paletki
            luc_pc_buf[o + k] = ((r * (4 - k) + 7 * k) >> 2) | (((g * (4 - k) + 7 * k) >> 2) << 5) | (((bl * (4 - k) + 7 * k) >> 2) << 10);
    }
    luc_pc_pend |= 1 << p;
}
void luc_pcol_send(void)   // zaraz po VBlank: same zapisy, bez obliczen
{
    if (luc_pc_pend & 1)
    {
        setPaletteColor(140, luc_pc_buf[0]);
        setPaletteColor(141, luc_pc_buf[1]);
        setPaletteColor(142, luc_pc_buf[2]);
        setPaletteColor(143, luc_pc_buf[3]);
    }
    if (luc_pc_pend & 2)
    {
        setPaletteColor(156, luc_pc_buf[4]);
        setPaletteColor(157, luc_pc_buf[5]);
        setPaletteColor(158, luc_pc_buf[6]);
        setPaletteColor(159, luc_pc_buf[7]);
    }
    luc_pc_pend = 0;
}
void luc_pcol(u8 p, u16 c)   // jasny pas i odcienie brzegu (kolor paletki zmieszany z szaroscia podlogi)
{
    u8 r = c & 31, g = (c >> 5) & 31, bl = (c >> 10) & 31, k;
    u16 base = 128 + 16 * p + 12;
    if (camo_timer[p])   // CAMO: cala paletka (pas i brzegi) w kolorze posadzki
    {
        for (k = 0; k < 4; k++)
            setPaletteColor(base + k, c);
        return;
    }
    setPaletteColor(base, ((r + 31) >> 1) | (((g + 31) >> 1) << 5) | (((bl + 31) >> 1) << 10));
    for (k = 1; k <= 3; k++)   // 13: 75%, 14: 50%, 15: 25% koloru paletki
    {
        setPaletteColor(base + k, ((r * (4 - k) + 7 * k) >> 2) | (((g * (4 - k) + 7 * k) >> 2) << 5) | (((bl * (4 - k) + 7 * k) >> 2) << 10));
    }
}
void draw_paddle(u16 id, s16 x, s16 y, u8 h, u8 pal)
{
    u16 sx = spr_x(x), hh = h, at = SPR_ATTR(pal, 0, 0);
    if (luc_on)   // plansza Lucifero: skosna, wygladzona paletka (data.asm)
    {
        luc_pad_asm(id, sx, y, hh, at);
        return;
    }
    pad_asm(id, sx, y, hh, at);   // szybka procedura w data.asm
}

void hide_paddle(u16 id)
{
    u8 i;
    if (!svis[id >> 2] && !svis[(id >> 2) + 3])   // paletka juz ukryta (pierwszy i czwarty segment)
        return;
    for (i = 0; i < PAD_MAX_SPR; i++)
    {
        oamMemory[id + i * 4 + 1] = 240;
        svis[(id >> 2) + i] = 0;
    }
}

u8 hist_index(u8 ago)
{
    return (hist_pos - 1 - ago) & 15;
}

void draw_xball(u8 k)
{
    u16 kk = k, sb = xb_spr[k], st = xt_spr[k];
    xb_draw_asm(kk, sb, st);   // pilka i ogon: szybka procedura w data.asm
}

void draw_sprites(void)
{
    u8 k, h, vis;
    s16 v = vel_x < 0 ? -vel_x : vel_x, ey;

    vis = !ghost_hidden && (!ghost_blink || (frame & 1));
    if (vis)
        SPR(SPR_BALL, spr_x(ball_x >> 8), ball_y >> 8, TILE_BALL, SPR_ATTR((sp_type || kim_level >= 6 || ff_level >= 6) ? 2 : 0, 0, 0))
    else
        HIDE(SPR_BALL)
    if (tele0_flash && (frame & 1))
        hide_paddle(SPR_P1);
    else
        draw_paddle(SPR_P1, pad_x[0], p1_y, pad_h[0], 0);
    if (tele_flash && (frame & 1))   // Telementor migocze przy teleportacji
        hide_paddle(SPR_P2);
    else
        draw_paddle(SPR_P2, pad_x[1], p2_y, pad_h[1], 1);
    if (spk_on)   // iskry Kimantero
    {
        for (k = 0; k < 6; k++)
        {
            if (spk_life[k])
                SPR(SPR_SPARK + k * 4, spr_x(spk_x[k]), spk_y[k], TILE_TAIL + 3, SPR_ATTR(4, 0, 0))
            else
                HIDE(SPR_SPARK + k * 4)
        }
        if ((spk_life[0] | spk_life[1] | spk_life[2] | spk_life[3] | spk_life[4] | spk_life[5]) == 0)
            spk_on = 0;   // wszystkie zgasly i sa juz schowane
    }
    ey = extra_y(0);
    if (ey != NO_Y)   // Changero po lewej: czesc paletki za krawedzia
        draw_paddle(SPR_TWIN0, pad_x[0], ey, pad_h[0], 0);
    else if (twin_timer[0])
        draw_paddle(SPR_TWIN0, twin_x[0], twin_y[0], pad_h[0], 0);
    else if (ghost_on[0])
        draw_paddle(SPR_TWIN0, twin_x[0], twin_y[0], pad_h[0], 5);
    else
        hide_paddle(SPR_TWIN0);
    ey = extra_y(1);
    if (ey != NO_Y)
        draw_paddle(SPR_TWIN1, pad_x[1], ey, pad_h[1], 1);
    else if (twin_timer[1])
        draw_paddle(SPR_TWIN1, twin_x[1], twin_y[1], pad_h[1], 1);
    else if (ghost_on[1])   // widmowy bliźniak Cyber-dopplera: polprzezroczysty, nie odbija
        draw_paddle(SPR_TWIN1, twin_x[1], twin_y[1], pad_h[1], 5);
    else
        hide_paddle(SPR_TWIN1);
    for (xk = 0; xk < XB; xk++)   // dodatkowe pilki (SPLIT) i ich ogony; nieistniejace i schowane pomijamy
    {
        if (xb_on[xk] || svis[xb_spr[xk] >> 2] || svis[xt_spr[xk] >> 2])
            draw_xball(xk);
    }
    v = vel_x < 0 ? -vel_x : vel_x;
    for (k = 0; k < 2; k++)
    {
        h = k ? SPR_FAKE2 : SPR_FAKE;
        if (fake_active[k] && (fake_life[k] > 8 || (frame & 1)))
            SPR(h, spr_x(fake_x[k] >> 8), fake_y[k] >> 8, TILE_BALL, SPR_ATTR(0, 0, 0))
        else
            HIDE(h)
    }

    // ogon komety: pozycje sprzed 2, 4, 6, 8 i 10 klatek (data.asm)
    tail_draw_asm();
}

void reset_history(void)
{
    u8 i;
    for (i = 0; i < 16; i++)
    {
        hist_x[i] = ball_x >> 8;
        hist_y[i] = ball_y >> 8;
    }
    tail_len = 0;
}

void push_history(void)
{
    hist_x[hist_pos] = ball_x >> 8;
    hist_y[hist_pos] = ball_y >> 8;
    hist_pos = (hist_pos + 1) & 15;
}

void draw_cursor_at(u16 id, s16 x, s16 y, s16 o, u8 pal, u8 vis)
{
    if (!vis)
    {
        hide_sprite(id);
        hide_sprite(id + 4);
        hide_sprite(id + 8);
        hide_sprite(id + 12);
        return;
    }
    oamSet(id, x - o, y - o, 3, 0, 0, TILE_CORNER, pal);
    oamSet(id + 4, x + 8 + o, y - o, 3, 1, 0, TILE_CORNER, pal);
    oamSet(id + 8, x - o, y + 8 + o, 3, 0, 1, TILE_CORNER, pal);
    oamSet(id + 12, x + 8 + o, y + 8 + o, 3, 1, 1, TILE_CORNER, pal);
}

void draw_cursor(u16 id, u8 idx, s16 o, u8 pal, u8 vis)
{
    s16 x = icon_col[idx];
    s16 y = icon_row[idx];
    x *= 8;
    y *= 8;
    draw_cursor_at(id, x, y, o, pal, vis);
}

//---------------------------------------------------------------------------------
// PASEK NAD BOISKIEM
//---------------------------------------------------------------------------------
void update_bar_map(u8 p)
{
    u16 *bm = (u16 *)&bar_map;   // 0 puste, 1-2 gracz 1, 3-4 gracz 2
    u8 t;
    s16 segs;
    u16 e;
    for (t = 0; t < 4; t++)
    {
        segs = (s16)bar[p] - 2 * t;
        if (segs > 2)
            segs = 2;
        if (p == 0)
        {
            e = segs <= 0 ? bm[0] : (segs == 1 ? bm[1] : bm[2]);
            bgmap[96 + 9 + t] = e;     // kolumny 9..12, od lewej
        }
        else
        {
            e = segs <= 0 ? bm[0] : (segs == 1 ? bm[3] : bm[4]);
            bgmap[96 + 22 - t] = e;    // kolumny 22..19, od prawej
        }
    }
    hud_dirty = 1;
}


void draw_score(void)
{
    consoleDrawText(6, 3, "%d", score1);
    consoleDrawText(25, 3, "%d", score2);
}

//---------------------------------------------------------------------------------
// EKRANY
//---------------------------------------------------------------------------------
//---------------------------------------------------------------------------------
// PLANSZA LUCIFERO (MODE 7) - etap 1
//---------------------------------------------------------------------------------
// Pochylone boisko: Mode 7 od linii 48, pasek u gory w zwyklym trybie 1 (HDMA przelacza tryb
// i warstwy). Mode 7 zajmuje tylko slowa VRAM $2200-$3FFF (kafelki 136-255 i wiersze 68-127
// mapy), wiec kafelki paska zostaja na miejscu; czcionka na czas walki przenosi sie na $5000.
// Logika gry dziala na plaskich wspolrzednych; sprite'y boiska sa przeliczane tuz przed VBlank
// i przywracane zaraz po nim. Napisy na boisku (PAUSE, PRESS START, wynik) to sprite'y.
#define LUC_SPR_TXT  320   // sprite'y 80-127: napisy na boisku
#define LUC_TXT_N    48
#define LUC_FONT_SPR 64    // kafelki sprite'ow 64-159: znaki 32-127
#define LUC_FONT_B   3072  // 96 znakow x 32 bajty
extern char luc_floor_til, luc_floor_tilend, luc_floor_map, luc_floor_mapend, luc_floor_pal, luc_m7;
extern u8 scr_txt_dirty, scr_txt_font_map[];
extern u8 videoMode;
void luc_project(void);     // data.asm: przeliczenie sprite'ow boiska na perspektywe
void luc_unproject(void);   // data.asm: przywrocenie ich prawdziwych pozycji
u16 luc_t;                  // (dla data.asm) pomocnicza
u8 luc_bak[660];            // (dla data.asm) offset (2 B), x, y, kafelek, atrybuty zmienionych sprite'ow
u8 luc_e, luc_hm, luc_hb;   // (dla data.asm) koniec zakresu, maska i bajt 9. bitu x
u8 luc_s, luc_txt_force;
// popiol (data.asm: luc_ash): 30 platkow na sprite'ach 98-127, wspolnych z napisami na boisku
#define ASH_N 30
u16 ash_x[ASH_N], ash_y[ASH_N], ash_vy[ASH_N], ash_ph[ASH_N], ash_lv[ASH_N], ash_t[ASH_N];
u16 ash_f, ash_g, ash_rng, ash_up;
// twarz zjawy: 96x96 (36 sprite'ow 16x16: 80-115), kafelki 64-255 kolumny 0-11 (na chwile zamiast
// czcionki napisow), paleta sprite'ow 7, polprzezroczysta - przez twarz przeswituje podloga
#define FACE_SPR 320
const u8 face_vis[51] = {1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0,
                         1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1};
u8 face_state, face_row, face_k, face_ts, face_pal_ok;
u16 face_timer;
u8 face_oam[3][144], face_hid[144];
// Twarz pojawia sie tylko w ciemnosci mocy HELL (gaszenie swiatla), raz na uzycie mocy, w losowym
// z pierwszych trzech zgaszen. luc_face_dark: 0 = nie, 1 = to zgaszenie ma twarz, 2 = twarz trwa.
u8 luc_face_dark, luc_dark_n, luc_face_pick;
// Wzor migania twarzy (face_vis, 51 krokow) jest odtwarzany w FACE_DUR klatkach obrazu, liczonych
// z licznika VBlank - niezaleznie od tego, jak wolno liczy gra przy wszystkich efektach.
#define FACE_DUR 54
u16 face_t0;
// Zgaszenie z twarza ma trwac ok. 1,25 s niezaleznie od tempa gry: po twarzy swiatlo wraca
// w stalych 16 klatkach obrazu (zwykle zgaszenia bez zmian).
#define FACE_RAMP 16
u8 luc_face_blk, luc_ramp_on;
u16 luc_ramp_t0;
extern char luc_face_til, luc_face_pal;
void luc_face_prep(void);
// rozszerzenie boiska (dzialanie mocy 2): kamera C0 -> C1 w 16 krokach, podloga z rozszerzona strona
// gracza, pasy paletek dla kamery C1 (tools/make_lucifero_widen.py)
extern char luc_cam_hdma, luc_cam_proj, luc_wide_map, luc_wide_lo, luc_wide_hi, luc_wpadx;
extern char luc_wpad0_a, luc_wpad0_b, luc_wpad1_a, luc_wpad1_b;
const u8 luc_wtab[16] = {0, 0, 1, 2, 4, 6, 8, 11, 13, 16, 18, 20, 22, 23, 24, 24};   // rozszerzenie (px) dla kroku kamery
u8 luc_pyr[256], luc_psr[224], luc_padxr[20];   // biezace tablice perspektywy (kopie z ROM)
u8 luc_pxk[16][20];   // x pasow paletek dla kazdego kroku kamery (obrazy pasow sa tylko dla C0 i C1)
u8 luc_cam, luc_cam_want, luc_cam_tick, luc_w, luc_ext[2], luc_pset, luc_h_pending, luc_breload, luc_bg_dirty;
u8 luc_wide;   // w VRAM jest (albo czeka) podloga rozszerzona
void luc_cam_hdma_asm(u16 step);   // data.asm: HDMA kamery prosto z tablic w ROM
u8 *luc_job_src[4];
u16 luc_job_va[4], luc_job_len[4], luc_job_done;
u8 luc_job_hi[4], luc_job_n, luc_job_ready;
u16 luc_job_chunk;
// moc Lucifero (HELL) - patrz luc_hell_begin
#define HELL_TIME 780   // 13 s
u16 luc_hell_t, luc_dark_wait;
u8 luc_hell_kind, luc_hell_p, luc_rust, luc_rust_want, luc_dark_t, luc_mus_luc, luc_bright, luc_pal_dirty, luc_ember_dirty;
u16 luc_rust_pal[16], luc_pal_buf[16], luc_rust_lv[17][16];   // wszystkie poziomy rdzy liczone raz, przy starcie
void luc_rust_levels(void);
u8 luc_txt_n, ash_hidden;
extern char luc_ash_til;
void luc_ash(void);
extern char PVSLFONT_PIC;   // czcionka biblioteki w ROM (96 znakow 4bpp, ta sama co na $3000)
u8 luc_buf[1024];
u8 luc_h_mode[6], luc_h_tm[6], luc_h_a[358], luc_h_v[358];

// Bajty niskie (mapa) albo wysokie (kafelki) slow VRAM - format Mode 7. Tylko przy wylaczonym ekranie.
void luc_vram_bytes(u8 *src, u16 vaddr, u16 len, u8 high)
{
    u16 done, n;
    for (done = 0; done < len; done += n)
    {
        n = len - done;
        if (n > 1024)
            n = 1024;
        memcpy(luc_buf, src + done, n);
        *(vuint8 *)0x2115 = high ? 0x80 : 0x00;
        *(vuint16 *)0x2116 = vaddr + done;
        DMA_REG(0, 0) = 0x00;
        DMA_REG(0, 1) = high ? 0x19 : 0x18;
        DMA_REG(0, 2) = (u16)luc_buf & 0xFF;
        DMA_REG(0, 3) = (u16)luc_buf >> 8;
        DMA_REG(0, 4) = 0x7E;
        DMA_REG(0, 5) = n & 0xFF;
        DMA_REG(0, 6) = n >> 8;
        *(vuint8 *)0x420B = 1;
    }
    *(vuint8 *)0x2115 = 0x80;
}

// Kanal HDMA podany wprost: przy numerze kanalu w zmiennej kompilator zapisywal do RAM ($7E:43xx),
// a nie do rejestrow. Biblioteka uzywa kanalu 0 (pamiec obrazu) i 7 (sprite'y w VBlank).
#define LUC_HDMA(ch, mode, reg, tab) do { DMA_REG(ch, 0) = (mode); DMA_REG(ch, 1) = (reg); \
    DMA_REG(ch, 2) = (u16)(tab) & 0xFF; DMA_REG(ch, 3) = (u16)(tab) >> 8; DMA_REG(ch, 4) = 0x7E; } while (0)

void luc_pad_size(u8 big)   // sprite'y paletek (3-22 i 37-56): 16x16 na planszy Lucifero, potem z powrotem 8x8
{
    u8 n, m;
    for (n = 3; n < 57; n++)
    {
        if (n == 23)
            n = 37;
        m = 2 << ((n & 3) << 1);
        if (big)
            oamMemory[512 + (n >> 2)] |= m;
        else
            oamMemory[512 + (n >> 2)] &= ~m;
    }
}

void luc_setup(void)   // przy wylaczonym ekranie (wczytywanie sceny)
{
    u8 i;
    u16 *pp = (u16 *)&luc_floor_pal;
    u8 *m7 = (u8 *)&luc_m7;
    // czcionka (z ROM): na $5000 dla paska i do kafelkow sprite'ow dla napisow na boisku
    dmaCopyVram((u8 *)&PVSLFONT_PIC, 0x5000, LUC_FONT_B);
    dmaCopyVram((u8 *)&PVSLFONT_PIC, VRAM_SPR + LUC_FONT_SPR * 16, LUC_FONT_B);
    *(vuint8 *)0x210B = 0x05;   // BG1 (tekst) z $5000, BG2 (pasek) z $0000
    // podloga: mapa w bajtach niskich, kafelki w bajtach wysokich slow $2200-$3FFF
    luc_vram_bytes((u8 *)&luc_floor_map, 0x2200, (&luc_floor_mapend - &luc_floor_map), 0);
    luc_vram_bytes((u8 *)&luc_floor_til, 0x2200, (&luc_floor_tilend - &luc_floor_til), 1);
    luc_vram_bytes((u8 *)&luc_wide_lo, 0x0100, 3840, 1);    // kafelki rozszerzonego boiska: od razu (w miejscu
    luc_vram_bytes((u8 *)&luc_wide_hi, 195 * 64, 1664, 1);  // logo z ekranu tytulowego i za kafelkami podlogi)
    luc_bg_dirty = 1;
    for (i = 0; i < 16; i++)   // (setPaletteColor to makro z trzech instrukcji: klamry konieczne)
    {
        setPaletteColor(64 + i, pp[i]);   // kolory podlogi: paleta 4 (w tej walce bez trzeciego awatara)
    }
    for (i = 1; i < 16; i++)
    {
        setPaletteColor(128 + 48 + i, 0);
    }
    setPaletteColor(128 + 48 + 1, RGB8(235, 235, 235));   // napisy na boisku: biale
    setPaletteColor(128 + 48 + 2, RGB8(168, 166, 160));   // popiol: jasny (jak w podgladzie po zmieszaniu z podloga)
    setPaletteColor(128 + 48 + 3, RGB8(136, 134, 128));   // popiol: ciemniejszy
    dmaCopyVram((u8 *)&luc_ash_til, VRAM_SPR + 172 * 16, 4 * 32);   // (kolumny 12-15: obok kafelkow twarzy)
    for (i = 0; i < ASH_N; i++)   // platki w losowych miejscach, rozna predkosc, faza i kolysanie
    {
        ash_x[i] = (rand() & 0xFF) << 8;
        ash_y[i] = (48 + rand() % 176) << 8;
        ash_vy[i] = 64 + rand() % 90;          // 0,25-0,6 piksela na klatke
        ash_ph[i] = rand() & 63;
        ash_lv[i] = (rand() & 3) * 64;
        ash_t[i] = 172 + ((rand() & 3) == 0 ? 1 : 0) + ((i & 1) ? 2 : 0);   // 3/4 platkow 2x2
    }
    ash_rng = 0xACE1;
    ash_f = 0;
    ash_up = 0;
    luc_hell_t = 0;
    luc_rust = 0;
    luc_rust_want = 0;
    luc_dark_t = 0;
    luc_bright = 0x0F;
    luc_pal_dirty = 0;
    luc_ember_dirty = 0;
    luc_face_prep();
    face_state = 0;
    memcpy(luc_pyr, luc_py, 256);
    memcpy(luc_psr, luc_ps, 224);
    {
        u8 *pa = (u8 *)&luc_padx, *pb = (u8 *)&luc_wpadx;
        u8 k;
        u16 a, b;
        for (k = 0; k < 16; k++)   // tor paletek przesuwa sie razem z kamera (obrazy pasow sa dla C0 i C1)
            for (i = 0; i < 20; i++)
            {
                a = pa[i];
                b = pb[i];
                if (b >= a)
                    luc_pxk[k][i] = a + ((b - a) * luc_wtab[k] + 12) / 24;
                else
                    luc_pxk[k][i] = a - ((a - b) * luc_wtab[k] + 12) / 24;
            }
    }
    memcpy(luc_padxr, luc_pxk[0], 20);
    luc_cam = 0;
    luc_cam_want = 0;
    luc_cam_tick = 0;
    luc_w = 0;
    luc_ext[0] = 0;
    luc_ext[1] = 0;
    luc_pset = 0;
    luc_h_pending = 0;
    luc_breload = 0;
    luc_wide = 0;
    luc_job_n = 0;
    luc_job_done = 0;
    luc_job_ready = 0;
    luc_hell_kind = 0;
    luc_hell_p = 1;
    face_ts = 0x02;
    face_timer = 0;   // (twarz nie pojawia sie juz losowo w walce)
    luc_face_dark = 0;
    luc_face_blk = 0;
    luc_ramp_on = 0;
    luc_dark_n = 0;
    {
        u16 *g = (u16 *)&luc_floor_pal;   // rdzawe kolory podlogi: wiecej czerwieni, mniej zieleni i blekitu
        u16 c, r, gg, bb;
        for (i = 0; i < 16; i++)
        {
            c = g[i];
            r = ((c & 31) * 3) >> 1;
            if (r > 31)
                r = 31;
            gg = (((c >> 5) & 31) * 3) >> 2;
            bb = ((c >> 10) & 31) >> 1;
            luc_rust_pal[i] = r | (gg << 5) | (bb << 10);
        }
    }
    luc_rust_levels();
    ash_hidden = 0;
    luc_txt_n = 0;
    // rejestry Mode 7 (M7A i przesuniecie pionowe podaje HDMA dla kazdej linii)
    *(vuint8 *)0x211A = 0x80;   // poza plansza: przezroczyscie
    *(vuint8 *)0x211B = 0x00; *(vuint8 *)0x211B = 0x01;
    *(vuint8 *)0x211C = 0x00; *(vuint8 *)0x211C = 0x00;
    *(vuint8 *)0x211D = 0x00; *(vuint8 *)0x211D = 0x00;
    *(vuint8 *)0x211E = 0x00; *(vuint8 *)0x211E = 0x01;
    *(vuint8 *)0x211F = 128;  *(vuint8 *)0x211F = 0x00;
    *(vuint8 *)0x2120 = 0x00; *(vuint8 *)0x2120 = 0x00;
    *(vuint8 *)0x210D = 0x00; *(vuint8 *)0x210D = 0x00;
    // HDMA: tryb (1 -> 7 od linii 48), warstwy, M7A i przesuniecie pionowe dla linii 48-223
    luc_h_mode[0] = 48; luc_h_mode[1] = 0x01; luc_h_mode[2] = 1; luc_h_mode[3] = 0x07; luc_h_mode[4] = 0;
    luc_h_tm[0] = 48; luc_h_tm[1] = 0x13; luc_h_tm[2] = 1; luc_h_tm[3] = 0x11; luc_h_tm[4] = 0;
    luc_h_a[0] = 48; luc_h_a[1] = 0x00; luc_h_a[2] = 0x01;
    luc_h_v[0] = 48; luc_h_v[1] = 0x00; luc_h_v[2] = 0x00;
    luc_h_a[3] = 0x80 | 127; luc_h_v[3] = 0x80 | 127;
    memcpy(luc_h_a + 4, m7, 254);
    memcpy(luc_h_v + 4, m7 + 352, 254);
    luc_h_a[258] = 0x80 | 49; luc_h_v[258] = 0x80 | 49;
    memcpy(luc_h_a + 259, m7 + 254, 98);
    memcpy(luc_h_v + 259, m7 + 352 + 254, 98);
    luc_h_a[357] = 0; luc_h_v[357] = 0;
    LUC_HDMA(2, 0x00, 0x05, luc_h_mode);
    LUC_HDMA(3, 0x00, 0x2C, luc_h_tm);
    LUC_HDMA(4, 0x02, 0x1B, luc_h_a);
    LUC_HDMA(5, 0x02, 0x0E, luc_h_v);
    hdma_mask = 0x3C;   // kanaly 2, 3, 4 i 5
    hdma_start = 1;
    arena_hidden = 0;
    memset(oamMemory + 512 + 20, 0, 12);   // sprite'y 80-127: male (napisy)
    for (i = 0; i < 20; i++)   // pelne pasy torow paletek
        luc_band_upload(luc_pimg(i / 10, i % 10, 0), luc_slot_tile(i));
    luc_pad_size(1);
    memset(luc_pv16, 0xFF, 16);
    memset(luc_cd, 0, 8);
    luc_pf[0] = col_p1;
    luc_pf[1] = col_p2;
    luc_pc_pend = 0;
    luc_pcol(0, col_p1);
    luc_pcol(1, col_p2);
    luc_txt_force = 1;
    luc_on = 1;
}

void luc_restore(void)   // nastepna scena (ekran wygaszony): zwykly tryb i czcionka na swoim miejscu
{
    u8 i;
    HDMAEN_REG = 0;
    SFP_BGMODE = 0x01;
    *(vuint8 *)0x210B = 0x03;   // BG1 (tekst) z $3000, BG2 z $0000
    *(vuint8 *)0x212C = videoMode;
    dmaCopyVram((u8 *)&PVSLFONT_PIC, VRAM_FONT, LUC_FONT_B);
    for (i = 0; i < LUC_TXT_N; i++)   // napisy-sprite'y: inne ekrany chowaja tylko sprite'y 0-79
        oamMemory[LUC_SPR_TXT + 4 * i + 1] = 240;
    memset(oamMemory + 512 + 20, 0, 12);   // (po twarzy) sprite'y 80-127 male
    *(vuint8 *)0x212D = 0x02;               // przezroczystosc: z powrotem bez podlogi
    face_state = 0;
    luc_w = 0;
    luc_ext[0] = 0;
    luc_ext[1] = 0;
    if (luc_bg_dirty)   // rozszerzona podloga zajela kafelki logo: grafika tla od nowa
    {
        dmaCopyVram(&court_til, VRAM_BG1_GFX, (&court_tilend - &court_til));
        dmaCopyVram(&logo_til, VRAM_BG1_GFX + TILES_LOGO * 16, (&logo_tilend - &logo_til));   // logo z ekranu tytulowego
        luc_bg_dirty = 0;
    }
    luc_pad_size(0);
    luc_on = 0;
}

// Napisy z warstwy tekstu w obszarze boiska (wiersze 6-27) jako sprite'y (Mode 7 nie pokazuje tekstu)
void luc_text_sprites(void)
{
    u16 *m = (u16 *)scr_txt_font_map;
    u8 *o = oamMemory + LUC_SPR_TXT;
    u8 r, c, n = 0;
    u16 e, k;
    for (r = 6; r < 28; r++)
    {
        k = r * 32;
        for (c = 0; c < 32; c++)
        {
            e = m[k + c] - txt_base;   // numer znaku od spacji (0 = spacja)
            if (e && e < 96 && n < LUC_TXT_N)
            {
                o[0] = c << 3;
                o[1] = (r << 3) - 1;
                o[2] = LUC_FONT_SPR + e;
                o[3] = 0x36;   // paleta 3, priorytet 3
                o += 4;
                n++;
            }
        }
    }
    luc_txt_n = n;   // gdy sa napisy, popiol (te same sprite'y) jest schowany
    for (; n < LUC_TXT_N; n++)
    {
        o[1] = 240;
        o += 4;
    }
}

// ---------------------------------------------------------------------------------
// Moc Lucifero (HELL): przez 10 s gry swiat zmienia sie jak w Silent Hill - podloga rdzewieje,
// muzyka przechodzi w czesc przemiany (pozycja 4 modulu), popiol zamienia sie w unoszace sie iskry -
// i losowo: paletka przeciwnika zmniejsza sie o polowe albo co chwile gasnie swiatlo (trzask,
// pilka przyspiesza).
void luc_rust_levels(void)   // przy starcie planszy: kolory podlogi dla poziomow rdzy 0-16
{
    u16 *g = (u16 *)&luc_floor_pal;
    u8 i, k;
    u16 a, b;
    for (k = 0; k <= 16; k++)
        for (i = 0; i < 16; i++)
        {
            a = g[i];
            b = luc_rust_pal[i];
            luc_rust_lv[k][i] = ((((a & 31) * (16 - k) + (b & 31) * k) >> 4))
                              | (((((a >> 5) & 31) * (16 - k) + ((b >> 5) & 31) * k) >> 4) << 5)
                              | (((((a >> 10) & 31) * (16 - k) + ((b >> 10) & 31) * k) >> 4) << 10);
        }
}
void luc_rust_prepare(void)   // kolory podlogi dla poziomu rdzy luc_rust (0 = szarosc, 16 = rdza)
{
    memcpy(luc_pal_buf, luc_rust_lv[luc_rust], 32);
    luc_pal_dirty = 1;
}
void luc_face_prep(void)   // gotowe wpisy OAM twarzy (przesuniecie -1, 0, +1) i wpisy schowane
{
    u8 j, r, c, *o;
    for (j = 0; j < 3; j++)
    {
        o = face_oam[j];
        for (r = 0; r < 6; r++)
            for (c = 0; c < 6; c++)
            {
                o[0] = 79 + j + 16 * c;
                o[1] = 65 + 16 * r;
                o[2] = 64 + 32 * r + 2 * c;
                o[3] = 0x3E;   // paleta 7 (polprzezroczysta), priorytet 3
                o += 4;
            }
    }
    for (j = 0; j < 36; j++)
    {
        face_hid[4 * j] = 0;
        face_hid[4 * j + 1] = 240;
        face_hid[4 * j + 2] = 0;
        face_hid[4 * j + 3] = 0;
    }
}
void luc_face_size(u8 big)   // sprite'y 80-115: 16x16 na czas twarzy, potem z powrotem 8x8 (napisy, popiol)
{
    memset(oamMemory + 512 + 20, big ? 0xAA : 0x00, 9);
}
void luc_face_stop(void)   // twarz znika; czcionka napisow wraca do kafelkow sprite'ow
{
    memcpy(oamMemory + FACE_SPR, face_hid, 144);
    luc_face_size(0);
    face_ts = 0x02;
    face_state = 3;
    face_row = 0;
    luc_face_dark = 0;
}
void luc_hide_for_face(void)   // twarz w ciemnosci: wszystkie inne sprite'y (pilka, paletki, popiol) poza ekranem
{
    u16 i;
    for (i = 0; i < 80; i++)
        oamMemory[(i << 2) + 1] = 240;
    for (i = 116; i < 128; i++)
        oamMemory[(i << 2) + 1] = 240;
}
void luc_face_update(void)   // co klatke, po popiele (twarz nadpisuje czesc jego sprite'ow)
{
    u8 j;
    if (face_state == 0)
    {
        if (luc_face_dark == 1 && luc_dark_t > 8 && state == ST_PLAY && !luc_txt_n)   // tylko w ciemnosci wybranego zgaszenia
        {
            face_state = 1;   // wgrywanie palety i kafelkow (po VBlank)
            face_row = 0;
            face_pal_ok = 0;
            luc_face_dark = 2;
        }
    }
    else if (face_state == 1)
    {
        if (luc_txt_n || state != ST_PLAY)
            luc_face_stop();
        else if (face_row >= 12 && face_pal_ok)
        {
            face_state = 2;
            face_k = 0;
            face_t0 = snes_vblank_count;
            memcpy(oamMemory + FACE_SPR, face_hid, 144);   // miejsca twarzy od razu puste (bez iskier popiolu)
            luc_face_size(1);
            face_ts = 0x00;   // w ciemnosci: bez mieszania z podloga
        }
    }
    else if (face_state == 2)
    {
        face_k = (u8)(((u16)(snes_vblank_count - face_t0) * 51) / FACE_DUR);   // krok wzoru wg uplywu czasu
        if (luc_txt_n || state != ST_PLAY || face_k >= 51)
            luc_face_stop();
        else
        {
            if (face_vis[face_k])
            {
                j = ((rand() & 3) == 0) ? (rand() % 3) : 1;   // czasem drgnie o piksel
                memcpy(oamMemory + FACE_SPR, face_oam[j], 144);
            }
            else
                memcpy(oamMemory + FACE_SPR, face_hid, 144);
        }
    }
}
void luc_face_vblank(void)   // po VBlank: kafelki twarzy, paleta, czcionka, przezroczystosc
{
    if (face_state == 1)
    {
        if (!face_pal_ok && vb_ok())   // najpierw paleta (az sie uda)
        {
            dmaCopyCGram((u8 *)&luc_face_pal, 240, 32);
            face_pal_ok = 1;
        }
        while (face_row < 12 && vb_ok())
        {
            dmaCopyVram((u8 *)&luc_face_til + face_row * 384, VRAM_SPR + (64 + 16 * face_row) * 16, 384);
            face_row++;
        }
    }
    else if (face_state == 3)
    {
        while (face_row < 6 && vb_ok())   // po jednym wierszu kafelkow (512 B): calosc zawsze w VBlank
        {
            dmaCopyVram((u8 *)&PVSLFONT_PIC + face_row * 512, VRAM_SPR + LUC_FONT_SPR * 16 + face_row * 256, 512);
            face_row++;
        }
        if (face_row >= 6)
        {
            face_state = 0;
        }
    }
    if (face_state == 2 && luc_face_dark)   // twarz w ciemnosci: tylko sprite'y (bez podlogi i HUD)
    {
        luc_h_tm[1] = 0x10;
        luc_h_tm[3] = 0x10;
    }
    else
    {
        luc_h_tm[1] = 0x13;
        luc_h_tm[3] = 0x11;
    }
    *(vuint8 *)0x212D = face_ts;
}

void luc_job_add(u8 *src, u16 va, u16 len, u8 high)   // podloga: przesylanie porcjami po VBlank
{
    if (luc_job_n < 4)
    {
        luc_job_src[luc_job_n] = src;
        luc_job_va[luc_job_n] = va;
        luc_job_len[luc_job_n] = len;
        luc_job_hi[luc_job_n] = high;
        luc_job_n++;
    }
}
void luc_job_prep(void)   // przed VBlank: kolejna porcja (512 B) do bufora
{
    u16 n;
    if (luc_job_n > 4)   // zabezpieczenie: niepoprawny stan kolejki (do zbadania) - zerujemy
    {
        luc_job_n = 0;
        luc_job_ready = 0;
        luc_job_done = 0;
    }
    if (!luc_job_n || luc_job_ready)
        return;
    n = luc_job_len[0] - luc_job_done;
    if (n > 512)
        n = 512;
    memcpy(luc_buf, luc_job_src[0] + luc_job_done, n);
    luc_job_chunk = n;
    luc_job_ready = 1;
}
void luc_job_vblank(void)   // po VBlank: porcja do VRAM (bajty niskie = mapa, wysokie = kafelki)
{
    u8 i;
    if (!luc_job_n || luc_job_n > 4)
    {
        luc_job_ready = 0;
        return;
    }
    if (!luc_job_ready || !vb_ok())
        return;
    *(vuint8 *)0x2115 = luc_job_hi[0] ? 0x80 : 0x00;
    *(vuint16 *)0x2116 = luc_job_va[0] + luc_job_done;
    DMA_REG(0, 0) = 0x00;
    DMA_REG(0, 1) = luc_job_hi[0] ? 0x19 : 0x18;
    DMA_REG(0, 2) = (u16)luc_buf & 0xFF;
    DMA_REG(0, 3) = (u16)luc_buf >> 8;
    DMA_REG(0, 4) = 0x7E;
    DMA_REG(0, 5) = luc_job_chunk & 0xFF;
    DMA_REG(0, 6) = luc_job_chunk >> 8;
    *(vuint8 *)0x420B = 1;
    *(vuint8 *)0x2115 = 0x80;
    luc_job_done += luc_job_chunk;
    luc_job_ready = 0;
    if (luc_job_done >= luc_job_len[0])   // zadanie skonczone: nastepne
    {
        for (i = 1; i < luc_job_n; i++)
        {
            luc_job_src[i - 1] = luc_job_src[i];
            luc_job_va[i - 1] = luc_job_va[i];
            luc_job_len[i - 1] = luc_job_len[i];
            luc_job_hi[i - 1] = luc_job_hi[i];
        }
        luc_job_n--;
        luc_job_done = 0;
    }
}
// Po VBlank: krok kamery co 3 klatki. Nowe tablice obowiazuja od nastepnej klatki - wtedy paletki,
// pozostale sprite'y i podloga (HDMA przelaczane zaraz po nastepnym VBlank) maja te sama kamere.
void luc_cam_update(void)
{
    u8 *src, ns;
    if (luc_cam == luc_cam_want || ++luc_cam_tick < 3)
        return;
    luc_cam_tick = 0;
    luc_cam += (luc_cam < luc_cam_want) ? 1 : -1;
    src = (u8 *)&luc_cam_proj + (u16)luc_cam * 480;
    memcpy(luc_pyr, src, 256);
    memcpy(luc_psr, src + 256, 224);
    memcpy(luc_padxr, luc_pxk[luc_cam], 20);
    luc_h_pending = 1;
    luc_w = luc_wtab[luc_cam];
    luc_ext[1 - luc_hell_p] = (luc_w * 15) >> 4;   // przy paletce (x 16 albo 232) rozszerzenie ok. 15/16
    luc_ext[luc_hell_p] = 0;
    ns = luc_cam >= 8;
    if (ns != luc_pset)   // pasy paletek dla drugiej kamery (wysyla luc_flush_asm)
    {
        luc_pset = ns;
        memset(luc_pv16, 0xFF, 16);
        luc_breload = 1;
    }
    if (luc_cam == 0 && luc_wide)   // kamera wrocila: dopiero teraz zwykla podloga, wiec pilka
    {                               // nigdy nie leci poza widoczna plyta
        luc_job_add((u8 *)&luc_floor_map, 0x2200, 3584, 0);
        luc_wide = 0;
    }
}

void luc_hell_end(void)
{
    u8 v = 1 - luc_hell_p;
    luc_hell_t = 0;
    luc_rust_want = 0;
    ash_up = 0;
    luc_ember_dirty = 1;
    luc_dark_t = 0;
    if (face_state == 1 || face_state == 2)   // koniec mocy przerywa twarz
        luc_face_stop();
    luc_face_dark = 0;
    luc_face_blk = 0;
    luc_ramp_on = 0;
    if (luc_hell_kind == 0)
        pad_target[v] = pad_base[v];
    if (luc_hell_kind == 2)   // kamera wraca, boisko sie zweza (zwykla podloga: luc_cam_update)
        luc_cam_want = 0;
    if (luc_mus_luc && music_on && !snd_dead)
        mus_pos = 1;   // z powrotem mgla (pozycja 0; wysle sound_tick)
}
void luc_hell_begin(u8 p)
{
    u8 v = 1 - p;
    if (!luc_on)
        return;
    if (luc_hell_t)
        luc_hell_end();
    luc_hell_p = p;
    luc_hell_t = HELL_TIME;
    luc_rust_want = 16;
    ash_up = 1;
    luc_ember_dirty = 1;
    luc_hell_kind = rand() % 3;   // 0: paletka przeciwnika o polowe, 1: gasnace swiatlo, 2: rozszerzenie boiska
    if (luc_hell_kind == 0)
        pad_target[v] = pad_base[v] >> 1;
    if (luc_hell_kind == 2)   // kamera odjezdza, strona przeciwnika sie rozszerza
    {
        luc_cam_want = 15;
        if (!luc_wide)   // (kafelki sa juz w VRAM od przygotowania planszy)
        {
            luc_job_add((u8 *)&luc_wide_map, 0x2200, 3584, 0);
            luc_wide = 1;
        }
    }
    luc_dark_wait = 30;
    luc_dark_n = 0;
    luc_face_pick = 1 + rand() % 3;   // twarz w 1., 2. albo 3. zgaszeniu (w 13 s sa zawsze co najmniej 4)
    luc_face_dark = 0;
    if (luc_mus_luc && music_on && !snd_dead)
        mus_pos = 5;   // czesc przemiany (pozycja 4; wysle sound_tick)
}
void luc_hell_update(void)   // co klatke (przed VBlank)
{
    u16 el;
    if (luc_rust != luc_rust_want && (ash_f & 1))
    {
        luc_rust += (luc_rust < luc_rust_want) ? 1 : -1;
        luc_rust_prepare();
    }
    if (!luc_hell_t || state != ST_PLAY)
    {
        luc_dark_t = 0;   // punkt albo koniec mocy: swiatlo od razu wraca
        luc_face_blk = 0;
        luc_ramp_on = 0;
        return;
    }
    if (luc_hell_kind == 1)
    {
        if (luc_dark_t)
        {
            if (luc_face_dark == 2 && (face_state == 1 || face_state == 2))
            {
                luc_face_blk = 1;   // twarz trwa: ciemnosc czeka (zgaszenie prowadzi twarz)
                if (luc_dark_t < 9)
                    luc_dark_t = 9;
            }
            else if (luc_face_blk)   // twarz sie skonczyla: swiatlo wraca w stalym czasie
            {
                luc_face_blk = 0;
                luc_ramp_on = 1;
                luc_ramp_t0 = snes_vblank_count;
                luc_dark_t = 8;
            }
            else if (luc_ramp_on)
            {
                el = snes_vblank_count - luc_ramp_t0;
                if (el >= FACE_RAMP)
                {
                    luc_dark_t = 0;
                    luc_ramp_on = 0;
                }
                else
                    luc_dark_t = 8 - (u8)(el >> 1);   // te same stopnie jasnosci co zwykle (8..1)
            }
            else
                luc_dark_t--;
            if (!luc_dark_t)
                luc_face_dark = 0;   // twarz, ktora nie zdazyla sie pokazac (np. napis), przepada
        }
        else if (--luc_dark_wait == 0)
        {
            luc_dark_n++;
            if (luc_dark_n == luc_face_pick)
                luc_face_dark = 1;               // w tym zgaszeniu pojawi sie twarz
            luc_dark_t = 45 + (rand() & 15);     // 0,75-1 s ciemnosci (ostatnie 8 klatek: swiatlo wraca)
            luc_dark_wait = 60 + (rand() & 63);
            play_sound(SND_THUNDER);             // trzask
            vel_x += vel_x >> 4;                 // pilka lekko przyspiesza
            vel_y += vel_y >> 4;
        }
    }
    if (--luc_hell_t == 0)
        luc_hell_end();
}
void luc_hell_vblank(void)   // po VBlank: kolory podlogi, iskry/popiol, jasnosc
{
    u8 b;
    if (luc_pal_dirty && vb_ok())
    {
        dmaCopyCGram((u8 *)luc_pal_buf, 64, 32);   // 16 kolorow podlogi jednym transferem
        luc_pal_dirty = 0;
    }
    if (luc_ember_dirty && vb_ok())
    {
        if (ash_up)
        {
            setPaletteColor(128 + 48 + 2, RGB8(250, 150, 50));   // iskry
            setPaletteColor(128 + 48 + 3, RGB8(210, 70, 20));
        }
        else
        {
            setPaletteColor(128 + 48 + 2, RGB8(168, 166, 160));  // popiol
            setPaletteColor(128 + 48 + 3, RGB8(136, 134, 128));
        }
        luc_ember_dirty = 0;
    }
    if (luc_face_dark && face_state == 2)   // twarz w ciemnosci: wszystko inne ukryte, wiec widac tylko ja
        b = 0x0F;
    else if (luc_dark_t > 8)        // ciemnosc: calkowita czern (na CRT jasnosc 1 byla za jasna)
        b = 0x00;
    else if (luc_dark_t)       // swiatlo wraca stopniowo: 1, 3, ... 15 (luc_dark_t 8..1)
        b = 1 + ((8 - luc_dark_t) << 1);
    else
        b = 0x0F;
    if (b != luc_bright)
    {
        *(vuint8 *)0x2100 = b;
        luc_bright = b;
    }
}

void luc_wait_vb(void)
{
    if (!luc_on)
    {
        (WaitForVBlank)();
        return;
    }
    if (scr_txt_dirty || luc_txt_force)
    {
        luc_text_sprites();
        luc_txt_force = 0;
    }
    luc_hell_update();
    luc_job_prep();
    if (!luc_txt_n)         // popiol (bez perspektywy; przy napisach na boisku schowany)
    {
        luc_ash();
        ash_hidden = 0;
    }
    luc_face_update();      // twarz zjawy (po popiele)
    luc_nb = 0;             // (paletki rysuje od razu w perspektywie draw_paddle)
    luc_project();          // pozostale sprite'y boiska; zapamietane do przywrocenia
    if (cg_cur[CGI_P1] && cg_cur[CGI_P1] != luc_pf[0])   // paletka zmienila kolor (pulsowanie, rozblysk, CAMO)
    {
        luc_pf[0] = cg_cur[CGI_P1];
        luc_pcol_prep(0, luc_pf[0]);
    }
    if (cg_cur[CGI_P2] && cg_cur[CGI_P2] != luc_pf[1])
    {
        luc_pf[1] = cg_cur[CGI_P2];
        luc_pcol_prep(1, luc_pf[1]);
    }
    if (luc_face_dark && face_state == 2)
        luc_hide_for_face();
    (WaitForVBlank)();      // w VBlank biblioteka wysyla przeliczone sprite'y
    if (luc_pc_pend && vb_ok())   // kolory paletek: pierwsze po VBlank, gotowe (bez obliczen)
        luc_pcol_send();
    if (luc_h_pending)      // podloga z kamery, dla ktorej policzono te sprite'y
    {
        luc_cam_hdma_asm(luc_cam);
        luc_h_pending = 0;
    }
    // Przyciete konce paletek (i pelne pasy po zmianie kamery) od razu po VBlank, szybko i tylko
    // w VBlank: obraz konca zawsze pasuje do pozycji sprite'ow wyslanej w tym samym VBlank.
    luc_flush_asm();
    luc_hell_vblank();
    luc_job_vblank();
    luc_face_vblank();
    luc_unproject();
    luc_cam_update();       // krok kamery: tablice dla nastepnej klatki
}

void reset_effects(void)
{
    HDMAEN_REG = 0;   // najpierw: zadne kopiowanie przy wlaczonym HDMA
    if (luc_on)       // po walce z Lucifero: zwykly tryb obrazu i czcionka na swoim miejscu
        luc_restore();
    pause_cmd = 0;    // nowa scena: zalegla pauza/wznowienie muzyki nie ma juz znaczenia
    mus_pos = 0;
    shake_t = 0;
    shake_x = 0;
    spr_dx = 0;
    scroll_dirty = 1;
    flash_t = 0;
    cm_wsel = CM_NORMAL_WSEL;
    cm_adsub = CM_NORMAL_ADSUB;
    cm_data = 0xE0;
    // Samonaprawa: rejestry mieszania kolorow zapisujemy od razu (wolno zawsze), a kolory
    // zmienne (tlo, paletki, pilka, paski) wysylamy od nowa, nawet jesli "nie zmienily sie" -
    // gdyby cos je wczesniej uszkodzilo, nowa scena wszystko przywroci.
    REG_CGWSEL = CM_NORMAL_WSEL;
    REG_CGADSUB = CM_NORMAL_ADSUB;
    REG_COLDATA = 0xE0;
    dmaCopyCGram((u8 *)font_pal, PAL_FONT * 16, 32);   // samonaprawa: paleta czcionki od nowa
    storm_on = 0;              // burza tylko w swoim meczu
    HDMAEN_REG = 0;            // tla aren (HDMA) wylaczone podczas wczytywania kazdej sceny
    arena = 0;
    arena_apply = 0;
    hdma_start = 0;
    crowd_dirty = 0;
    wave_ready = 0;
    torch_dirty = 0;
    hide_bats();
    arena2_reset();
    REG_TS = 0x02;   // przezroczystosc: z powrotem tylko boisko (duch Maltena dodaje mgle)
    bolt_t = 0;
    bolt_dirty = 0;
    thunder_t = 0;
    storm_flash = 0;
    storm_bri = 0;
    bright_max = 15;
    cm_norm_adsub = CM_NORMAL_ADSUB;
    SFP_BGMODE = 0x01;
    bgSetDisable(2);
    for (shake_t = 0; shake_t < CG_COUNT; shake_t++)
        cg_cur[shake_t] = 0xFFFF;
    shake_t = 0;
    cm_dirty = 1;
    sp_type = SP_NONE;
    ghost_hidden = 0;
    ghost_blink = 0;
    cpu_ghost_mode = 0;
    armed[1] = 0;
    armed[0] = 0;
    bar[1] = 0;
    bar[0] = 0;
    tail_len = 0;
    clear_xballs();
    fake_active[0] = 0;
    fake_active[1] = 0;
    fake_timer = 360;
    wall_hp[0] = WALL_HP;
    wall_hp[1] = WALL_HP;
    wall_hp[2] = WALL_HP;
    wall_hp[3] = WALL_HP;
    grow_timer[0] = 0;
    grow_timer[1] = 0;
    fort_timer[0] = 0;
    fort_timer[1] = 0;
    pad_h[0] = pad_base[0];
    pad_target[0] = pad_base[0];
    pad_h[1] = pad_base[1];
    pad_target[1] = pad_base[1];
    for (fake_timer = 0; fake_timer < 32; fake_timer++)
    {
        blk[0][fake_timer] = 0;
        blk[1][fake_timer] = 0;
    }
    fake_timer = 360;
    blk_dirty = 0;
    court_shown = 0;
    twin_timer[0] = 0;
    twin_timer[1] = 0;
    swap_timer[0] = 0;
    swap_timer[1] = 0;
    slow_timer[0] = 0;
    slow_timer[1] = 0;
    ghost_on[0] = 0;
    ghost_on[1] = 0;
    ghost_t[0] = 300;
    ghost_t[1] = 300;
    tele0_done = 0;
    tele0_cool = 0;
    tele0_flash = 0;
    cpu_inv = 0;
    cpu_inv_t = 1;
    wrap[0] = 0;
    wrap[1] = 0;
    status_dirty = 0;
    pad_x[0] = P1_X;
    pad_x[1] = P2_X;
    catch_timer = 0;
    tele_done = 0;
    tele_flash = 0;
    blink_side = 0xFF;
    blink_ret = 0;
    blink_left[0] = 0;
    blink_left[1] = 0;
    force_tail = 0;
    camo_timer[0] = 0;
    camo_timer[1] = 0;
    back_col = 0;
    back_t = 240;
    back_idx = 0;
    pull_total = 0;
    chaos_icon_t[0] = 0;
    chaos_icon_t[1] = 0;
    for (status_dirty = 0; status_dirty < 6; status_dirty++)
        spk_life[status_dirty] = 0;
    status_dirty = 0;
    spk_on = 1;   // nastepne draw_sprites schowa iskry
    twin_x[0] = 96;    // TWIN: blizniak na ok. 1/4 boiska...
    twin_x[1] = 152;   // ...albo 3/4 (po stronie wlasciciela)
    twin_y[0] = 104;
    twin_y[1] = 104;
    hit_fx = NO_Y;
    chron_slowed = 0;
    kim_level = 0;
    ff_level = 0;
    tele_cool = 0;
    chq_pending = 0;
}

void draw_menu_labels(void)
{
    consoleDrawText(12, 18, "              ");
    consoleDrawText(12, 20, "              ");
    consoleDrawText(12, 22, "              ");
    if (title_sub)   // podmenu po wybraniu QUICK MATCH albo FAST & FURIOUS
    {
        consoleDrawText(12, 18, "1 PLAYER");
        consoleDrawText(12, 20, "2 PLAYERS");
        consoleDrawText(10, 22, " ");
    }
    else
    {
        consoleDrawText(12, 18, "STORY MODE");
        consoleDrawText(12, 20, "QUICK MATCH");
        consoleDrawText(12, 22, "FAST & FURIOUS");
    }
    consoleDrawText(10, 26, "                    ");
    // wiersz 24: ustawienie muzyki (ten sam wiersz co pytanie o kasowanie zapisu)
    consoleDrawText(5, 24, "                      ");
    if (!title_sub)
    {
        if (music_on)
            consoleDrawText(12, 24, "MUSIC: ON");
        else
            consoleDrawText(12, 24, "MUSIC: OFF");
    }
}

void draw_menu(void)
{
    u8 i, n = 5;
    if (title_sub)
        n = 2;
    for (i = 0; i < n; i++)
        consoleDrawText(10, 18 + 2 * i, i == menu_idx ? ">" : " ");
}

extern char title_bolt_til, title_bolt_tilend, title_bolt_map;
u8 dsv_lp0, dsv_lp1, dsv_pts, dsv_qm, dsv_mode, dsv_c0, dsv_c1;
const u8 tfl_bolt[16] = {31, 31, 18, 31, 28, 24, 20, 16, 13, 10, 8, 6, 4, 2, 1, 0};   // jasnosc pioruna
const u8 tfl_back[16] = {6, 12, 5, 10, 8, 6, 5, 4, 3, 2, 2, 1, 1, 0, 0, 0};          // rozblysk nieba

void show_title(u8 first)
{
    u8 k;
    luc_test = 0;   // STAGE 11: LUCIFERO dotyczy tylko jednej walki
    if (!first)
        fade(0);
    state = ST_TITLE;
    story = 0;
    demo = 0;
    music_want = 0;
    spc_music_stop();
    reset_effects();
    hide_sprites();
    dmaCopyCGram(&logo_pal, PAL_LOGO * 16, 32);
    dmaCopyVram(&title_bolt_til, VRAM_RAIN_GFX, (&title_bolt_tilend - &title_bolt_til));
    dmaCopyVram(&title_bolt_map, VRAM_RAIN_MAP, 2048);

    memset(bgmap, 0, sizeof(bgmap));
    map_put(&logo_map, 32, 6, 0, 1);            // logo 256x48 od wiersza 1
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    bgSetScroll(2, 0, 0);   // blyskawice na warstwie BG3, niewidoczne do rozblysku
    bgSetEnable(2);

    clear_text();
    consoleDrawText(8, 7, "A PADDLE ODYSSEY");
    title_sub = 0;
    menu_idx = 0;
    draw_menu_labels();
    erase_ask = 0;
    draw_menu();
    title_idle = 0;
    tfl_k = 0;
    tfl_t = 90 + rand() % 180;
    for (k = 0; k < 4; k++)
        tfl_col[k] = 0;
    tcol_dirty = 1;
    fade(1);
}

// Blyskawice na ekranie tytulowym: rozblysk nieba (kolor tla) i piorun z lewej albo z prawej
void title_fx(void)
{
    u8 st, b, n;
    u16 c1, c2;
    if (tfl_k)
    {
        st = 16 - tfl_k;
        tfl_k--;
        b = tfl_bolt[st];
        n = tfl_back[st];
        c1 = b | (b << 5) | ((b > 27 ? 31 : b + 4) << 10);   // rdzen: biel z odcieniem niebieskim
        c2 = (b >> 1) | ((b >> 1) << 5) | ((b > 21 ? 31 : (b >> 1) + 10) << 10);   // poswiata
        tfl_col[0] = tfl_side ? 0 : c1;
        tfl_col[1] = tfl_side ? 0 : c2;
        tfl_col[2] = tfl_side ? c1 : 0;
        tfl_col[3] = tfl_side ? c2 : 0;
        tcol_dirty = 1;
        cg_want[CGI_BACK] = (n >> 1) | ((n >> 1) << 5) | (n << 10);   // granatowy rozblysk
    }
    else if (--tfl_t == 0)
    {
        tfl_k = 16;
        tfl_side = rand() & 1;
        tfl_t = 150 + rand() % 330;   // nastepna za 2,5-8 s
    }
}

u8 rand_unlocked(void);
void start_match(void);
// Pokaz po bezczynnosci: komputer kontra komputer na losowej arenie (Ruden, Malten, Waller)
void start_demo(void)
{
    u8 g = rand() % 3;
    dsv_lp0 = last_power[0];
    dsv_lp1 = last_power[1];
    dsv_pts = pts_idx;
    dsv_qm = qm_track;
    dsv_mode = game_mode;
    dsv_c0 = char_of[0];
    dsv_c1 = char_of[1];
    demo = 1;
    demo_t = 2700;   // najwyzej 45 s
    demo_over = 0;
    demo_prev = 0;
    demo_err = 0;
    two_players = 0;
    game_mode = 0;
    pts_idx = 0;     // do 3 punktow
    qm_track = g + 1;   // muzyka strażnika (gdy MUSIC ON)
    char_of[0] = CH_G0 + g;
    char_of[1] = (rand() & 1) ? CH_MUGGY : CH_JOY;
    sel_idx[0] = g_power[g];
    sel_idx[1] = rand_unlocked();
    start_match();
    consoleDrawText(14, 2, "DEMO");
}

void end_demo(void)
{
    demo = 0;
    last_power[0] = dsv_lp0;   // ustawienia gracza wracaja jak przed pokazem
    last_power[1] = dsv_lp1;
    pts_idx = dsv_pts;
    qm_track = dsv_qm;
    game_mode = dsv_mode;
    char_of[0] = dsv_c0;
    char_of[1] = dsv_c1;
    show_title(0);
}

// "Gracz" po lewej w pokazie: sledzi pilke lecaca w jego strone, uzywa mocy przy pelnym pasku
void demo_ai(void)
{
    s16 c, t;
    u16 k = 0;
    if ((vel_x < 0) != (demo_prev >> 7))   // pilka zmienila kierunek: nowy, lekki blad
    {
        demo_err = (s8)(rand() % 17) - 8;
        demo_prev = (demo_prev & 0x7F) | (vel_x < 0 ? 0x80 : 0);
    }
    c = p1_y + (pad_h[0] >> 1);
    t = (FIELD_TOP + FIELD_BOTTOM) / 2;
    if (vel_x < 0)
        t = (s16)(ball_y >> 8) + 4 + demo_err;
    if (c < t - 3)
        k = KEY_DOWN;
    else if (c > t + 3)
        k = KEY_UP;
    if (bar[0] >= BAR_MAX && vel_x < 0 && (ball_x >> 8) > 150 && !(frame & 15))
        k |= KEY_A;
    pad0_new = k & ~pad0;
    pad0 = k;
    pad1 = 0;
    pad1_new = 0;
}

u8 is_locked(u8 pw);
u8 icon_of(u8 pw);

// Nazwa i opis mocy wskazanej przez gracza p (wiersze row i row+1)
void draw_pwr_line(u8 p, u8 row)
{
    u8 i = sel_idx[p];
    consoleDrawText(2, row, (char *)blank28);
    consoleDrawText(2, row + 1, (char *)blank28);
    if (p)
        consoleDrawText(2, row, "P2");
    else
        consoleDrawText(2, row, "P1");
    if (is_locked(i) && i >= PWR_DRAWN)
    {
        consoleDrawText(5, row, "???");
        consoleDrawText(2, row + 1, "LOCKED");
    }
    else
    {
        consoleDrawText(5, row, (char *)pwr_name[i]);
        if (is_locked(i))
            consoleDrawText(2, row + 1, (char *)lock_desc[i - 4]);
        else
            consoleDrawText(2, row + 1, (char *)pwr_desc[i]);
    }
}

void draw_descs(void)
{
    draw_pwr_line(0, 19);
    if (two_players)
        draw_pwr_line(1, 22);
    desc_dirty = 0;
}

// Ramka kursora wokol ikony nr idx w siatce 7 x 2
void draw_grid_cursor(u16 id, u8 idx, s16 o, u8 pal, u8 vis)
{
    s16 cx = idx % 7;
    s16 cy = idx / 7;
    cx = (2 + 4 * cx) * 8;
    cy = (11 + 4 * cy) * 8;
    draw_cursor_at(id, cx, cy, o, pal, vis);
}

// Losowa moc, ktora jest juz odblokowana (dla AI Agenta)
u8 rand_unlocked(void)
{
    u8 n, t;
    for (t = 0; t < 40; t++)
    {
        n = rand() % PWR_ALL;
        if (!is_locked(n))
            return n;
    }
    return rand() & 3;
}

void show_select(u8 players2)
{
    u8 i, ic;
    u16 *im = (u16 *)&icons_map;   // mapa 30x2: ikona i to kolumny 2i, 2i+1

    srand(snes_vblank_count);   // losowanie zalezne od chwili wcisniecia START
    fade(0);
    two_players = players2;
    story = 0;
    state = ST_SELECT;
    // kolory paletek i ramek kursorow trybu 1/2 PLAYER (po trybie fabularnym byly inne)
    set_paddle_colors(COL_P1, COL_P1_LIT, RGB8(225, 100, 125), COL_P2, COL_P2_LIT, RGB8(110, 170, 255));
    reset_effects();
    hide_sprites();

    memset(bgmap, 0, sizeof(bgmap));
    hud_char(0, 1, 1);
    hud_char(1, 27, 1);
    for (i = 0; i < PWR_ALL; i++)   // te same 14 mocy co w trybie fabularnym
    {
        ic = is_locked(i) ? ICON_LOCK : icon_of(i);
        map_put_stride(im + 2 * ic, 2, 2, ICON_STRIDE, 2 + 4 * (i % 7), 11 + 4 * (i / 7));
    }
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));

    clear_text();
    hud_names2();
    consoleDrawText(7, 7, "CHOOSE YOUR POWER");

    sel_idx[0] = last_power[0];
    sel_idx[1] = last_power[1];
    if (is_locked(sel_idx[0]))
        sel_idx[0] = PWR_SUPER;
    if (is_locked(sel_idx[1]))
        sel_idx[1] = PWR_SUPER;
    sel_done[0] = 0;
    sel_done[1] = 0;
    cpu_think = 0;
    ready_timer = 0;
    for (i = 0; i < 2; i++)   // strażnik gra swoja moca, jak w trybie fabularnym
    {
        if (char_of[i] >= CH_G0)
        {
            sel_idx[i] = g_power[char_of[i] - CH_G0];
            sel_done[i] = 1;
        }
    }
    if (!two_players && char_of[1] == CH_SFC && sel_done[0])
    {
        cpu_think = 12;   // gracz ma moc z gory: AI Agent wybiera od razu
        cpu_delay = think_delay[0];
    }
    draw_descs();
    fade(1);
}

void go_serve(void)
{
    state = ST_SERVE;
    tele_done = 0;       // Telementor: nowe podejscie (wczesniej stal po punkcie w miejscu)
    kim_level = 0;
    ff_level = 0;
    chron_slowed = 0;
    timer = 60;   // 1 s pauzy przed serwisem (NTSC)
    ball_x = FP(128 - BALL_SIZE / 2);
    ball_y = FP((FIELD_TOP + FIELD_BOTTOM) / 2 - BALL_SIZE / 2);
    vel_x = 0;
    vel_y = 0;
    reset_history();
}

void new_cpu_error(void)
{
    u8 e = cpu_err_r;   // EASY: -10..+10 px
    cpu_error = (s16)(rand() % (2 * e + 1)) - e;
    if (!two_players && is_g(1, 9))
        cpu_error = (s16)(rand() % (2 * e + 5)) - e - 2;   // Kimantero: o 2 px wiecej
}

// Parametry komputera dla wybranego poziomu (po ustawieniu predkosci strażnika)
void apply_difficulty(void)
{
    u8 d = difficulty;
    if (two_players)
        d = 0;
    cpu_react = diff_react[d];
    cpu_delay_d = diff_delay[d];
    cpu_err_r = diff_err[d];
    cpu_pw = diff_pw[d];
    cpu_aim_k = diff_aim[d];
    cpu_speed = (cpu_speed * diff_spd[d]) >> 4;
    serve_spd = ((u16)SERVE_SPEED * (u16)diff_ball[d]) >> 6;   // szybsza pilka od poczatku do konca wymiany
    spd_step = ((u16)SPEED_STEP * (u16)diff_ball[d]) >> 6;
    max_spd = ((u16)MAX_SPEED * (u16)diff_ball[d]) >> 6;
    pred_ok = 0;
    if (!two_players && char_of[1] == CH_G0 + G_LUCIFERO)   // Lucifero: wczesniej reaguje, mniej sie myli,
    {                                                       // przewiduje i celuje krawedzia
        cpu_react -= 6;
        cpu_delay_d = cpu_delay_d > 8 ? cpu_delay_d - 2 : 6;
        cpu_err_r = cpu_err_r > 6 ? cpu_err_r - 2 : 4;
        if (cpu_pw < 2)
            cpu_pw = 2;
        if (cpu_aim_k < 2)
            cpu_aim_k = 2;
    }
}

// NORMAL/HARD: odbicie krawedzia paletki, zeby pilka poleciala w strone dalsza od gracza
s16 aim_off(void)
{
    s16 a = (pad_h[1] * cpu_aim_k) >> 3;   // ulamek wysokosci paletki: zawsze z zapasem
    if (!a)
        return 0;
    if (p1_y + pad_h[0] / 2 < (FIELD_TOP + FIELD_BOTTOM) / 2)
        return -a;   // gracz u gory: pilka trafia ponizej srodka paletki i leci w dol
    return a;
}

u8 icon_of(u8 pw)
{
    if (pw < PWR_DRAWN)
        return pw;
    return ICON_LOCK;
}

// Wspolna czesc startu meczu; ekran jest juz wygaszony (fade(0))
// ---------------------------------------------------------------------------
// BURZA: deszcz na pierwszym planie (BG3, polprzezroczysty), przyciemniona scena,
// blyskawice z piorunem w tle i grzmotem - tym czestsze, im szybciej gra Kimantero
// Falowanie mgly Maltena: tablice wskaznikow dla 32 faz (raz, przy wczytywaniu walki)
void wave_vals_asm(u16 base);   // data.asm
void build_wave_tables(void)
{
    u8 ph, i, *t;
    u16 a;
    wave_zero = 0;
    for (ph = 0; ph < 32; ph++)
    {
        t = wave_ind[ph];
        a = (u16)&wave_zero;
        t[0] = 48;           // linie 0-47: pasek u gory, bez przesuniecia
        t[1] = a & 0xFF;
        t[2] = a >> 8;
        for (i = 0; i < 76; i++)   // boisko: pasy po 2 linie
        {
            a = (u16)&wave_val[(i + ph) & 31];
            t[3 + i * 3] = 2;
            t[4 + i * 3] = a & 0xFF;
            t[5 + i * 3] = a >> 8;
        }
        a = (u16)&wave_zero;
        t[231] = 24;         // reszta ekranu (za 3 + 76 * 3 bajtami pasow)
        t[232] = a & 0xFF;
        t[233] = a >> 8;
        t[234] = 0;          // koniec tablicy
    }
}

void build_wave(void)   // co klatke: tylko 32 wartosci (dryf + fala)
{
    u16 b = arena_x;
    wave_vals_asm(b);
}

//---------------------------------------------------------------------------------
// ARENY 4-9: Cyber-doppler, Changero, Chronos, Magneton, Telementor, Blinker.
// Tlo na warstwie BG3 za boiskiem. Ruch glownie przez cykl palet (w meczu wolne sa kolory
// 2-15 i 19-31), przesuniecia HDMA (kanal 5) i kilka sprite'ow 96-127 (poza tablica svis).
// Grafiki i tablice kolorow: tools/make_arena2.py
//---------------------------------------------------------------------------------
#define AR_DOPPLER  4
#define AR_CHANGERO 5
#define AR_CHRONOS  6
#define AR_MAGNETON 7
#define AR_TELE     8
#define AR_BLINKER  9
#define TILE_ARSPR  64           // kafelki sprite'ow aren: 64-191
#define SPR_AR      384          // pierwszy sprite aren (nr 96)
#define SPR_PAL3    (128 + 48)   // paleta sprite'ow 3: wskazowki, iskra, UFO
#define ATTR_AR     0x16         // paleta 3, priorytet 1: przed BG3, za boiskiem i paletkami
extern char doppler_code_til, doppler_code_tilend, doppler_code_map, doppler_ca, doppler_cb, doppler_grad, doppler_gradend;
extern char changero_plasma_til, changero_plasma_tilend, changero_plasma_map, changero_cols;
extern char chronos_dial_til, chronos_dial_tilend, chronos_dial_map, chronos_grad, chronos_gradend;
extern char chronos_hands_til, chronos_hands_tilend, chronos_hm, chronos_hh, chronos_wave;
extern char magneton_field_til, magneton_field_tilend, magneton_field_map, magneton_cols, magneton_grad, magneton_gradend;
extern char magneton_spark_til, magneton_spark_tilend, magneton_sparks;
extern char telementor_sky_til, telementor_sky_tilend, telementor_sky_map, telementor_cols, telementor_grad, telementor_gradend;
extern char telementor_ufo_til, telementor_ufo_tilend, telementor_beam;
extern char blinker_rainbow_til, blinker_rainbow_tilend, blinker_rainbow_map, blinker_cols;
extern char ar_hidblk;                    // 32 ukryte wpisy OAM (y = 240)
void wave2_vals_asm(u16 base, u16 amp);   // data.asm: falowanie Changero

u8 ar_hmask, ar_hid, ar_redraw;
u8 ar_t1, ar_t2, ar_st, ar_n1, ar_n2, ar_amp, ar_amax, ar_lv;
u16 ar_o1, ar_o2, ar_ev, ar_last;
u8 *ar_cg1, *ar_cg2;          // kolory do wyslania w VBlank: zrodlo, numer koloru, bajty
u8 ar_ci1, ar_ci2, ar_cn1, ar_cn2;
u16 ar_hptr;                  // nowy adres tablicy HDMA kanalu 5 (0 = bez zmiany)
u16 ar_vaddr, ar_vval;        // wpis mapy BG3 do zapisania w VBlank (znaki Dopplera)
u8 ar_vpend;
u8 ar_hbuf[5 * 64];           // Doppler: tablice przesuniec pasow BG3 (0 = bez zaklocen)
u8 ar_wtab[769];              // Chronos: tablica fali czasu (okno przesuwa sie w dol)
u16 chr_acc;                  // Chronos: czas zegara (7 na klatke, 2 gdy dziala jego SLOW)
s16 ufo_x, ufo_stop, ufo_dir;
u8 ufo_y;

const u16 chr_pal[6] = {RGB8(40, 30, 20), RGB8(120, 88, 44), RGB8(176, 136, 72),     // tarcza
                        RGB8(56, 44, 30), RGB8(176, 134, 72), RGB8(244, 206, 128)};  // fala czasu
const u16 chr_spal[2] = {RGB8(80, 58, 28), RGB8(196, 156, 86)};
const u16 mag_off[12] = {0, 22, 44, 66, 88, 110, 132, 154, 176, 198, 220, 242};
const u16 mag_spal[2] = {RGB8(80, 120, 240), RGB8(225, 235, 255)};
const u16 spk_var[4] = {0, 76, 152, 228};   // iskra: 4 warianty zygzaka po 19 sprite'ow
const u16 tele_spal[10] = {RGB8(70, 70, 100), RGB8(130, 130, 170), RGB8(190, 190, 220), RGB8(90, 170, 190),
                           RGB8(180, 240, 250), RGB8(255, 220, 80), RGB8(255, 90, 120), RGB8(150, 190, 120),
                           RGB8(90, 130, 80), RGB8(120, 200, 160)};
const u16 tele_lt[4] = {RGB8(255, 220, 80), RGB8(255, 90, 120), RGB8(255, 90, 120), RGB8(255, 220, 80)};
const u16 tele_bgc[7] = {RGB8(40, 30, 74), RGB8(14, 12, 30), 0, 0, RGB8(60, 64, 110), 0, RGB8(220, 225, 255)};
const s8 ufo_bob[8] = {0, 1, 2, 1, 0, -1, -2, -1};

// Kod C zapisujacy sprite'y w petli byl za wolny (do 100 linii obrazu): gotowe wpisy OAM
// z tools/make_arena2.py kopiuje memcpy.
// ---------------------------------------------------------------------------
// Duch na arenie Maltena: co 20-40 s wylania sie z mgly, plynie chwile w bok i rozplywa sie.
// Polprzezroczysty (paleta sprite'ow 7 + mieszanie z mgla), za liniami boiska, pilka i paletkami.
// Pojawia sie i znika przez coraz czestsze / rzadsze wyswietlanie w kolejnych klatkach:
// sciemnianie palety dawaloby przy usrednianiu z tlem ciemny "cien".
extern char malten_ghost_til, malten_ghost_tilend;
u8 gh_state, gh_t, gh_lv;
s16 gh_x, gh_y0, gh_vx;   // gh_x w 1/16 piksela
u16 gh_timer, gh_age;
const s8 gh_bob[16] = {0, 1, 2, 2, 3, 2, 2, 1, 0, -1, -2, -2, -3, -2, -2, -1};
void ar_hide_spr(void);

void update_ghost(void)
{
    u8 *o = oamMemory + SPR_AR;
    u8 tile;
    s16 x, y;
    if (arena_hidden)   // CAMO: bez ducha
    {
        if (gh_state)
            ar_hide_spr();
        return;
    }
    if (gh_state == 0)
    {
        if (--gh_timer == 0)
        {
            gh_x = (40 + rand() % 150) << 4;
            gh_y0 = 56 + rand() % 80;   // duch ma 48 px wysokosci: zostaje w obrebie boiska
            gh_vx = 4 + (rand() & 3);   // 0,25-0,44 px na klatke
            if (rand() & 1)
                gh_vx = -gh_vx;
            gh_state = 1;
            gh_lv = 0;
            gh_t = 5;
            gh_age = 0;
        }
        return;
    }
    gh_age++;
    gh_x += gh_vx;
    if (gh_state == 1)   // wylania sie z mgly
    {
        if (--gh_t == 0)
        {
            gh_t = 5;
            if (++gh_lv >= 8)
            {
                gh_state = 2;
                gh_t = 150 + (rand() & 63);
            }
        }
    }
    else if (gh_state == 2)   // plynie
    {
        if (--gh_t == 0 || (gh_x >> 4) < 24 || (gh_x >> 4) > 200)
        {
            gh_state = 3;
            gh_t = 6;
        }
    }
    else if (--gh_t == 0)   // rozplywa sie
    {
        gh_t = 6;
        if (--gh_lv == 0)
        {
            gh_state = 0;
            ar_hide_spr();
            gh_timer = 1200 + rand() % 1200;   // nastepny za 20-40 s
            return;
        }
    }
    if ((gh_age & 7) >= gh_lv)   // w tej klatce niewidoczny
    {
        o[1] = 240;
        o[5] = 240;
        o[9] = 240;
        o[13] = 240;
        o[17] = 240;
        o[21] = 240;
        return;
    }
    x = gh_x >> 4;
    y = gh_y0 + gh_bob[(gh_age >> 2) & 15];
    tile = TILE_ARSPR + (((gh_age >> 4) & 1) << 2);   // 2 klatki falujacego ogona
    o[0] = x;
    o[1] = y;
    o[2] = tile;
    o[3] = 0x1E;   // paleta 7, priorytet 1
    o[4] = x + 16;
    o[5] = y;
    o[6] = tile + 2;
    o[7] = 0x1E;
    o[8] = x;
    o[9] = y + 16;
    o[10] = tile + 32;
    o[11] = 0x1E;
    o[12] = x + 16;
    o[13] = y + 16;
    o[14] = tile + 34;
    o[15] = 0x1E;
    o[16] = x;          // trzeci wiersz sprite'ow (duch ma 32x48)
    o[17] = y + 32;
    o[18] = tile + 64;
    o[19] = 0x1E;
    o[20] = x + 16;
    o[21] = y + 32;
    o[22] = tile + 66;
    o[23] = 0x1E;
}

void ar_hide_spr(void)
{
    memcpy(oamMemory + SPR_AR, &ar_hidblk, 128);
}

void arena2_reset(void)
{
    ar_cn1 = 0;
    ar_cn2 = 0;
    ar_hptr = 0;
    ar_vpend = 0;
    ar_hid = 0;
    mag_glow = 0;
    ar_hide_spr();
}

// W VBlank: kolory z kolejki, adres tablicy HDMA, jeden wpis mapy BG3
void vblank_arena2(void)
{
    if (ar_cn1 && vb_ok())
    {
        dmaCopyCGram(ar_cg1, ar_ci1, ar_cn1);
        ar_cn1 = 0;
    }
    if (ar_cn2 && vb_ok())
    {
        dmaCopyCGram(ar_cg2, ar_ci2, ar_cn2);
        ar_cn2 = 0;
    }
    if (ar_hptr)   // wazne od nastepnej klatki (HDMA czyta adres na poczatku obrazu)
    {
        DMA_REG(5, 2) = ar_hptr & 0xFF;
        DMA_REG(5, 3) = ar_hptr >> 8;
        ar_hptr = 0;
    }
    if (ar_vpend && (REG_VBLANK & 0x80))
    {
        VPORT_MAIN = 0x80;
        VPORT_ADDL = ar_vaddr & 0xFF;
        VPORT_ADDH = ar_vaddr >> 8;
        VPORT_DATAL = ar_vval & 0xFF;
        VPORT_DATAH = ar_vval >> 8;
        ar_vpend = 0;
    }
}

void hdma5_setup(u8 mode, u16 tab)   // kanal 5: dwa zapisy do BG3HOFS (0x02 wprost, 0x42 posrednio)
{
    DMA_REG(5, 0) = mode;
    DMA_REG(5, 1) = 0x11;
    DMA_REG(5, 2) = tab & 0xFF;
    DMA_REG(5, 3) = tab >> 8;
    DMA_REG(5, 4) = 0x7E;
    DMA_REG(5, 7) = 0x7E;
}

// Cyber-doppler: kod splywa (dwa cykle palet o roznej predkosci), znaki sie zmieniaja,
// a gdy pojawia sie widmowy blizniak, pasy tla na chwile sie rozjezdzaja i zmieniaja kolor.
void upd_doppler(void)
{
    u16 c, e;
    u16 *mp;
    u8 r, nc = 0;
    if (--ar_t1 == 0)
    {
        ar_t1 = 5;
        ar_o1 += 28;
        if (ar_o1 >= 280)
            ar_o1 = 0;
        nc = 1;
    }
    if (--ar_t2 == 0)
    {
        ar_t2 = 3;
        ar_o2 += 26;
        if (ar_o2 >= 260)
            ar_o2 = 0;
        nc = 1;
    }
    if (ghost_on[0] == 90)
        ar_ev = 24;
    if (ghost_on[1] == 90)
        ar_ev = 24;
    if (ar_ev)
    {
        ar_ev--;
        nc = 1;
        if (ar_ev == 0)
            ar_hptr = (u16)ar_hbuf;
        else if (ar_ev & 1)
        {
            r = arn_rand();
            ar_hptr = (u16)ar_hbuf + 64 + ((u16)(r & 3) << 6);
            if (r & 4)   // kolory zaklocenia (2 warianty)
            {
                ar_cg1 = (u8 *)&doppler_ca + 280;
                ar_cg2 = (u8 *)&doppler_cb + 260;
                if (r & 8)
                {
                    ar_cg1 += 28;
                    ar_cg2 += 26;
                }
                ar_ci1 = 2;
                ar_cn1 = 28;
                ar_ci2 = 19;
                ar_cn2 = 26;
                nc = 0;
            }
        }
        else
            nc = 0;
    }
    if (nc)
    {
        ar_cg1 = (u8 *)&doppler_ca + ar_o1;
        ar_ci1 = 2;
        ar_cn1 = 28;
        ar_cg2 = (u8 *)&doppler_cb + ar_o2;
        ar_ci2 = 19;
        ar_cn2 = 26;
    }
    if (frame & 1)   // co 2 klatki jeden znak zmienia ksztalt (kolor i paleta zostaja)
    {
        c = ((6 + (arn_rand() & 15) + (arn_rand() & 3)) << 5) + (arn_rand() & 31);
        mp = (u16 *)&doppler_code_map;
        e = mp[c];
        if (e & 0x3F0)
        {
            ar_vval = (e & 0xFFF0) | (arn_rand() & 15);
            ar_vaddr = VRAM_RAIN_MAP + c;
            ar_vpend = 1;
        }
    }
}

// Changero: barwy przelewaja sie po pasmach wzoru; co 5-9 s warstwa faluje, tym mocniej,
// im wiecej punktow juz rozegrano
void upd_changero(void)
{
    u16 b, s;
    if (--ar_t1 == 0)
    {
        ar_t1 = 4;
        if (ar_st)
            ar_t1 = 2;
        ar_o1 += 44;
        if (ar_o1 >= 2112)
            ar_o1 = 0;
        ar_cg1 = (u8 *)&changero_cols + ar_o1;
        ar_ci1 = 5;
        ar_cn1 = 22;
        ar_cg2 = ar_cg1 + 22;
        ar_ci2 = 21;
        ar_cn2 = 22;
    }
    if (ar_st == 0)
    {
        if (--ar_ev == 0)
        {
            s = score1 + score2;
            s = 2 + (s * 6) / (win_score + win_score - 1);
            if (s > 8)
                s = 8;
            ar_amax = s;
            ar_st = 1;
            ar_t2 = 1;
        }
    }
    else if (--ar_t2 == 0)
    {
        ar_t2 = 6;
        if (ar_st == 1)
        {
            ar_amp++;
            if (ar_amp >= ar_amax)
            {
                ar_st = 2;
                ar_t2 = 90;
            }
        }
        else if (ar_st == 2)
            ar_st = 3;
        else
        {
            ar_amp--;
            if (ar_amp == 0)
            {
                ar_st = 0;
                ar_ev = 300 + (rand() & 255);
            }
        }
    }
    b = arena_x >> 1;
    s = 0;
    if (b != ar_last)
        s = 1;
    if (ar_amp != ar_lv)
        s = 1;
    if (s)
    {
        ar_last = b;
        ar_lv = ar_amp;
        wave2_vals_asm(b, ar_amp);
    }
    if (frame & 1)
    {
        wave_phase = (wave_phase + 1) & 31;
        wave_ready = 1;
    }
}

// Chronos: wskazowki ze sprite'ow (minutowa krok co sekunde, godzinowa co 12 krokow)
void chr_draw(void)
{
    memcpy(oamMemory + SPR_AR, (u8 *)&chronos_hm + ar_o1, 40);
    memcpy(oamMemory + SPR_AR + 40, (u8 *)&chronos_hh + ar_o2, 24);
}

void upd_chronos(void)
{
    u16 s;
    if (ar_redraw)
    {
        ar_redraw = 0;
        chr_draw();
    }
    s = 7;   // SLOW Chronosa daje paletce przeciwnika 2/7 predkosci - zegar zwalnia tak samo
    if (char_of[0] == CH_G0 + 5 && slow_timer[1])
        s = 2;
    if (char_of[1] == CH_G0 + 5 && slow_timer[0])
        s = 2;
    chr_acc += s;
    if (chr_acc >= 420)   // 420 = 60 klatek w zwyklym tempie
    {
        chr_acc -= 420;
        ar_o1 += 40;
        if (ar_o1 >= 2400)
            ar_o1 = 0;
        if (--ar_t2 == 0)
        {
            ar_t2 = 12;
            ar_o2 += 24;
            if (ar_o2 >= 1440)
                ar_o2 = 0;
        }
        chr_draw();
    }
    if (chron_slowed)   // Chronos spowolnil pilke: po tarczy przechodzi fala czasu
    {
        if (ar_st == 0)
        {
            ar_ev = 37;
            ar_cg1 = (u8 *)chr_pal + 6;
            ar_ci1 = 29;
            ar_cn1 = 6;
        }
    }
    ar_st = chron_slowed;
    if (ar_ev)
    {
        ar_ev--;
        s = ar_ev << 2;   // poczatek okna tablicy: 144 -> 0, garb fali wedruje w dol
        ar_hptr = (u16)ar_wtab + s + s + s;
        if (ar_ev == 0)
        {
            ar_cg1 = (u8 *)chr_pal;
            ar_ci1 = 29;
            ar_cn1 = 6;
        }
    }
}

// Magneton: kreski plyna po liniach pola od N do S; przy przyciaganiu pilki linie rozblyskuja
// i plyna szybciej. Co 5-13 s iskra przeskakuje miedzy bandami.
void mag_spark(void)   // ar_o2: kolumna iskry, wariant zygzaka losowy przy kazdym odswiezeniu
{
    memcpy(oamMemory + SPR_AR, (u8 *)&magneton_sparks + ar_o2 + spk_var[arn_rand() & 3], 76);
}

void upd_magneton(void)
{
    u8 tg = 0, ch = 0;
    if (mag_glow)
    {
        mag_glow--;
        tg = 3;
    }
    if (--ar_n2 == 0)   // jasnosc linii dochodzi do celu o stopien co 4 klatki
    {
        ar_n2 = 4;
        if (ar_lv < tg)
        {
            ar_lv++;
            ch = 1;
        }
        else if (ar_lv > tg)
        {
            ar_lv--;
            ch = 1;
        }
    }
    if (--ar_t1 == 0)
    {
        ar_t1 = 8 - ar_lv - ar_lv;
        ar_n1++;
        if (ar_n1 == 3)
            ar_n1 = 0;
        ch = 1;
    }
    if (ch)
    {
        ar_cg1 = (u8 *)&magneton_cols + mag_off[ar_lv + ar_lv + ar_lv + ar_n1];
        ar_ci1 = 21;
        ar_cn1 = 22;
    }
    if (ar_t2)
    {
        ar_t2--;
        mag_glow = 6;
        if (ar_t2 == 0)
            ar_hide_spr();
        else if (ar_t2 & 1)
            mag_spark();
    }
    else if (--ar_ev == 0)
    {
        ar_ev = 300 + (rand() & 511);
        ar_o2 = (u16)(arn_rand() & 7) * 304;
        ar_t2 = 14;
        mag_spark();
    }
}

// Telementor: gwiazdy migocza; co 15-25 s przelatuje UFO, zatrzymuje sie i swieci wiazka w dol
void tele_ufo(void)
{
    s16 x = ufo_x;
    u8 y, hb = 0x0A;   // sprite'y 96 i 97 duze (16x16), 9. bit x ustawiany ponizej
    u8 *o = oamMemory + SPR_AR;
    y = ufo_y;
    if (ar_st != 2)   // w locie kolysze sie, nad wiazka wisi nieruchomo
        y += ufo_bob[(frame >> 3) & 7];
    o[1] = 240;
    o[5] = 240;
    if (x > -16)
    {
        if (x < 256)
        {
            o[0] = x;
            o[1] = y;
            o[2] = TILE_ARSPR;
            o[3] = ATTR_AR;
            if (x < 0)
                hb |= 0x01;
        }
    }
    x += 16;
    if (x > -16)
    {
        if (x < 256)
        {
            o[4] = x;
            o[5] = y;
            o[6] = TILE_ARSPR + 2;
            o[7] = ATTR_AR;
            if (x < 0)
                hb |= 0x04;
        }
    }
    oamMemory[512 + 24] = hb;
}

void tele_beam(u8 on)   // sprite'y 100-108; ar_o2: wpisy dla miejsca postoju i wysokosci UFO
{
    if (on)
        memcpy(oamMemory + SPR_AR + 16, (u8 *)&telementor_beam + ar_o2, 36);
    else
        memcpy(oamMemory + SPR_AR + 16, &ar_hidblk, 36);
}

void upd_tele(void)
{
    u8 on, ch, k;
    if (--ar_t1 == 0)
    {
        ar_t1 = 10;
        ar_o1 += 6;
        if (ar_o1 >= 96)
            ar_o1 = 0;
        ar_cg1 = (u8 *)&telementor_cols + ar_o1;
        ar_ci1 = 29;
        ar_cn1 = 6;
    }
    if (ar_redraw)
    {
        ar_redraw = 0;
        if (ar_st)
            tele_ufo();
        if (ar_st == 2)
        {
            tele_beam(1);
            ar_n1 = 1;
        }
    }
    if (ar_st == 0)
    {
        if (--ar_ev == 0)
        {
            ufo_x = -32;
            ufo_dir = 1;
            if (arn_rand() & 1)
            {
                ufo_x = 256;
                ufo_dir = -1;
            }
            ufo_y = 58;
            k = arn_rand() & 15;   // 8 miejsc postoju (x = 48..160) i 2 wysokosci
            if (k & 1)
                ufo_y = 66;
            ufo_stop = 48 + ((k >> 1) << 4);
            ar_o2 = ((u16)k << 5) + ((u16)k << 2);
            ar_st = 1;
        }
        return;
    }
    if ((frame & 7) == 0)   // swiatla UFO na zmiane
    {
        ar_cg2 = (u8 *)tele_lt;
        if (frame & 8)
            ar_cg2 += 4;
        ar_ci2 = SPR_PAL3 + 6;
        ar_cn2 = 4;
    }
    if (ar_st == 2)
    {
        ar_t2--;
        on = 1;
        if (ar_t2 > 136)   // wiazka zapala sie z migotaniem...
            on = (ar_t2 >> 1) & 1;
        if (ar_t2 < 8)     // ...i tak samo gasnie
            on = ar_t2 & 1;
        if (ar_t2 == 0)
        {
            on = 0;
            ar_st = 3;
        }
        ch = 0;
        if (on != ar_n1)
            ch = 1;
        if (ch)
        {
            ar_n1 = on;
            tele_beam(on);
            tele_ufo();
        }
        return;
    }
    ufo_x += ufo_dir;
    tele_ufo();
    if (ar_st == 1)
    {
        if (ufo_x == ufo_stop)
        {
            ar_st = 2;
            ar_t2 = 150;
            ar_n1 = 0;
        }
        return;
    }
    ch = 0;
    if (ufo_x < -32)
        ch = 1;
    if (ufo_x > 256)
        ch = 1;
    if (ch)
    {
        ar_st = 0;
        ar_ev = 900 + (rand() & 511);
        ar_hide_spr();
    }
}

// Blinker: tecza, ktorej barwy lekko sie mienia (cykl palet jak u Changero)
void upd_blinker(void)
{
    if (--ar_t1 == 0)
    {
        ar_t1 = 4;
        ar_o1 += 44;
        if (ar_o1 >= 1408)
            ar_o1 = 0;
        ar_cg1 = (u8 *)&blinker_cols + ar_o1;
        ar_ci1 = 5;
        ar_cn1 = 22;
        ar_cg2 = ar_cg1 + 22;
        ar_ci2 = 21;
        ar_cn2 = 22;
    }
}

void update_arena2(void)
{
    if (arena_hidden)   // CAMO: warstwa i HDMA sa wylaczone, sprite'y tez chowamy
    {
        if (ar_hid == 0)
        {
            ar_hid = 1;
            ar_hide_spr();
        }
        return;
    }
    if (ar_hid)
    {
        ar_hid = 0;
        ar_redraw = 1;
    }
    if (arena == AR_DOPPLER)
        upd_doppler();
    else if (arena == AR_CHANGERO)
        upd_changero();
    else if (arena == AR_CHRONOS)
        upd_chronos();
    else if (arena == AR_MAGNETON)
        upd_magneton();
    else if (arena == AR_TELE)
        upd_tele();
    else
        upd_blinker();
}

// Wczytanie areny 4-9 (ekran zgaszony, HDMA wylaczone)
void arena2_setup(void)
{
    u8 i, j, r;
    u8 *t;
    s16 e;
    bgSetScroll(2, 0, 0);
    ar_hmask = 0x40;
    ar_t1 = 1;
    ar_t2 = 1;
    ar_n1 = 0;
    ar_n2 = 1;
    ar_o1 = 0;
    ar_o2 = 0;
    ar_st = 0;
    ar_ev = 0;
    ar_amp = 0;
    ar_lv = 0;
    ar_last = 0xFFFF;
    ar_redraw = 0;
    for (i = 24; i < 32; i++)   // sprite'y 96-127: male, x < 256
        oamMemory[512 + i] = 0;
    if (arena == AR_DOPPLER)
    {
        dmaCopyVram(&doppler_code_til, VRAM_RAIN_GFX, (&doppler_code_tilend - &doppler_code_til));
        dmaCopyVram(&doppler_code_map, VRAM_RAIN_MAP, 2048);
        memcpy(hdma_grad, &doppler_grad, (&doppler_gradend - &doppler_grad));
        dmaCopyCGram(&doppler_ca, 2, 28);
        dmaCopyCGram(&doppler_cb, 19, 26);
        t = ar_hbuf;
        for (i = 0; i < 5; i++)   // tablica 0: bez przesuniec, 1-4: losowe zaklocenia
        {
            t[0] = 48;
            t[1] = 0;
            t[2] = 0;
            t += 3;
            for (j = 0; j < 19; j++)   // 19 pasow po 8 linii (boisko)
            {
                r = rand() & 0xFF;
                e = 0;
                if (i)
                {
                    if (r & 3)
                    {
                        e = (r >> 2) & 15;
                        e -= 8;
                        if ((r & 0xC0) == 0xC0)
                            e = e + e + e;
                    }
                }
                t[0] = 8;
                t[1] = e & 0xFF;
                t[2] = e >> 8;
                t += 3;
            }
            t[0] = 24;
            t[1] = 0;
            t[2] = 0;
            t[3] = 0;
            t += 4;
        }
        hdma5_setup(0x02, (u16)ar_hbuf);
        ar_hmask = 0x60;
    }
    else if (arena == AR_CHANGERO)
    {
        dmaCopyVram(&changero_plasma_til, VRAM_RAIN_GFX, (&changero_plasma_tilend - &changero_plasma_til));
        dmaCopyVram(&changero_plasma_map, VRAM_RAIN_MAP, 2048);
        dmaCopyCGram(&changero_cols, 5, 22);
        dmaCopyCGram(&changero_cols + 22, 21, 22);
        wave_phase = 0;
        build_wave_tables();
        wave2_vals_asm(0, 0);
        hdma5_setup(0x42, (u16)wave_ind[0]);
        wave_ready = 0;
        ar_ev = 240;
        ar_hmask = 0x20;   // wzor pokrywa cale boisko: bez gradientu
    }
    else if (arena == AR_CHRONOS)
    {
        dmaCopyVram(&chronos_dial_til, VRAM_RAIN_GFX, (&chronos_dial_tilend - &chronos_dial_til));
        dmaCopyVram(&chronos_dial_map, VRAM_RAIN_MAP, 2048);
        dmaCopyVram(&chronos_hands_til, VRAM_SPR + TILE_ARSPR * 16, (&chronos_hands_tilend - &chronos_hands_til));
        memcpy(hdma_grad, &chronos_grad, (&chronos_gradend - &chronos_grad));
        dmaCopyCGram((u8 *)chr_pal, 29, 6);
        dmaCopyCGram((u8 *)chr_spal, SPR_PAL3 + 1, 4);
        memcpy(ar_wtab, &chronos_wave, 769);
        hdma5_setup(0x02, (u16)ar_wtab);
        chr_acc = 0;
        ar_t2 = 12;
        ar_o2 = 50 * 24;   // godzina 10:00
        ar_redraw = 1;
        ar_hmask = 0x60;
    }
    else if (arena == AR_MAGNETON)
    {
        dmaCopyVram(&magneton_field_til, VRAM_RAIN_GFX, (&magneton_field_tilend - &magneton_field_til));
        dmaCopyVram(&magneton_field_map, VRAM_RAIN_MAP, 2048);
        dmaCopyVram(&magneton_spark_til, VRAM_SPR + TILE_ARSPR * 16, (&magneton_spark_tilend - &magneton_spark_til));
        memcpy(hdma_grad, &magneton_grad, (&magneton_gradend - &magneton_grad));
        dmaCopyCGram(&magneton_cols, 21, 22);
        dmaCopyCGram((u8 *)mag_spal, SPR_PAL3 + 1, 4);
        ar_t1 = 8;
        ar_n2 = 4;
        ar_ev = 300 + (rand() & 255);
    }
    else if (arena == AR_TELE)
    {
        dmaCopyVram(&telementor_sky_til, VRAM_RAIN_GFX, (&telementor_sky_tilend - &telementor_sky_til));
        dmaCopyVram(&telementor_sky_map, VRAM_RAIN_MAP, 2048);
        dmaCopyVram(&telementor_ufo_til, VRAM_SPR + TILE_ARSPR * 16, (&telementor_ufo_tilend - &telementor_ufo_til));
        memcpy(hdma_grad, &telementor_grad, (&telementor_gradend - &telementor_grad));
        dmaCopyCGram(&telementor_cols, 29, 6);
        dmaCopyCGram((u8 *)tele_bgc, 21, 14);
        dmaCopyCGram((u8 *)tele_spal, SPR_PAL3 + 1, 20);
        oamMemory[512 + 24] = 0x0A;   // UFO (96, 97) i wiazka (100-108): sprite'y 16x16
        oamMemory[512 + 25] = 0xAA;
        oamMemory[512 + 26] = 0xAA;
        oamMemory[512 + 27] = 0x02;
        ar_t1 = 10;
        ar_ev = 300 + (rand() & 255);
    }
    else
    {
        dmaCopyVram(&blinker_rainbow_til, VRAM_RAIN_GFX, (&blinker_rainbow_tilend - &blinker_rainbow_til));
        dmaCopyVram(&blinker_rainbow_map, VRAM_RAIN_MAP, 2048);
        dmaCopyCGram(&blinker_cols, 5, 22);
        dmaCopyCGram(&blinker_cols + 22, 21, 22);
        ar_t1 = 4;
        ar_hmask = 0;   // tlo to kolor 0 Blinkera: bez gradientu
    }
}

// Tlo areny strażnika: w trybie fabularnym jego walka, w trybach 1/2 PLAYER - gdy gra po lewej
void arena_setup(void)
{
    u16 i, e;
    u8 f, g;
    u16 *cm;
    u8 *t;
    arena = 0;
    g = 0xFF;
    if (story)
        g = stage;
    else if (char_of[0] >= CH_G0)
        g = char_of[0] - CH_G0;
    if (g < 9)   // Kimantero (9) ma burze
        arena = g + 1;
    if (g == G_LUCIFERO || (!story && char_of[1] == CH_G0 + G_LUCIFERO))   // Lucifero: pochylone boisko
    {
        arena = ARENA_LUC;
        luc_setup();
        return;
    }
    if (!arena)
        return;
    arena_x = 0;
    arena_hidden = 0;
    if (arena == 1)
    {
        dmaCopyVram(&ruden_dust_til, VRAM_RAIN_GFX, (&ruden_dust_tilend - &ruden_dust_til));
        dmaCopyVram(&ruden_dust_map, VRAM_RAIN_MAP, 2048);
        dmaCopyVram(&ruden_crowd_til, VRAM_BG1_GFX + TILES_BOLT * 16, (&ruden_crowd_tilend - &ruden_crowd_til));
        memcpy(hdma_grad, &ruden_grad, (&ruden_gradend - &ruden_grad));
        setPaletteColor(29, RGB8(90, 45, 20));                    // kurz
        setPaletteColor(30, RGB8(130, 70, 32));
        setPaletteColor(PAL_COURT * 16 + 5, RGB8(26, 12, 8));     // sylwetki ogrow
        setPaletteColor(PAL_COURT * 16 + 6, RGB8(120, 50, 14));   // obrys od nieba
        setPaletteColor(PAL_COURT * 16 + 7, eye_glow[0]);   // oczy (pulsuja)
        setPaletteColor(PAL_COURT * 16 + 8, eye_halo[0]);   // poswiata wokol oczu
        eye_i = 0;
        eye_dir = 1;
        eye_t = 2;
        eye_dirty = 0;
        cm = (u16 *)&ruden_crowd_map;   // 4 mapy po 7 wierszy (18-24); 0xFFFF = zostaje boisko
        for (f = 0; f < 5; f++)
            for (i = 0; i < 256; i++)       // klatka obejmuje wiersze 17-24
            {
                e = 0xFFFF;
                if (f < 4 && i >= 32)
                    e = cm[f * 224 + i - 32];
                else if (f == 4 && i < 224)   // wiwat w podskoku: poza wiwatu o wiersz wyzej
                    e = cm[3 * 224 + i];
                if (e == 0xFFFF)
                    e = bgmap[17 * 32 + i];
                crowd_rows[f][i] = e;
            }
        memcpy(bgmap + 17 * 32, crowd_rows[0], 512);
        dmaCopyVram((u8 *)(bgmap + 17 * 32), VRAM_BG1_MAP + 17 * 32, 512);
        crowd_frame = 0;
        crowd_step = 0;
        crowd_t = 10;
        cheer_t = 0;
        last_owner_score = 0;
    }
    else if (arena == 3)   // Waller: noc, mur, pochodnie, nietoperze
    {
        dmaCopyVram(&waller_wall_til, VRAM_RAIN_GFX, (&waller_wall_tilend - &waller_wall_til));
        dmaCopyVram(&waller_wall_map, VRAM_RAIN_MAP, 2048);
        dmaCopyVram(&waller_torch_til, VRAM_BG1_GFX + TILES_BOLT * 16, (&waller_torch_tilend - &waller_torch_til));
        dmaCopyVram(&bat_til, VRAM_SPR + TILE_BAT * 16, (&bat_tilend - &bat_til));
        memcpy(hdma_grad, &waller_grad, (&waller_gradend - &waller_grad));
        bgSetScroll(2, 0, 0);
        setPaletteColor(29, RGB8(6, 6, 10));       // mur: zaprawa
        setPaletteColor(30, RGB8(30, 32, 46));     // kamien
        setPaletteColor(31, RGB8(44, 48, 66));     // krawedz cegly
        setPaletteColor(25, RGB8(6, 6, 10));       // mur w swietle pochodni: zaprawa i kamien jak wyzej,
        setPaletteColor(26, RGB8(30, 32, 46));     // kolor 3 to cieple, migoczace swiatlo
        setPaletteColor(27, glow_col[4]);
        setPaletteColor(PAL_COURT * 16 + 3, RGB8(70, 70, 80));     // pochodnie: zelazo
        setPaletteColor(PAL_COURT * 16 + 4, RGB8(96, 60, 30));     // drewno
        setPaletteColor(PAL_COURT * 16 + 5, RGB8(150, 30, 10));    // plomien
        setPaletteColor(PAL_COURT * 16 + 6, RGB8(240, 120, 24));
        setPaletteColor(PAL_COURT * 16 + 7, RGB8(255, 214, 64));
        setPaletteColor(PAL_COURT * 16 + 12, RGB8(255, 250, 210));
        setPaletteColor(128 + 7 * 16 + 1, RGB8(20, 12, 26));      // nietoperze: cialo
        setPaletteColor(128 + 7 * 16 + 2, RGB8(44, 30, 56));      // blona skrzydel
        setPaletteColor(128 + 7 * 16 + 3, RGB8(230, 40, 40));     // oczy
        for (i = 0; i < TORCHES; i++)
        {
            tor_f[i] = (i * 3) & 7;   // kazda pochodnia w innej fazie
            tor_t[i] = 2 + i;
            bgmap[16 * 32 + torch_col[i]] = (TILES_BOLT + 0) | (PAL_COURT << 10);   // uchwyt
            bgmap[14 * 32 + torch_col[i]] = (TILES_BOLT + 1 + tor_f[i] * 2) | (PAL_COURT << 10);
            bgmap[15 * 32 + torch_col[i]] = (TILES_BOLT + 2 + tor_f[i] * 2) | (PAL_COURT << 10);
        }
        dmaCopyVram((u8 *)(bgmap + 14 * 32), VRAM_BG1_MAP + 14 * 32, 192);
        glow_lv = 4;
        glow_cur = 4;
        glow_t = 3;
        for (i = 0; i < BATS; i++)
            bat_on[i] = 0;
        for (i = 20; i < 24; i++)   // sprite'y 80-95: male, bez 9. bitu pozycji
            oamMemory[512 + i] = 0;
        bat_timer = 600 + rand() % 600;   // pierwsze stadko po 10-20 s
    }
    else if (arena == 2)
    {
        dmaCopyVram(&malten_fog_til, VRAM_RAIN_GFX, (&malten_fog_tilend - &malten_fog_til));
        dmaCopyVram(&malten_fog_map, VRAM_RAIN_MAP, 2048);
        memcpy(hdma_grad, &malten_grad, (&malten_gradend - &malten_grad));
        setPaletteColor(29, RGB8(70, 60, 100));    // mgla
        dmaCopyVram(&malten_ghost_til, VRAM_SPR + TILE_ARSPR * 16, (&malten_ghost_tilend - &malten_ghost_til));
        setPaletteColor(128 + 7 * 16 + 1, RGB8(215, 215, 240));   // duch: cialo
        setPaletteColor(128 + 7 * 16 + 2, RGB8(140, 140, 185));   // kontur i cien
        setPaletteColor(128 + 7 * 16 + 3, RGB8(20, 16, 36));      // oczy i usta
        setPaletteColor(128 + 7 * 16 + 4, RGB8(250, 250, 255));   // rozblysk
        oamMemory[512 + 24] = 0xAA;   // sprite'y 96-99: 16x16
        oamMemory[512 + 25] = 0x0A;   // sprite'y 100-101: 16x16 (duch ma 6 sprite'ow)
        REG_TS = 0x06;                // przezroczystosc miesza sprite'y z boiskiem i mgla
        gh_state = 0;
        gh_timer = 480 + rand() % 420;   // pierwszy duch po 8-15 s
        setPaletteColor(30, RGB8(120, 110, 160));
        wave_phase = 0;
        build_wave_tables();
        build_wave();
        t = wave_ind[0];
        DMA_REG(5, 0) = 0x42;   // HDMA kanal 5, tryb posredni: dwa zapisy do BG3HOFS
        DMA_REG(5, 1) = 0x11;
        DMA_REG(5, 2) = (u16)t & 0xFF;
        DMA_REG(5, 3) = (u16)t >> 8;
        DMA_REG(5, 4) = 0x7E;
        DMA_REG(5, 7) = 0x7E;   // bank wartosci (posrednich)
        wave_ready = 0;
    }
    else
        arena2_setup();
    t = hdma_grad;
    DMA_REG(6, 0) = 0x03;   // HDMA kanal 6: CGADD, CGADD, CGDATA, CGDATA (kolor 0 = tlo)
    DMA_REG(6, 1) = 0x21;
    DMA_REG(6, 2) = (u16)t & 0xFF;
    DMA_REG(6, 3) = (u16)t >> 8;
    DMA_REG(6, 4) = 0x7E;
    hdma_mask = 0x40;
    if (arena == 2)
        hdma_mask |= 0x20;
    if (arena >= AR_DOPPLER)
        hdma_mask = ar_hmask;
    bgSetEnable(2);
    hdma_start = 1;   // HDMA wlaczy dopiero pierwszy VBlank po wczytaniu (nie przy kopiowaniu palet)
}

void hide_bats(void)
{
    u16 id;
    for (id = SPR_BAT; id < SPR_BAT + BATS * 8; id += 4)
        HIDE(id)
}

// Waller: plomienie pochodni (kazda w swoim rytmie), migotanie swiatla, stadka nietoperzy.
// Uwaga: kompilator zamienia mnozenie na wolna procedure - tu tylko dodawanie i przesuniecia.
void update_waller(void)
{
    u8 i, n, slit, r8;
    s16 x, y, r;
    u16 at, id, age;
    for (i = 0; i < TORCHES; i++)
        if (--tor_t[i] == 0)
        {
            r8 = arn_rand();
            tor_f[i] = (tor_f[i] + 1 + (r8 & 3) + ((r8 >> 4) & 1)) & 7;   // nastepny ksztalt: przypadkowy, bez rytmu
            tor_t[i] = 2 + ((r8 >> 2) & 3);                            // co 2-5 klatek obrazu (nierowno)
            at = TILES_BOLT + 1 + (tor_f[i] << 1) + (PAL_COURT << 10);
            id = torch_col[i];
            bgmap[14 * 32 + id] = at;
            bgmap[15 * 32 + id] = at + 1;
            torch_dirty = 1;
        }
    if (--glow_t == 0)   // swiatlo na murze: bladzenie losowe jasnosci
    {
        r8 = arn_rand();
        glow_t = 3 + (r8 & 3);
        n = (r8 >> 3) & 3;
        if (n == 0 && glow_lv > 0)
            glow_lv--;
        else if (n == 1 && glow_lv < 4)
            glow_lv++;
    }
    if (arena_hidden)   // CAMO: bez nietoperzy
    {
        hide_bats();
        return;
    }
    if (bat_timer)
    {
        if (--bat_timer == 0)   // nowe stadko z jednego z otworow strzelniczych
        {
            n = 3 + rand() % 3;
            slit = rand() & 1;
            bat_sy = 104;
            for (i = 0; i < BATS; i++)
            {
                bat_on[i] = (i < n);
                bat_del[i] = bat_dl[i] + (rand() & 3);
                bat_x[i] = slit ? (172 << 4) : (76 << 4);   // srodek otworu (84 lub 180) - pol nietoperza
                bat_vx[i] = 20 + (rand() & 7);       // 1,25-1,7 px na klatke
                if (slit)
                    bat_vx[i] = -bat_vx[i];   // z prawego otworu leca w lewo, z lewego w prawo
                bat_rise[i] = 24 + rand() % 26;
                bat_age[i] = 0;
            }
        }
        return;
    }
    bats_asm();   // ruch i sprite'y nietoperzy (asembler: kod C byl za wolny)
    if (bat_n == 0)   // stadko odlecialo: nastepne za 20-40 s
        bat_timer = 1200 + rand() % 1200;
}

void update_arena(void)
{
    u8 hid = 0, i;
    u16 own, e;
    if (!arena)
        return;
    if (frame & 1)
        arena_x++;   // kurz i mgla dryfuja w bok
    if (camo_timer[0] || camo_timer[1])   // CAMO: tlo nie moze zdradzac paletki
        hid = 1;
    if (hid != arena_hidden)
    {
        arena_hidden = hid;
        arena_apply = 1;
    }
    if (arena == 1)
    {
        own = score1;   // punkty Rudena (w trybie fabularnym gra po prawej)
        if (story)
            own = score2;
        if (own != last_owner_score)
        {
            last_owner_score = own;
            cheer_t = 90;   // ogry wiwatuja
        }
        if (cheer_t)
            cheer_t--;
        if (--crowd_t == 0)
        {
            if (cheer_t)   // wiwat: podskoki z rekami w gorze
            {
                crowd_frame = (crowd_frame == 3) ? 4 : 3;
                crowd_t = 7;
            }
            else
            {
                crowd_step = (crowd_step + 1) & 3;
                crowd_frame = crowd_seq[crowd_step];
                crowd_t = 10;
            }
            for (i = 0; i < 8; i++)   // brzegi wierszy (np. mury FORTRESS) z aktualnej mapy boiska
            {
                e = (17 + i) << 5;
                memcpy(&crowd_rows[crowd_frame][i << 5], &bgmap[e], 8);
                memcpy(&crowd_rows[crowd_frame][(i << 5) + 28], &bgmap[e + 28], 8);
            }
            crowd_dirty = 1;
        }
        if (--eye_t == 0)   // swiecace oczy: puls tam i z powrotem przez 16 odcieni (ok. 1 s)
        {
            eye_t = 2;
            if (eye_dir)
            {
                if (++eye_i == 15)
                    eye_dir = 0;
            }
            else if (--eye_i == 0)
                eye_dir = 1;
            eye_dirty = 1;
        }
    }
    else if (arena == 3)
        update_waller();
    else if (arena == 2)
    {
        build_wave();   // dryf mgly (32 wartosci)
        if (frame & 1)  // falowanie: nastepna faza co 2 klatki (podmiana wskaznika w VBlank)
        {
            wave_phase = (wave_phase + 1) & 31;
            wave_ready = 1;
        }
        update_ghost();   // duch wylaniajacy sie z mgly
    }
    else if (arena != ARENA_LUC)   // (Lucifero ma wlasne efekty w luc_wait_vb)
        update_arena2();
}

void storm_check(void)
{
    if (story)
    {
        if (stage != 9)   // tylko walka z Kimantero
            return;
    }
    else if (!is_g(0, 9))   // tryby 1/2 PLAYER: arena nalezy do postaci po lewej
        return;
    storm_on = 1;
    // kafelki i mapa deszczu od nowa: areny i ekran tytulowy uzywaja tego samego miejsca w VRAM
    dmaCopyVram(&rain_til, VRAM_RAIN_GFX, (&rain_tilend - &rain_til));
    dmaCopyVram(&rain_map, VRAM_RAIN_MAP, (&rain_mapend - &rain_map));
    dmaCopyVram(&bolt_til, VRAM_BG1_GFX + TILES_BOLT * 16, (&bolt_tilend - &bolt_til));
    setPaletteColor(29, RGB8(100, 118, 150));                  // smugi deszczu
    setPaletteColor(30, RGB8(168, 182, 209));                  // jasniejsze konce kropli
    setPaletteColor(PAL_COURT * 16 + 3, RGB8(120, 150, 255));  // poswiata pioruna
    setPaletteColor(PAL_COURT * 16 + 4, RGB8(240, 245, 255));  // rdzen pioruna
    cm_norm_adsub = CM_STORM_ADSUB;
    cm_adsub = CM_STORM_ADSUB;
    REG_CGADSUB = CM_STORM_ADSUB;
    SFP_BGMODE = 0x09;   // tryb 1 + BG3 z wysokim priorytetem: deszcz przed wszystkim
    bgSetEnable(2);
    bright_max = STORM_BRIGHT;
    storm_t = 240;
}

u16 storm_interval(void)   // odstep do nastepnej blyskawicy (klatki)
{
    if (kim_level >= 9)
        return 60 + rand() % 90;
    if (kim_level >= 6)
        return 120 + rand() % 120;
    if (kim_level >= 3)
        return 240 + rand() % 180;
    return 480 + rand() % 240;
}

void bolt_strike(void)
{
    u8 sh = rand() % 3, x, y, i;
    u16 e, m;
    bolt_col = 3 + rand() % 25;
    bolt_row = 6 + rand() % 6;
    for (y = 0; y < 8; y++)
    {
        for (x = 0; x < 2; x++)
        {
            i = y * 2 + x;
            m = (bolt_row + y) * 32 + bolt_col + x;
            bolt_save[i] = bgmap[m];
            e = (TILES_BOLT + sh * 16 + i) | (PAL_COURT << 10);
            bolt_new[i] = e;
            bgmap[m] = e;
        }
    }
    bolt_dirty = 1;
    storm_flash = RGB8(190, 205, 255);   // niebo rozswietlone
    storm_bri = 15;
    thunder_t = 8 + rand() % 30;         // grzmot chwile po blysku
    bolt_t = 1;
}

void bolt_clear(void)
{
    u8 y, x, i;
    u16 m;
    for (y = 0; y < 8; y++)
    {
        for (x = 0; x < 2; x++)
        {
            i = y * 2 + x;
            m = (bolt_row + y) * 32 + bolt_col + x;
            bgmap[m] = bolt_save[i];
            bolt_new[i] = bolt_save[i];
        }
    }
    bolt_dirty = 1;
}

// Wpisy pioruna do mapy boiska w VRAM: 8 wierszy po 2 kafelki (wywolywane w VBlank)
void bolt_upload(void)
{
    u8 y;
    u16 a;
    // Poza VBlank konsola ignoruje zapisy do pamieci obrazu: gdy brakuje czasu, przerywamy,
    // a caly zapis powtarza sie w nastepnej klatce (inaczej fragmenty pioruna zostawaly na ekranie)
    VPORT_MAIN = 0x80;
    for (y = 0; y < 8; y++)
    {
        if (!vb_ok())
            return;   // bolt_dirty zostaje: ponowienie w nastepnej klatce
        a = VRAM_BG1_MAP + (bolt_row + y) * 32 + bolt_col;
        VPORT_ADDL = a & 0xFF;
        VPORT_ADDH = a >> 8;
        VPORT_DATAL = bolt_new[y * 2] & 0xFF;
        VPORT_DATAH = bolt_new[y * 2] >> 8;
        VPORT_DATAL = bolt_new[y * 2 + 1] & 0xFF;
        VPORT_DATAH = bolt_new[y * 2 + 1] >> 8;
    }
    bolt_dirty = 0;
}

void update_storm(void)
{
    if (!storm_on)
        return;
    rain_x += 2;   // deszcz: w lewo...
    rain_y -= 4;   // ...i w dol, zgodnie z nachyleniem smug
    if (thunder_t)
    {
        if (--thunder_t == 0)
            play_sound(SND_THUNDER);
    }
    if (bolt_t)   // trwa blyskawica: dwa rozblyski, potem piorun gasnie
    {
        bolt_t++;
        if (bolt_t == 3)
            storm_flash = 0;
        else if (bolt_t == 5)
            storm_flash = RGB8(120, 135, 190);
        else if (bolt_t == 8)
        {
            storm_flash = 0;
            storm_bri = bright_max;
        }
        else if (bolt_t == 16)
        {
            bolt_clear();
            bolt_t = 0;
        }
        return;
    }
    if (storm_t)
    {
        storm_t--;
        return;
    }
    // bez blyskawic, gdy dziala CAMO albo blysk mocy specjalnej (te tez zmieniaja kolory)
    if (state != ST_PLAY || camo_timer[0] || camo_timer[1] || flash_t)
    {
        storm_t = 30;
        return;
    }
    bolt_strike();
    storm_t = storm_interval();
}

// Poza rozgrywka (wynik, koniec meczu, pauza): deszcz pada dalej (gdy move = 1),
// a ewentualna blyskawica od razu gasnie, zeby nie zostala na ekranie
void storm_idle(u8 move)
{
    if (!storm_on)
        return;
    if (move)
    {
        rain_x += 2;
        rain_y -= 4;
    }
    if (bolt_t)
    {
        bolt_clear();
        bolt_t = 0;
        storm_flash = 0;
        storm_bri = bright_max;
    }
    thunder_t = 0;
}

void setup_match(void)
{
    u16 *mm = (u16 *)&minicons_map;
    u16 sn;
    u8 len;

    srand(snes_vblank_count);
    score1 = 0;
    score2 = 0;
    reset_effects();
    wrap[0] = is_g(0, 4);   // Changero przechodzi przez krawedzie boiska
    wrap[1] = is_g(1, 4);
    setPaletteColor(128 + 80 + 1, g_fill[3]);   // paleta sprite'ow 5: polprzezroczysty
    setPaletteColor(128 + 80 + 2, g_edge[3]);   // widmowy bliźniak Cyber-dopplera
    p1_y = (FIELD_TOP + FIELD_BOTTOM - pad_h[0]) / 2;
    p2_y = (FIELD_TOP + FIELD_BOTTOM - pad_h[1]) / 2;
    serve_right = rand() & 1;
    new_cpu_error();
    hide_sprites();
    go_serve();
    draw_sprites();

    // boisko + male portrety, ikony mocy i paski nad nim
    dmaCopyCGram(&court_pal, PAL_COURT * 16, 32);
    memcpy(bgmap, &court_map, (u8 *)&court_mapend - (u8 *)&court_map);
    hud_char(0, 1, 1);    // portrety postaci po obu stronach
    hud_char(1, 27, 1);
    bgmap[96 + 8] = mm[icon_of(power[0])];
    bgmap[96 + 23] = mm[icon_of(power[1])];
    update_bar_map(0);
    update_bar_map(1);
    passive_blocks(0);
    passive_blocks(1);
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    hud_dirty = 0;
    blk_dirty = 0;
    court_shown = 1;

    clear_text();
    hud_names2();
    if (story)
    {
        sn = stage + 1;
        consoleDrawText(14, 3, "%d/10", sn);
    }
    draw_score();
}

void start_match(void)
{
    u16 f2, l2, e2;
    fade(0);
    story = 0;
    last_power[0] = sel_idx[0];
    power[0] = last_power[0];
    last_power[1] = sel_idx[1];
    power[1] = last_power[1];
    pad_base[0] = PADDLE_H;
    pad_base[1] = PADDLE_H;
    if (char_of[0] >= CH_G0)   // strażnik: jego paletka (Ruden 50 px)
        pad_base[0] = g_height[char_of[0] - CH_G0];
    if (char_of[1] >= CH_G0)
        pad_base[1] = g_height[char_of[1] - CH_G0];
    cpu_speed = CPU_SPEED;
    if (!two_players && char_of[1] >= CH_G0)   // strażnik jako przeciwnik: jego predkosc
        cpu_speed = g_speed[char_of[1] - CH_G0];
    apply_difficulty();
    win_score = pts_val[pts_idx];   // wybrana liczba punktow
    ff_mode = game_mode;            // FAST & FURIOUS: piłka przyspiesza bez konca
    char_cols(char_of[1]);
    f2 = cf;
    l2 = cl;
    e2 = ce;
    if (char_of[0] == char_of[1])   // ta sama postac po obu stronach: kolory dopelniajace
    {
        f2 ^= 0x7FFF;
        l2 ^= 0x7FFF;
        e2 ^= 0x7FFF;
    }
    char_cols(char_of[0]);
    set_paddle_colors(cf, cl, ce, f2, l2, e2);
    setup_match();
    storm_check();
    arena_setup();
    music_off();
    luc_mus_luc = luc_test;   // przemiana przelacza muzyke tylko w module Lucifero
    if (luc_test)
        spc_music_load(MOD_LUCIFERO);   // STAGE 11: LUCIFERO - jego muzyka (mgla, w petli)
    else if (qm_track)
        spc_music_load(story_mod[qm_track - 1]);
    else
        spc_music_load(MOD_TANGO);
    spc_music_play();
    fade(1);
    play_sound(SND_TADA);
}

void story_match(void)
{
    fade(0);
    power[0] = run_pw[run_cur];
    power[1] = g_power[stage];
    ff_mode = 0;
    char_of[0] = CH_MUGGY;
    char_of[1] = CH_G0 + stage;
    pad_base[0] = PADDLE_H;
    pad_base[1] = g_height[stage];
    cpu_speed = g_speed[stage];
    apply_difficulty();
    win_score = g_points[stage];
    load_guardian_gfx();
    set_paddle_colors(COL_MUG, COL_MUG_LIT, COL_MUG_EDGE, g_fill[stage], g_lit[stage], g_edge[stage]);
    setup_match();
    storm_check();
    arena_setup();
    luc_mus_luc = 0;
    if (stage == G_LUCIFERO)   // punkty stracone z Kimantero licza sie dalej; muzyka z przemiana
    {
        luc_mus_luc = 1;
        score2 = luc_carry;
        draw_score();
    }
    music_off();
    spc_music_load(story_mod[stage]);   // utwor walki z tym strażnikiem
    spc_music_play();
    fade(1);
    play_sound(SND_TADA);
}

//---------------------------------------------------------------------------------
// TRYB FABULARNY: zapis, dialogi, wybor mocy, wyniki, zakonczenie
//---------------------------------------------------------------------------------
void save_write(void)
{
    u8 i, chk = 0;
    save_buf[0] = 'S';
    save_buf[1] = 'F';
    save_buf[2] = 'P';
    save_buf[3] = 'G';
    save_buf[4] = 1;   // wersja formatu
    save_buf[5] = unlock_mask & 0xFF;
    save_buf[6] = unlock_mask >> 8;
    save_buf[7] = story_power;
    for (i = 0; i < 8; i++)
        chk += save_buf[i];
    save_buf[8] = chk ^ 0x5A;
    save_buf[9] = 0xA0 | (music_on & 1);   // ustawienie MUSIC ON/OFF
    save_buf[16] = 'H';   // tabela najlepszych wynikow: 10 x (9 znakow imienia + wynik)
    save_buf[17] = 'S';
    chk = 0;
    for (i = 0; i < HS_N; i++)
    {
        memcpy(save_buf + 18 + i * 11, hs_name[i], NAME_MAX);
        save_buf[18 + i * 11 + 9] = hs_score[i] & 0xFF;
        save_buf[18 + i * 11 + 10] = (u16)hs_score[i] >> 8;
    }
    for (i = 16; i < 128; i++)
        chk += save_buf[i];
    save_buf[128] = chk ^ 0x3C;
    consoleCopySram(save_buf, 136);
}

void save_read(void)
{
    u8 i, chk = 0;
    consoleLoadSram(save_buf, 136);
    for (i = 0; i < 8; i++)
        chk += save_buf[i];
    unlock_mask = 0;
    story_power = PWR_SUPER;
    if (save_buf[0] == 'S' && save_buf[1] == 'F' && save_buf[2] == 'P' && save_buf[3] == 'G' &&
        save_buf[4] == 1 && save_buf[8] == (chk ^ 0x5A))
    {
        unlock_mask = save_buf[5] | (save_buf[6] << 8);
        if (save_buf[7] < PWR_ALL)
            story_power = save_buf[7];
    }
    music_on = 1;   // domyslnie muzyka wlaczona
    if ((save_buf[9] & 0xFE) == 0xA0)
        music_on = save_buf[9] & 1;
    chk = 0;   // tabela najlepszych wynikow (starsze zapisy jej nie maja: pusta tabela)
    for (i = 16; i < 128; i++)
        chk += save_buf[i];
    for (i = 0; i < HS_N; i++)
    {
        hs_name[i][0] = 0;
        hs_score[i] = HS_EMPTY;
    }
    if (save_buf[16] == 'H' && save_buf[17] == 'S' && save_buf[128] == (chk ^ 0x3C))
        for (i = 0; i < HS_N; i++)
        {
            memcpy(hs_name[i], save_buf + 18 + i * 11, NAME_MAX);
            hs_name[i][NAME_MAX] = 0;
            hs_score[i] = save_buf[18 + i * 11 + 9] | (save_buf[18 + i * 11 + 10] << 8);
        }
}

u8 is_locked(u8 pw)
{
    return pw >= 4 && !((unlock_mask | TEST_UNLOCK) & (1 << (pw - 4)));
}

void show_story_select(void);
void show_the_end(void);
void story_match(void);

// Tekst dialogu z imieniem gracza: MUGGY -> wpisane imie, a wiersze lamane od nowa do 28 znakow.
// Gdy imie to MUGGY, tekst zostaje dokladnie taki jak w scenariuszu.
const char *hero_text(const char *s)
{
    u8 i = 0, j = 0, k, w, lw = 0, n;
    if (!strcmp(player_name, "MUGGY"))
        return s;
    n = strlen(player_name);
    while (*s && i < 180)
    {
        if (s[0] == 'M' && s[1] == 'U' && s[2] == 'G' && s[3] == 'G' && s[4] == 'Y')
        {
            for (k = 0; k < n; k++)
                dlg_tmp[i++] = player_name[k];
            s += 5;
        }
        else
        {
            dlg_tmp[i++] = (*s == '\n') ? ' ' : *s;
            s++;
        }
    }
    dlg_tmp[i] = 0;
    i = 0;
    while (dlg_tmp[i])
    {
        while (dlg_tmp[i] == ' ')
            i++;
        if (!dlg_tmp[i])
            break;
        w = 0;
        while (dlg_tmp[i + w] && dlg_tmp[i + w] != ' ')
            w++;
        if (lw && lw + 1 + w > 28)
        {
            dlg_buf[j++] = '\n';
            lw = 0;
        }
        else if (lw)
        {
            dlg_buf[j++] = ' ';
            lw++;
        }
        for (k = 0; k < w; k++)
            dlg_buf[j++] = dlg_tmp[i++];
        lw += w;
    }
    dlg_buf[j] = 0;
    return dlg_buf;
}

void dlg_box_start(void)
{
    u8 r;
    speaker = box_spk[box_i];
    tptr = hero_text(box_txt[box_i]);
    tcol = 0;
    trow = 0;
    typing = 1;
    tick_n = 0;
    consoleDrawText(2, 19, (char *)blank28);
    for (r = 0; r < 4; r++)
        consoleDrawText(2, 21 + r, (char *)blank28);
    if (speaker == SPK_MUGGY)
        consoleDrawText(2, 19, player_name);
    else if (speaker == SPK_GUARD2)
        consoleDrawText(2, 19, "DOPPLER R");
    else if (speaker == SPK_GUARD)
    {
        if (stage == 3)
            consoleDrawText(2, 19, "DOPPLER L");
        else if (!luc_phase)   // scena przemiany: do okienka 6 mowi jeszcze Kimantero
            consoleDrawText(2, 19, (char *)g_name[9]);
        else
            consoleDrawText(2, 19, (char *)g_name[stage]);
    }
    av_dim[0] = speaker != SPK_MUGGY;
    av_dim[1] = speaker != SPK_GUARD;
    av_dim[2] = speaker != SPK_GUARD2;
    prep_avatar_pals();
    avpal_dirty = 2;   // 2 = poczekaj klatke (teraz leci kopia tekstu), potem wyslij
}

u16 luc_morph_buf[16];
void luc_scene_frame(void)   // reszta klatki sceny przemiany (jak w fade)
{
    vblank_tasks();
    sound_tick();
    snd_process();
    music_update();
}
void luc_morph_prep(u8 n, u8 old)   // kolory awatara: Kimantero -> Lucifero (n = 0..64); old = migniecie starych
{
    u16 *a = (u16 *)&kimantero48_pal;
    u16 c1, c2, r, g, b, m = 64 - n;
    u8 i;
    for (i = 0; i < 16; i++)
    {
        c1 = a[i];
        c2 = old ? c1 : luc_av_pal[i];
        r = ((c1 & 31) * m + (c2 & 31) * n) >> 6;
        g = (((c1 >> 5) & 31) * m + ((c2 >> 5) & 31) * n) >> 6;
        b = (((c1 >> 10) & 31) * m + ((c2 >> 10) & 31) * n) >> 6;
        luc_morph_buf[i] = r | (g << 5) | (b << 10);
    }
}
void luc_transform(void)   // przemiana: grzmot, blysk, kolory awatara plyna w piekielne, imie litera po literze
{
    char nm[10];
    const char *to = "LUCIFERO ";
    u8 f, i, n;
    for (i = 0; i < 9; i++)
        nm[i] = g_name[9][i];
    nm[9] = 0;
    for (i = 0; i < 4; i++)
        consoleDrawText(2, 21 + i, (char *)blank28);   // puste okno na czas przemiany
    avpal_dirty = 0;
    play_sound(SND_THUNDER);
    for (f = 0; f < 96; f++)
    {
        n = 0;
        if (f >= 8)
            n = f - 8;
        if (n > 64)
            n = 64;
        luc_morph_prep(n, ((f & 7) == 5) && f < 56);   // liczone PRZED VBlank
        WaitForVBlank();
        dmaCopyCGram((u8 *)luc_morph_buf, (PAL_AV1 + 1) * 16, 32);   // wpisane zaraz po poczatku VBlank
        if (f < 8)
            setBrightness((f & 2) ? 15 : 4);   // blyskawica
        else if (f == 8)
            setBrightness(15);
        luc_scene_frame();
        if (f >= 16 && !(f & 7))   // co 8 klatek kolejna litera imienia
        {
            i = (f - 16) >> 3;
            if (i < 9)
            {
                nm[i] = to[i];
                consoleDrawText(2, 19, nm);
            }
        }
    }
    luc_phase = 1;
    set_avatar_pal(1, (u8 *)luc_av_pal);   // dalej zwykle przyciemnianie awatarow
}
void luc_darkness(void)   // po przedstawieniu sie: blyskawica, ciemnosc, w ciemnosci upiorna twarz, potem okienko 8
{
    u8 f, j;
    play_sound(SND_THUNDER);
    luc_face_prep();
    for (f = 0; f < 14; f++)   // blyskawica i wygaszanie
    {
        WaitForVBlank();
        if (f < 6)
            setBrightness((f & 1) ? 15 : 5);
        else
            setBrightness(14 - f);
        luc_scene_frame();
    }
    for (f = 0; f < 6; f++)   // ekran czarny: paleta i kafelki twarzy (po 2 wiersze na klatke, zaraz po VBlank)
    {
        WaitForVBlank();
        setBrightness(0);
        if (f == 0)
            dmaCopyCGram((u8 *)&luc_face_pal, 240, 32);
        j = f << 1;
        dmaCopyVram((u8 *)&luc_face_til + j * 384, VRAM_SPR + (64 + 16 * j) * 16, 384);
        j++;
        dmaCopyVram((u8 *)&luc_face_til + j * 384, VRAM_SPR + (64 + 16 * j) * 16, 384);
        luc_scene_frame();
    }
    luc_face_size(1);
    for (f = 0; f < 51; f++)   // twarz: miga i drga jak w walce; tlo wylaczone, widac tylko sprite'y
    {
        if (face_vis[f])
        {
            j = ((rand() & 3) == 0) ? (rand() % 3) : 1;
            memcpy(oamMemory + FACE_SPR, face_oam[j], 144);
        }
        else
            memcpy(oamMemory + FACE_SPR, face_hid, 144);
        WaitForVBlank();
        if (f == 0)
        {
            *(vuint8 *)0x212C = 0x10;   // tylko sprite'y
            *(vuint8 *)0x2131 = 0x00;   // bez mieszania kolorow
            setBrightness(15);
        }
        luc_scene_frame();
    }
    memcpy(oamMemory + FACE_SPR, face_hid, 144);
    WaitForVBlank();
    setBrightness(0);
    luc_scene_frame();
    luc_face_size(0);
    WaitForVBlank();
    *(vuint8 *)0x212C = videoMode;   // warstwy jak przed twarza
    cm_dirty = 1;                    // mieszanie kolorow jak przed twarza (vblank_tasks)
    luc_scene_frame();
    for (f = 0; f < 30; f++)
    {
        WaitForVBlank();
        luc_scene_frame();
        if (f == 10)
            dlg_box_start();   // okienko 8 (narrator) zaczyna sie w ciemnosci
    }
    for (f = 1; f < 16; f++)
    {
        WaitForVBlank();
        setBrightness(f);
        luc_scene_frame();
    }
}

void play_scene(u8 scn, u8 after)
{
    u16 *dm = (u16 *)&dlg_map;   // 0 siatka, 1 wypelnienie, 2-5 krawedzie, 6-9 rogi, 10 siec
    u16 bg, e;
    u8 x, y;
    scene_now = scn;

    fade(0);
    state = ST_DIALOG;
    music_want = 0;
    spc_music_stop();
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    bg = dm[scn == SCN_ENDING ? 10 : 0];
    for (y = 0; y < 28; y++)
        for (x = 0; x < 32; x++)
            bgmap[y * 32 + x] = bg;
    for (y = 18; y <= 26; y++)   // ramka okna: wiersze 18..26, kolumny 1..30
    {
        for (x = 1; x <= 30; x++)
        {
            e = dm[1];
            if (y == 18)
                e = dm[2];
            else if (y == 26)
                e = dm[3];
            if (x == 1)
                e = (y == 18) ? dm[6] : ((y == 26) ? dm[8] : dm[4]);
            else if (x == 30)
                e = (y == 18) ? dm[7] : ((y == 26) ? dm[9] : dm[5]);
            bgmap[y * 32 + x] = e;
        }
    }
    set_avatar_pal(0, &muggy48_pal);
    if (scn == SCN_INTRO || scn == SCN_ENDING)
        map_put((u16 *)&muggy48_map, 6, 6, 13, 5);
    else
    {
        load_guardian_gfx();
        map_put((u16 *)&muggy48_map, 6, 6, 3, 5);
        if (stage == 3)   // Cyber-doppler: dwaj bliźniacy, drugi z paleta nr 4
        {
            map_put(g48_map, 6, 6, 16, 5);
            map_put(g48_map, 6, 6, 23, 5);
            for (y = 5; y < 11; y++)
                for (x = 23; x < 29; x++)
                    bgmap[y * 32 + x] = (bgmap[y * 32 + x] & 0xE3FF) | (PAL_LOGO << 10);
        }
        else
            map_put(g48_map, 6, 6, 23, 5);
        luc_phase = 1;
        if (scn == SCN_G11)   // przed przemiana: Kimantero w swoich kolorach
        {
            luc_phase = 0;
            set_avatar_pal(1, &kimantero48_pal);
        }
    }
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    dmaCopyCGram(&dlg_pal, PAL_DLG * 16, 32);
    clear_text();
    box_i = scn_first[scn];
    box_end = box_i + scn_count[scn];
    after_scene = after;
    dlg_box_start();
    flush_avatar_pals();
    fade(1);
}

void scene_done(void)
{
    if (after_scene == AFT_SELECT)
        show_story_select();
    else if (after_scene == AFT_MATCH)
        story_match();
    else if (after_scene == AFT_G1)   // po wstepie: rozmowa z pierwszym strażnikiem
        play_scene(SCN_G1, AFT_MATCH);
    else
        show_the_end();
}

void dlg_put_char(u8 snd)
{
    char c = *tptr++;
    u16 i, v;
    if (c == '\n')
    {
        trow++;
        tcol = 0;
        return;
    }
    if (snd)
    {
        // Jeden znak wpisujemy sami: do bufora tekstu (bez znacznika "do kopiowania") i do VRAM
        // w VBlank. Wysylanie calej mapy tekstu (2 KB) co klatke powodowalo miganie tla.
        i = (21 + trow) * 32 + 2 + tcol;
        v = txt_base + (u8)c - 32;
        scr_txt_font_map[i * 2] = v & 0xFF;
        scr_txt_font_map[i * 2 + 1] = v >> 8;
        chq_addr = VRAM_TXT_MAP + i;
        chq_val = v;
        chq_pending = 1;
    }
    else
    {
        chbuf[0] = c;
        chbuf[1] = 0;
        consoleDrawText(2 + tcol, 21 + trow, c == '%' ? "%%" : chbuf);
    }
    tcol++;
    if (snd && c != ' ' && !(++tick_n & 3))
        play_sound(SND_TICK);
}

void dlg_update(void)
{
    u8 k;
    // START pomija cala scene - ale nie zakonczenie gry, zeby nie dalo sie go przeskoczyc
    // przypadkiem (po ostatniej walce ekran wyniku tez prosi o START)
    if ((pad0_new & KEY_START) && scene_now != SCN_ENDING)
    {
        scene_done();
        return;
    }
    if (typing)
    {
        if (pad0_new & KEY_A)   // A pokazuje od razu caly tekst
        {
            while (*tptr)
                dlg_put_char(0);
        }
        else
            dlg_put_char(1);
        if (!*tptr)
            typing = 0;
    }
    else if (pad0_new & KEY_A)
    {
        box_i++;
        if (box_i >= box_end)
            scene_done();
        else
        {
            k = 0xFF;
            if (scene_now == SCN_G11)
                k = box_i - scn_first[SCN_G11];
            if (k == 6)
                luc_transform();   // przed przedstawieniem sie Lucifero
            if (k == 7)
                luc_darkness();    // sama zaczyna okienko 8
            else
                dlg_box_start();
        }
    }
}

// L/R: przelaczanie miedzy mocami zebranymi w tym podejsciu
// L/R: zmiana mocy. W trybie fabularnym - moce zebrane w tym podejsciu; w trybach
// 1/2 PLAYER - tylko Muggy (po przejsciu gry) i wszystkie 14 mocy.
void switch_power(u8 p, u16 pn)
{
    u16 *mm = (u16 *)&minicons_map;
    u8 t, k;
    // Uwaga: 816-tcc zle kompilowal warunki zapisane jako jedno "a || b || c", stad osobne if-y.
    if ((pn & (KEY_L | KEY_R)) == 0)
        return;
    if (story)
    {
        if (p)
            return;
        if (run_n < 2)
            return;
        if (pn & KEY_R)
            run_cur = (run_cur + 1) % run_n;
        else
            run_cur = run_cur ? run_cur - 1 : run_n - 1;
        power[0] = run_pw[run_cur];
    }
    else
    {
        if (char_of[p] != CH_MUGGY)
            return;
        t = power[p];
        for (k = 0; k < PWR_ALL; k++)   // tylko moce odblokowane w trybie fabularnym
        {
            if (pn & KEY_R)
                t = (t + 1) % PWR_ALL;
            else
                t = t ? t - 1 : PWR_ALL - 1;
            if (!is_locked(t))
                break;
        }
        if (t == power[p])
            return;
        power[p] = t;
    }
    armed[p] = 0;   // zmiana mocy kasuje uzbrojenie, ladunek paska zostaje
    if (p)
        bgmap[96 + 23] = mm[icon_of(power[1])];
    else
        bgmap[96 + 8] = mm[icon_of(power[0])];
    hud_dirty = 1;
    play_sound(SND_TICK);
}

void show_name_entry(void);
void show_hiscores(void);
void story_start(void)
{
    srand(snes_vblank_count);
    story = 1;
    stage = 0;
    two_players = 0;
    run_score = 0;
    show_name_entry();     // najpierw imie, potem wybor mocy i wstep
}

void draw_story_desc(void)
{
    u8 i = sel_idx[0];
    consoleDrawText(2, 19, (char *)blank28);
    consoleDrawText(2, 21, (char *)blank28);
    if (is_locked(i) && i >= PWR_DRAWN)
    {
        consoleDrawText(2, 19, "???");
        consoleDrawText(2, 21, "LOCKED");
    }
    else
    {
        consoleDrawText(2, 19, (char *)pwr_name[i]);
        if (is_locked(i))
            consoleDrawText(2, 21, (char *)lock_desc[i - 4]);
        else
            consoleDrawText(2, 21, (char *)pwr_desc[i]);
    }
    desc_dirty = 0;
}

void show_story_select(void)
{
    u8 i, ic;
    u16 *im = (u16 *)&icons_map;

    fade(0);
    state = ST_SSELECT;
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    map_put((u16 *)&muggy32_map, 4, 4, 1, 1);
    for (i = 0; i < PWR_ALL; i++)   // siatka 7 x 2: moce podstawowe i moce strażnikow
    {
        ic = is_locked(i) ? ICON_LOCK : icon_of(i);
        map_put_stride(im + 2 * ic, 2, 2, ICON_STRIDE, 2 + 4 * (i % 7), 11 + 4 * (i / 7));
    }
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    set_avatar_pal(0, &muggy48_pal);
    av_dim[0] = 0;
    flush_avatar_pals();
    clear_text();
    consoleDrawText(6, 1, player_name);
    consoleDrawText(7, 7, "CHOOSE YOUR POWER");
    sel_idx[0] = story_power;
    if (is_locked(sel_idx[0]))
        sel_idx[0] = PWR_SUPER;
    sel_done[0] = 0;
    ready_timer = 0;
    draw_story_desc();
    fade(1);
}

void update_story_select(void)
{
    u8 i = sel_idx[0], c = i % 7, r = i / 7, vis;
    s16 cx, cy;
    if (ready_timer)
    {
        if (--ready_timer == 0)
        {
            story_power = sel_idx[0];
            save_write();
            stage = 0;
            run_pw[0] = story_power;   // nowe podejscie: na razie tylko wybrana moc
            run_n = 1;
            run_cur = 0;
            play_scene(SCN_INTRO, AFT_G1);
            return;
        }
    }
    else
    {
        if (pad0_new & KEY_LEFT)
            c = c ? c - 1 : 6;
        if (pad0_new & KEY_RIGHT)
            c = c < 6 ? c + 1 : 0;
        if (pad0_new & (KEY_UP | KEY_DOWN))
            r ^= 1;
        if (r * 7 + c != i)
        {
            sel_idx[0] = r * 7 + c;
            play_sound(SND_TICK);
            draw_story_desc();
        }
        if (pad0_new & (KEY_A | KEY_START))
        {
            if (is_locked(sel_idx[0]))
                play_sound(SND_WALL);
            else
            {
                sel_done[0] = 1;
                ready_timer = 60;
                play_sound(SND_CONFIRM);
                consoleDrawText(13, 24, "READY?");
            }
        }
    }
    // wspolrzedne liczymy osobno: 816-tcc zle liczy takie wyrazenia w argumentach funkcji
    i = sel_idx[0];
    cx = i % 7;
    cy = i / 7;
    cx = (2 + 4 * cx) * 8;
    cy = (11 + 4 * cy) * 8;
    vis = !sel_done[0] || (frame & 4);
    draw_cursor_at(SPR_CUR1, cx, cy, 4, 0, vis);
}

void story_result(u8 win)
{
    u8 len, x;
    s16 lost;
    lost = (s16)score2;
    if (stage == G_LUCIFERO)   // punkty przeniesione z walki z Kimantero zostaly juz raz odjete
        lost -= (s16)luc_carry;
    run_score += (s16)score1 * (1 + difficulty) - lost;   // wynik: zdobyte x mnoznik poziomu - stracone
    music_stop_safe();   // koniec walki: cisza przed fanfara (przez kolejke dzwieku)
    state = ST_RESULT;
    result_win = win;
    clear_xballs();
    fake_active[0] = 0;
    fake_active[1] = 0;
    if (win)
    {
        len = strlen(g_name[stage]) + 10;
        x = (32 - len) / 2;
        consoleDrawText(x, 10, (char *)g_name[stage]);
        consoleDrawText(x + len - 10, 10, " DEFEATED!");
        for (x = 0; x < run_n && run_pw[x] != g_power[stage]; x++)
            ;
        if (x == run_n)   // Muggy przejmuje moc pokonanego strażnika (do konca podejscia)
            run_pw[run_n++] = g_power[stage];
        x = (32 - len) / 2;
        if (!(unlock_mask & (1 << stage)))   // pierwsze zwyciestwo: moc odblokowana i zapisana
        {
            unlock_mask |= 1 << stage;
            save_write();
            consoleDrawText(6, 13, "NEW POWER UNLOCKED:");
            len = strlen(pwr_name[g_power[stage]]);
            consoleDrawText((32 - len) / 2, 15, (char *)pwr_name[g_power[stage]]);
        }
        consoleDrawText(10, 20, "PRESS START");
        play_sound(SND_FANFARE);
    }
    else
    {
        len = strlen(player_name) + 8;
        consoleDrawText((32 - len) / 2, 10, player_name);
        consoleDrawText((32 - len) / 2 + len - 8, 10, " LOST...");
        consoleDrawText(8, 13, "TRY AGAIN? START");
        consoleDrawText(9, 15, "SELECT: TITLE");
        play_sound(SND_SAD);
    }
}

void update_result(void)
{
    if (result_win)
    {
        if (pad0_new & KEY_START)
        {
            if (stage == 9)   // wygrana z Kimantero: jego punkty przechodza na walke z Lucifero
                luc_carry = score2;
            stage++;
            if (stage >= STORY_STAGES)   // etap 2: po trzecim strażniku od razu zakonczenie
                play_scene(SCN_ENDING, AFT_THEEND);
            else
                play_scene(SCN_G1 + stage, AFT_MATCH);
        }
    }
    else if (pad0_new & KEY_START)
        play_scene(SCN_TAUNT1 + stage, AFT_MATCH);
    else if (pad0_new & KEY_SELECT)
        show_hiscores();   // rezygnacja konczy podejscie: tabela najlepszych wynikow
}

void show_the_end(void)
{
    fade(0);
    state = ST_THEEND;
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    clear_text();
    consoleDrawText(12, 13, "THE END");
    result_timer = 180;
    fade(1);
}

void update_the_end(void)
{
    if (result_timer)
    {
        if (--result_timer == 0)
        {
            play_sound(SND_TOK1);
            consoleDrawText(5, 17, "THANK YOU FOR PLAYING!");
            consoleDrawText(9, 19, "SANDBOX ESCAPE");
            consoleDrawText(8, 20, "A PADDLE ODYSSEY");
            consoleDrawText(10, 22, "BY SYLWESTER");
        }
    }
    else if (pad0_new & KEY_START)
        show_hiscores();   // koniec gry: tabela najlepszych wynikow
}

// ---------------------------------------------------------------------------
// Wpisywanie imienia (tryb fabularny): gora/dol litera, lewo/prawo kursor, A dalej, B kasuje, START
void draw_name(void)
{
    u8 i;
    char b[2];
    b[1] = 0;
    for (i = 0; i < NAME_MAX; i++)
    {
        b[0] = name_ed[i];
        consoleDrawText(11 + i, 11, b);
        b[0] = (i == name_pos) ? '^' : '-';
        consoleDrawText(11 + i, 12, b);
    }
}

void show_name_entry(void)
{
    u8 i;
    fade(0);
    state = ST_NAME;
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    clear_text();
    consoleDrawText(8, 6, "ENTER YOUR NAME");
    consoleDrawText(6, 16, "UP/DOWN:    LETTER");
    consoleDrawText(6, 18, "LEFT/RIGHT: MOVE");
    consoleDrawText(6, 20, "B:          DELETE");
    consoleDrawText(6, 22, "START:      OK");
    for (i = 0; i < NAME_MAX; i++)
        name_ed[i] = ' ';
    name_ed[NAME_MAX] = 0;
    memcpy(name_ed, "MUGGY", 5);   // domyslnie MUGGY
    name_pos = 5;
    name_rep = 0;
    draw_name();
    fade(1);
}

u8 name_char_idx(char c)
{
    u8 i;
    for (i = 0; name_chars[i]; i++)
        if (name_chars[i] == c)
            return i;
    return 0;
}

void update_name_entry(void)
{
    u16 k = pad0_new, d = pad0 & (KEY_UP | KEY_DOWN | KEY_LEFT | KEY_RIGHT);
    u8 n = sizeof(name_chars) - 1, c;
    s8 i;
    if (d && !(k & d))   // przytrzymanie: po chwili powtarzanie co 4 klatki
    {
        if (++name_rep > 18 && !(name_rep & 3))
            k |= d;
    }
    else
        name_rep = 0;
    c = name_char_idx(name_ed[name_pos]);
    if (k & KEY_UP)
        name_ed[name_pos] = name_chars[(c + 1) % n];
    else if (k & KEY_DOWN)
        name_ed[name_pos] = name_chars[(c + n - 1) % n];
    else if ((k & KEY_LEFT) && name_pos > 0)
        name_pos--;
    else if ((k & (KEY_RIGHT | KEY_A)) && name_pos < NAME_MAX - 1)
        name_pos++;
    else if (k & KEY_B)   // kasowanie: znak przed kursorem (albo pod nim)
    {
        if (name_pos > 0 && name_ed[name_pos] == ' ')
            name_pos--;
        name_ed[name_pos] = ' ';
    }
    else if (k & KEY_START)
    {
        for (i = NAME_MAX - 1; i >= 0 && name_ed[i] == ' '; i--)
            name_ed[i] = 0;   // bez spacji na koncu
        if (!name_ed[0])
            strcpy(name_ed, "MUGGY");
        strcpy(player_name, name_ed);
        play_sound(SND_TOK1);
        show_difficulty(0);   // po imieniu: poziom trudnosci, potem wybor mocy
        return;
    }
    if (k)
    {
        if (k & (KEY_UP | KEY_DOWN | KEY_B))
            play_sound(SND_TICK);
        draw_name();
    }
}

// ---------------------------------------------------------------------------
// Najlepsze wyniki: 10 miejsc, wynik = punkty zdobyte - punkty stracone w calym podejsciu
u8 hs_insert(void)
{
    u8 i, k;
    for (i = 0; i < HS_N; i++)
        if (hs_score[i] == HS_EMPTY || run_score > hs_score[i])
            break;
    if (i >= HS_N)
        return 0xFF;
    for (k = HS_N - 1; k > i; k--)
    {
        hs_score[k] = hs_score[k - 1];
        memcpy(hs_name[k], hs_name[k - 1], NAME_MAX + 1);
    }
    hs_score[i] = run_score;
    strcpy(hs_name[i], player_name);
    return i;
}

// liczba ze znakiem jako tekst; wynik: wskaznik do pierwszego znaku w b (8 bajtow)
char *num_str(s16 v, char *b)
{
    u16 a = v < 0 ? -v : v;
    u8 d = 7;
    b[7] = 0;
    do
    {
        b[--d] = '0' + a % 10;
        a /= 10;
    } while (a);
    if (v < 0)
        b[--d] = '-';
    return b + d;
}

void draw_hs_row(u8 i, u8 show)
{
    char b[8];
    char *t;
    u8 r = 6 + i * 2;
    consoleDrawText(4, r, "                         ");
    b[0] = (i == 9) ? '1' : ' ';
    b[1] = (i == 9) ? '0' : '1' + i;
    b[2] = '.';
    b[3] = 0;
    consoleDrawText(4, r, b);
    if (!show)
        return;
    if (hs_score[i] == HS_EMPTY)
    {
        consoleDrawText(8, r, "---");
        return;
    }
    consoleDrawText(8, r, hs_name[i]);
    t = num_str(hs_score[i], b);   // wynik wyrownany do prawej
    consoleDrawText(28 - strlen(t), r, t);
}

void show_hiscores(void)
{
    u8 i;
    char b[8];
    fade(0);
    state = ST_HISCORE;
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    clear_text();
    hs_new = hs_insert();
    save_write();
    consoleDrawText(10, 2, "HIGH SCORES");
    consoleDrawText(4, 4, "YOUR SCORE:");
    consoleDrawText(16, 4, num_str(run_score, b));
    for (i = 0; i < HS_N; i++)
        draw_hs_row(i, 1);
    hs_blink = 0;
    fade(1);
}

void update_hiscore(void)
{
    if (hs_new != 0xFF && !(++hs_blink & 15))   // nowy wynik miga
        draw_hs_row(hs_new, hs_blink & 16);
    if (pad0_new & (KEY_START | KEY_A))
        show_title(0);
}

// ---------------------------------------------------------------------------
// Wybor poziomu trudnosci: tryb fabularny (po imieniu) i gra z komputerem w QUICK MATCH / F&F
void draw_diff(void)
{
    u8 i;
    for (i = 0; i < 3; i++)
        consoleDrawText(9, 10 + i * 2, i == diff_idx ? ">" : " ");
}

void show_difficulty(u8 next)
{
    fade(0);
    state = ST_DIFF;
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    clear_text();
    consoleDrawText(7, 6, "CHOOSE DIFFICULTY");
    consoleDrawText(11, 10, "EASY");
    consoleDrawText(11, 12, "NORMAL");
    consoleDrawText(11, 14, "HARD");
    diff_next = next;
    diff_idx = difficulty;
    draw_diff();
    fade(1);
}

void update_difficulty(void)
{
    if ((pad0_new & KEY_UP) && diff_idx > 0)
    {
        diff_idx--;
        play_sound(SND_TICK);
        draw_diff();
    }
    else if ((pad0_new & KEY_DOWN) && diff_idx < 2)
    {
        diff_idx++;
        play_sound(SND_TICK);
        draw_diff();
    }
    else if (pad0_new & (KEY_A | KEY_START))
    {
        difficulty = diff_idx;
        play_sound(SND_TOK1);
        if (diff_next == 0)
            show_story_select();
        else if (luc_test)   // STAGE 11: LUCIFERO - Muggy kontra Lucifero, do 10 punktow
        {
            char_of[0] = CH_MUGGY;
            char_of[1] = CH_G0 + G_LUCIFERO;
            sel_idx[0] = 0;
            sel_idx[1] = PWR_HELL;
            pts_idx = 3;
            start_match();
        }
        else
            show_points(0);
    }
}

u8 char_locked(u8 c)
{
    if (c == CH_MUGGY)   // Muggy: dostepny od poczatku
        return 0;
    if (c < CH_G0)
        return 0;
    return !((unlock_mask | TEST_UNLOCK) & (1 << (c - CH_G0)));
}

// Czy strona p moze wybrac pozycje i listy postaci
u8 char_ok(u8 p, u8 i)
{
    u8 c = list_char[i];
    if (char_locked(c))
        return 0;
    if (game_mode == 1 && c == CH_G0 + 9)   // FAST & FURIOUS: bez Kimantero (nie da sie z nim wygrac)
        return 0;
    if (p == 1 && !two_players)   // przeciwnik komputerowy: kazda odblokowana postac (takze AI Agent)
        return 1;
    if (c == CH_SFC)
        return 0;
    return 1;
}

void draw_char_cursor(u8 p, u8 on)
{
    if (p)
    {
        if (on)
            consoleDrawText(24, 4 + csel[1], "<");
        else
            consoleDrawText(24, 4 + csel[1], " ");
    }
    else
    {
        if (on)
            consoleDrawText(8, 4 + csel[0], ">");
        else
            consoleDrawText(8, 4 + csel[0], " ");
    }
}

void draw_char_hint(void)
{
    consoleDrawText(2, 20, (char *)blank28);
    if (two_players)
        consoleDrawText(6, 20, "CHOOSE YOUR FIGHTERS");
    else if (cphase == 0)
        consoleDrawText(6, 20, "CHOOSE YOUR FIGHTER");
    else
        consoleDrawText(7, 20, "CHOOSE OPPONENT");
}

void show_chars(u8 players2)
{
    u8 i, c;
    srand(snes_vblank_count);
    fade(0);
    two_players = players2;
    story = 0;
    state = ST_CHARS;
    reset_effects();
    hide_sprites();
    set_paddle_colors(COL_P1, COL_P1_LIT, RGB8(225, 100, 125), COL_P2, COL_P2_LIT, RGB8(110, 170, 255));
    csel[0] = 0;   // MUGGY
    csel[1] = 2;   // AI AGENT
    if (two_players)
        csel[1] = 1;   // JOYBOT
    cdone[0] = 0;
    cdone[1] = 0;
    cphase = 0;
    ctimer = 0;
    prev_dirty = 0;
    char_of[0] = list_char[csel[0]];
    char_of[1] = list_char[csel[1]];
    memset(bgmap, 0, sizeof(bgmap));
    for (i = 0; i < NUM_GUARD; i++)   // male awatary odblokowanych strażnikow - od razu do VRAM
    {
        if (!char_locked(CH_G0 + i))
            load_guardian(i, TILES_CHARS + 16 * i - TILES_GRD32, 0);
    }
    preview_prepare(0);   // podglad postaci gracza 1
    preview_prepare(1);   // ...i gracza 2 / przeciwnika
    preview_send(0);      // ekran jest wygaszony, mozna od razu
    preview_send(1);
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    clear_text();
    for (i = 0; i < CHAR_N; i++)
    {
        c = list_char[i];
        if (char_locked(c))
            consoleDrawText(10, 4 + i, "???");
        else
            consoleDrawText(10, 4 + i, char_name(c));
    }
    consoleDrawText(3, 13, "P1");
    if (two_players)
        consoleDrawText(27, 13, "P2");
    else
        consoleDrawText(26, 13, "CPU");
    draw_char_hint();
    draw_char_cursor(0, 1);
    draw_char_cursor(1, 1);
    fade(1);
}

void char_input(u8 p, u16 pn)
{
    u8 i, t;
    if (cdone[p])
    {
        if (pn & KEY_B)
        {
            cdone[p] = 0;
            play_sound(SND_TICK);
        }
        return;
    }
    if (pn & KEY_B)
    {
        if (!two_players && p == 1)   // wroc do wyboru wlasnej postaci
        {
            cphase = 0;
            cdone[0] = 0;
            draw_char_hint();
        }
        return;
    }
    if (pn & (KEY_UP | KEY_DOWN))
    {
        draw_char_cursor(p, 0);
        i = csel[p];
        for (t = 0; t < CHAR_N; t++)   // nastepna pozycja, ktora ta strona moze wybrac
        {
            if (pn & KEY_UP)
                i = i ? i - 1 : CHAR_N - 1;
            else
                i = i < CHAR_N - 1 ? i + 1 : 0;
            if (char_ok(p, i))
                break;
        }
        csel[p] = i;
        char_of[p] = list_char[i];
        preview_prepare(p);
        prev_dirty |= p ? 2 : 1;
        prev_wait = 1;   // w tej klatce leci kopia tekstu; podglad w nastepnej
        draw_char_cursor(p, 1);
        play_sound(SND_TICK);
    }
    if (pn & (KEY_A | KEY_START))
    {
        cdone[p] = 1;
        play_sound(SND_CONFIRM);
        if (!two_players && p == 0)
        {
            cphase = 1;
            draw_char_hint();
        }
    }
}

void update_chars(void)
{
    if (ctimer)
    {
        if (--ctimer == 0)
        {
            // strażnicy po obu stronach: moce z gory, od razu mecz
            if (char_of[0] >= CH_G0 && char_of[1] >= CH_G0)
            {
                sel_idx[0] = g_power[char_of[0] - CH_G0];
                sel_idx[1] = g_power[char_of[1] - CH_G0];
                start_match();
            }
            else
                show_select(two_players);
        }
        return;
    }
    if (two_players)
    {
        char_input(0, pad0_new);
        char_input(1, pad1_new);
    }
    else if (cphase == 0)
        char_input(0, pad0_new);
    else
        char_input(1, pad0_new);
    if (cdone[0] && cdone[1])
        ctimer = 30;
}

void draw_points_cursor(void)
{
    u8 i;
    for (i = 0; i < 6; i++)
        consoleDrawText(13, 9 + 2 * i, i == pts_idx ? ">" : " ");
}

// Muzyka meczu: TANGO albo utwor pokonanego strażnika (LEWO/PRAWO)
void draw_points_music(void)
{
    consoleDrawText(2, 21, "                            ");
    if (!music_on)
    {
        consoleDrawText(11, 21, "MUSIC: OFF");
        return;
    }
    consoleDrawText(4, 21, "MUSIC: <");
    if (qm_track)
        consoleDrawText(13, 21, (char *)g_name[qm_track - 1]);
    else
        consoleDrawText(13, 21, "TANGO");
    consoleDrawText(27, 21, ">");
}

// Osobny ekran: do ilu punktow trwa mecz (QUICK MATCH i FAST & FURIOUS)
void show_points(u8 players2)
{
    u8 i;
    u16 v;   // %d wypisuje liczbe 16-bitowa
    fade(0);
    state = ST_POINTS;
    pts_players = players2;
    reset_effects();
    hide_sprites();
    memset(bgmap, 0, sizeof(bgmap));
    dmaCopyVram((u8 *)bgmap, VRAM_BG1_MAP, sizeof(bgmap));
    clear_text();
    if (game_mode)
        consoleDrawText(9, 3, "FAST & FURIOUS");
    else
        consoleDrawText(10, 3, "QUICK MATCH");
    if (players2)
        consoleDrawText(11, 5, "2 PLAYERS");
    else
        consoleDrawText(11, 5, "1 PLAYER");
    consoleDrawText(9, 7, "POINTS TO WIN");
    for (i = 0; i < 6; i++)
    {
        v = pts_val[i];
        consoleDrawText(15, 9 + 2 * i, "%d", v);
    }
    draw_points_cursor();
    if (qm_track && !(unlock_mask & (1 << (qm_track - 1))))
        qm_track = 0;   // utwor strażnika tylko po jego pokonaniu
    draw_points_music();
    consoleDrawText(7, 23, "A: OK      B: BACK");
    fade(1);
}

void update_points(void)
{
    u16 pn = pad0_new | pad1_new;
    u8 k;
    if (music_on && (pn & (KEY_LEFT | KEY_RIGHT)))   // nastepny dostepny utwor
    {
        for (k = 0; k < 10 + 1; k++)
        {
            if (pn & KEY_RIGHT)
                qm_track = qm_track < 10 ? qm_track + 1 : 0;
            else
                qm_track = qm_track ? qm_track - 1 : 10;
            if (qm_track == 0 || (unlock_mask & (1 << (qm_track - 1))))
                break;
        }
        play_sound(SND_TICK);
        draw_points_music();
    }
    if (pn & KEY_UP)
    {
        pts_idx = pts_idx ? pts_idx - 1 : 5;
        play_sound(SND_TICK);
        draw_points_cursor();
    }
    if (pn & KEY_DOWN)
    {
        pts_idx = pts_idx < 5 ? pts_idx + 1 : 0;
        play_sound(SND_TICK);
        draw_points_cursor();
    }
    if (pn & (KEY_A | KEY_START))
    {
        play_sound(SND_CONFIRM);
        show_chars(pts_players);
    }
    else if (pn & KEY_B)
        show_title(0);
}

void update_title(void)
{
    u16 combo = KEY_L | KEY_R | KEY_SELECT;
    u8 n;
    title_fx();
    if (pad0 | pad1)
        title_idle = 0;
    else if (++title_idle >= 900 && !title_sub && !erase_ask)   // 15 s bez przyciskow: pokaz
    {
        start_demo();
        return;
    }
    if (erase_ask)
    {
        if (pad0_new & KEY_A)
        {
            unlock_mask = 0;
            story_power = PWR_SUPER;
            save_write();
            consoleDrawText(5, 24, "     SAVE ERASED      ");
            erase_ask = 0;
        }
        else if (pad0_new & KEY_B)
        {
            erase_ask = 0;
            draw_menu_labels();
            draw_menu();
        }
        return;
    }
    if (!title_sub && (pad0 & combo) == combo && (pad0_new & combo))
    {
        erase_ask = 1;
        consoleDrawText(5, 24, "ERASE SAVE? A=YES B=NO");
        return;
    }
    n = 3;   // ostatnia pozycja menu
    if (title_sub)
        n = 1;
    if (pad0_new & KEY_UP)
    {
        menu_idx = menu_idx ? menu_idx - 1 : n;
        play_sound(SND_TICK);
        draw_menu_labels();
        draw_menu();
    }
    if (pad0_new & KEY_DOWN)
    {
        menu_idx = menu_idx < n ? menu_idx + 1 : 0;
        play_sound(SND_TICK);
        draw_menu_labels();
        draw_menu();
    }
    if (title_sub && (pad0_new & KEY_B))   // B: powrot do glownego menu
    {
        title_sub = 0;
        menu_idx = game_mode + 1;
        draw_menu_labels();
        draw_menu();
        play_sound(SND_TICK);
        return;
    }
    if (!title_sub && menu_idx == 3 && (pad0_new & (KEY_START | KEY_A | KEY_LEFT | KEY_RIGHT)))
    {
        music_on ^= 1;   // MUSIC ON/OFF - zapisywane na karcie
        save_write();
        play_sound(SND_CONFIRM);
        draw_menu_labels();
        draw_menu();
        return;
    }
    if (pad0_new & (KEY_START | KEY_A))
    {
        if (title_sub)
        {
            if (menu_idx == 0)
                show_difficulty(1);   // 1 PLAYER: najpierw poziom trudnosci
            else
                show_points(1);       // 2 PLAYERS
        }
        else if (menu_idx == 0)
            story_start();
        else if (menu_idx == 4)   // STAGE 11: LUCIFERO (na czas prac): poziom trudnosci, potem od razu walka
        {
            luc_test = 1;
            game_mode = 0;
            two_players = 0;
            show_difficulty(1);
        }
        else
        {
            game_mode = menu_idx - 1;   // 0 = QUICK MATCH, 1 = FAST & FURIOUS
            title_sub = 1;
            menu_idx = 0;
            draw_menu_labels();
            draw_menu();
            play_sound(SND_CONFIRM);
        }
    }
    else if ((pad1_new & KEY_START) && !title_sub)   // START na padzie 2: od razu 2 graczy (QUICK MATCH)
    {
        game_mode = 0;
        show_points(1);
    }
}

//---------------------------------------------------------------------------------
// EKRAN WYBORU MOCY
//---------------------------------------------------------------------------------
void select_input(u8 p, u16 pn)
{
    u8 i = sel_idx[p], c = i % 7, r = i / 7;
    if (char_of[p] >= CH_G0)   // strażnik ma moc z gory
        return;
    if (!sel_done[p])
    {
        if (pn & KEY_LEFT)
            c = c ? c - 1 : 6;
        if (pn & KEY_RIGHT)
            c = c < 6 ? c + 1 : 0;
        if (pn & (KEY_UP | KEY_DOWN))
            r ^= 1;
        if (r * 7 + c != i)
        {
            sel_idx[p] = r * 7 + c;
            play_sound(SND_TICK);
            desc_dirty = 1;
        }
        if (pn & (KEY_A | KEY_START))
        {
            if (is_locked(sel_idx[p]) || (p == 0 && sel_done[0]))
                play_sound(SND_WALL);   // zablokowanej mocy nie da sie wybrac
            else
            {
                sel_done[p] = 1;
                play_sound(SND_CONFIRM);
                if (p == 0 && !two_players)   // teraz wybiera AI Agent
                {
                    cpu_think = 12;
                    cpu_delay = think_delay[0];
                }
            }
        }
    }
    else if (pn & KEY_B)
    {
        sel_done[p] = 0;
        if (p == 0 && !two_players)
        {
            cpu_think = 0;
            sel_done[1] = 0;
        }
    }
}

void update_select(void)
{
    u8 n;

    if (!ready_timer)
    {
        select_input(0, pad0_new);
        if (two_players)
        {
            select_input(1, pad1_new);
        }
        else if (cpu_think && --cpu_delay == 0)
        {
            // "namysl": kursor skacze losowo, coraz wolniej
            n = rand() & 3;   // AI Agent: jedna z 4 podstawowych mocy
            cpu_think--;
            if (cpu_think)
            {
                if (n == sel_idx[1])
                    n = (n + 1) & 3;
                cpu_delay = think_delay[12 - cpu_think];
                play_sound(SND_TICK);
            }
            else
            {
                sel_done[1] = 1;
                play_sound(SND_CONFIRM);
            }
            sel_idx[1] = n;
        }
        if (desc_dirty)
            draw_descs();
        if (sel_done[0] && sel_done[1])
        {
            ready_timer = 60;
            consoleDrawText(13, 14, "READY?");
        }
    }
    else if (--ready_timer == 0)
    {
        start_match();
        return;
    }

    n = !sel_done[0] || (frame & 4);
    draw_grid_cursor(SPR_CUR1, sel_idx[0], 4, 0, n);
    n = (two_players || cpu_think || sel_done[1]) && (!sel_done[1] || (frame & 4));
    draw_grid_cursor(SPR_CUR2, sel_idx[1], 8, 1, n);
}

//---------------------------------------------------------------------------------
// MOCE SPECJALNE
//---------------------------------------------------------------------------------
u8 is_cpu(u8 p)
{
    return p == 1 && !two_players;
}

void arm(u8 p)
{
    armed[p] = 1;
    play_sound(SND_ARM);
}

#define PAD_B_BIT 0x8000u   // KEY_B to BIT(15): w 16-bitowym int jest ujemne i 816-tcc liczyl test zle

void arm_input(u8 p, u16 pn)
{
    u16 held;
    if (p)
        held = pad1;
    else
        held = pad0;
    if ((pn & KEY_Y) && armed[p])   // Y rozbraja moc (u wszystkich postaci); pasek zostaje pelny
    {
        armed[p] = 0;
        return;
    }
    // A wystarczy przytrzymac: wcisniecie nie przepadnie nawet przy przestoju klatki
    if ((held & KEY_A) && !(held & KEY_Y) && !armed[p] && bar[p] >= BAR_MAX)
        arm(p);
}

// Ladowanie paska po zwyklym odbiciu; gra tez dzwiek odbicia
void charge(u8 p, s16 hit)
{
    // Odbicie krawedzia laduje pasek podwojnie. Prog liczony od wysokosci paletki: przy stalym
    // progu 12 px duza paletka (Ruden 50 px, GROW 80 px) prawie zawsze "trafiala krawedzia".
    s16 edge = (pad_h[p] >> 1) - EDGE_ZONE;
    u8 add = (hit >= edge || hit <= -edge) ? 2 : 1;
    u8 snd = p ? SND_TOK2 : SND_TOK1;

    if (arena == ARENA_LUC && power[p] == PWR_FORTRESS)   // mur rysuje na warstwie boiska (brak w Mode 7)
        return;
    if (bar[p] < BAR_MAX)
    {
        bar[p] += add;
        if (bar[p] >= BAR_MAX)
        {
            bar[p] = BAR_MAX;
            snd = SND_READY;
            if (is_cpu(p))
            {
                cpu_arm_wait = rand() % 3;   // uzbroi po 0-2 kolejnych odbiciach
                if (is_g(p, 7) || is_g(p, 8))
                    cpu_arm_wait = 0;        // Telementor i Blinker: od razu
                if (difficulty && !two_players)
                    cpu_arm_wait = 0;        // NORMAL/HARD: moc od razu po zapelnieniu paska
            }
        }
        update_bar_map(p);
    }
    else if (is_cpu(p) && !armed[p] && cpu_arm_wait)
    {
        cpu_arm_wait--;
    }
    play_sound(snd);
    if (is_cpu(p) && bar[p] >= BAR_MAX && !armed[p] && cpu_arm_wait == 0)
        arm(p);
}

void end_special(void)
{
    sp_type = SP_NONE;
    ghost_hidden = 0;
    ghost_blink = 0;
    cpu_ghost_mode = 0;
    ghost_lag = 0;
}

// Zygzak: losowa dlugosc odcinka i losowa predkosc pionowa (z losowym kierunkiem)
u8 zig_length(void)
{
    return ZIG_MIN + rand() % (ZIG_MAX - ZIG_MIN + 1);
}

s16 zig_speed(void)
{
    s16 m = ZIG_VMIN + rand() % (ZIG_VMAX - ZIG_VMIN + 1);
    return (rand() & 1) ? m : -m;
}

// CHAOS: wybor mocy najkorzystniejszej w danej chwili; co czwarty raz zupelnie losowo
u8 chaos_choose(u8 p)
{
    s16 oc, by, me, him;
    u8 r;
    if ((rand() & 3) == 0)
        return chaos_set[rand() % 8];
    if (p)
    {
        oc = p1_y + pad_h[0] / 2;
        me = score2;
        him = score1;
    }
    else
    {
        oc = p2_y + pad_h[1] / 2;
        me = score1;
        him = score2;
    }
    by = (s16)(ball_y >> 8) + BALL_SIZE / 2;
    if (me < him)   // przegrywa: obrona
    {
        if (rand() & 1)
            return PWR_FORTRESS;
        return PWR_TWIN;
    }
    if (oc - by > 48 || by - oc > 48)   // przeciwnik daleko od pilki: utrudnic mu ruch
    {
        if (rand() & 1)
            return PWR_SWAP;
        return PWR_SLOW;
    }
    if (vel_x > 0x0300 || vel_x < -0x0300)   // szybka pilka: niech nie widzi paletki
        return PWR_CAMO;
    r = rand() % 3;
    if (r == 0)
        return PWR_CATCH;
    if (r == 1)
        return PWR_SPLIT;
    return PWR_GROW;
}

// Nowa pilka z pilki zrodlowej (0xFF = glowna): to samo miejsce, o 30% wolniejsza,
// rozjezdzaja sie lekko w pionie
void spawn_xball(u8 src)
{
    u8 j, f = 0xFF;
    for (j = 0; j < XB; j++)
    {
        if (!xb_on[j])
        {
            f = j;
            break;
        }
    }
    if (f == 0xFF)
        return;   // juz 4 pilki
    if (src == 0xFF)
    {
        memcpy(xh_x[f], hist_x, 16);
        memcpy(xh_y[f], hist_y, 16);
        xtail[f] = tail_len;
        xb_x[f] = ball_x;
        xb_y[f] = ball_y;
        xb_vx[f] = vel_x * SPLIT_SLOW / 10;
        xb_vy[f] = vel_y + SPLIT_VY;
        vel_y -= SPLIT_VY;
    }
    else
    {
        memcpy(xh_x[f], xh_x[src], 16);
        memcpy(xh_y[f], xh_y[src], 16);
        xtail[f] = xtail[src];
        xb_x[f] = xb_x[src];
        xb_y[f] = xb_y[src];
        xb_vx[f] = xb_vx[src] * SPLIT_SLOW / 10;
        xb_vy[f] = xb_vy[src] + SPLIT_VY;
        xb_vy[src] -= SPLIT_VY;
    }
    xb_cs[f] = 0;
    xb_pull[f] = 0;
    xb_on[f] = 1;
    split_active++;
}

void do_split(void)
{
    u8 k, was[XB];
    for (k = 0; k < XB; k++)
        was[k] = xb_on[k];
    spawn_xball(0xFF);
    for (k = 0; k < XB; k++)
    {
        if (was[k])
            spawn_xball(k);
    }
}

// Iskry Kimantero przy odbiciu od bandy; up = 1: iskry leca w gore (odbicie od dolnej)
void spawn_sparks(s16 x, s16 y, u8 up)
{
    u8 k;
    for (k = 0; k < 6; k++)
    {
        spk_x[k] = x + 2;
        spk_y[k] = y + 2;
        spk_vx[k] = (s16)(rand() % 7) - 3;
        spk_vy[k] = 1 + rand() % 3;
        if (up)
            spk_vy[k] = -spk_vy[k];
        spk_life[k] = 12;
    }
    spk_on = 1;
}

void start_special(u8 p, s16 hit)
{
    u8 pw = power[p];
    u16 held = p ? pad1 : pad0;
    s16 v, dir;
    u16 *mm = (u16 *)&minicons_map;
    u8 n, tries;

    if (pw == PWR_HELL)   // Lucifero: przemiana swiata
        luc_hell_begin(p);

    if (pw == PWR_CHAOS)   // moc dobrana do sytuacji (z odrobina losowosci); ikona na 1 s
    {
        n = chaos_choose(p);
        for (tries = 0; tries < 8 && n == chaos_last; tries++)
            n = chaos_set[rand() % 8];
        while (arena == ARENA_LUC && n == PWR_FORTRESS)   // plansza Lucifero: bez muru
            n = chaos_set[rand() % 8];
        chaos_last = n;
        pw = n;
        chaos_icon_t[p] = 60;
        bgmap[96 + (p ? 23 : 8)] = mm[icon_of(n)];
        hud_dirty = 1;
    }

    armed[p] = 0;
    bar[p] = 0;
    update_bar_map(p);
    flash_t = 3;     // blysk widoczny przez 2 klatki
    sfx_lock = 24;   // przez 0.4 s bez dzwiekow band
    play_sound(power_snd[pw]);

    // moce strażnikow: dzialaja dla strony p, wiec po odblokowaniu tak samo u Muggy'ego
    if (pw == PWR_GROW)
    {
        pad_target[p] = GROW_H;
        grow_timer[p] = GROW_TIME;
        return;
    }
    if (pw == PWR_SPLIT)   // rozdwojenie; gdy sa juz dwie pilki, dziela sie obie (razem 4)
    {
        do_split();
        return;
    }
    if (pw == PWR_FORTRESS)
    {
        fortress(p);
        return;
    }
    if (pw == PWR_TWIN)   // blizniak wychodzi do przodu i sam przechwytuje pilke
    {
        twin_timer[p] = TWIN_TIME;
        twin_y[p] = (FIELD_TOP + FIELD_BOTTOM - pad_h[p]) / 2;
        return;
    }
    if (pw == PWR_SWAP)   // odwraca sterowanie przeciwnika
    {
        swap_timer[1 - p] = SWAP_TIME;
        cpu_inv_t = 1;
        status_dirty = 1;
        return;
    }
    if (pw == PWR_SLOW)   // spowalnia paletke przeciwnika
    {
        slow_timer[1 - p] = SLOW_TIME;
        status_dirty = 1;
        return;
    }
    if (pw == PWR_CATCH)   // pilka przykleja sie do paletki
    {
        catch_side = p;
        catch_timer = CATCH_TIME;
        if (p == 0 || two_players)   // gracz strzela sam (A), wycelowawszy paletka i strzalkami
            catch_timer = CATCH_TIME_HUMAN;
        return;
    }
    if (pw == PWR_CAMO)    // tlo w kolorze paletki przeciwnika
    {
        camo_timer[1 - p] = CAMO_TIME;
        return;
    }

    sp_type = pw + 1;
    sp_owner = p;
    cg_want[CGI_BALL] = ball_col[pw];

    if (pw == PWR_SUPER)
    {
        v = vel_x < 0 ? -vel_x : vel_x;
        sp_saved = v;
        if (v > SUPER_MAX / SUPER_MULT)   // (bez przepelnienia przy bardzo szybkiej pilce)
            v = SUPER_MAX;
        else
            v *= SUPER_MULT;
        if (v > SUPER_MAX)
            v = SUPER_MAX;
        v = ff_boost(v, sp_saved);
        vel_x = p ? -v : v;
        shake_t = 8;
    }
    else if (pw == PWR_CURVE)
    {
        if (is_cpu(p))
            held = (rand() & 1) ? KEY_UP : KEY_DOWN;
        // luk w gore (-1) lub w dol (+1); bez strzalki przeciwnie do kierunku z odbicia
        if (held & KEY_UP)
            dir = -1;
        else if (held & KEY_DOWN)
            dir = 1;
        else
            dir = (vel_y >= 0) ? -1 : 1;
        vel_y = dir > 0 ? -CURVE_START : CURVE_START;   // najpierw w przeciwna strone...
        curve_acc = dir > 0 ? CURVE_ACC : -CURVE_ACC;   // ...a potem mocny skret: "banan"
    }
    else if (pw == PWR_ZIGZAG)
    {
        v = vel_x < 0 ? -vel_x : vel_x;   // pilka 25% szybsza; po odbiciu wraca do dawnej
        sp_saved = v;
        v += v / 4;
        v = ff_boost(v, sp_saved);
        vel_x = p ? -v : v;
        vel_y = zig_speed();
        if ((hit < 0) != (vel_y < 0))   // pierwszy odcinek w strone wynikajaca z trafienia
            vel_y = -vel_y;
        zig_timer = zig_length();
        zig_flips = ZIG_SEGMENTS - 1;
    }
}

// Co klatke, przed ruchem pilki
void special_tick(void)
{
    s16 oc, by, m;
    if (sp_type == SP_CURVE)
    {
        vel_y += curve_acc;
        if (vel_y > CURVE_MAX)
            vel_y = CURVE_MAX;
        if (vel_y < -CURVE_MAX)
            vel_y = -CURVE_MAX;
    }
    else if (sp_type == SP_ZIGZAG && zig_flips)
    {
        if (--zig_timer == 0)
        {
            vel_y = zig_speed();   // nowy odcinek: losowy kierunek i predkosc
            zig_flips--;
            zig_timer = zig_length();
            if (zig_flips == 0)   // ostatni odcinek: ostry skret, zwykle z dala od przeciwnika
            {
                if (sp_owner)
                    oc = p1_y + pad_h[0] / 2;
                else
                    oc = p2_y + pad_h[1] / 2;
                by = (s16)(ball_y >> 8) + BALL_SIZE / 2;
                m = 0x0180 + rand() % 0x0100;
                if (rand() % 10 < 7)
                {
                    if (oc < by)
                        vel_y = m;    // przeciwnik nad pilka: w dol
                    else
                        vel_y = -m;   // przeciwnik pod pilka: w gore
                }
                else if (rand() & 1)
                    vel_y = m;
                else
                    vel_y = -m;
            }
        }
    }
}

// Gdzie pilka przetnie linie paletki komputera, liczac liniowo z odbiciami od band
s16 predict_y_to(s16 tx)
{
    u16 px = ball_x, py = ball_y;
    s16 vy = vel_y;
    u8 n;
    for (n = 0; n < 200; n++)   // w prawo albo w lewo, zaleznie od kierunku pilki
    {
        if (vel_x > 0 && (s16)(px >> 8) >= tx)
            break;
        if (vel_x <= 0 && (s16)(px >> 8) <= tx)
            break;
        px += vel_x;
        py += vy;
        if ((s16)(py >> 8) < FIELD_TOP)
        {
            py = FP(FIELD_TOP);
            vy = -vy;
        }
        else if ((s16)(py >> 8) > FIELD_BOTTOM - BALL_SIZE)
        {
            py = FP(FIELD_BOTTOM - BALL_SIZE);
            vy = -vy;
        }
    }
    return (s16)(py >> 8) + BALL_SIZE / 2;
}

s16 predict_y(void)
{
    return predict_y_to(P2_X - BALL_SIZE);
}

// Przewidywanie dla pilki, ktora wybral komputer (glowna albo dodatkowa)
s16 predict_tgt(void)
{
    u16 sx = ball_x, sy = ball_y;
    s16 svx = vel_x, svy = vel_y, r;
    if (cpu_tgt == 0xFF)
        return predict_y();
    ball_x = xb_x[cpu_tgt];   // na chwile podstawiamy wybrana pilke jako glowna
    ball_y = xb_y[cpu_tgt];
    vel_x = xb_vx[cpu_tgt];
    vel_y = xb_vy[cpu_tgt];
    r = predict_y();
    ball_x = sx;
    ball_y = sy;
    vel_x = svx;
    vel_y = svy;
    return r;
}

void ghost_update(s16 bx)
{
    u8 was = ghost_hidden;
    s16 m, v, n, d;

    ghost_hidden = 0;
    ghost_blink = 0;
    if (sp_type != SP_GHOST)
        return;
    v = vel_x < 0 ? -vel_x : vel_x;
    m = (v >> 8) * 4 + 4;   // ok. 4 klatki lotu przed i za strefa
    if (bx >= GHOST_X1 && bx < GHOST_X2)
        ghost_hidden = 1;
    else if ((bx >= GHOST_X1 - m && bx < GHOST_X1) || (bx >= GHOST_X2 && bx < GHOST_X2 + m))
        ghost_blink = 1;

    if (ghost_hidden && !was)
    {
        // komputer traci pilke z oczu i zgaduje, gdzie sie pojawi - z toru, ktory widzial
        if (sp_owner == 0 && !two_players)
        {
            cpu_ghost_target = predict_y() + (s16)(rand() % (2 * CPU_GHOST_ERR + 1)) - CPU_GHOST_ERR;
            cpu_ghost_mode = 1;
        }
        // w ukryciu pilka zmienia tor: na wyjsciu ze strefy bedzie o GHOST_SHIFT px wyzej lub nizej
        n = ((GHOST_X2 - GHOST_X1) << 8) / v;   // ile klatek pilka bedzie niewidoczna
        if (n < 1)
            n = 1;
        d = (GHOST_SHIFT << 8) / n;
        vel_y += (rand() & 1) ? d : -d;
        if (vel_y > 0x0300)
            vel_y = 0x0300;
        if (vel_y < -0x0300)
            vel_y = -0x0300;
    }
    if (!ghost_hidden && was)
        ghost_lag = CPU_DELAY;   // po pojawieniu sie pilki komputer potrzebuje chwili na reakcje
}

//---------------------------------------------------------------------------------
// ROZGRYWKA
//---------------------------------------------------------------------------------
void go_serve(void);

void point_scored(void)
{
    u8 w, len, x;
    char *nm;
    draw_score();
    if (score1 < win_score && score2 < win_score)
    {
        go_serve();
        return;
    }

    music_want = 0;
    hide_sprite(SPR_BALL);
    if (story)
    {
        story_result(score1 >= win_score);
        return;
    }
    music_stop_safe();   // koniec meczu: cisza przed fanfara (przez kolejke dzwieku)
    state = ST_OVER;
    w = 1;
    if (score1 >= win_score)
        w = 0;
    nm = char_name(char_of[w]);
    len = strlen(nm) + 6;
    x = (32 - len) / 2;
    consoleDrawText(x, 12, nm);
    consoleDrawText(x + len - 6, 12, " WINS!");
    if (w == 1 && !two_players)
        play_sound(SND_SAD);       // wygral komputer
    else
        play_sound(SND_FANFARE);   // wygral czlowiek (we dwoje zawsze fanfary)
    consoleDrawText(10, 15, "PRESS START");
}

void lose_point(u8 p);

// Strata punktu przez gracza p: kasujemy jego pasek i uzbrojenie
void lose_point(u8 p)
{
    bar[p] = 0;
    armed[p] = 0;
    grow_timer[p] = 0;               // GROW konczy sie, gdy wlasciciel straci punkt
    catch_timer = 0;
    force_tail = 0;
    tele_done = 0;
    tele0_done = 0;
    kim_level = 0;
    ff_level = 0;
    chron_slowed = 0;
    blink_left[0] = 0;               // po punkcie BLINK STRIKE sie konczy
    blink_left[1] = 0;
    if (blink_side != 0xFF)          // teleportowana paletka wraca od razu
    {
        pad_x[0] = P1_X;
        pad_x[1] = P2_X;
        blink_side = 0xFF;
        blink_ret = 0;
    }
    pad_target[p] = pad_base[p];
    clear_xballs();
    update_bar_map(p);
    end_special();
    tail_len = 0;
    if (p == 0)
    {
        score2++;
        serve_right = 0;   // serwis w strone gracza, ktory stracil punkt
    }
    else
    {
        score1++;
        serve_right = 1;
    }
    point_scored();
}

s16 clamp_paddle_s(u8 p, s16 y, u8 h)   // plansza Lucifero: strona gracza moze byc rozszerzona
{
    s16 t = FIELD_TOP - luc_ext[p], b = FIELD_BOTTOM + luc_ext[p];
    if (y < t)
        return t;
    if (y > b - h)
        return b - h;
    return y;
}

s16 clamp_paddle(s16 y, u8 h)
{
    if (y < FIELD_TOP)
        return FIELD_TOP;
    if (y > FIELD_BOTTOM - h)
        return FIELD_BOTTOM - h;
    return y;
}

u8 icon_of(u8 pw);

// Blizniak (TWIN, widmo Cyber-dopplera): wlasny, prosty ruch w strone pilki, ktora do niego leci
void update_twins(void)
{
    u8 p, st;
    s16 target, c, by = (s16)(ball_y >> 8) + BALL_SIZE / 2, bx = (s16)(ball_x >> 8);
    for (p = 0; p < 2; p++)
    {
        if (!twin_timer[p] && !ghost_on[p])
            continue;
        target = (FIELD_TOP + FIELD_BOTTOM) / 2;
        if (p == 1 && vel_x > 0 && bx < twin_x[1])
            target = by;
        if (p == 0 && vel_x < 0 && bx > twin_x[0] + PADDLE_W)
            target = by;
        twin_acc[p] += 0x0180;   // 1.5 px na klatke
        st = twin_acc[p] >> 8;
        twin_acc[p] &= 0x00FF;
        c = twin_y[p] + pad_h[p] / 2;
        if (c < target - 2)
            twin_y[p] += st;
        else if (c > target + 2)
            twin_y[p] -= st;
        twin_y[p] = clamp_paddle(twin_y[p], pad_h[p]);
    }
}

// Co klatke: plynna zmiana wysokosci paletek (GROW) i czasy mocy
void update_heights_timers(void)
{
    u8 p, n;
    s16 d, home;
    u16 *mm = (u16 *)&minicons_map;
    for (p = 0; p < 2; p++)
    {
        if (grow_timer[p] && --grow_timer[p] == 0)
            pad_target[p] = pad_base[p];
        if (fort_timer[p] && --fort_timer[p] == 0)
            passive_blocks(p);
        if (pad_h[p] != pad_target[p])
        {
            d = (s16)pad_target[p] - (s16)pad_h[p];
            if (d > 6)
                d = 6;
            if (d < -6)
                d = -6;
            pad_h[p] += d;
            if (p == 0)
                p1_y -= d / 2;   // paletka rosnie wokol swojego srodka
            else
                p2_y -= d / 2;
        }
    }
    if (tele_flash)
        tele_flash--;
    if (tele_cool)
        tele_cool--;
    if (tele0_flash)
        tele0_flash--;
    if (tele0_cool)
        tele0_cool--;
    if ((story && is_g(1, 8)) || (!story && is_g(0, 8)))   // Blinker: co 4-6 s nowy kolor tla
    {
        if (--back_t == 0)
        {
            n = rand() % 6;
            if (n == back_idx)
                n = (n + 1) % 6;
            back_idx = n;
            back_col = back_cols[n];
            back_t = 240 + rand() % 121;
        }
    }
    if (blink_side != 0xFF)   // BLINK STRIKE: powrot paletki na miejsce
    {
        if (blink_ret == 0)
        {
            if (blink_side == 1 && vel_x > 0 && (s16)(ball_x >> 8) > 110)
                blink_ret = BLINK_RET;   // pilka minela paletke
            if (blink_side == 0 && vel_x < 0 && (s16)(ball_x >> 8) < 140)
                blink_ret = BLINK_RET;
        }
        if (blink_ret)
        {
            if (blink_side)
                home = P2_X;
            else
                home = P1_X;
            d = home - (s16)pad_x[blink_side];
            pad_x[blink_side] += d / blink_ret;
            if (--blink_ret == 0)
            {
                pad_x[blink_side] = home;
                blink_side = 0xFF;
            }
        }
    }
    for (p = 0; p < 2; p++)
    {
        if (camo_timer[p])
            camo_timer[p]--;
        if (chaos_icon_t[p] && --chaos_icon_t[p] == 0)   // CHAOS: wraca ikona wlasnej mocy
        {
            bgmap[96 + (p ? 23 : 8)] = mm[icon_of(power[p])];
            hud_dirty = 1;
        }
        if (twin_timer[p])
            twin_timer[p]--;
        if (swap_timer[p] && --swap_timer[p] == 0)
            status_dirty = 1;
        if (slow_timer[p] && --slow_timer[p] == 0)
            status_dirty = 1;
    }
    // Cyber-doppler: co 5-9 s na 1.5 s widmowy bliźniak paletki (po stronie Dopplera)
    for (p = 0; p < 2; p++)
    {
        if (is_g(p, 3) && !twin_timer[p])
        {
            if (ghost_on[p])
                ghost_on[p]--;
            else if (--ghost_t[p] == 0)
            {
                ghost_on[p] = 90;
                ghost_t[p] = 300 + rand() % 241;
            }
        }
    }
    if (status_dirty)
    {
        if (swap_timer[0])
            consoleDrawText(6, 2, "SWAP!");
        else if (slow_timer[0])
            consoleDrawText(6, 2, "SLOW!");
        else
            consoleDrawText(6, 2, "     ");
        if (story || two_players || char_of[1] != CH_SFC)
        {
            if (swap_timer[1])
                consoleDrawText(21, 2, "SWAP!");
            else if (slow_timer[1])
                consoleDrawText(21, 2, "SLOW!");
            else
                consoleDrawText(21, 2, "     ");
        }
        status_dirty = 0;
    }
    if (!wrap[0])
        p1_y = clamp_paddle_s(0, p1_y, pad_h[0]);
    if (!wrap[1])
        p2_y = clamp_paddle_s(1, p2_y, pad_h[1]);
}

// Telementor sterowany przez gracza: strzalki - zwykly ruch. X - teleport w gore, B - w dol,
// w punkt, w ktorym pilka lecaca do Telementora przetnie jego linie (przy kilku pilkach -
// ta, ktora doleci najszybciej). X dziala tylko, gdy ten punkt jest powyzej srodka paletki,
// B - gdy ponizej; zly przycisk nic nie robi. Po teleporcie przerwa 3 s.
void tele_assist(u8 p)
{
    u16 pn, sx = ball_x, sy = ball_y;
    s16 svx = vel_x, svy = vel_y, ty, best, pc;
    u8 k, ok;
    if (!is_g(p, 7) || blink_side != 0xFF)
        return;
    if (p == 0 && tele0_cool)   // przerwa 3 s po poprzednim teleporcie
        return;
    if (p == 1 && tele_cool)
        return;
    if (p)
        pn = pad1_new;
    else
        pn = pad0_new;
    if (!(pn & (KEY_X | PAD_B_BIT)))
        return;
    // pilka, ktora pierwsza doleci do Telementora (glowna albo dodatkowa)
    best = 0x7FFF;
    if (p == 0 && vel_x < 0)
        best = (s16)(ball_x >> 8);
    if (p == 1 && vel_x > 0)
        best = 255 - (s16)(ball_x >> 8);
    for (k = 0; k < XB; k++)
    {
        if (!xb_on[k])
            continue;
        if (p == 0 && xb_vx[k] < 0 && (s16)(xb_x[k] >> 8) < best)
        {
            best = (s16)(xb_x[k] >> 8);
            ball_x = xb_x[k]; ball_y = xb_y[k]; vel_x = xb_vx[k]; vel_y = xb_vy[k];
        }
        if (p == 1 && xb_vx[k] > 0 && 255 - (s16)(xb_x[k] >> 8) < best)
        {
            best = 255 - (s16)(xb_x[k] >> 8);
            ball_x = xb_x[k]; ball_y = xb_y[k]; vel_x = xb_vx[k]; vel_y = xb_vy[k];
        }
    }
    ok = 0;
    if (best != 0x7FFF)
    {
        // punkt przeciecia linii Telementora i srodek jego paletki
        if (p)
        {
            ty = predict_y();
            pc = p2_y + pad_h[1] / 2;
        }
        else
        {
            ty = predict_y_to(P1_X + PADDLE_W);
            pc = p1_y + pad_h[0] / 2;
        }
        if ((pn & KEY_X) && ty < pc)       // przeciecie powyzej paletki: X (w gore)
            ok = 1;
        if ((pn & PAD_B_BIT) && ty > pc)   // ponizej: B (w dol)
            ok = 1;
    }
    if (ok)
    {
        if (p)
        {
            p2_y = clamp_paddle_s(1, ty - pad_h[1] / 2, pad_h[1]);
            tele_flash = 8;
            tele_cool = 180;
        }
        else
        {
            p1_y = clamp_paddle_s(0, ty - pad_h[0] / 2, pad_h[0]);
            tele0_flash = 8;
            tele0_cool = 180;
        }
        play_sound(SND_GHOST);
    }
    ball_x = sx;   // przywracamy glowna pilke (do przewidywania podstawialismy wybrana)
    ball_y = sy;
    vel_x = svx;
    vel_y = svy;
}

void update_paddles(void)
{
    s16 zby;
    s16 target, center, step, tvx, d, tri;
    u16 tx, ty, up, dn, t, spd;
    u8 sp1;

    sp1 = PADDLE_SPEED;
    if (slow_timer[0])   // SLOW: 0.9 px na klatke (70% wolniej)
    {
        sp1 = 1;   // ok. 0.86 px na klatke
        if (frame % 7 == 0)
            sp1 = 0;
    }
    up = pad0 & KEY_UP;
    dn = pad0 & KEY_DOWN;
    if (swap_timer[0])   // SWAP: strzalki odwrocone
    {
        t = up;
        up = dn;
        dn = t;
    }
    if (up)
        p1_y -= sp1;
    if (dn)
        p1_y += sp1;
    if (wrap[0])   // Changero po lewej: wyjazd za krawedz = wjazd z drugiej strony
    {
        center = p1_y + pad_h[0] / 2;
        if (center < FIELD_TOP)
            p1_y += FIELD_H;
        else if (center >= FIELD_BOTTOM)
            p1_y -= FIELD_H;
    }
    else
        p1_y = clamp_paddle_s(0, p1_y, pad_h[0]);
    tele_assist(0);

    if (two_players)
    {
        sp1 = PADDLE_SPEED;
        if (slow_timer[1])   // SLOW: 0.9 px na klatke (70% wolniej)
        {
            sp1 = 1;   // ok. 0.86 px na klatke
            if (frame % 7 == 0)
                sp1 = 0;
        }
        up = pad1 & KEY_UP;
        dn = pad1 & KEY_DOWN;
        if (swap_timer[1])
        {
            t = up;
            up = dn;
            dn = t;
        }
        if (up)
            p2_y -= sp1;
        if (dn)
            p2_y += sp1;
        tele_assist(1);
    }
    else
    {
        // Przy dwoch pilkach (SPLIT) komputer pilnuje tej, ktora pierwsza do niego dotrze
        tx = ball_x;
        ty = ball_y;
        tvx = vel_x;
        cpu_tgt = 0xFF;   // 0xFF = glowna pilka
        for (xk = 0; xk < XB; xk++)
        {
            if (xb_on[xk] && xb_vx[xk] > 0)
            {
                if (tvx <= 0 || xb_x[xk] > tx)
                {
                    tx = xb_x[xk];
                    ty = xb_y[xk];
                    tvx = xb_vx[xk];
                    cpu_tgt = xk;
                }
            }
        }
        if (sp_owner == 0 && sp_type == SP_ZIGZAG)   // pas, w ktorym wije sie zygzak (najwyzszy i najnizszy punkt)
        {
            zby = (s16)(ball_y >> 8);
            if (!zig_track)
            {
                zig_track = 1;
                zig_ymin = zby;
                zig_ymax = zby;
            }
            if (zby < zig_ymin)
                zig_ymin = zby;
            if (zby > zig_ymax)
                zig_ymax = zby;
        }
        else
            zig_track = 0;
        if (sp_type == SP_ZIGZAG && !zig_flips)   // ile klatek minelo od ostatniego skretu zygzaka
        {
            if (zig_final_t < 255)
                zig_final_t++;
        }
        else
            zig_final_t = 0;
        // Komputer goni pilke tylko gdy leci w jego strone i minela srodek.
        // Wobec mocy gracza gra uczciwie: Ducha zgaduje, na luki reaguje z opoznieniem.
        if (cpu_tgt != pred_ball)   // inna pilka: przewidywanie od nowa
        {
            pred_ok = 0;
            pred_ball = cpu_tgt;
        }
        if (tvx > 0 && (tx >> 8) > cpu_react)
        {
            if (cpu_ghost_mode)
            {
                target = cpu_ghost_target;
                if (!ghost_hidden && ghost_lag && --ghost_lag == 0)
                    cpu_ghost_mode = 0;
            }
            else if (sp_owner == 0 && sp_type == SP_ZIGZAG && zig_flips && (is_g(1, 7) || is_g(1, 8)))
                target = ((zig_ymin + zig_ymax) >> 1) + BALL_SIZE / 2;   // w trakcie skretow: srodek pasa zygzaka
            else if (sp_owner == 0 && (sp_type == SP_CURVE || sp_type == SP_ZIGZAG))
                target = hist_y[hist_index(cpu_delay_d)] + BALL_SIZE / 2 + cpu_error;
            else
            {
                target = (s16)(ty >> 8) + BALL_SIZE / 2;
                if (!two_players && cpu_pw && !any_g(4))   // NORMAL/HARD: gdzie pilka doleci
                {
                    if (pred_cool)
                        pred_cool--;
                    if (pred_ok && pred_cool == 0 && vel_x != pred_vx && cpu_tgt == 0xFF)
                        pred_ok = 0;   // pilka zmienila predkosc pozioma w locie (np. spowolnienie Chronosa): od nowa
                    if (!pred_ok)
                    {
                        pred_y = predict_tgt();
                        pred_ok = 1;
                        pred_vx = vel_x;
                        pred_vy = vel_y;
                        pred_cool = 8;   // najwyzej raz na 8 klatek
                    }
                    target = (target * (4 - cpu_pw) + pred_y * cpu_pw) >> 2;
                }
                target += cpu_error + aim_off();
            }
        }
        else
        {
            target = (FIELD_TOP + FIELD_BOTTOM) / 2;
            pred_ok = 0;
        }
        if (tvx > 0 && (tx >> 8) > cpu_react && !cpu_ghost_mode)
        {
            if (camo_timer[1])   // CAMO Muggy'ego: komputer "oslepiony", reaguje z opoznieniem 20 klatek
                target = hist_y[hist_index(20)] + BALL_SIZE / 2 + cpu_error;
            else if (is_g(1, 9))   // Kimantero: szybki, ale z opoznieniem 8 klatek
                target = hist_y[hist_index(8)] + BALL_SIZE / 2 + cpu_error;
        }
        if (is_g(1, 7) && blink_side == 0xFF)   // Telementor: teleport w punkt przeciecia
        {
            // Zygzak: prawdziwy kierunek widac dopiero po ostatnim skrecie, a teleport wymaga chwili
            // na reakcje. Gdy zygzak skreci pozno, blisko paletki, Telementor nie zdazy sie teleportowac.
            if (tvx > 0 && (tx >> 8) > CPU_REACT_X && !tele_done && tele_cool == 0 &&
                !(sp_owner == 0 && sp_type == SP_ZIGZAG &&
                  (zig_flips || zig_final_t < CPU_DELAY || pad_x[1] - (s16)(tx >> 8) < 40)))
            {
                tele_done = 1;   // trafnie, ale najwyzej raz na 3 s (szybka wymiana go pokona)
                p2_y = predict_tgt() - pad_h[1] / 2;
                tele_flash = 8;
                tele_cool = 180;
            }
            if (tvx < 0)
                tele_done = 0;
        }

        spd = cpu_speed;
        if (slow_timer[1])   // SLOW przeciw komputerowi: 37.5% predkosci
            spd = (spd * 2) / 7;    // ok. 29% predkosci
        cpu_acc += spd;
        step = cpu_acc >> 8;
        cpu_acc &= 0x00FF;
        if (swap_timer[1])   // SWAP przeciw komputerowi: losowe odcinki jazdy w zla strone
        {
            if (--cpu_inv_t == 0)
            {
                cpu_inv = rand() & 1;
                cpu_inv_t = 10 + rand() % 11;
            }
            if (cpu_inv)
                step = -step;
        }

        center = p2_y + pad_h[1] / 2;
        d = target - center;
        if (wrap[1])   // Changero: krotsza droga, takze przez krawedz boiska
        {
            if (d > FIELD_H / 2)
                d -= FIELD_H;
            else if (d < -FIELD_H / 2)
                d += FIELD_H;
        }
        // po teleporcie (Telementor, BLINK STRIKE) paletka czeka w miejscu na pilke
        if (blink_side != 1 && !(is_g(1, 7) && tele_done && !split_active))
        {
            if (d > 2)
                p2_y += step;
            else if (d < -2)
                p2_y -= step;
        }
    }
    if (wrap[1])
    {
        center = p2_y + pad_h[1] / 2;
        if (center < FIELD_TOP)
            p2_y += FIELD_H;
        else if (center >= FIELD_BOTTOM)
            p2_y -= FIELD_H;
    }
    else
        p2_y = clamp_paddle_s(1, p2_y, pad_h[1]);
}

// Laskawsza kolizja (tolerancja na rogach) tylko dla ludzi; komputer ma ja scisla,
// zeby poprawka nie zrobila go trudniejszym
u8 tol_of(u8 p)
{
    return (p == 0 || two_players) ? EDGE_TOL : 0;
}

u8 overlaps(s16 by, s16 py, u8 h, u8 t)
{
    return by + BALL_SIZE + t > py && by < py + h + t;
}

// Druga paletka strony p: bliźniak (TWIN, lustrzanie w pionie) albo czesc paletki
// Changero, ktora wyjechala za krawedz i pojawila sie po drugiej stronie
s16 extra_y(u8 p)
{
    s16 y;
    u8 h = pad_h[p];
    if (p)
        y = p2_y;
    else
        y = p1_y;
    if (wrap[p])
    {
        if (y < FIELD_TOP)
            return y + FIELD_H;
        if (y + h > FIELD_BOTTOM)
            return y - FIELD_H;
        return NO_Y;
    }
    return NO_Y;   // blizniak TWIN ma wlasna pozycje (twin_x, twin_y)
}

// Czy pilka dotyka paletki strony p (glownej lub drugiej); zwraca jej y albo NO_Y
s16 touch(u8 p, s16 by, s16 pby)
{
    s16 py, ey;
    u8 h = pad_h[p], t = tol_of(p);
    if (p)
        py = p2_y;
    else
        py = p1_y;
    if (overlaps(by, py, h, t))
        return py;
    if (overlaps(pby, py, h, t))
        return py;
    ey = extra_y(p);
    if (ey != NO_Y)
    {
        if (overlaps(by, ey, h, t))
            return ey;
        if (overlaps(pby, ey, h, t))
            return ey;
    }
    return NO_Y;
}

// Pilka przeciela linie paletki albo juz na niej jest, bo paletka gracza na nia wjechala
u8 crosses(u8 p, s16 pbx, s16 bx)
{
    s16 px = pad_x[p];
    if (p == 0)
    {
        if (pbx >= px + PADDLE_W && bx <= px + PADDLE_W)
            return 1;
        if (tol_of(0) && bx < px + PADDLE_W && bx + BALL_SIZE > px)
            return 1;
        return 0;
    }
    if (pbx <= px - BALL_SIZE && bx >= px - BALL_SIZE)
        return 1;
    if (tol_of(1) && bx > px - BALL_SIZE && bx < px + PADDLE_W)
        return 1;
    return 0;
}

// BLINK STRIKE strony b: teleport na polowe przeciwnika, na tor pilki
void do_blink(u8 b)
{
    if (blink_left[b])
        blink_left[b]--;
    armed[b] = 0;
    bar[b] = 0;
    update_bar_map(b);
    flash_t = 3;
    play_sound(SND_GHOST);
    blink_side = b;
    blink_ret = 0;
    if (b == 1)
    {
        pad_x[1] = 96;
        p2_y = clamp_paddle_s(1, predict_y_to(88) - pad_h[1] / 2 + (s16)(rand() % 13) - 6, pad_h[1]);
    }
    else
    {
        pad_x[0] = 152;
        p1_y = clamp_paddle_s(0, (s16)(ball_y >> 8) + BALL_SIZE / 2 - pad_h[0] / 2, pad_h[0]);
    }
}

// Wystrzal CATCH: zawsze 3,5 px na klatke; u Magnetona o 5% szybciej (3,67 px)
s16 catch_speed(u8 p)
{
    if (is_g(p, 6))
        return 0x03AC;
    return 0x0380;
}

void paddle_hit(u8 p, s16 by, s16 py)
{
    u8 strong;
    s16 hit = (by + BALL_SIZE / 2) - (py + pad_h[p] / 2);   // ok. -20..+20 (przy 32 px)
    s16 spd = vel_x < 0 ? -vel_x : vel_x;

    if (sp_type == SP_SUPER || sp_type == SP_ZIGZAG)
        spd = sp_saved;   // po Superstrzale i zygzaku powrot do predkosci sprzed nich
    if (chron_slowed)     // po spowolnieniu Chronosa piłka wraca do dawnej predkosci
    {
        spd = chron_saved < 0 ? -chron_saved : chron_saved;
        chron_slowed = 0;
    }
    // Ruden, Malten, Waller, Cyber-Doppler, Chronos i Magneton: +5% wzgledem predkosci, z jaka
    // pilka przyleciala (u Chronosa: sprzed jego spowolnienia). Ruden z GROW i Waller
    // z FORTRESS: +7%. U pozostalych moc specjalna nic tu nie zmienia.
    strong = is_g(p, 0) || is_g(p, 1) || is_g(p, 2) || is_g(p, 3) || is_g(p, 5) || is_g(p, 6) || is_g(p, 7) || is_g(p, 8)
             || is_g(p, G_LUCIFERO);
    if (strong)
    {
        if (is_g(p, G_LUCIFERO))   // Lucifero: +7%, do 4,5 px na klatke (miedzy zwyklymi a Kimantero)
        {
            spd += spd / 14;
            if (spd > 0x0480)
                spd = 0x0480;
        }
        else if ((is_g(p, 0) && grow_timer[p]) || (is_g(p, 2) && fort_timer[p]))
            spd += spd / 14;
        else
            spd += spd / 20;
    }
    else
        spd += spd_step;
    if (ff_mode)   // FAST & FURIOUS: kazde odbicie +5%, bez limitu poziomow
    {
        if (ff_level < 250)
            ff_level++;
        spd += spd / 20;
        if (is_g(p, 9) && kim_level < 10)   // zdolnosc stala Kimantero jak w QUICK MATCH
        {
            kim_level++;
            spd += spd / 20;
        }
        if (spd > FF_MAX)
            spd = FF_MAX;
        if (ff_level >= 8 || (is_g(p, 9) && kim_level >= 8))
            shake_t = 6;   // od 8. poziomu odbicia trzesa ekranem
    }
    else if (any_g(9))   // Kimantero: kazde jego odbicie +5%, do 10 poziomow
    {
        if (is_g(p, 9) && kim_level < 10)
        {
            kim_level++;
            spd += spd / 20;
        }
        if (spd > 0x0600)
            spd = 0x0600;
        if (is_g(p, 9) && kim_level >= 8)
            shake_t = 6;   // od 8. poziomu jego uderzenia trzesa ekranem
    }
    else if (spd > max_spd && !strong)   // (odbicia tych strażnikow nie sa przycinane - zawsze przyspieszaja)
        spd = max_spd;
    if (spd > FF_MAX)   // techniczny limit 32 px na klatke
        spd = FF_MAX;
    if (blink_side == p && blink_ret == 0 && p == 1)
        spd = ff_boost(0x0280, spd);   // odbicie z teleportu: 2.5 px na klatke (w FAST & FURIOUS nie zwalnia)

    if (hit_fx != NO_Y)
        ball_x = FP(hit_fx);
    else if (p)
        ball_x = FP(pad_x[1] - BALL_SIZE);
    else
        ball_x = FP(pad_x[0] + PADDLE_W);
    vel_x = p ? -spd : spd;
    vel_y = hit * SPIN;
    if (blink_side == p && blink_ret == 0 && p == 1 && !two_players)   // BLINK STRIKE komputera: ukosnie
    {
        vel_y = 0x0130 + (rand() & 0x7F);
        if (p1_y + pad_h[0] / 2 > (FIELD_TOP + FIELD_BOTTOM) / 2)
            vel_y = -vel_y;   // w strone dalsza od paletki gracza
    }
    if (ff_mode && ff_level >= 11)   // FAST & FURIOUS: od 11. poziomu iskry takze przy paletce
        spawn_sparks((s16)(ball_x >> 8), (s16)(ball_y >> 8), rand() & 1);
    end_special();   // kontakt z paletka konczy kazde uderzenie specjalne
    new_cpu_error();

    force_tail = 0;
    if (is_g(p, 9) || ff_mode)
        force_tail = 1;   // po odbiciu Kimantero (i w FAST & FURIOUS) pilka zawsze ma ogon komety
    if (blink_side == p && blink_ret == 0)
        blink_ret = BLINK_RET;   // po odbiciu z teleportu paletka wraca na miejsce
    if (armed[p] && power[p] != PWR_BLINK)
        start_special(p, hit);
    else
        charge(p, hit);
    if (armed[1 - p] && power[1 - p] == PWR_BLINK && blink_side == 0xFF)
    {
        blink_left[1 - p] = 3;   // BLINK STRIKE: trzy teleporty z jednej aktywacji
        do_blink(1 - p);         // pierwszy zaraz po naszym odbiciu
    }
    else if (blink_left[1 - p] && blink_side == 0xFF)
        do_blink(1 - p);         // kolejne przy nastepnych odbiciach przeciwnika
}

void wall_bounce(void)
{
    u8 k;
    if (any_g(9) || ff_mode)   // Kimantero i FAST & FURIOUS: odbicia od band sypia iskrami
        spawn_sparks((s16)(ball_x >> 8), (s16)(ball_y >> 8), vel_y > 0);
    vel_y = -vel_y;
    curve_acc = -curve_acc;   // luk odbija sie razem z pilka
    if (!sfx_lock)
        play_sound(SND_WALL);
}

void update_ball(void)
{
    s16 bx, by, pbx;
    u16 old_x = ball_x;
    u8 wrap_l, wrap_r, comet;
    s16 pby = (s16)(ball_y >> 8), ty, d;

    if (catch_timer)   // CATCH: pilka jedzie z paletka, potem strzal
    {
        if (catch_side)
        {
            ball_x = FP(pad_x[1] - BALL_SIZE);
            ball_y = FP(clamp_paddle(p2_y + pad_h[1] / 2 - BALL_SIZE / 2, BALL_SIZE));
        }
        else
        {
            ball_x = FP(pad_x[0] + PADDLE_W);
            ball_y = FP(clamp_paddle(p1_y + pad_h[0] / 2 - BALL_SIZE / 2, BALL_SIZE));
        }
        catch_timer--;
        if (catch_side == 0 && (pad0_new & KEY_A))
            catch_timer = 0;   // gracz moze strzelic wczesniej
        if (catch_side == 1 && two_players && (pad1_new & KEY_A))
            catch_timer = 0;
        if (catch_timer == 0)
        {
            if (catch_side && two_players)   // gracz 2 celuje strzalkami
            {
                vel_x = -catch_speed(1);   // CATCH: zawsze ten sam mocny wystrzal
                vel_y = 0;
                if (pad1 & KEY_UP)
                    vel_y = -0x0180;
                if (pad1 & KEY_DOWN)
                    vel_y = 0x0180;
            }
            else if (catch_side)
            {
                vel_x = -catch_speed(1);   // CATCH: zawsze ten sam mocny wystrzal
                if (p1_y + pad_h[0] / 2 < (FIELD_TOP + FIELD_BOTTOM) / 2)
                    vel_y = 0x0180;   // w rog dalszy od paletki Muggy'ego
                else
                    vel_y = -0x0180;
            }
            else
            {
                vel_x = catch_speed(0);    // CATCH: zawsze ten sam mocny wystrzal
                vel_y = 0;
                if (pad0 & KEY_UP)
                    vel_y = -0x0180;
                if (pad0 & KEY_DOWN)
                    vel_y = 0x0180;
            }
            play_sound(SND_SUPER);
        }
        push_history();
        return;
    }
    // Chronos: pilka lecaca do niego zwalnia o 25% (nie dotyczy uderzen specjalnych)
    if (sp_type == SP_NONE && !chron_slowed)
    {
        d = 0;
        if (is_g(1, 5) && vel_x > 0 && (s16)(ball_x >> 8) > 160)
            d = 1;
        if (is_g(0, 5) && vel_x < 0 && (s16)(ball_x >> 8) < 88)
            d = 1;
        if (d)
        {
            chron_saved = vel_x;
            vel_x = vel_x - vel_x / 4 - vel_x / 26;   // ok. 29% wolniej
            chron_slowed = 1;
        }
    }
    // Magneton wyraznie przyciaga pilke lecaca w jego strone
    d = NO_Y;
    if (is_g(1, 6) && vel_x > 0 && (s16)(ball_x >> 8) > P2_X - 96)
        d = p2_y + pad_h[1] / 2;
    if (is_g(0, 6) && vel_x < 0 && (s16)(ball_x >> 8) < P1_X + PADDLE_W + 96)
        d = p1_y + pad_h[0] / 2;
    if (d != NO_Y && pull_total < 422)   // o 10% mocniej niz wczesniej (srednio 6.6 na klatke)
    {
        mag_glow = 12;
        pull_step = 6;
        if (frame % 5 < 3)
            pull_step = 7;
        d -= (s16)(ball_y >> 8) + BALL_SIZE / 2;
        if (d > 2)
            vel_y += pull_step;
        else if (d < -2)
            vel_y -= pull_step;
        pull_total += pull_step;
    }
    if ((is_g(1, 6) && vel_x < 0) || (is_g(0, 6) && vel_x > 0))
        pull_total = 0;

    pbx = (s16)(ball_x >> 8);
    special_tick();
    ball_x += vel_x;
    wrap_l = vel_x < 0 && ball_x > old_x;   // przy 12 px na klatke pozycja moze sie
    wrap_r = vel_x > 0 && ball_x < old_x;   // przewinac przez krawedz ekranu
    ball_y += vel_y;
    bx = (s16)(ball_x >> 8);
    by = (s16)(ball_y >> 8);

    {
        s16 ft = FIELD_TOP, fb = FIELD_BOTTOM, f;
        if (luc_w)   // plansza Lucifero: rozszerzona strona gracza - bandy rozchylaja sie ku niemu
        {
            f = luc_hell_p ? (((256 - bx) * luc_w) >> 8) : ((bx * luc_w) >> 8);
            ft -= f;
            fb += f;
        }
        // Odbicie tylko, gdy pilka leci w strone bandy: banda, ktora sie przesuwa (rozszerzenie
        // boiska Lucifero), tylko ja popycha - inaczej pilka odbijalaby sie w kolko w miejscu.
        if (by < ft)
        {
            ball_y = FP(ft);
            if (vel_y < 0)
                wall_bounce();
        }
        else if (by > fb - BALL_SIZE)
        {
            ball_y = FP(fb - BALL_SIZE);
            if (vel_y > 0)
                wall_bounce();
        }
    }
    by = (s16)(ball_y >> 8);

    // Kolizje "przez przeciecie": czy pilka przeszla przez linie paletki w tej klatce.
    // Dziala przy kazdej predkosci, takze 12 px na klatke (Superstrzal).
    // Kolizja liczy sie, gdy pilka przeciela linie paletki ALBO juz na niej jest (paletka
    // wjechala na pilke), a w pionie zachodzi na paletke przed ruchem lub po nim (+-2 px na rogach).
    ty = NO_Y;
    if (vel_x < 0)
    {
        if (twin_timer[0] && pbx >= twin_x[0] + PADDLE_W && bx <= twin_x[0] + PADDLE_W &&
            overlaps(by, twin_y[0], pad_h[0], 0))
        {
            hit_fx = twin_x[0] + PADDLE_W;   // odbicie przez wysunietego blizniaka
            paddle_hit(0, by, twin_y[0]);
            hit_fx = NO_Y;
        }
        else
        {
            if (crosses(0, pbx, bx))
                ty = touch(0, by, pby);
            if (ty != NO_Y)
                paddle_hit(0, by, ty);
        }
    }
    else if (vel_x > 0)
    {
        if (twin_timer[1] && pbx <= twin_x[1] - BALL_SIZE && bx >= twin_x[1] - BALL_SIZE &&
            overlaps(by, twin_y[1], pad_h[1], 0))
        {
            hit_fx = twin_x[1] - BALL_SIZE;
            paddle_hit(1, by, twin_y[1]);
            hit_fx = NO_Y;
        }
        else
        {
            if (crosses(1, pbx, bx))
                ty = touch(1, by, pby);
            if (ty != NO_Y)
                paddle_hit(1, by, ty);
        }
    }

    bx = (s16)(ball_x >> 8);
    push_history();
    ghost_update(bx);

    // Bloki za paletkami (Waller, FORTRESS): pilka odbija sie zamiast zdobyc punkt
    if (vel_x > 0 && (bx > 240 || wrap_r) && blocked(1, (s16)(ball_y >> 8)))
    {
        comet = (sp_type == SP_SUPER) || vel_x >= TAIL_SPEED;
        ball_x = FP(240);
        vel_x = -vel_x;
        wrap_r = 0;
        end_special();
        play_sound(SND_WALL);
        if (comet)
            damage_wall(1, (s16)(ball_y >> 8));
    }
    else if (vel_x < 0 && (bx < 8 || wrap_l) && blocked(0, (s16)(ball_y >> 8)))
    {
        if ((sp_type == SP_SUPER) || vel_x <= -TAIL_SPEED)
            damage_wall(0, (s16)(ball_y >> 8));
        ball_x = FP(8);
        vel_x = -vel_x;
        wrap_l = 0;
        end_special();
        play_sound(SND_WALL);
    }
    bx = (s16)(ball_x >> 8);

    // Punkty: za linia paletki albo po przewinieciu pozycji przez krawedz ekranu
    if (vel_x < 0 && (bx < 8 || wrap_l))
        lose_point(0);   // punkt: obie pilki znikaja, serwis ze srodka
    else if (vel_x > 0 && (bx > 240 || wrap_r))
        lose_point(1);
}

// Zamiana rol pilek: odbita druga pilka staje sie glowna i przechodzi przez zwykly kod
// odbicia (pasek, uzbrojone moce, przyspieszenie, Kimantero, CATCH...). Pilki sa
// identyczne poza predkoscia, wiec dla gracza zamiana jest niewidoczna.
void swap_balls(u8 k)
{
    u16 t;
    s16 v;
    u8 i, b;
    t = ball_x; ball_x = xb_x[k]; xb_x[k] = t;
    t = ball_y; ball_y = xb_y[k]; xb_y[k] = t;
    v = vel_x; vel_x = xb_vx[k]; xb_vx[k] = v;
    v = vel_y; vel_y = xb_vy[k]; xb_vy[k] = v;
    for (i = 0; i < 16; i++)
    {
        b = hist_x[i]; hist_x[i] = xh_x[k][i]; xh_x[k][i] = b;
        b = hist_y[i]; hist_y[i] = xh_y[k][i]; xh_y[k][i] = b;
    }
    b = tail_len; tail_len = xtail[k]; xtail[k] = b;
    b = chron_slowed; chron_slowed = xb_cs[k]; xb_cs[k] = b;   // Chronos i Magneton
    v = chron_saved; chron_saved = xb_csv[k]; xb_csv[k] = v;
    t = pull_total; pull_total = xb_pull[k]; xb_pull[k] = t;
    end_special();   // specjalne zachowanie mialo poprzednia glowna pilka
}

void clear_xballs(void)
{
    u8 k;
    for (k = 0; k < XB; k++)
    {
        xb_on[k] = 0;
        xtail[k] = 0;
        xb_cs[k] = 0;
        xb_pull[k] = 0;
    }
    split_active = 0;
}

// Dodatkowa pilka k (SPLIT): odbija sie od band, paletek i blokow, moze zdobyc punkt
// Zdolnosci Chronosa (spowolnienie pilki lecacej do niego) i Magnetona (przyciaganie)
// dla dodatkowej pilki k - tak samo jak dla glownej
void xball_abilities(u8 k, s16 bx)
{
    s16 d, v;
    if (!xb_cs[k] && any_g(5))
    {
        d = 0;
        if (is_g(1, 5) && xb_vx[k] > 0 && bx > 160)
            d = 1;
        if (is_g(0, 5) && xb_vx[k] < 0 && bx < 88)
            d = 1;
        if (d)
        {
            v = xb_vx[k];
            xb_csv[k] = v;
            xb_vx[k] = v - v / 4 - v / 26;
            xb_cs[k] = 1;
        }
    }
    if (any_g(6))
    {
        d = NO_Y;
        if (is_g(1, 6) && xb_vx[k] > 0 && bx > P2_X - 96)
            d = p2_y + pad_h[1] / 2;
        if (is_g(0, 6) && xb_vx[k] < 0 && bx < P1_X + PADDLE_W + 96)
            d = p1_y + pad_h[0] / 2;
        if (d != NO_Y && xb_pull[k] < 422)
        {
            mag_glow = 12;
            pull_step = 6;
            if (frame % 5 < 3)
                pull_step = 7;
            d -= (s16)(xb_y[k] >> 8) + BALL_SIZE / 2;
            if (d > 2)
                xb_vy[k] += pull_step;
            else if (d < -2)
                xb_vy[k] -= pull_step;
            xb_pull[k] += pull_step;
        }
        if (is_g(1, 6) && xb_vx[k] < 0)
            xb_pull[k] = 0;
        if (is_g(0, 6) && xb_vx[k] > 0)
            xb_pull[k] = 0;
    }
}

void update_xball(u8 k)
{
    s16 bx, by, pbx, pby, ty;
    u8 wl, wr, hh;

    if (!xb_on[k])
        return;
    xb_move_asm(k);   // ruch, odbicia od band i historia pozycji (data.asm)
    pbx = xm_pbx;
    pby = xm_pby;
    wl = (xm_flags >> 1) & 1;
    wr = (xm_flags >> 2) & 1;
    if ((xm_flags & 1) && !sfx_lock)
        play_sound(SND_WALL);
    bx = (s16)(xb_x[k] >> 8);
    if ((xm_flags & 1) && (any_g(9) || ff_mode))   // iskry przy bandzie, jak przy glownej pilce
        spawn_sparks(bx, (s16)(xb_y[k] >> 8), xb_vy[k] < 0);
    xball_abilities(k, bx);   // Chronos i Magneton dzialaja na kazda pilke
    // W srodku boiska nie ma z czym sie zderzyc: paletki, mury i linie koncowe sa dalej,
    // wiec kolizje liczymy tylko blisko nich (albo gdy sa bliźniaki lub BLINK STRIKE)
    bx = (s16)(xb_x[k] >> 8);
    if (bx > 44 && bx < 204 && !wl && !wr && !twin_timer[0] && !twin_timer[1] && blink_side == 0xFF)
        return;
    by = (s16)(xb_y[k] >> 8);
    bx = (s16)(xb_x[k] >> 8);
    // Uwaga: if / else if - po odbiciu przez Muggy'ego pilka nie moze w tej samej klatce
    // "odbic sie" od paletki Maltena (wczesniej przeskakiwala wtedy na jego strone).
    // Odbicie: zamiana rol i zwykly kod odbicia, wiec druga pilka ma te same wlasciwosci
    ty = NO_Y;
    if (xb_vx[k] < 0)
    {
        if (twin_timer[0] && pbx >= twin_x[0] + PADDLE_W && bx <= twin_x[0] + PADDLE_W &&
            overlaps(by, twin_y[0], pad_h[0], 0))
        {
            swap_balls(k);
            hit_fx = twin_x[0] + PADDLE_W;
            paddle_hit(0, by, twin_y[0]);
            hit_fx = NO_Y;
            return;
        }
        if (crosses(0, pbx, bx))
            ty = touch(0, by, pby);
        if (ty != NO_Y)
        {
            swap_balls(k);
            paddle_hit(0, by, ty);
            return;
        }
    }
    else if (xb_vx[k] > 0)
    {
        if (twin_timer[1] && pbx <= twin_x[1] - BALL_SIZE && bx >= twin_x[1] - BALL_SIZE &&
            overlaps(by, twin_y[1], pad_h[1], 0))
        {
            swap_balls(k);
            hit_fx = twin_x[1] - BALL_SIZE;
            paddle_hit(1, by, twin_y[1]);
            hit_fx = NO_Y;
            return;
        }
        if (crosses(1, pbx, bx))
            ty = touch(1, by, pby);
        if (ty != NO_Y)
        {
            swap_balls(k);
            paddle_hit(1, by, ty);
            return;
        }
    }
    bx = (s16)(xb_x[k] >> 8);
    if (xb_vx[k] > 0 && (bx > 240 || wr) && blocked(1, by))
    {
        xb_x[k] = FP(240);
        if (xb_vx[k] >= TAIL_SPEED)
            damage_wall(1, by);
        xb_vx[k] = -xb_vx[k];
        wr = 0;
    }
    else if (xb_vx[k] < 0 && (bx < 8 || wl) && blocked(0, by))
    {
        if (xb_vx[k] <= -TAIL_SPEED)   // Waller po lewej: szybka pilka kruszy mur
            damage_wall(0, by);
        xb_x[k] = FP(8);
        xb_vx[k] = -xb_vx[k];
        wl = 0;
    }
    bx = (s16)(xb_x[k] >> 8);
    if (xb_vx[k] < 0 && (bx < 8 || wl))
        lose_point(0);
    else if (xb_vx[k] > 0 && (bx > 240 || wr))
        lose_point(1);
}

void update_xballs(void)
{
    for (xk = 0; xk < XB; xk++)
    {
        if (state != ST_PLAY)   // punkt zdobyty ktoras pilka: reszta znika
            return;
        if (xb_on[xk])
            update_xball(xk);
    }
}

// Malten: co 6-10 s na polowie Muggy'ego pojawia sie jedna albo (losowo) dwie falszywe pilki
u8 spawn_fake(u8 k)
{
    s16 fx, fy, dx, dy;
    fx = 72 + rand() % 56;
    // pierwsza w gornej, druga w dolnej polowie boiska - nigdy obok siebie
    if (k == 0)   // gorna czesc boiska...
        fy = FIELD_TOP + rand() % 40;
    else          // ...albo dolna, z co najmniej 60 px odstepu
        fy = FIELD_BOTTOM - BALL_SIZE - rand() % 40;
    if (k == 1 && fake_active[0])
    {
        dx = fx - (s16)(fake_x[0] >> 8);
        if (dx < 24 && dx > -24)
            fx = (fx < 100) ? fx + 32 : fx - 32;
    }
    dx = fx - (s16)(ball_x >> 8);
    dy = fy - (s16)(ball_y >> 8);
    if (dx <= 24 && dx >= -24 && dy <= 24 && dy >= -24)   // nigdy tuz przy prawdziwej pilce
        return 0;
    fake_active[k] = 1;
    fake_life[k] = 68;   // 60 klatek lotu + 8 klatek migania
    fake_x[k] = FP(fx);
    fake_y[k] = FP(fy);
    fake_vx[k] = -(0x0180 + rand() % 0x0100);
    if (is_g(0, 1))   // Malten po lewej: falszywe pilki na polowie przeciwnika, lecace w prawo
    {
        fake_x[k] = FP(256 - BALL_SIZE - fx);
        fake_vx[k] = -fake_vx[k];
    }
    fake_vy[k] = (s16)(rand() & 0x00FF);   // gorna leci w gore, dolna w dol: nie zbiegaja sie
    if (k == 0)
        fake_vy[k] = -fake_vy[k];
    return 1;
}

void update_fake(void)
{
    u8 k;
    s16 fy;
    if (!any_g(1))
        return;
    if (split_active)   // w trakcie SPLIT obie widoczne pilki sa prawdziwe
    {
        fake_active[0] = 0;
        fake_active[1] = 0;
        return;
    }
    for (k = 0; k < 2; k++)
    {
        if (!fake_active[k])
            continue;
        fake_x[k] += fake_vx[k];
        fake_y[k] += fake_vy[k];
        fy = (s16)(fake_y[k] >> 8);
        if (fy < FIELD_TOP || fy > FIELD_BOTTOM - BALL_SIZE)
            fake_vy[k] = -fake_vy[k];
        if (--fake_life[k] == 0 || (s16)(fake_x[k] >> 8) < 12 || (s16)(fake_x[k] >> 8) > 236)
            fake_active[k] = 0;
    }
    if (!fake_active[0] && !fake_active[1] && --fake_timer == 0)
    {
        // losowo jedna albo dwie; w losowej polowie zaczynamy
        if (rand() & 1)
        {
            if (spawn_fake(0) && (rand() & 1))
                spawn_fake(1);
        }
        else
        {
            if (spawn_fake(1) && (rand() & 1))
                spawn_fake(0);
        }
        fake_timer = 360 + rand() % 241;
    }
}

void update_tail(void)
{
    s16 v = vel_x < 0 ? -vel_x : vel_x;
    u8 want = (sp_type == SP_SUPER) || (v >= TAIL_SPEED) || force_tail;
    u8 k, want2;
    s16 v2;
    for (k = 0; split_active && k < XB; k++)   // ogony dodatkowych pilek (bez SPLIT: xtail juz zerowe)
    {
        v2 = xb_vx[k];
        if (v2 < 0)
            v2 = -v2;
        want2 = 0;
        if (xb_on[k] && v2 >= TAIL_SPEED)
            want2 = 1;
        if (!xb_on[k] || state != ST_PLAY)
            xtail[k] = 0;
        else if (frame & 1)
        {
            if (want2 && xtail[k] < TAIL_LEN)
                xtail[k]++;
            else if (!want2 && xtail[k])
                xtail[k]--;
        }
    }
    for (k = 0; spk_on && k < 6; k++)
    {
        if (spk_life[k])
        {
            spk_life[k]--;
            spk_x[k] += spk_vx[k];
            spk_y[k] += spk_vy[k];
        }
    }

    if (ghost_hidden || state != ST_PLAY)
        tail_len = 0;
    else if (frame & 1)
    {
        if (want && tail_len < TAIL_LEN)
            tail_len++;
        else if (!want && tail_len)
            tail_len--;   // ogon znika stopniowo, od konca
    }
}

void launch_ball(void)
{
    vel_x = serve_right ? serve_spd : -serve_spd;
    vel_y = (s16)(rand() & 0xFF) - 128;   // -0.5..+0.5 px na klatke
    state = ST_PLAY;
    music_want = 1;
}

//---------------------------------------------------------------------------------
// EFEKTY (liczone co klatke, wysylane w vblank_tasks)
//---------------------------------------------------------------------------------
void update_effects(void)
{
    frame++;

    if (shake_t)   // trzesienie ekranu: +-2 px w poziomie
    {
        shake_t--;
        shake_x = shake_t ? ((shake_t & 1) ? 2 : -2) : 0;
        scroll_dirty = 1;
    }
    spr_dx = -shake_x;

    if (flash_t)
    {
        if (flash_t == 3)
        {
            cm_wsel = CM_FLASH_WSEL;
            cm_adsub = CM_FLASH_ADSUB;
            cm_data = 0xE0 | CM_FLASH_LEVEL;
            cm_dirty = 1;
        }
        if (--flash_t == 0)
        {
            cm_wsel = CM_NORMAL_WSEL;
            cm_adsub = cm_norm_adsub;
            cm_data = 0xE0;
            cm_dirty = 1;
        }
    }
    if (sfx_lock)
        sfx_lock--;

    // pulsowanie uzbrojonej paletki (co 4 klatki) i miganie pelnego paska (co 8)
    cg_want[CGI_P1] = (armed[0] && (frame & 4)) ? col_p1_lit : col_p1;
    cg_want[CGI_P2] = (armed[1] && (frame & 4)) ? col_p2_lit : col_p2;
    if (slow_timer[0])   // spowolniona paletka jest niebieskawa
        cg_want[CGI_P1] = RGB8(90, 130, 255);
    if (slow_timer[1])
        cg_want[CGI_P2] = RGB8(90, 130, 255);
    cg_want[CGI_BACK] = back_col;
    if (storm_flash)   // blyskawica rozswietla niebo
        cg_want[CGI_BACK] = storm_flash;
    cg_want[CGI_P1E] = col_p1_edge;
    cg_want[CGI_P2E] = col_p2_edge;
    if (is_g(0, 9))
        cg_want[CGI_P1E] = rainbow[(frame >> 3) % 6];
    if (any_g(9))
    {
        if (is_g(1, 9))
            cg_want[CGI_P2E] = rainbow[(frame >> 3) % 6];
        if (kim_level >= 6 && sp_type == SP_NONE)   // od 6. poziomu pilka sie zarzy
            cg_want[CGI_BALL] = (frame & 4) ? RGB8(255, 150, 0) : RGB8(255, 48, 16);
    }
    if (ff_mode && ff_level >= 6 && sp_type == SP_NONE)   // FAST & FURIOUS: zarzenie od 6. poziomu
        cg_want[CGI_BALL] = (frame & 4) ? RGB8(255, 150, 0) : RGB8(255, 48, 16);
    if (camo_timer[0])   // CAMO: tlo w kolorze paletki, ktora znika
    {
        cg_want[CGI_BACK] = col_p1;
        cg_want[CGI_P1E] = col_p1;
        cg_want[CGI_P1] = col_p1;
        if (camo_timer[0] > CAMO_TIME / 2 - 6 && camo_timer[0] <= CAMO_TIME / 2 + 6)
            cg_want[CGI_P1E] = RGB8(255, 255, 255);   // w polowie: na chwile zarys paletki
    }
    if (camo_timer[1])
    {
        cg_want[CGI_BACK] = col_p2;
        cg_want[CGI_P2E] = col_p2;
        cg_want[CGI_P2] = col_p2;
        if (camo_timer[1] > CAMO_TIME / 2 - 6 && camo_timer[1] <= CAMO_TIME / 2 + 6)
            cg_want[CGI_P2E] = RGB8(255, 255, 255);
    }
    if (luc_on && (camo_timer[0] || camo_timer[1]))   // plansza Lucifero: CAMO zmienia paletke, nie tlo
    {
        cg_want[CGI_BACK] = storm_flash ? storm_flash : back_col;
        if (camo_timer[0])
            cg_want[CGI_P1] = luc_rust_lv[luc_rust][5];   // najczestszy kolor posadzki (przy obecnej rdzy)
        if (camo_timer[1])
            cg_want[CGI_P2] = luc_rust_lv[luc_rust][5];
    }
    cg_want[CGI_BAR1] = (bar[0] >= BAR_MAX && (frame & 8)) ? COL_BAR1_LIT : COL_BAR1;
    cg_want[CGI_BAR2] = (bar[1] >= BAR_MAX && (frame & 8)) ? COL_BAR2_LIT : COL_BAR2;
}

//---------------------------------------------------------------------------------
// Zmienne globalne NIE sa zerowane przy starcie konsoli (RAM ma przypadkowa zawartosc),
// dlatego ustawiamy je jawnie.
void init_state(void)
{
    last_power[0] = PWR_SUPER;
    last_power[1] = PWR_SUPER;
    power[0] = PWR_SUPER;
    power[1] = PWR_SUPER;
    two_players = 0;
    serve_right = 0;
    timer = 0;
    frame = 0;
    cpu_acc = 0;
    cpu_error = 0;
    cpu_arm_wait = 0;
    sp_saved = 0;
    curve_acc = 0;
    zig_timer = 0;
    zig_flips = 0;
    cpu_ghost_target = 0;
    ghost_lag = 0;
    sel_idx[0] = 0;
    sel_idx[1] = 0;
    sel_done[0] = 0;
    sel_done[1] = 0;
    cpu_think = 0;
    cpu_delay = 0;
    ready_timer = 0;
    desc_dirty = 0;
    hist_pos = 0;
    sfx_lock = 0;
    snd_req = SND_NONE;
    snd_gap = 0;
    snd_cur_prio = 0;
    snd_left = 0;
    dbg_vmax = 0;
    hud_dirty = 0;
    score1 = 0;
    score2 = 0;
    ball_x = FP(124);
    ball_y = FP(120);
    vel_x = 0;
    vel_y = 0;
    p1_y = 104;
    p2_y = 104;
    pad_base[0] = PADDLE_H;
    pad_base[1] = PADDLE_H;
    cpu_speed = CPU_SPEED;
    win_score = WIN_SCORE;
    col_p1 = COL_P1;
    col_p1_lit = COL_P1_LIT;
    col_p2 = COL_P2;
    col_p2_lit = COL_P2_LIT;
    col_p1_edge = RGB8(225, 100, 125);
    col_p2_edge = RGB8(110, 170, 255);
    story = 0;
    stage = 0;
    menu_idx = 0;
    erase_ask = 0;
    run_pw[0] = PWR_SUPER;
    run_n = 1;
    run_cur = 0;
    chaos_last = 0xFF;
    title_sub = 0;
    game_mode = 0;
    ff_mode = 0;
    ff_level = 0;
    pts_idx = 2;   // domyslnie mecz do 7 punktow
    qm_track = 0;
    music_on = 1;
    spc_mus = 0;
    snd_dead = 0;
    spc_err = 0;
    play_wait = 0;
    prev_dirty = 0;
    prev_wait = 0;
    char_of[0] = CH_MUGGY;
    char_of[1] = CH_SFC;
    avpal_dirty = 0;
    av_dim[0] = 0;
    av_dim[1] = 0;
    av_dim[2] = 0;
    g48_map = (u16 *)&ruden48_map;
    g32_map = (u16 *)&ruden32_map;
    reset_effects();
    reset_history();
}

//---------------------------------------------------------------------------------
int main(void)
{
    u8 i;

    pause_cmd = 0;    // zmienne globalne nie sa zerowane: po wlaczeniu w RAM sa przypadkowe dane
    mus_pos = 0;
    nmi_shadow = NMI_OFF;   // do pierwszego rozjasnienia ekranu przerwanie VBlank jest wylaczone
    strcpy(player_name, "MUGGY");
    run_score = 0;
    difficulty = 0;
    serve_spd = SERVE_SPEED;
    spd_step = SPEED_STEP;
    max_spd = MAX_SPEED;
    arn_rng = 0x5A;
    spcBoot();   // uruchomienie sterownika dzwieku (chwile trwa)
    spcSetBank(&SOUNDBANK__5);   // bank muzyki zajmuje 6 bankow ROM (z muzyka Lucifero) - od ostatniego
    spcSetBank(&SOUNDBANK__4);
    spcSetBank(&SOUNDBANK__3);
    spcSetBank(&SOUNDBANK__2);
    spcSetBank(&SOUNDBANK__1);
    spcSetBank(&SOUNDBANK__0);
    load_graphics();
    init_sound();
    msu_present = msu_detect();
    music_state = MUS_OFF;
    music_want = 0;
    init_state();
    save_read();   // odblokowane moce z SRAM
    consoleDrawText(0, 31, "A");   // wiersz poza ekranem: odczyt atrybutow znaku czcionki
    txt_base = scr_txt_font_map[(31 * 32) * 2] | (scr_txt_font_map[(31 * 32) * 2 + 1] << 8);
    txt_base -= 'A' - 32;
    consoleDrawText(0, 31, " ");

    for (i = 0; i < SPR_COUNT; i++)
        oamSetEx(i * 4, OBJ_SMALL, OBJ_SHOW);

    show_title(1);

    while (1)
    {
        // Pady sa odczytywane automatycznie w VBlank
        pad0 = padsCurrent(0);
        pad1 = padsCurrent(1);
        pad0_new = padsDown(0);
        pad1_new = padsDown(1);
        if (demo)   // pokaz: dowolny przycisk wraca do tytulu; koniec meczu albo 45 s tez
        {
            if (state == ST_OVER)
                demo_over++;
            if ((pad0_new | pad1_new) || --demo_t == 0 || demo_over > 150)
            {
                end_demo();
                pad0 = pad1 = pad0_new = pad1_new = 0;
            }
            else
                demo_ai();
        }

        switch (state)
        {
        case ST_TITLE:
            update_title();
            break;

        case ST_DIALOG:
            dlg_update();
            break;

        case ST_SSELECT:
            update_story_select();
            break;

        case ST_RESULT:
            storm_idle(1);
            update_result();
            break;

        case ST_THEEND:
            update_the_end();
            break;

        case ST_NAME:
            update_name_entry();
            break;

        case ST_DIFF:
            update_difficulty();
            break;

        case ST_HISCORE:
            update_hiscore();
            break;

        case ST_CHARS:
            update_chars();
            break;

        case ST_POINTS:
            update_points();
            break;

        case ST_SELECT:
            update_select();
            break;

        case ST_SERVE:
            arm_input(0, pad0_new);
            switch_power(0, pad0_new);
            if (two_players)
                switch_power(1, pad1_new);
            if (two_players)
                arm_input(1, pad1_new);
            update_heights_timers();
            update_paddles();
            update_twins();
            update_storm();
            update_arena();
            if (--timer == 0)
                launch_ball();
            draw_sprites();
            break;

        case ST_PLAY:
            if ((pad0_new | pad1_new) & KEY_START)
            {
                state = ST_PAUSE;
                music_want = 0;
                if (spc_mus == 2)
                    pause_cmd = (pause_cmd == 2) ? 0 : 1;   // wyslemy w spokojnej chwili
                consoleDrawText(13, 12, "PAUSE");
                break;
            }
            arm_input(0, pad0_new);
            switch_power(0, pad0_new);
            if (two_players)
                switch_power(1, pad1_new);
            if (two_players)
                arm_input(1, pad1_new);
            update_heights_timers();
            update_paddles();
            update_twins();
            update_storm();
            update_arena();
            update_ball();
            if (state == ST_PLAY)
            {
                update_xballs();
                update_fake();
            }
            update_tail();
            if (state == ST_PLAY || state == ST_SERVE)
                draw_sprites();
            else   // po ostatnim punkcie pilki zostaja schowane
            {
                for (i = 0; i < TAIL_LEN; i++)
                {
                    hide_sprite(SPR_TAIL + i * 4);
                    hide_sprite(SPR_TAIL2 + i * 4);
                    hide_sprite(SPR_TAIL3 + i * 4);
                    hide_sprite(SPR_TAIL4 + i * 4);
                }
                hide_sprite(SPR_BALL2);
                hide_sprite(SPR_BALL3);
                hide_sprite(SPR_BALL4);
                hide_sprite(SPR_FAKE);
                hide_sprite(SPR_FAKE2);
            }
            break;

        case ST_PAUSE:
            storm_idle(0);
            if ((pad0_new | pad1_new) & KEY_START)
            {
                state = ST_PLAY;
                music_want = 1;
                if (spc_mus == 2)
                    pause_cmd = (pause_cmd == 1) ? 0 : 2;   // pauza jeszcze nie wyslana: nic nie robimy
                consoleDrawText(13, 12, "     ");
            }
            break;

        case ST_OVER:
            storm_idle(1);
            if ((pad0_new | pad1_new) & KEY_START)
                show_title(0);
            break;
        }

        update_effects();
        REG_NMI = NMI_ON;   // zabezpieczenie: bez przerwania WaitForVBlank czekalby w nieskonczonosc
        nmi_shadow = NMI_ON;
        WaitForVBlank();  // biblioteka kopiuje wtedy OAM i bufor tekstu
        vblank_tasks();
        sound_tick();     // najwyzej jeden nowy dzwiek co 2 klatki
        snd_process();    // przesyla dzwieki do SPC700 (zaraz po VBlank - patrz snd_process)
        music_update();   // obsluga MSU-1
    }
    return 0;
}
