#!/usr/bin/env python3
"""Render the Cube Phone's boot animation (CubeOS 2.x): bootanimation-cube.zip.

  pip install pillow
  ./make-bootanimation-cube.py [--preview]   # writes bootanimation-cube.zip (and preview-cube.png) here

CubeOS 1.x (ContiSX phones) keeps make-bootanimation.py / bootanimation.zip.

It plays after the bootloader's logo: Runyee's signed Cube logo (root-of-trust/logo-stock.img,
"Cube / powered by cubeOS"). The animation is 720x1280 centred on the 720x1600 screen, so its
first frame is that logo's rows 160-1440 (cube-handoff.png): the phone shows no cut when Android
takes over the screen, and the logo then dissolves into the new mark.

Design (720x1280, 60 fps, pure black, one mark, no words):
  * The Cube mark is three machined plates (top, left, right) of an isometric cube, separated by
    fine black seams, lit from the upper left like brushed titanium.
  * part0 intro (2.4 s, once): the bootloader's logo softly dissolves (0.45 s) as the plates glide in along the cube's own axes on Cube Motion's
    `settle` spring (response 0.38 s, damping 0.85), a few ms apart; as they lock, light runs along
    the Y-shaped seams, then a soft sheen sweeps across the faces.
  * part1 loop (2.4 s, until boot completes): nothing moves; the light slowly circles the cube, so
    the faces trade brightness as if it were turning. Calm, and it shows the phone is working.
  * part2 outro (0.7 s, once): the plates drift a little apart while the mark zooms through
    (grows 8 %, softens, dissolves) into black, and the lock screen arrives.
The last intro frame (`still()`) is the bootloader logo, at the same place, so power-on, the
animation and the lock screen hand off without a jump (device/cube/ygf_f35/tools/make-logo.py).
"""
import io
import math
import os
import sys
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 720, 1280, 60
SS = 4                 # supersampling for the plates
CX, CY = W // 2, 616   # the mark's centre: a touch above centre, where the eye rests
R = 74                 # centre to hexagon vertex (the mark is 2R tall, ~1.73R wide)
SEAM = 3.4             # black seam between plates, px
ROUND = 3.0            # corner softening of each plate, px (machined, not sharp)
TRAVEL = 58            # how far each plate starts from home, px
REFLECT = 0.17         # the polished-black floor's reflection strength
REFLECT_GAP = 10       # gap between the mark and its reflection, px

# Plate tones (top lightest, left mid, right in shade), from the back edge to the front edge.
TONES = {
    "top":   ((246, 246, 248), (206, 206, 212)),
    "left":  ((172, 172, 180), (128, 128, 136)),
    "right": ((112, 112, 120), (76, 76, 84)),
}
# Direction each plate travels in from (its outward normal on screen).
FROM = {"top": (0.0, -1.0), "left": (-0.866, 0.5), "right": (0.866, 0.5)}


def clamp(t):
    return max(0.0, min(1.0, t))


def span(t, a, b):
    return 0.0 if t <= a else 1.0 if t >= b else (t - a) / (b - a)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def spring(t, response=0.38, damping=0.85):
    """Cube Motion spring (cubeSpring): 0 -> 1 with a small, physical overshoot."""
    if t <= 0:
        return 0.0
    w0 = 2 * math.pi / response
    wd = w0 * math.sqrt(1 - damping ** 2)
    return 1 - math.exp(-damping * w0 * t) * (math.cos(wd * t) + damping * w0 / wd * math.sin(wd * t))


# ── geometry ───────────────────────────────────────────────────────────────────────────────────

SIZE = int(R * 2.5)            # plate canvas (1x), centred on the cube's centre
C = SIZE * SS / 2
RS = R * SS
V = [(C + RS * math.cos(math.radians(a)), C + RS * math.sin(math.radians(a))) for a in (-90, -30, 30, 90, 150, 210)]
O = (C, C)
FACES = {
    "top":   [V[0], V[1], O, V[5]],
    "left":  [V[5], O, V[3], V[4]],
    "right": [V[1], V[2], V[3], O],
}
SEAMS = [(O, V[1]), (O, V[3]), (O, V[5])]


def _gradient(poly, top_rgb, bottom_rgb):
    ys = [p[1] for p in poly]
    y0, y1 = min(ys), max(ys)
    s = SIZE * SS
    col = Image.new("RGB", (1, s))
    for y in range(s):
        t = clamp((y - y0) / max(1, y1 - y0))
        col.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(top_rgb, bottom_rgb)))
    return col.resize((s, s))


