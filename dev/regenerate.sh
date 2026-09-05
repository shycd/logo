#!/bin/bash
# Regenerates SHYCD.svg, SHYCD.png and SHYCD_white_background.png from dev/SHYCD_editable.svg.
# Requires: inkscape 1.4 and ImageMagick, plus the Python dependencies in pyproject.toml (lxml, numpy, shapely, scour)
# (run it with `uv run dev/regenerate.sh`, or set PYTHON to a virtualenv interpreter).
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON=${PYTHON:-python3}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# 1. drop Inkscape-only elements
"$PYTHON" dev/svg_tools.py preclean dev/SHYCD_editable.svg "$TMP/0.svg"
# 2. wordmark text to path, flatten groups and transforms, fit the page to the drawing
inkscape "$TMP/0.svg" --actions="select-by-id:text4828-7-0;object-to-path;select-clear;select-all:groups;selection-ungroup;select-clear;select-all:groups;selection-ungroup;select-clear;select-all:groups;selection-ungroup;select-clear;select-all:groups;selection-ungroup;select-clear;select-all:groups;selection-ungroup;select-clear;page-fit-to-selection;export-plain-svg;export-filename:$TMP/1.svg;export-do"
# 3. tidy numbers
scour -i "$TMP/1.svg" -o "$TMP/2.svg" --set-precision=7 --disable-simplify-colors --disable-group-collapsing --remove-metadata --enable-comment-stripping --indent=space --nindent=2 --disable-style-to-xml >/dev/null
# 4. descriptive ids, presentation attributes, copyright header
"$PYTHON" dev/svg_tools.py restructure "$TMP/2.svg" "$TMP/3.svg"
# 5. wordmark: thin the Smudged Bold outlines to the 2012 weight, enlarge the dots, re-space along the arc
"$PYTHON" dev/wordmark_postprocess.py "$TMP/3.svg" SHYCD.svg
# 6. rasters
inkscape SHYCD.svg --export-type=png -w 1024 -h 1024 --export-background-opacity=0 --export-filename=SHYCD.png
inkscape SHYCD.svg --export-type=png -w 1024 -h 1024 --export-background='#ffffff' --export-background-opacity=1 --export-filename="$TMP/white.png"
magick "$TMP/white.png" -background white -alpha remove -alpha off SHYCD_white_background.png
echo "done: SHYCD.svg SHYCD.png SHYCD_white_background.png"
