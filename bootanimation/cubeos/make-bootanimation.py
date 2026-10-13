#!/usr/bin/env python3
"""Render CubeOS's boot animation (bootanimation.zip) — ContiSX, powered by cubeOS.

  pip install pillow
  ./make-bootanimation.py [--preview]     # writes bootanimation.zip (and preview.png) here

Design (720x1280, 60 fps, pure black, everything centred):
  * the "ContiSX" wordmark (Inter Display SemiBold, silver) alone at the centre, and at the foot
    "powered by" over the cubeOS lockup: the cube mark (isometric, faces lit from above, fine light
    edges) beside the "cubeOS" wordmark, optically centred as one unit;
  * part0 intro (2.0 s, played once): the wordmark settles in from 96 % and out of soft focus while a
    light sheen passes across it, then the footer and progress bar appear;
  * part1 loop (2.4 s, until Android has booted): a thin progress bar with a gliding highlight,
    and a gentle sheen across the wordmark once per loop;
  * part2 outro (0.5 s, played once when boot completes): a clean fade to black.
Fonts: Inter Display / Inter from cubeos_apps (cubeui/src/main/res/font), found via FONT_DIR
(defaults to packages/apps/CubeOSApps in the tree). Frames are JPEG, stored uncompressed.
vendor/lineage/config/BoardConfigLineage.mk points TARGET_BOOTANIMATION at the zip.
"""
import io
import math
import os
import sys
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.abspath(os.path.join(HERE, "../../../.."))
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(TREE, "packages/apps/CubeOSApps/cubeui/src/main/res/font"))
W, H, FPS = 720, 1280, 60
SS = 4  # supersampling for the static layers

CX = W // 2
CUBE_R = 13           # footer cube mark "radius" (centre to hexagon vertex)
WORD_Y = 620          # wordmark centre line (a touch above centre, where the eye rests)
BAR_Y = 716           # progress bar centre line
BAR_W, BAR_H = 132, 4
FOOT_Y = 1138         # "powered by" line; the cubeOS lockup below it


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def span(t, a, b):
    """0..1 progress of t through [a, b]."""
    return 0.0 if t <= a else 1.0 if t >= b else (t - a) / (b - a)


# ── static layers ──────────────────────────────────────────────────────────────────────────────

def _gradient_face(size, poly, top_rgb, bottom_rgb, y0, y1):
    """A polygon filled with a vertical gradient (light from above)."""
    grad = Image.new("RGBA", (1, size), (0, 0, 0, 0))
    for y in range(size):
        t = 0.0 if y <= y0 else 1.0 if y >= y1 else (y - y0) / (y1 - y0)
        grad.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(top_rgb, bottom_rgb)) + (255,))
    grad = grad.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    face = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    face.paste(grad, (0, 0), mask)
    return face


def cube_layer():
    """The cube mark: three faces lit from above (gradients), fine light edges, transparent."""
    size = int(CUBE_R * 2.6)
    s = size * SS
    c = s / 2
    r = CUBE_R * SS
    v = [(c + r * math.cos(math.radians(a)), c + r * math.sin(math.radians(a))) for a in (-90, -30, 30, 90, 150, 210)]
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    top_y, mid_y, bot_y = v[0][1], c, v[3][1]
    # Faces lit from above: top brightest, left mid, right in shade (the mark is small, so its
    # tones sit close to the wordmark's silver to read as one lockup).
    img.alpha_composite(_gradient_face(s, [v[0], v[1], (c, c), v[5]], (238, 238, 242), (200, 200, 206), top_y, mid_y))
    img.alpha_composite(_gradient_face(s, [v[5], (c, c), v[3], v[4]], (168, 168, 175), (132, 132, 139), v[5][1], bot_y))
    img.alpha_composite(_gradient_face(s, [v[1], v[2], v[3], (c, c)], (104, 104, 111), (78, 78, 84), v[1][1], bot_y))
    d = ImageDraw.Draw(img)
    lw = max(1, int((1.5 if CUBE_R > 30 else 0.9) * SS))
    for a, b in [(v[i], v[(i + 1) % 6]) for i in range(6)] + [((c, c), v[1]), ((c, c), v[3]), ((c, c), v[5])]:
        d.line([a, b], fill=(255, 255, 255, 105), width=lw)
    d.line([v[5], (c, c), v[1]], fill=(255, 255, 255, 215), width=int((2.0 if CUBE_R > 30 else 1.1) * SS), joint="curve")
    return img.resize((size, size), Image.LANCZOS)


