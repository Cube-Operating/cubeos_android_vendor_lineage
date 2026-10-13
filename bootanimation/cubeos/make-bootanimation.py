#!/usr/bin/env python3
"""Build CubeOS's boot animation (bootanimation.zip) from cubeos-boot.mp4.

  pip install opencv-python-headless pillow
  ./make-bootanimation.py            # writes bootanimation.zip next to this script

The video (1080x1920, 30 fps, 9 s: "ContiSX" glowing in, then "powered by cubeOS") becomes:
  part0  every frame, played completely once (c 1 0)
  part1  the last frame, held until Android has booted (p 0 0)
at 720x1280, centred on black (the video's own background), stored uncompressed as bootanimation
requires. vendor/lineage/config/BoardConfigLineage.mk points TARGET_BOOTANIMATION at the zip.
"""
import io
import os
import zipfile

import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 720, 1280, 30

cap = cv2.VideoCapture(os.path.join(HERE, "cubeos-boot.mp4"))
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    img = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90, optimize=True)
    frames.append(buf.getvalue())
assert frames, "no frames decoded"

desc = f"{W} {H} {FPS}\nc 1 0 part0 #000000\np 0 0 part1 #000000\n"
out = os.path.join(HERE, "bootanimation.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
    z.writestr("desc.txt", desc)
    for i, data in enumerate(frames):
        z.writestr(f"part0/{i:03d}.jpg", data)
    z.writestr("part1/000.jpg", frames[-1])
print(f"{out}: {len(frames)} frames, {os.path.getsize(out) // 1024} KiB")
