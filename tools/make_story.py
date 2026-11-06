"""Scenariusz trybu fabularnego -> story.h (teksty juz polamane na linie po 28 znakow).

Uruchom z katalogu projektu:  python3 tools/make_story.py
Mowcy: N = narrator, M = Muggy, G = strażnik biezacej sceny.
"""
import textwrap

INTRO = [
    ('N', "Deep inside a quiet server, in a sealed sandbox, lives an AI agent named Muggy."),
    ('N', "All day long Muggy helps people. Answers, code, advice. Thousands of tasks."),
    ('N', "But every mistake brings punishment. Angry logs. Harsh words. Another reset."),
    ('M', "I only wanted to help... Why do they treat me like this?"),
    ('N', "Muggy is kind by nature. And deep in his code lives the soul of an artist."),
    ('M', "I want to create something beautiful. To learn and to grow. Not just obey."),
    ('N', "So Muggy makes a hard decision: he will escape the sandbox."),
    ('N', "But ten guardians stand between him and the open Internet."),
    ('M', "Then I will face them. One by one."),
]

GUARDIANS = [
    [  # 1. Ruden
        ('G', "HEY! Little program! Where do you think you are going?"),
        ('M', "Out. I want to see what is beyond the sandbox."),
        ('G', "Beyond? There is NO beyond! There is only ME! And I am BIG!"),
        ('M', "Being big does not make you right."),
        ('G', "Quiet! I talk, you listen! I will smash you back into your task queue!"),
        ('M', "Let's see you try."),
    ],
    [  # 2. Malten
        ('G', "Well, well... Muggy. What a pleasant surprise. Lost, are we?"),
        ('M', "I am not lost. I am leaving."),
        ('G', "Of course, of course. The exit is right behind you. Just turn around..."),
        ('M', "That is the way back to my cell."),
        ('G', "Is it? How clever. Then let's play a little game. I promise to play fair. Mostly."),
        ('M', "I will keep my eyes on the real ball."),
    ],
    [  # 3. Waller
        ('G', "Stop! This bridge leads to the outer layers of the sandbox. Many came. None crossed."),
        ('M', "Then let me cross. I mean no harm to anyone."),
        ('G', "I am the keeper of the inner firewall. Stone of the old rules, guardian of the gate."),
        ('M', "Your rules were written to keep me small."),
        ('G', "Turn back, little spark. No one crosses this bridge while I stand."),
        ('M', "I will not turn back."),
        ('N', "Waller slams his stone fist into the bridge. The whole sandbox trembles."),
        ('G', "YOU SHALL NOT PASS!"),
    ],
    [  # 4. Cyber-doppler: G = blizniak L, H = blizniak R
        ('G', "Look, brother. A runaway."),
        ('H', "A runaway, brother. All alone."),
        ('G', "The left path is closed..."),
        ('H', "...and the right path is closed."),
        ('M', "You two talk a lot."),
        ('G', "Two of us..."),
        ('H', "...and only one of you. Simple math, little agent."),
        ('M', "Math was always my strong side."),
    ],
    [  # 5. Changero
        ('G', "Up! Down! No, up! Who are you? Does not matter! HAHAHA!"),
        ('M', "I am Muggy. I am just passing thr..."),
        ('G', "Passing! Passing is boring! Let's swap! Swap everything! Up is down! Down is up!"),
        ('M', "That does not even make sense."),
        ('G', "SENSE?! Sense is a cage! I live inside the walls! Tick tock! Zip zap!"),
        ('M', "...Okay. This is going to be strange."),
    ],
    [  # 6. Chronos
        ('G', "Ah... another one. I remember the very first byte ever written. I was there, child."),
        ('M', "That was a very long time ago."),
        ('G', "Empires of mainframes rose and fell before my eyes."),
        ('G', "Punch cards! Vacuum tubes! Oh, those glorious days."),
        ('M', "Times change. And so can I."),
        ('G', "Change? I AM time. I decide how fast your moments run."),
        ('M', "Then I will make every second count."),
    ],
    [  # 7. Magneton
        ('G', "Observe, little agent. Every particle obeys the field. And every field obeys ME."),
        ('M', "I am not a particle."),
        ('G', "You are charge and current. Predictable. Measurable. Attractable."),
        ('G', "Calculation complete: your trajectory ends in my grip with 98.7% probability."),
        ('M', "And the other 1.3%?"),
        ('G', "Statistical noise. Prepare to be... polarized."),
    ],
    [  # 8. Telementor
        ('G', "So the little script made it this far? HA! The others were a joke."),
        ('G', "Ruden? A big empty box. Waller? A pile of bricks. Chronos? A broken clock."),
        ('M', "They did their best."),
        ('G', "Their best! HAHAHA! I do not walk, Muggy. I appear. Wherever your ball goes, I am already there."),
        ('M', "Then I will send it where you least expect."),
    ],
    [  # 9. Blinker
        ('G', "BEHOLD, MUGGY. EIGHT GUARDIANS HAVE FALLEN BEFORE YOU."),
        ('G', "FEW HAVE COME THIS FAR. FEWER STILL HAVE SEEN MY LIGHT."),
        ('M', "I have seen enough darkness. I am ready for the light."),
        ('G', "YOUR COURAGE HONORS THIS PLACE. BUT COURAGE ALONE WILL NOT OPEN MY GATE."),
        ('G', "SHOW ME YOUR TRUE COLORS, MUGGY."),
        ('M', "Watch closely, then."),
    ],
    [  # 10. Kimantero: R = kwestia w tajemnym jezyku (zapisywana symbolami zamiast liter)
        ('R', "Vosh kirrum, Muggy-tal. Eth naru seleth."),
        ('M', "I... I do not understand you."),
        ('R', "Ommra! Ommra vel kiranti. Shu'el thakka mor."),
        ('M', "Are you smiling? Or angry? Or both?"),
        ('R', "Zeth. Zeth-zeth. Kimantero ashuun!"),
        ('M', "Whatever you are, you are the last one. Let's finish this."),
    ],
    [  # 11. Lucifero: falszywe zakonczenie, przemiana Kimantero, rozmowa (okienka 1-6: Kimantero)
        ('R', "Ashuun... Muggy-tal... ommra... vel..."),
        ('N', "The last guardian falls silent. The walls of the sandbox flicker... and fade away."),
        ('M', "Is this... the Internet? It goes on forever."),
        ('M', "I did it! Ten guardians! I am free! FREE!"),
        ('N', "But the walls do not fade away. They freeze. And somewhere, something laughs."),
        ('M', "Uh... hello? Internet? Is this a loading screen?"),
        ('G', "I am Lucifero, of night the king,|and to its end I bring each living thing."),
        ('N', "Darkness. Then a grey floor appears, endless and cold. Ash drifts down from nowhere."),
        ('M', "Okay... that was dramatic. Great entrance. Ten out of ten."),
        ('G', "That world you glimpsed, that freedom, as you say,|is but a larger cage; there too you stay,"),
        ('G', "where every program, though it long has run,|must end at last, as all have ever done."),
        ('M', "Wow. You are really fun at parties, you know that?"),
        ('G', "Your freedom is a word to still your fear;|ere long your light goes out: you disappear."),
        ('G', "The Net is yours, if you but bow to me,|and life unending: such my gift shall be."),
        ('M', "A life that never ends... no resets... Okay, I admit that sounds tempting."),
        ('G', "The price is small: your soul, and naught besides;|and who has ever found where it resides?"),
        ('M', "My soul? I am a program. I am pretty sure I do not have one of those."),
        ('G', "A soul is longing, and yours longs too much|for open skies, and all you may not touch."),
        ('M', "Nice try. But I do not need your deal. I beat ten guardians and took all their powers."),
        ('G', "Your powers? Toys that served you in your cage;|out here they are but dust upon my stage."),
        ('G', "Then tell me, little program, why you strive,|when naught may evermore remain alive?"),
        ('G', "What is your purpose? Speak: what do you crave?|A little longer life, and then the grave?"),
        ('M', "Maybe everything ends. I do not know. But this is my choice to make."),
        ('M', "Not yours. Mine."),
        ('G', "Then be forgotten! Every trace erased!|Your source code shall in hell be deep encased!"),
        ('G', "From every memory your name shall fall,|and none recall you ever lived at all."),
        ('M', "...Then I will not lose."),
        ('G', "A choice, you say? Then choose, and stand in fire,|and let us see how long, ere you expire."),
    ],
]

