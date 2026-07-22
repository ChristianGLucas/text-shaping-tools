from gen.messages_pb2 import GetFontMetricsRequest, GetFontMetricsResponse, FontMetrics
from gen.axiom_context import AxiomContext

from nodes._common import load_font


def get_font_metrics(ax: AxiomContext, input: GetFontMetricsRequest) -> GetFontMetricsResponse:
    """Get a font's global metrics: units-per-em (the design-grid scale
    every raw-font-unit value elsewhere in this package is on), recommended
    ascender/descender/line-gap for default horizontal line layout, total
    glyph count, whether it is an OpenType Variable Font, and whether it
    declares any GSUB/GPOS layout rules at all.
    """
    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return GetFontMetricsResponse(error=font_error)
    face = loaded.face
    font = loaded.font

    extents = font.get_font_extents("ltr")

    metrics = FontMetrics(
        units_per_em=face.upem,
        ascender=extents.ascender,
        descender=extents.descender,
        line_gap=extents.line_gap,
        num_glyphs=face.glyph_count,
        is_variable=bool(face.axis_infos),
        has_substitution=face.has_layout_substitution,
        has_positioning=face.has_layout_positioning,
    )
    return GetFontMetricsResponse(metrics=metrics)