def plate(name):
    """One plate as RGBA (1x): gradient face, seams cut away, a fine light rim on its top edges."""
    s = SIZE * SS
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).polygon(FACES[name], fill=255)
    # Soften the corners (blur + threshold rounds every vertex), then cut the seams.
    mask = mask.filter(ImageFilter.GaussianBlur(ROUND * SS)).point(lambda p: 255 if p > 128 else 0)
    mask = mask.filter(ImageFilter.GaussianBlur(0.6 * SS))
    cut = ImageDraw.Draw(mask)
    for a, b in SEAMS:
        cut.line([a, b], fill=0, width=int(SEAM * SS))
    img = _gradient(FACES[name], *TONES[name]).convert("RGBA")
    if name == "top":
        # Where the light lands: a soft bloom towards the back corner of the top plate.
        bloom = Image.new("L", (s, s), 0)
        bx, by = V[0][0], V[0][1] + RS * 0.38
        ImageDraw.Draw(bloom).ellipse([bx - RS * 0.55, by - RS * 0.30, bx + RS * 0.55, by + RS * 0.30], fill=120)
        bloom = bloom.filter(ImageFilter.GaussianBlur(RS * 0.18))
        img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (s, s), (255, 255, 255)).split(), bloom)))
    img.putalpha(mask)
    # Light catches the top plate's two back edges and the side plates' upper edges.
    rim = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(rim)
    edges = {"top": [(V[5], V[0]), (V[0], V[1])], "left": [(V[4], V[5])], "right": [(V[1], V[2])]}[name]
    for a, b in edges:
        d.line([a, b], fill=150 if name == "top" else 70, width=int(1.4 * SS))
    rim = ImageChops.multiply(rim, mask)
    img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (s, s), (255, 255, 255)).split(), rim)))
    return img.resize((SIZE, SIZE), Image.LANCZOS)


PLATES = {n: plate(n) for n in FACES}
HANDOFF = Image.open(os.path.join(HERE, "cube-handoff.png")).convert("RGBA")
UNION = Image.new("L", (SIZE, SIZE), 0)
for p in PLATES.values():
    UNION = ImageChops.lighter(UNION, p.getchannel("A"))


def seam_light(k):
    """The Y-shaped seams lit (0..1): a thin bright line that fades out to the outer vertices."""
    if k <= 0.002:
        return None
    s = SIZE * SS
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    steps = 40
    for a, b in SEAMS:
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            d.line([p0, p1], fill=int(255 * k * (1 - 0.7 * t0)), width=int(2.0 * SS))
    m = m.resize((SIZE, SIZE), Image.LANCZOS)
    glow = m.filter(ImageFilter.GaussianBlur(6)).point(lambda p: min(255, int(p * 1.1)))
    a = ImageChops.lighter(m, glow)
    return Image.merge("RGBA", (*Image.new("RGB", (SIZE, SIZE), (255, 255, 255)).split(), a))


def sheen(pos, k):
    """A soft diagonal band of light across the whole mark."""
    if k <= 0.002:
        return None
    band = Image.new("L", (SIZE, SIZE), 0)
    d = ImageDraw.Draw(band)
    cx = -0.4 * SIZE + pos * 1.8 * SIZE
    half = 0.22 * SIZE
    for x in range(int(cx - half), int(cx + half) + 1):
        v = int(255 * k * (1 - abs(x - cx) / half) ** 2)
        if v > 0:
            d.line([(x + SIZE * 0.45, 0), (x, SIZE)], fill=v)
    band = ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(3)), UNION)
    return Image.merge("RGBA", (*Image.new("RGB", (SIZE, SIZE), (255, 255, 255)).split(), band))


def lit(img, factor):
    """A plate brightened or darkened (the light circling in the loop)."""
    if abs(factor - 1) < 1e-3:
        return img
    rgb = img.convert("RGB").point(lambda p: min(255, int(p * factor)))
    out = rgb.convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


# ── frames ─────────────────────────────────────────────────────────────────────────────────────

def place(canvas, img, dx=0.0, dy=0.0, alpha=1.0, scale=1.0, blur=0.0):
    if img is None or alpha <= 0.002:
        return
    if abs(scale - 1) > 1e-3:
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    if blur > 0.05:
        pad = int(blur * 3) + 2
        big = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
        big.paste(img, (pad, pad))
        img = big.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 0.999:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda p: int(p * alpha)))
    canvas.alpha_composite(img, (round(CX + dx - img.width / 2), round(CY + dy - img.height / 2)))


