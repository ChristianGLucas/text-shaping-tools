from gen.messages_pb2 import Font, GetGlyphMetricsRequest
from nodes.get_glyph_metrics import get_glyph_metrics
from nodes.testkit import FakeAxiomContext, dejavu_sans_font


def test_get_glyph_metrics_known_glyph():
    """The space character's advance (hand-verified at 651 font units via
    direct HarfBuzz shaping of DejaVu Sans, cross-checked here through the
    unshaped cmap-lookup path this node actually uses) and glyph name
    "space" are both fixed, known values for this font.
    """
    ax = FakeAxiomContext()
    result = get_glyph_metrics(
        ax, GetGlyphMetricsRequest(font=dejavu_sans_font(), text=" ")
    )
    assert result.error.code == ""
    assert len(result.glyphs) == 1
    glyph = result.glyphs[0]
    assert glyph.codepoint == 32
    assert glyph.glyph_found is True
    assert glyph.glyph_name == "space"
    assert glyph.advance_x == 651


def test_get_glyph_metrics_missing_glyph_reports_not_found():
    """U+E000 (start of the Private Use Area) has no glyph in DejaVu Sans
    -- must report glyph_found=false against .notdef, never a guess.
    """
    ax = FakeAxiomContext()
    result = get_glyph_metrics(
        ax, GetGlyphMetricsRequest(font=dejavu_sans_font(), text="")
    )
    assert result.error.code == ""
    glyph = result.glyphs[0]
    assert glyph.glyph_found is False
    assert glyph.glyph_id == 0
    assert glyph.glyph_name == ".notdef"


def test_get_glyph_metrics_font_size_scales_advance():
    ax = FakeAxiomContext()
    raw = get_glyph_metrics(
        ax, GetGlyphMetricsRequest(font=dejavu_sans_font(), text="A")
    )
    scaled = get_glyph_metrics(
        ax, GetGlyphMetricsRequest(font=dejavu_sans_font(), text="A", font_size=100)
    )
    units_per_em = 2048
    expected = raw.glyphs[0].advance_x * (100 / units_per_em)
    assert abs(scaled.glyphs[0].advance_x - expected) < 0.05


def test_get_glyph_metrics_empty_text_is_structured_error():
    ax = FakeAxiomContext()
    result = get_glyph_metrics(
        ax, GetGlyphMetricsRequest(font=dejavu_sans_font(), text="")
    )
    assert result.error.code == "EMPTY_INPUT"


def test_get_glyph_metrics_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = get_glyph_metrics(
        ax, GetGlyphMetricsRequest(font=Font(font_data=b"garbage" * 5), text="A")
    )
    assert result.error.code == "INVALID_FONT"
