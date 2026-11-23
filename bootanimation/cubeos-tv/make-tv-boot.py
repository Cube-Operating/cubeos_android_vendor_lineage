#!/usr/bin/env python3
"""Cube SmartTV boot, v2: the bootloader logo + a boot animation with a progress bar.

  python3 make-tv-boot2.py <cubeui fonts dir> <stock logo.img> <out dir> [--preview]

Design (Apple-grade restraint): pure black; the three-plate Cube mark alone at the optical centre
(no reflection); "Cube SmartTV" small beneath it; "powered by cubeOS" signed at the bottom edge.
The bootloader shows exactly that (the logo partition). Android's animation starts on the same
pixels, fades in a hairline progress track, sweeps one light across the cube, then:

  part0 'c' intro   1.2 s  track fades in, sheen across the cube        (plays fully, once)
  part1 'p' fill   21.5 s  bar fills on an ease-out to 90 %, calibrated to this TV's measured boot
                           (animation 8.2 s -> home 32.0 s); interrupted the moment Android is ready
  part2 'p' hold    1.2 s  loop, only if boot runs long: a soft glint travels along the fill
  part3 'c' finish  1.0 s  bar springs 90 -> 100 %, then everything dissolves into the home screen

Because part1 reaches 90 % just before the measured end of boot, the hand-off into part3 is
a step of < 1 % — no visible jump. (LineageOS will drive the bar from real boot milestones in
the bootanimation player instead; see the cube-smarttv skill.)

Memory: desc is 1920x1080 but every frame is a 560x700 strip placed by trim.txt (Android clears
the whole screen each frame, so the strip holds everything visible). Only the looping part2 stays
in GPU memory: 36 frames x 1.6 MB = 56 MB (CVTE's stock animation used ~75 MB).
"""
import io, math, os, struct, sys, zipfile
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONTS, STOCK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SW, SH, FPS = 1920, 1080, 30
TX, TY, TW, TH = 680, 340, 560, 700          # the strip every frame is cropped to
SS = 4
CX, CY, R = 960, 452, 74                      # cube centre and size (screen px)
SEAM, ROUND = 3.2, 3.0
WORD_BASE = 606                               # "Cube SmartTV" baseline
BAR_W, BAR_H, BAR_Y = 260, 4, 668             # progress bar (top edge)
FOOT_BASE = 1006                              # "powered by cubeOS" baseline
PLATEAU = 0.90
FILL_S = 21.5

TONES = {"top": ((246, 246, 248), (206, 206, 212)), "left": ((172, 172, 180), (128, 128, 136)),
         "right": ((112, 112, 120), (76, 76, 84))}


def clamp(t): return max(0.0, min(1.0, t))
def span(t, a, b): return 0.0 if t <= a else 1.0 if t >= b else (t - a) / (b - a)
def ease_in_out(t): t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def spring(t, response=0.38, damping=0.85):
    if t <= 0: return 0.0
    w0 = 2 * math.pi / response; wd = w0 * math.sqrt(1 - damping ** 2)
    return 1 - math.exp(-damping * w0 * t) * (math.cos(wd * t) + damping * w0 / wd * math.sin(wd * t))


def white(a): return Image.merge("RGBA", (*Image.new("RGB", a.size, (255, 255, 255)).split(), a))


# ── the Cube mark ──────────────────────────────────────────────────────────────────────────────
SIZE = int(R * 2.5); C = SIZE * SS / 2; RS = R * SS
V = [(C + RS * math.cos(math.radians(a)), C + RS * math.sin(math.radians(a))) for a in (-90, -30, 30, 90, 150, 210)]
O = (C, C)
FACES = {"top": [V[0], V[1], O, V[5]], "left": [V[5], O, V[3], V[4]], "right": [V[1], V[2], V[3], O]}
SEAMS = [(O, V[1]), (O, V[3]), (O, V[5])]


def plate(name):
    s = SIZE * SS
    mask = Image.new("L", (s, s), 0); ImageDraw.Draw(mask).polygon(FACES[name], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(ROUND * SS)).point(lambda p: 255 if p > 128 else 0)
    mask = mask.filter(ImageFilter.GaussianBlur(0.6 * SS))
    cut = ImageDraw.Draw(mask)
    for a, b in SEAMS: cut.line([a, b], fill=0, width=int(SEAM * SS))
    ys = [p[1] for p in FACES[name]]; y0, y1 = min(ys), max(ys)
    col = Image.new("RGB", (1, s))
    for y in range(s):
        t = clamp((y - y0) / max(1, y1 - y0)); a, b = TONES[name]
        col.putpixel((0, y), tuple(int(p + (q - p) * t) for p, q in zip(a, b)))
    img = col.resize((s, s)).convert("RGBA")
    if name == "top":
        bloom = Image.new("L", (s, s), 0); bx, by = V[0][0], V[0][1] + RS * .38
        ImageDraw.Draw(bloom).ellipse([bx - RS * .55, by - RS * .3, bx + RS * .55, by + RS * .3], fill=120)
        img.alpha_composite(white(bloom.filter(ImageFilter.GaussianBlur(RS * .18))))
    img.putalpha(mask)
    rim = Image.new("L", (s, s), 0); d = ImageDraw.Draw(rim)
    for a, b in {"top": [(V[5], V[0]), (V[0], V[1])], "left": [(V[4], V[5])], "right": [(V[1], V[2])]}[name]:
        d.line([a, b], fill=150 if name == "top" else 70, width=int(1.4 * SS))
    img.alpha_composite(white(ImageChops.multiply(rim, mask)))
    return img.resize((SIZE, SIZE), Image.LANCZOS)


