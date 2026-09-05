# Building the logo

Edit `SHYCD_editable.svg` in Inkscape, then run `regenerate.sh` from the repository root. It outlines the wordmark, flattens the drawing, fits the page to it, tidies the file and reshapes the wordmark with `wordmark_postprocess.py`, then exports the PNGs.

The wordmark is set in TypeWrong (Digital Graphic Labs, freeware, e.g. https://www.dafont.com/type-wrong.font). The only file available today is the Smudged Bold face, while the 2012 logo used a lighter cut, so the outlines are thinned, the dots enlarged and the glyphs re-spaced along the arc to match the 2012 raster.

Requirements: Inkscape 1.4, ImageMagick, and the Python dependencies declared in `pyproject.toml`.

```
uv sync
uv run dev/regenerate.sh
```

or, with pip 25.1 or newer:

```
python -m venv .venv
.venv/bin/pip install --group dev
PYTHON=.venv/bin/python dev/regenerate.sh
```

## Files

- `SHYCD_editable.svg`: Inkscape source, with the wordmark as live text on an invisible arc path. It needs the TypeWrong font installed to show the word correctly.
- `regenerate.sh`, `svg_tools.py`, `wordmark_postprocess.py`: the build scripts.

The original raster logos (`SHYCD_logo_2011.png`, `SHYCD_logo_2012.jpg`) and the construction pieces of the 2019 vectorization, made with Inkscape 0.92 on Ubuntu 18.04, are in `../archive/`.
