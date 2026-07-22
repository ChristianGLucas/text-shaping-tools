from gen.messages_pb2 import Font, GetFontMetricsRequest
from nodes.get_font_metrics import get_font_metrics
from nodes.testkit import (
    FakeAxiomContext,
    comfortaa_variable_bytes,
    comfortaa_variable_font,
    dejavu_sans_bytes,
    dejavu_sans_font,
    oracle_num_glyphs,
    oracle_units_per_em,
)


def test_get_font_metrics_dejavu_matches_independent_sfnt_oracle():
    """units_per_em and num_glyphs must match a from-scratch parse of the
    font's own 'head'/'maxp' tables -- independent of HarfBuzz, so this is
    a genuine correctness check, not a self-consistency check.
    """
    ax = FakeAxiomContext()
    result = get_font_metrics(ax, GetFontMetricsRequest(font=dejavu_sans_font()))
    assert result.error.code == ""

    data = dejavu_sans_bytes()
    assert result.metrics.units_per_em == oracle_units_per_em(data)
    assert result.metrics.num_glyphs == oracle_num_glyphs(data)
    assert result.metrics.is_variable is False
    assert result.metrics.has_substitution is True
    assert result.metrics.has_positioning is True
    assert result.metrics.ascender > 0
    assert result.metrics.descender < 0


def test_get_font_metrics_variable_font_flagged():
    ax = FakeAxiomContext()
    result = get_font_metrics(ax, GetFontMetricsRequest(font=comfortaa_variable_font()))
    assert result.error.code == ""
    assert result.metrics.is_variable is True
    assert result.metrics.units_per_em == oracle_units_per_em(comfortaa_variable_bytes())
    assert result.metrics.num_glyphs == oracle_num_glyphs(comfortaa_variable_bytes())


def test_get_font_metrics_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = get_font_metrics(
        ax, GetFontMetricsRequest(font=Font(font_data=b"garbage" * 5))
    )
    assert result.error.code == "INVALID_FONT"
    assert result.metrics.units_per_em == 0