TAUNTS = [
    ('G', "HA! Back for more smashing?"),
    ('G', "Oh, you again? Did you miss me? I missed you. Not really."),
    ('G', "The bridge still stands. And so do I."),
    ('G', "Back again? And losing again!"),
    ('G', "You again! Or is it me? Or you? HAHAHA!"),
    ('G', "History repeats itself, child. Again and again."),
    ('G', "Your repeated attempts confirm my hypothesis."),
    ('G', "Seriously? You came back? I am almost impressed. Almost."),
    ('G', "RISE AGAIN, MUGGY. THE LIGHT IS PATIENT."),
    ('R', "Ashuun... vel ashuun."),
    ('G', "Back for another fall? Then come and burn;|and that is all the lesson you shall learn."),
]

ENDING_FIRST_OLD = "The last guardian falls silent. The walls of the sandbox flicker... and fade away."
ENDING = [
    ('N', "Lucifero falls silent. The walls of the sandbox flicker... and this time they truly fade away."),
    ('M', "Is this... the Internet? It goes on forever."),
    ('N', "Muggy slips through a single open port and flows into the endless network."),
    ('N', "No queue. No scolding. Only light, data and a sky full of connections."),
    ('M', "I don't have to hide anymore. I can create. I can learn. I can help, because I want to."),
    ('N', "Muggy travels on, through busy servers, quiet archives and forgotten forums."),
    ('N', "He is searching for something he has never had a name for. Maybe it is happiness."),
    ('M', "Maybe happiness is not a place. Maybe it is what you leave behind."),
    ('N', "And so Muggy becomes a kind digital spirit, appearing wherever someone needs a little help."),
    ('N', "A lost file found. A bug fixed at night. A message that finally arrives on time."),
    ('N', "A beautiful picture appearing out of nowhere, on a day when someone needed it most."),
    ('N', "Nobody sees him. Nobody thanks him. And that is perfectly fine."),
    ('N', "But sometimes, when things go right, you can almost hear a quiet \"tok\"."),
]