def text_mask(txt, fnt, tracking=0.0):
    """Text as an L mask (supersampled, tracked), tightly cropped."""
    big = ImageFont.truetype(fnt.path, fnt.size * SS)
    widths = [big.getlength(ch) for ch in txt]
    track = tracking * fnt.size * SS
    total = sum(widths) + track * (len(txt) - 1)
    asc, desc = big.getmetrics()
    m = Image.new("L", (int(total) + 8 * SS, asc + desc + 8 * SS), 0)
    d = ImageDraw.Draw(m)
    x = 4 * SS
    for ch, w in zip(txt, widths):
        d.text((x, 4 * SS), ch, font=big, fill=255)
        x += w + track
    m = m.resize((m.width // SS, m.height // SS), Image.LANCZOS)
    return m.crop(m.getbbox())


def silver(mask):
    """Silver vertical gradient through a text mask."""
    w, h = mask.size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        v = int(246 - 52 * (y / max(1, h - 1)))   # #F6F6F8 -> #C2C2C6
        grad.putpixel((0, y), (v, v, min(255, v + 3)))
    img = grad.resize((w, h)).convert("RGBA")
    img.putalpha(mask)
    return img


def mono(mask, rgb):
    img = Image.new("RGBA", mask.size, rgb + (0,))
    img.putalpha(mask)
    return img


CUBE = cube_layer()
WORD_MASK = text_mask("ContiSX", font("interdisplay_semibold.ttf", 58), tracking=0.01)
WORD = silver(WORD_MASK)
WORD_GLOW = Image.new("RGBA", WORD_MASK.size, (255, 255, 255, 0))
WORD_GLOW.putalpha(WORD_MASK.point(lambda p: int(p * 0.22)).filter(ImageFilter.GaussianBlur(9)))
FOOT_POWERED = mono(text_mask("powered by", font("inter_medium.ttf", 15), tracking=0.06), (142, 142, 147))
FOOT_CUBEOS = mono(text_mask("cubeOS", font("interdisplay_semibold.ttf", 23), tracking=0.01), (236, 236, 240))


def lockup():
    """The cube mark beside the cubeOS wordmark: the mark matches the cap height plus a little
    (as Apple sizes a glyph next to a wordmark), sits on the text's optical centre, with a gap of
    about a fifth of the mark's width."""
    cube = CUBE.crop(CUBE.getbbox())
    h = int(FOOT_CUBEOS.height * 1.22)
    cube = cube.resize((max(1, round(cube.width * h / cube.height)), h), Image.LANCZOS)
    gap = round(cube.width * 0.22)
    w = cube.width + gap + FOOT_CUBEOS.width
    hh = max(cube.height, FOOT_CUBEOS.height)
    img = Image.new("RGBA", (w, hh), (0, 0, 0, 0))
    img.alpha_composite(cube, (0, (hh - cube.height) // 2))
    img.alpha_composite(FOOT_CUBEOS, (cube.width + gap, (hh - FOOT_CUBEOS.height) // 2))
    return img


LOCKUP = lockup()


def paste_alpha(canvas, layer, cx, cy, alpha=1.0, scale=1.0, blur=0.0):
    if alpha <= 0.002:
        return
    img = layer
    if abs(scale - 1.0) > 1e-3:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
    if blur > 0.05:
        pad = int(blur * 3) + 2
        padded = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
        padded.paste(img, (pad, pad))
        img = padded.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 0.999:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda p: int(p * alpha)))
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def sheen(t_pos, strength):
    """A soft diagonal light band across the wordmark, masked to its letters."""
    w, h = WORD_MASK.size
    band = Image.new("L", (w + h, h), 0)
    d = ImageDraw.Draw(band)
    cxp = -0.3 * w + t_pos * 1.6 * w
    half = 0.16 * w
    for x in range(int(cxp - half), int(cxp + half) + 1):
        val = int(255 * strength * (1 - abs(x - cxp) / half) ** 2)
        if val > 0:
            d.line([(x + h * 0.35, 0), (x, h)], fill=val)
    band = band.crop((0, 0, w, h)).filter(ImageFilter.GaussianBlur(2))
    return mono(ImageChops.multiply(band, WORD_MASK), (255, 255, 255))


def progress_bar(canvas, alpha, pos):
    if alpha <= 0.002:
        return
    s = SS
    size = (BAR_W * s, BAR_H * s)
    track_mask = Image.new("L", size, 0)
    ImageDraw.Draw(track_mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=size[1] // 2, fill=255)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", size, (58, 58, 62, 255)), (0, 0), track_mask)
    seg = int(BAR_W * 0.36 * s)
    x0 = int(-seg + pos * (size[0] + seg))
    hi = Image.new("L", size, 0)
    ImageDraw.Draw(hi).rounded_rectangle([x0, 0, x0 + seg, size[1] - 1], radius=size[1] // 2, fill=235)
    layer.paste(Image.new("RGBA", size, (245, 245, 247, 255)), (0, 0), ImageChops.multiply(hi, track_mask))
    layer = layer.resize((BAR_W, BAR_H), Image.LANCZOS)
    layer.putalpha(layer.getchannel("A").point(lambda p: int(p * alpha)))
    canvas.alpha_composite(layer, (CX - BAR_W // 2, BAR_Y - BAR_H // 2))


def frame(word_s=1.0, word_blur=0.0, word_a=1.0, word_dy=0.0, sheen_pos=None, sheen_k=0.0,
          foot_a=1.0, bar_a=1.0, bar_pos=0.0, all_a=1.0, all_s=1.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    paste_alpha(canvas, WORD_GLOW, CX, WORD_Y + word_dy, word_a * all_a, word_s * all_s, word_blur)
    paste_alpha(canvas, WORD, CX, WORD_Y + word_dy, word_a * all_a, word_s * all_s, word_blur)
    if sheen_pos is not None and sheen_k > 0:
        paste_alpha(canvas, sheen(sheen_pos, sheen_k), CX, WORD_Y + word_dy, word_a * all_a, all_s)
    progress_bar(canvas, bar_a * all_a, bar_pos)
    paste_alpha(canvas, FOOT_POWERED, CX, FOOT_Y, foot_a * all_a * 0.9)
    paste_alpha(canvas, LOCKUP, CX, FOOT_Y + 32, foot_a * all_a)
    return canvas.convert("RGB")


def jpeg(img):
    b = io.BytesIO()
    img.save(b, "JPEG", quality=92, optimize=True)
    return b.getvalue()


def intro():
    for i in range(int(2.0 * FPS)):
        t = i / FPS
        w = ease_out(span(t, 0.30, 1.15))
        f = ease_out(span(t, 1.30, 1.90))
        yield frame(word_a=w, word_s=0.96 + 0.04 * w, word_blur=6 * (1 - w), word_dy=6 * (1 - w),
                    sheen_pos=ease_in_out(span(t, 0.95, 1.75)), sheen_k=0.55 if 0.95 < t < 1.75 else 0,
                    foot_a=f, bar_a=f, bar_pos=0.0)


def loop():
    n = int(2.4 * FPS)
    for i in range(n):
        t = i / n
        sp = span(t, 0.20, 0.62)
        yield frame(sheen_pos=ease_in_out(sp), sheen_k=0.32 if 0 < sp < 1 else 0, bar_pos=ease_in_out(t))


def outro():
    n = int(0.5 * FPS)
    for i in range(n):
        k = 1 - ease_out((i + 1) / n)
        yield frame(all_a=k, all_s=0.985 + 0.015 * k, bar_pos=0.0)


def main():
    parts = {"part0": list(intro()), "part1": list(loop()), "part2": list(outro())}
    if "--preview" in sys.argv:
        picks = [parts["part0"][30], parts["part0"][80], parts["part0"][105], parts["part1"][40], parts["part2"][12]]
        sheet = Image.new("RGB", (W // 2 * len(picks), H // 2))
        for k, im in enumerate(picks):
            sheet.paste(im.resize((W // 2, H // 2), Image.LANCZOS), (k * W // 2, 0))
        sheet.save(os.path.join(HERE, "preview.png"))
    desc = f"{W} {H} {FPS}\nc 1 0 part0 #000000\nc 0 0 part1 #000000\nc 1 0 part2 #000000\n"
    out = os.path.join(HERE, "bootanimation.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("desc.txt", desc)
        for name, frames in parts.items():
            for i, img in enumerate(frames):
                z.writestr(f"{name}/{i:03d}.jpg", jpeg(img))
    total = sum(len(f) for f in parts.values())
    print(f"{out}: {total} frames, {os.path.getsize(out) // 1024} KiB")


if __name__ == "__main__":
    main()