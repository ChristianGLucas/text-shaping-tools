from gen.messages_pb2 import Font, FeatureSetting, ShapeTextRequest
from nodes.shape_text import shape_text
from nodes.testkit import FakeAxiomContext, dejavu_sans_bytes, dejavu_sans_font


def test_shape_text_ligature_formed_by_default():
    """DejaVu Sans defines an 'fi' ligature glyph (hand-verified against
    our subsetted test fixture: glyph ID 116, glyph name "fi") and enables
    the 'liga' feature by default for the "latn" script. Shaping the two
    letters "fi" must produce exactly one glyph named "fi" whose cluster
    is the first character.
    """
    ax = FakeAxiomContext()
    result = shape_text(ax, ShapeTextRequest(font=dejavu_sans_font(), text="fi"))
    assert result.error.code == ""
    assert len(result.glyphs) == 1
    assert result.glyphs[0].glyph_name == "fi"
    assert result.glyphs[0].glyph_id == 116
    assert result.glyphs[0].cluster == 0
    assert result.resolved_script == "Latn"
    assert result.resolved_language == "en"
    assert result.resolved_direction == "ltr"
    # total_advance_x is the sum of (here, the one) glyph's x_advance.
    assert result.total_advance_x == result.glyphs[0].x_advance
    assert result.glyphs[0].x_advance > 0


def test_shape_text_liga_feature_disables_ligature():
    """Explicitly disabling 'liga' (value=0) must fall back to two
    separate glyphs, "f" and "i" -- proving the features field actually
    reaches HarfBuzz rather than being silently ignored.
    """
    ax = FakeAxiomContext()
    result = shape_text(
        ax,
        ShapeTextRequest(
            font=dejavu_sans_font(),
            text="fi",
            features=[FeatureSetting(tag="liga", value=0)],
        ),
    )
    assert result.error.code == ""
    assert [g.glyph_name for g in result.glyphs] == ["f", "i"]
    assert [g.cluster for g in result.glyphs] == [0, 1]


def test_shape_text_font_size_scales_advances():
    """Shaping the same text at font_size=100 must scale every advance by
    exactly (100 / units_per_em) relative to the raw-units result -- the
    documented font_size contract, checked as a ratio (independent of
    HarfBuzz's internal fixed-point rounding at either scale).
    """
    ax = FakeAxiomContext()
    raw = shape_text(ax, ShapeTextRequest(font=dejavu_sans_font(), text="A"))
    scaled = shape_text(
        ax, ShapeTextRequest(font=dejavu_sans_font(), text="A", font_size=100)
    )
    units_per_em = 2048  # DejaVu Sans, hand-verified via HarfBuzz face.upem
    expected = raw.glyphs[0].x_advance * (100 / units_per_em)
    assert abs(scaled.glyphs[0].x_advance - expected) < 0.05


def test_shape_text_empty_text_is_structured_error():
    ax = FakeAxiomContext()
    result = shape_text(ax, ShapeTextRequest(font=dejavu_sans_font(), text=""))
    assert result.error.code == "EMPTY_INPUT"
    assert len(result.glyphs) == 0


def test_shape_text_oversized_text_is_structured_error():
    ax = FakeAxiomContext()
    huge = "a" * 10_001
    result = shape_text(ax, ShapeTextRequest(font=dejavu_sans_font(), text=huge))
    assert result.error.code == "TOO_LARGE"


def test_shape_text_invalid_font_is_structured_error_not_a_crash():
    ax = FakeAxiomContext()
    bad_font = Font(font_data=b"not a font, just garbage bytes 1234567890")
    result = shape_text(ax, ShapeTextRequest(font=bad_font, text="a"))
    assert result.error.code == "INVALID_FONT"


def test_shape_text_invalid_direction_is_structured_error():
    ax = FakeAxiomContext()
    result = shape_text(
        ax, ShapeTextRequest(font=dejavu_sans_font(), text="a", direction="sideways")
    )
    assert result.error.code == "INVALID_ARGUMENT"


def test_shape_text_malformed_script_tag_is_rejected_not_truncated():
    """HarfBuzz itself silently truncates an over-length script tag
    ("toolong" -> "Tool") instead of erroring -- this node must reject it
    up front instead of inheriting that surprising behavior.
    """
    ax = FakeAxiomContext()
    result = shape_text(
        ax, ShapeTextRequest(font=dejavu_sans_font(), text="a", script="toolong")
    )
    assert result.error.code == "INVALID_ARGUMENT"


def test_shape_text_oversized_font_is_structured_error():
    ax = FakeAxiomContext()
    oversized = dejavu_sans_bytes() + b"0" * (700 * 1024)
    result = shape_text(ax, ShapeTextRequest(font=Font(font_data=oversized), text="a"))
    assert result.error.code == "TOO_LARGE"


def test_shape_text_out_of_range_face_index_is_rejected():
    """DejaVu Sans has exactly 1 face; HarfBuzz itself silently accepts an
    out-of-range face_index rather than erroring, so this node must catch
    it explicitly instead of returning a confusing (wrong) result.
    """
    ax = FakeAxiomContext()
    result = shape_text(
        ax,
        ShapeTextRequest(
            font=Font(font_data=dejavu_sans_bytes(), face_index=5), text="a"
        ),
    )
    assert result.error.code == "INVALID_ARGUMENT"


def test_shape_text_is_deterministic():
    """Same input, same output -- run twice, byte-for-byte identical glyph
    run. Also guards against the language field ever leaking the host OS
    locale (which would make repeated runs disagree only if the locale
    changed mid-test, but nondeterminism here would show up as any
    difference between two back-to-back calls).
    """
    ax = FakeAxiomContext()
    req = ShapeTextRequest(font=dejavu_sans_font(), text="Hello, World!")
    first = shape_text(ax, req)
    second = shape_text(ax, req)
    assert list(first.glyphs) == list(second.glyphs)
    assert first.resolved_language == second.resolved_language == "en"