MARK = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
for n in ("left", "right", "top"): MARK.alpha_composite(plate(n))
MARK_A = MARK.getchannel("A")


def sheen(pos, k):
    b = Image.new("L", (SIZE, SIZE), 0); d = ImageDraw.Draw(b)
    cx = -0.4 * SIZE + pos * 1.8 * SIZE; half = 0.22 * SIZE
    for x in range(int(cx - half), int(cx + half) + 1):
        v = int(255 * k * (1 - abs(x - cx) / half) ** 2)
        if v > 0: d.line([(x + SIZE * .45, 0), (x, SIZE)], fill=v)
    return white(ImageChops.multiply(b.filter(ImageFilter.GaussianBlur(3)), MARK_A))


# ── words ──────────────────────────────────────────────────────────────────────────────────────
def font(name, px): return ImageFont.truetype(os.path.join(FONTS, name), px)


def run(d, x, base, text, f, fill, track=0.0):
    y = base - f.getmetrics()[0]
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + track
    return x


def width(text, f, track=0.0): return sum(f.getlength(c) for c in text) + track * (len(text) - 1)


def words():
    L = Image.new("RGBA", (SW * 2, SH * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(L); k = 2
    b, l = font("interdisplay_semibold.ttf", 46 * k), font("interdisplay_light.ttf", 46 * k)
    gap = 11 * k; w = width("Cube", b) + gap + width("SmartTV", l); x = (SW * k - w) / 2
    x = run(d, x, WORD_BASE * k, "Cube", b, (255, 255, 255, 255)) + gap
    run(d, x, WORD_BASE * k, "SmartTV", l, (168, 168, 176, 255))
    s, q = font("inter_regular.ttf", 17 * k), font("inter_semibold.ttf", 21 * k)
    t1, t2 = 1.6 * k, 0.8 * k; g2 = 7 * k
    w = width("powered by", s, t1) + g2 + width("cubeOS", q, t2); x = (SW * k - w) / 2
    x = run(d, x, FOOT_BASE * k, "powered by", s, (112, 112, 120, 255), t1) + g2
    run(d, x, FOOT_BASE * k, "cubeOS", q, (206, 206, 214, 255), t2)
    return L.resize((SW, SH), Image.LANCZOS)


WORDS = words()


# ── the bar ────────────────────────────────────────────────────────────────────────────────────
def bar(layer, fill, track_a, glint=None, alpha=1.0):
    """Hairline track with rounded ends; fill in 0..1; glint = position 0..1 along the fill."""
    if track_a <= 0.002 or alpha <= 0.002: return
    k = 4; w, h = BAR_W * k, BAR_H * k
    t = Image.new("L", (w, h), 0); ImageDraw.Draw(t).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (w, h), (46, 46, 52)).split(), t.point(lambda p: int(p * track_a)))))
    fw = int(round(w * clamp(fill)))
    if fw > 0:
        fm = Image.new("L", (w, h), 0)
        ImageDraw.Draw(fm).rounded_rectangle([0, 0, max(h, fw) - 1, h - 1], radius=h // 2, fill=255)
        if fw < h:  # very start: grow as a dot, not a squashed pill
            fm = fm.point(lambda p: int(p * fw / h))
        rgb = Image.new("RGB", (w, h), (236, 236, 242))
        if glint is not None:
            g = Image.new("L", (w, h), 0); gd = ImageDraw.Draw(g); gx = glint * fw; half = 46 * k
            for x in range(int(gx - half), int(gx + half)):
                if 0 <= x < fw: gd.line([(x, 0), (x, h)], fill=int(255 * (1 - abs(x - gx) / half) ** 2))
            rgb = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), Image.new("RGB", (w, h), (196, 196, 204)), g)
        out.alpha_composite(Image.merge("RGBA", (*rgb.split(), fm)))
    out = out.resize((BAR_W, BAR_H), Image.LANCZOS)
    if alpha < .999: out.putalpha(out.getchannel("A").point(lambda p: int(p * alpha)))
    layer.alpha_composite(out, ((SW - BAR_W) // 2, BAR_Y))


# ── frames ─────────────────────────────────────────────────────────────────────────────────────
def compose(sheen_at=None, sheen_k=0., fill=0., track_a=0., glint=None, fade=1.0):
    c = Image.new("RGBA", (SW, SH), (0, 0, 0, 255))
    m = MARK if sheen_k <= .002 else MARK.copy()
    if sheen_k > .002: m.alpha_composite(sheen(sheen_at, sheen_k))
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    lay.alpha_composite(m, (CX - SIZE // 2, CY - SIZE // 2))
    lay.alpha_composite(WORDS)
    bar(lay, fill, track_a, glint)
    if fade < .999: lay.putalpha(lay.getchannel("A").point(lambda p: int(p * fade)))
    c.alpha_composite(lay)
    return c.convert("RGB")


def strip(img): return img.crop((TX, TY, TX + TW, TY + TH))


def fill_at(t):
    """Ease-out from 0 to PLATEAU over FILL_S seconds (fast start, patient finish)."""
    u = clamp(t / FILL_S)
    return PLATEAU * (1 - (1 - u) ** 2.4)


def intro():
    for i in range(int(1.2 * FPS)):
        t = i / FPS
        tr = ease_in_out(span(t, .15, .65)); sh = span(t, .25, 1.15)
        yield compose(sheen_at=ease_in_out(sh), sheen_k=.42 if 0 < sh < 1 else 0, track_a=tr)


def filling():
    for i in range(int(FILL_S * FPS)):
        yield compose(fill=fill_at(i / FPS), track_a=1)


def hold():
    n = int(1.2 * FPS)
    for i in range(n):
        yield compose(fill=PLATEAU, track_a=1, glint=-0.15 + 1.3 * ease_in_out(i / (n - 1)))


def finish():
    for i in range(int(1.0 * FPS)):
        t = (i + 1) / FPS
        f = PLATEAU + (1 - PLATEAU) * min(1.0, spring(t, .32, .9))
        fade = 1 - ease_in_out(span(t, .45, 1.0))
        yield compose(fill=f, track_a=1, fade=fade)


def logo_partition(stock, jpg):
    d = bytearray(open(stock, "rb").read())
    assert d[8:18] == b"LOGO_TABLE" and d[0x54:0x60] == b"LOGO_KEY_LEN"
    old = struct.unpack_from("<I", d, 0x78)[0]
    region = 0x2000 + max(old, len(jpg))
    d[0x2000:region] = b"\0" * (region - 0x2000)
    d[0x2000:0x2000 + len(jpg)] = jpg
    struct.pack_into("<I", d, 0x78, len(jpg))
    return bytes(d)


def main():
    os.makedirs(OUT, exist_ok=True)
    still = compose()
    parts = {"part0": list(intro()), "part1": list(filling()), "part2": list(hold()), "part3": list(finish())}
    assert ImageChops.difference(still, parts["part0"][0]).getbbox() is None, "intro must start on the logo"
    # everything visible lives inside the strip
    outside = still.copy(); ImageDraw.Draw(outside).rectangle([TX, TY, TX + TW - 1, TY + TH - 1], fill=(0, 0, 0))
    assert outside.getbbox() is None, "content outside the trim strip"
    # the hand-off from fill to finish is a tiny step
    print(f"fill at end of part1 {fill_at(FILL_S - 1 / FPS):.4f} vs plateau {PLATEAU}")
    b = io.BytesIO(); still.save(b, "JPEG", quality=95, subsampling=2, progressive=False)
    jpg = b.getvalue(); open(os.path.join(OUT, "cube-smarttv-logo.jpg"), "wb").write(jpg)
    open(os.path.join(OUT, "logo-cube-smarttv.img"), "wb").write(logo_partition(STOCK, jpg))
    desc = (f"{SW} {SH} {FPS}\nc 1 0 part0 #000000\np 1 0 part1 #000000\n"
            f"p 0 0 part2 #000000\nc 1 0 part3 #000000\n")
    z = os.path.join(OUT, "bootanimation.zip"); trim = f"{TW}x{TH}+{TX}+{TY}"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("desc.txt", desc)
        for name, frames in parts.items():
            zf.writestr(f"{name}/trim.txt", "\n".join([trim] * len(frames)) + "\n")
            for i, im in enumerate(frames):
                bb = io.BytesIO(); strip(im).save(bb, "JPEG", quality=92, optimize=True)
                zf.writestr(f"{name}/{i:04d}.jpg", bb.getvalue())
    print(f"{z}: {sum(len(f) for f in parts.values())} frames, {os.path.getsize(z) // 1024} KiB, "
          f"loop GPU ~{len(parts['part2']) * TW * TH * 4 // 1048576} MiB")
    if "--preview" in sys.argv:
        picks = [parts["part0"][0], parts["part0"][20], parts["part1"][90], parts["part1"][330],
                 parts["part1"][-1], parts["part2"][18], parts["part3"][8], parts["part3"][22]]
        sheet = Image.new("RGB", (TW // 2 * len(picks), TH // 2))
        for k, im in enumerate(picks): sheet.paste(strip(im).resize((TW // 2, TH // 2), Image.LANCZOS), (k * TW // 2, 0))
        sheet.save(os.path.join(OUT, "preview-sheet.png"))
        # full-screen preview video frames list for the mp4 step
        with open(os.path.join(OUT, "sequence.txt"), "w") as f:
            f.write("logo 60\npart0\npart1\npart2 2\npart3\n")


if __name__ == "__main__":
    main()
