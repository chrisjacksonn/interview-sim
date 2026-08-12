#!/bin/bash
# Turn a screen recording into a README-sized GIF.
#
#   tools/screencast-to-gif.sh recording.mov demo-posting.gif [start] [duration]
#
# The terminal demo is recorded with vhs, which is reproducible and small. This
# is for the other kind: the flow that starts in a browser and ends in an editor,
# which no terminal recorder can show because none of it happens in a terminal.
#
# Two passes, because a single-pass GIF picks 256 colours per frame and a UI
# recording ends up banded and enormous. palettegen looks at the whole clip
# first, then paletteuse maps to it with dithering.
set -euo pipefail

SOURCE=${1:?usage: screencast-to-gif.sh <input.mov> [output.gif] [start] [duration]}
TARGET=${2:-demo-posting.gif}
START=${3:-0}
LENGTH=${4:-}

WIDTH=${WIDTH:-1000}   # README images render about this wide
FPS=${FPS:-12}         # a UI recording reads fine at 12; 24 doubles the bytes

command -v ffmpeg >/dev/null || {
    echo "ffmpeg not found. brew install ffmpeg" >&2
    exit 1
}

PALETTE=$(mktemp -t interview-sim-palette).png
trap 'rm -f "$PALETTE"' EXIT

trim=(-ss "$START")
if [ -n "$LENGTH" ]; then
    trim+=(-t "$LENGTH")
fi

filters="fps=$FPS,scale=$WIDTH:-1:flags=lanczos"

ffmpeg -v error -y "${trim[@]}" -i "$SOURCE" \
    -vf "$filters,palettegen=stats_mode=diff" "$PALETTE"

ffmpeg -v error -y "${trim[@]}" -i "$SOURCE" -i "$PALETTE" \
    -lavfi "$filters [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
    "$TARGET"

size=$(du -h "$TARGET" | cut -f1)
echo "$TARGET  $size"
echo ""
echo "GitHub renders it inline up to about 10MB, but anything over ~3MB is slow"
echo "on a phone. If it is too big: lower FPS, drop WIDTH, or cut the clip"
echo "shorter with the start and duration arguments."