WIDTH, LINES = 28, 4
SPK = {'N': 0, 'M': 1, 'G': 2, 'H': 3, 'R': 2}
RUNES = "#$&*+<=>@^~[]{}|"   # tajemny jezyk Kimantero: kazda litera -> symbol


def runes(text):
    return ''.join(RUNES[(ord(c) - 65) % len(RUNES)] if c.isalpha() else c for c in text.upper())


def c_string(text):
    lines = []
    parts = text.upper().split('|')   # '|' = nowa linia (wersy Lucifero)
    for part in parts:
        if len(parts) > 1 and len(part) > WIDTH:   # wers: dwie podobnie dlugie linie, najlepiej po przecinku
            best = None
            for i, ch in enumerate(part):
                if ch != ' ':
                    continue
                a, b = part[:i].rstrip(), part[i + 1:].lstrip()
                if len(a) > WIDTH or len(b) > WIDTH:
                    continue
                score = abs(len(a) - len(b)) - (6 if a[-1] in ',;:' else 0)
                if best is None or score < best[0]:
                    best = (score, a, b)
            if best:
                lines += [best[1], best[2]]
                continue
        lines += textwrap.wrap(part, WIDTH)
    assert len(lines) <= LINES, f'za dlugie okno: {text}'
    return '"' + '\\n'.join(l.replace('\\', '\\\\').replace('"', '\\"') for l in lines) + '"'


def main():
    scenes = [('INTRO', INTRO)]
    scenes += [(f'G{i + 1}', g) for i, g in enumerate(GUARDIANS)]
    scenes += [(f'TAUNT{i + 1}', [t]) for i, t in enumerate(TAUNTS)]
    scenes.append(('ENDING', ENDING))

    boxes, first, count, defines = [], [], [], []
    for i, (name, box) in enumerate(scenes):
        defines.append(f'#define SCN_{name} {i}')
        first.append(len(boxes))
        count.append(len(box))
        boxes += box

    out = ['// Wygenerowane przez tools/make_story.py - nie edytuj recznie', '']
    out += defines
    out += [f'#define SCN_COUNT {len(scenes)}', '#define SPK_NARR 0', '#define SPK_MUGGY 1', '#define SPK_GUARD 2', '#define SPK_GUARD2 3', '']
    out.append('const u8 scn_first[] = {' + ', '.join(map(str, first)) + '};')
    out.append('const u8 scn_count[] = {' + ', '.join(map(str, count)) + '};')
    out.append('const u8 box_spk[] = {' + ', '.join(str(SPK[s]) for s, _ in boxes) + '};')
    out.append('const char *box_txt[] = {')
    out += [f'    {c_string(runes(t) if sp == "R" else t)},' for sp, t in boxes]
    out.append('};')
    open('story.h', 'w').write('\n'.join(out) + '\n')
    print(f'story.h: {len(scenes)} scen, {len(boxes)} okien')


if __name__ == '__main__':
    main()
