# text-shaping-tools

Composable **text-shaping and OpenType font-introspection** nodes for the
[Axiom](https://axiomide.com) marketplace, published as
`christiangeorgelucas/text-shaping-tools`.

Wraps [HarfBuzz](https://harfbuzz.github.io/) — the shaping engine behind
Chrome, Android, and LibreOffice — via its official Python binding,
[`uharfbuzz`](https://github.com/harfbuzz/uharfbuzz) (Apache-2.0; HarfBuzz
itself "Old MIT" — both permissive, verified from source; see
`THIRD_PARTY_NOTICES.md`).

Shape a Unicode string with a font into a positioned glyph run (glyph IDs,
cluster indices, x/y advances/offsets) — Unicode-aware and OpenType-feature-
aware across simple and complex scripts (Arabic joining, ligatures, kerning,
contextual alternates). Also introspect a font's OpenType layout features and
scripts, global and per-glyph metrics, name table, and variable-font axes,
and subset a font down to only the glyphs a given text needs.

This is distinct from `christiangeorgelucas/charset-tools` (character
encodings, not glyphs), `christiangeorgelucas/emoji-tools` (Unicode grapheme
segmentation, not OpenType shaping), and `christiangeorgelucas/image-tools`
/ `christiangeorgelucas/pdf-tools` (rendering to pixels/pages, not glyph-
level typography) — this package stops at the shaped glyph run, one layer
below rasterization.

Every node is **stateless**, **offline** (no network, no API keys, no
signup), and **deterministic** — including buffer language, which is never
inferred from the host OS locale (a common HarfBuzz-integration pitfall that
would make output depend on where the node happens to run).

## Nodes

| Node | Input &rarr; Output | Purpose |
|---|---|---|
| `ShapeText` | `ShapeTextRequest` &rarr; `ShapeTextResponse` | Shape text with a font: positioned glyph run (glyph ID, name, cluster, x/y advance/offset) |
| `ListFontFeatures` | `ListFontFeaturesRequest` &rarr; `ListFontFeaturesResponse` | Every OpenType GSUB/GPOS feature the font declares, per script + overall |
| `ListFontScripts` | `ListFontScriptsRequest` &rarr; `ListFontScriptsResponse` | Every script the font's layout tables declare support for |
| `GetFontMetrics` | `GetFontMetricsRequest` &rarr; `GetFontMetricsResponse` | Units-per-em, ascender/descender/line-gap, glyph count, variable-font flag |
| `GetGlyphMetrics` | `GetGlyphMetricsRequest` &rarr; `GetGlyphMetricsResponse` | Per-character (unshaped, cmap-direct) glyph ID/name/advance/extents |
| `GetFontNameTable` | `GetFontNameTableRequest` &rarr; `GetFontNameTableResponse` | The font's OpenType `name` table: family, subfamily, full name, version, PostScript name |
| `GetVariableFontAxes` | `GetVariableFontAxesRequest` &rarr; `GetVariableFontAxesResponse` | An OpenType Variable Font's variation axes (e.g. weight, width, optical size) |
| `SubsetFont` | `SubsetFontRequest` &rarr; `SubsetFontResponse` | Subset a font to only the glyphs a given text/code-point set needs |

## Supported font formats

Raw SFNT-based fonts only: TrueType (`.ttf`), OpenType/CFF (`.otf`), and
TrueType/OpenType Collections (`.ttc`, via `face_index`). WOFF/WOFF2 web-font
wrappers are **not** unwrapped — HarfBuzz itself has no WOFF decompressor;
feed it raw sfnt bytes. An unparseable font returns a structured
`INVALID_FONT` error, never a crash.

## Development

```bash
axiom validate     # static checks
axiom test         # unit tests (goldens + independent oracles + error paths)
axiom dev          # local HTTP bridge (prints the port it binds)
```

## Correctness

The test suite checks every claim against an **independent oracle** wherever
one is available, not just a round-trip through HarfBuzz itself:

- `GetFontMetrics` (units-per-em, glyph count) and `GetFontNameTable`
  (family name) are cross-checked against a from-scratch, dependency-free
  parser of the font's own `head`/`maxp`/`name` sfnt tables (see
  `nodes/testkit.py`'s `oracle_*` functions) — a genuinely separate code
  path from HarfBuzz's own table introspection.
- `SubsetFont`'s output is verified structurally valid (a real sfnt
  directory whose table offsets/lengths all fit inside the blob) by that
  same from-scratch parser, not merely "HarfBuzz says it's fine."
- `ShapeText`'s ligature formation (DejaVu Sans's "fi" ligature) and glyph
  names are checked against hand-verified, known values for that specific
  font.

## Composability

`SubsetFont`'s `subset_font_data` output feeds directly into any other
node's `Font.font_data` field (see `subset-then-shape.flow.yaml` for a
worked two-step flow: subset a font to the glyphs some text needs, then
shape that same text with the much-smaller subsetted font).

## License

MIT — (c) 2026 Christian George Lucas. Built for the Axiom marketplace.
See `THIRD_PARTY_NOTICES.md` for the wrapped library's license and the test
fixtures' font licenses.