def frame(progress=None, alpha=None, light=None, seam=0.0, sheen_at=None, sheen_k=0.0,
          spread=0.0, scale=1.0, blur=0.0, fade=1.0, width=W, height=H, cy=None,
          handoff=0.0, handoff_s=1.0, handoff_blur=0.0):
    """One frame. progress/alpha/light: per plate (0..1 home, 0..1 opacity, brightness factor)."""
    global CY
    keep = CY
    if cy is not None:
        CY = cy
    mark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for n in ("left", "right", "top"):
        p = 1.0 if progress is None else progress[n]
        a = (1.0 if alpha is None else alpha[n]) * fade
        f = 1.0 if light is None else light[n]
        ux, uy = FROM[n]
        off = TRAVEL * (1 - p) + spread
        place(mark, lit(PLATES[n], f), ux * off * scale, uy * off * scale, a, scale, blur + 5 * (1 - clamp(p)))
    place(mark, seam_light(seam), alpha=fade, scale=scale, blur=blur)
    if sheen_at is not None:
        place(mark, sheen(sheen_at, sheen_k), alpha=fade, scale=scale, blur=blur)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    if handoff > 0.002:
        # The bootloader's logo, as the phone was showing it, dissolving (slightly receding).
        img = HANDOFF
        if abs(handoff_s - 1) > 1e-3:
            img = img.resize((round(W * handoff_s), round(H * handoff_s)), Image.LANCZOS)
        if handoff_blur > 0.05:
            img = img.filter(ImageFilter.GaussianBlur(handoff_blur))
        if handoff < 0.999:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda p: int(p * handoff)))
        canvas.alpha_composite(img, ((width - img.width) // 2, (height - img.height) // 2))
    # The polished-black floor: the mark mirrored about a line just below it, fading with depth.
    floor = CY + R * scale + REFLECT_GAP
    refl = mark.transpose(Image.FLIP_TOP_BOTTOM)
    fadeout = Image.new("L", (1, height), 0)
    depth = 1.15 * R
    for y in range(height):
        yy = y - (height - 1 - floor) + floor   # the row's position once mirrored about the floor
        t = clamp((yy - floor) / depth)
        fadeout.putpixel((0, y), int(255 * REFLECT * (1 - t) ** 2) if yy >= floor else 0)
    fadeout = fadeout.resize((width, height))
    refl.putalpha(ImageChops.multiply(refl.getchannel("A"), fadeout))
    refl = refl.filter(ImageFilter.GaussianBlur(1.2))
    canvas.alpha_composite(refl, (0, round(2 * floor - (height - 1))))
    canvas.alpha_composite(mark)
    CY = keep
    return canvas.convert("RGB")


STAGGER = {"top": 0.0, "left": 0.07, "right": 0.14}
HOLD = 0.12      # the bootloader's logo, untouched, as Android takes the screen
START = 0.30     # the plates begin while the logo is still dissolving


def intro():
    n = int(2.4 * FPS)
    for i in range(n):
        t = i / FPS
        h = ease_in_out(span(t, HOLD, HOLD + 0.45))
        prog = {k: spring(t - START - d) for k, d in STAGGER.items()}
        alph = {k: ease_out(span(t, START + d, START + d + 0.30)) for k, d in STAGGER.items()}
        lock = START + 0.14 + 0.42       # the last plate is home
        seam = math.sin(math.pi * span(t, lock, lock + 0.55)) * 0.9
        sh = span(t, lock + 0.15, lock + 1.05)
        yield frame(prog, alph, seam=seam, sheen_at=ease_in_out(sh), sheen_k=0.45 if 0 < sh < 1 else 0,
                    handoff=1 - h, handoff_s=1 - 0.04 * h, handoff_blur=6 * h)


def light_at(phase):
    """The light circling the cube: each plate peaks as the light passes its side."""
    centres = {"top": -90.0, "left": 150.0, "right": 30.0}
    out = {}
    for n, c in centres.items():
        a = math.radians(phase * 360 - 135 - c)
        out[n] = 1.0 + 0.09 * math.cos(a)
    return out


def loop():
    n = int(2.4 * FPS)
    base = light_at(0.0)
    for i in range(n):
        cur = light_at(i / n)
        # relative to the resting tones, so the loop's first frame equals the still mark
        yield frame(light={k: cur[k] / base[k] for k in cur})


def outro():
    n = int(0.7 * FPS)
    for i in range(n):
        t = (i + 1) / n
        z = t * t * (3 - 2 * t)
        yield frame(spread=14 * z, scale=1 + 0.08 * z, blur=9 * z, fade=1 - z)


def still(width=W, height=H, cy=CY):
    """The finished mark alone: the bootloader logo and the animation's resting frame."""
    return frame(width=width, height=height, cy=cy)


def main():
    parts = {"part0": list(intro()), "part1": list(loop()), "part2": list(outro())}
    if "--preview" in sys.argv:
        picks = [parts["part0"][0], parts["part0"][22], parts["part0"][34], parts["part0"][50],
                 parts["part0"][66], parts["part0"][100], parts["part1"][70], parts["part2"][24]]
        sheet = Image.new("RGB", (W // 3 * len(picks), H // 3))
        for k, im in enumerate(picks):
            sheet.paste(im.resize((W // 3, H // 3), Image.LANCZOS), (k * W // 3, 0))
        sheet.save(os.path.join(HERE, "preview-cube.png"))
        still().save(os.path.join(HERE, "still-cube.png"))
    desc = f"{W} {H} {FPS}\nc 1 0 part0 #000000\nc 0 0 part1 #000000\nc 1 0 part2 #000000\n"
    out = os.path.join(HERE, "bootanimation-cube.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("desc.txt", desc)
        for name, frames in parts.items():
            for i, img in enumerate(frames):
                b = io.BytesIO()
                img.save(b, "JPEG", quality=92, optimize=True)
                z.writestr(f"{name}/{i:03d}.jpg", b.getvalue())
    total = sum(len(f) for f in parts.values())
    print(f"{out}: {total} frames, {os.path.getsize(out) // 1024} KiB")


if __name__ == "__main__":
    main()
