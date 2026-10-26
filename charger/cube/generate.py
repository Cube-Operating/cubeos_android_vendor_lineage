#!/usr/bin/env python3
# Copyright (C) 2026 The CubeOS Project
# SPDX-License-Identifier: Apache-2.0
"""
Draws the Cube Phone's power-off charging screen for AOSP's charger UI (/system/bin/charger):

  battery_scale.png  every frame of the battery filling up, interleaved row by row, with the
                     "Frames" text chunk minui reads (system/core/healthd, bootable/recovery/minui)
  battery_fail.png   the battery while its level can't be read yet
  percent_font.png   the percentage digits: a 96x2 grid of ASCII 0x20-0x7f cells (regular, bold)
  animation.txt      frame timing, level ranges and where the percentage sits

Original artwork (no third-party images); text is Roboto (Apache 2.0, external/roboto-fonts).
Laid out for the 720x1600 screen: the frame is centred on screen, and the percentage is drawn
by the charger in the frame's empty top band. Run: python3 generate.py (needs Pillow).
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from PIL.PngImagePlugin import PngInfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE  # installed by ../Android.bp when lineage_charger density is "cube"
FONT = os.path.join(HERE, "../../../../external/roboto-fonts/Roboto-Regular.ttf")

SCREEN_W, SCREEN_H = 720, 1600
FW, FH = 560, 460            # one frame, centred on screen
SS = 4                        # supersampling for smooth edges

# Battery body and terminal, in frame pixels.
BODY = (70, 196, 468, 376)
RADIUS, STROKE = 46, 7
CAP = (478, 256, 498, 316)
INSET = 13                    # gap between outline and fill

OUTLINE = (72, 72, 76)
GREEN_TOP, GREEN_BOTTOM = (64, 222, 112), (30, 168, 74)
RED_TOP, RED_BOTTOM = (255, 104, 88), (214, 58, 48)
LABEL = (142, 142, 148)

# Percentage: drawn by the charger, centred, top at this screen row (in the frame's top band).
PERCENT_Y = (SCREEN_H - FH) // 2 + 34
CELL_W, CELL_H = 64, 128


def roboto(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])  # Roboto's wght axis
    except Exception:
        pass
    return f


def s(box):
    return tuple(v * SS for v in box)


def bolt(d, cx, cy, h, fill):
    """A charging bolt, h tall, centred on (cx, cy)."""
    w = h * 0.56
    pts = [(0.62, 0.0), (0.0, 0.57), (0.42, 0.57), (0.30, 1.0), (1.0, 0.40), (0.56, 0.40), (0.74, 0.0)]
    d.polygon([((cx - w / 2 + x * w) * SS, (cy - h / 2 + y * h) * SS) for x, y in pts], fill=fill)


def frame(level, fail=False):
    """The frame for a battery at `level` percent (or the can't-read-it frame)."""
    img = Image.new("RGB", (FW * SS, FH * SS), (0, 0, 0))
    low = level <= 20
    top, bottom = (RED_TOP, RED_BOTTOM) if low else (GREEN_TOP, GREEN_BOTTOM)

    # A soft glow of the fill colour beneath the battery.
    if not fail and level > 0:
        glow = Image.new("RGB", img.size, (0, 0, 0))
        g = ImageDraw.Draw(glow)
        strength = 0.10 + 0.22 * level / 100
        col = tuple(int(c * strength) for c in bottom)
        g.ellipse(s((BODY[0] + 10, BODY[3] - 30, BODY[2] - 10, BODY[3] + 60)), fill=col)
        glow = glow.filter(ImageFilter.GaussianBlur(34 * SS))
        img = Image.composite(img, glow, Image.new("L", img.size, 0))

    d = ImageDraw.Draw(img)
    d.rounded_rectangle(s(BODY), radius=RADIUS * SS, outline=OUTLINE, width=STROKE * SS)
    d.rounded_rectangle(s(CAP), radius=9 * SS, fill=OUTLINE)

    inner = (BODY[0] + INSET, BODY[1] + INSET, BODY[2] - INSET, BODY[3] - INSET)
    if not fail and level > 0:
        width = (inner[2] - inner[0]) * level / 100
        fill_box = (inner[0], inner[1], inner[0] + max(width, 2 * (RADIUS - INSET)), inner[3])
        # Vertical gradient for the fill, clipped to its rounded shape.
        grad = Image.new("RGB", img.size)
        gd = ImageDraw.Draw(grad)
        y0, y1 = fill_box[1] * SS, fill_box[3] * SS
        for y in range(y0, y1):
            t = (y - y0) / max(1, y1 - y0)
            gd.line([(0, y), (img.size[0], y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(s(fill_box), radius=(RADIUS - INSET) * SS, fill=255)
        img.paste(grad, (0, 0), mask)
        d = ImageDraw.Draw(img)

    cx, cy = (BODY[0] + BODY[2]) / 2, (BODY[1] + BODY[3]) / 2
    if fail:
        bolt(d, cx, cy, 86, (88, 88, 92))
    else:
        # The bolt sits over the battery: dark on a fill that reaches it, white otherwise.
        covered = inner[0] + (inner[2] - inner[0]) * level / 100 > cx + 30
        bolt(d, cx, cy, 86, (12, 40, 20) if covered and not low else (255, 255, 255))

    text = "Checking battery…" if fail else "Charging"
    f = roboto(30 * SS, 500)
    tw = d.textlength(text, font=f)
    d.text(((FW * SS - tw) / 2, 436 * SS), text, font=f, fill=LABEL, anchor="ls")
    return img.resize((FW, FH), Image.LANCZOS)


# The charger plays frames in order and skips any whose level range doesn't hold the current
# charge. Each drawn level L gets two: a quick "sweep" frame for any charge >= L, and a "hold"
# frame only for charges in L's own band. So the battery fills from empty up to the current
# level, rests there, and starts again.
LEVELS = list(range(0, 101, 5))  # 0, 5, ... 100
SWEEP_MS, HOLD_MS = 60, 1600


def plan():
    """(level, disp_ms, min_level, max_level) for every frame, in play order."""
    out = []
    for l in LEVELS:
        out.append((l, SWEEP_MS, l, 100))
        hi = 100 if l == 100 else (99 if l == 95 else l + 4)
        out.append((l, HOLD_MS, l, hi))
    return out


def battery_scale():
    drawn = {l: frame(l) for l in LEVELS}
    frames = [drawn[l] for l, _, _, _ in plan()]
    n = len(frames)
    # minui's multi-frame format: row y of frame k is image row y * n + k.
    out = Image.new("RGB", (FW, FH * n))
    for k, f in enumerate(frames):
        for y in range(FH):
            out.paste(f.crop((0, y, FW, y + 1)), (0, y * n + k))
    info = PngInfo()
    info.add_text("Frames", str(n))
    out.save(os.path.join(OUT, "battery_scale.png"), pnginfo=info, optimize=True)


def percent_font():
    img = Image.new("L", (CELL_W * 96, CELL_H * 2), 0)
    d = ImageDraw.Draw(img)
    for row, weight in ((0, 560), (1, 700)):
        digits = roboto(112, weight)
        small = roboto(66, weight)
        for i in range(96):
            ch = chr(0x20 + i)
            if not ch.isprintable() or ch == " ":
                continue
            f = small if ch == "%" else digits
            w = d.textlength(ch, font=f)
            x = i * CELL_W + (CELL_W - w) / 2
            # Digits sit on a shared baseline; % is smaller and aligned to their cap height.
            base = row * CELL_H + 112
            d.text((x, base), ch, font=f, fill=255, anchor="ls")
    img.save(os.path.join(OUT, "percent_font.png"), optimize=True)


def animation():
    lines = [
        "# CubeOS power-off charging (vendor/lineage/charger/cube/generate.py).",
        "# animation: num_cycles, first_frame_repeats, animation_file",
        "animation: 6 1 charger/battery_scale",
        "# percent_display: x, y (top of the text), r, g, b, a, font",
        f"percent_display: c {PERCENT_Y} 255 255 255 255 charger/percent_font",
        "fail: charger/battery_fail",
        "# frame: disp_time min_level max_level",
    ]
    for _, ms, lo, hi in plan():
        lines.append(f"frame: {ms} {lo} {hi}")
    with open(os.path.join(OUT, "animation.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    battery_scale()
    frame(0, fail=True).save(os.path.join(OUT, "battery_fail.png"), optimize=True)
    percent_font()
    animation()
    print("wrote", sorted(os.listdir(OUT)))