# Third-party notices

## Runtime dependency

| Component | License | Notes |
|---|---|---|
| [`uharfbuzz`](https://github.com/harfbuzz/uharfbuzz) | Apache-2.0 | Official Cython bindings to HarfBuzz, published by the HarfBuzz project. Verified from the PyPI package metadata (`license: Apache License 2.0`) and the `LICENSE` file bundled inside the published wheel (`uharfbuzz-0.55.0.dist-info/licenses/LICENSE`). |
| [HarfBuzz](https://github.com/harfbuzz/harfbuzz) itself (statically compiled into the `uharfbuzz` wheel) | "Old MIT" | A permissive MIT-style license (no advertising/attribution clause beyond the standard notice-preservation requirement). Verified from HarfBuzz's own `COPYING` file at the project's GitHub repository. Multiple copyright holders (Google, Mozilla, Red Hat, Behdad Esfahbod, and others) all under the same license text. |

No other runtime dependency. No transitive dependency tree beyond what
`uharfbuzz`'s own wheel bundles (it ships a statically-linked, prebuilt
HarfBuzz — there is no separate installable HarfBuzz package to audit).
Neither license is copyleft; both permit unrestricted commercial use,
modification, and redistribution.

## Test fixtures (not shipped as a runtime dependency — bundled only under `tests/fixtures/` to give the test suite real font files to exercise)

| Font | License | Source |
|---|---|---|
| DejaVu Sans, subsetted to printable ASCII + fi/fl (`DejaVuSans-subset.ttf`, produced with this package's own `SubsetFont`/HarfBuzz subsetter, `retain_layout_tables=true`, to stay under the package's own font-size cap) | Bitstream Vera License (public-domain-like, permissive; DejaVu's own changes are public domain; the license explicitly permits merging/modifying/redistributing) | [dejavu-fonts/dejavu-fonts](https://github.com/dejavu-fonts/dejavu-fonts); full license text captured at `tests/fixtures/DejaVu-LICENSE.txt`. |
| Comfortaa Variable (`Comfortaa-Variable.ttf`, renamed from `Comfortaa[wght].ttf`) | SIL Open Font License 1.1 | [google/fonts](https://github.com/google/fonts/tree/main/ofl/comfortaa); full license text captured at `tests/fixtures/Comfortaa-OFL.txt`. |

Both are used exactly as intended by their licenses: bundled with software,
not sold standalone, with license text preserved alongside the font files.
