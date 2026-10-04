#!/bin/bash -e
#
# Builds cubeos-bootanimation.zip from the CubeOS boot video.
#
# The video is a full-screen piece (wordmark fading in, a glow that pulses, "powered by
# cubeOS", then a fade-out), so it ships as a prebuilt zip (TARGET_BOOTANIMATION) instead of
# going through gen-bootanimation.sh, which squeezes frames into a logo strip.
#
#   part0  frames 0-137    intro, played once
#   part1  frames 138-221  glow pulse, looped until the system has booted
#                          (frame 221 matches frame 138, so the loop is seamless)
#   part2  frames 222-269  fade-out, played once boot completes
#
# Usage: make-bootanimation-from-video.sh <video.mp4> [width] [height]
# Needs ffmpeg and zip.

VIDEO=$1
W=${2:-720}
H=${3:-1600}
OUT=$(cd "$(dirname "$0")" && pwd)/cubeos-bootanimation.zip
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# Scale to the screen width, centre vertically on black, greyscale (the piece has no colour).
SCALED_H=$((W * 16 / 9))
ffmpeg -v error -i "$VIDEO" \
    -vf "scale=$W:$SCALED_H:flags=lanczos,pad=$W:$H:0:$(((H - SCALED_H) / 2)):black,format=gray" \
    "$WORK/%03d.png"

mkdir "$WORK/part0" "$WORK/part1" "$WORK/part2"
for f in "$WORK"/*.png; do
    n=$((10#$(basename "$f" .png) - 1))
    if [ $n -le 137 ]; then part=part0; elif [ $n -le 221 ]; then part=part1; else part=part2; fi
    mv "$f" "$WORK/$part/$(printf %03d $n).png"
done

printf '%s %s 30\nc 1 0 part0 #000000\np 0 0 part1 #000000\nc 1 0 part2 #000000\n' "$W" "$H" > "$WORK/desc.txt"
rm -f "$OUT"
(cd "$WORK" && zip -0 -q -r -X "$OUT" desc.txt part0 part1 part2)
echo "Wrote $OUT"
