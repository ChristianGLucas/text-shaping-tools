from gen.messages_pb2 import (
    GetGlyphMetricsRequest,
    GetGlyphMetricsResponse,
    CharGlyphMetrics,
)
from gen.axiom_context import AxiomContext

from nodes._common import apply_font_size, check_text, load_font


def get_glyph_metrics(ax: AxiomContext, input: GetGlyphMetricsRequest) -> GetGlyphMetricsResponse:
    """Look up each character in `text` directly via the font's cmap
    (nominal-glyph mapping) -- NOT shaped, so no ligatures, reordering, or
    contextual positioning are applied (use ShapeText for that). Returns
    each character's glyph ID, glyph name, horizontal/vertical advance, and
    ink-extent bounding box. A character with no glyph in the font reports
    glyph_found=false against the font's .notdef glyph. font_size scales
    the metrics to that unit; 0 (default) returns raw font design units.
    """
    text_error = check_text(input.text)
    if text_error is not None:
        return GetGlyphMetricsResponse(error=text_error)

    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return GetGlyphMetricsResponse(error=font_error)

    divisor = apply_font_size(loaded, input.font_size)
    font = loaded.font

    glyphs = []
    for ch in input.text:
        codepoint = ord(ch)
        glyph_id = font.get_nominal_glyph(codepoint)
        found = glyph_id is not None
        gid = glyph_id if found else 0
        extents = font.get_glyph_extents(gid)
        glyphs.append(
            CharGlyphMetrics(
                codepoint=codepoint,
                glyph_id=gid,
                glyph_name=font.glyph_to_string(gid),
                glyph_found=found,
                advance_x=font.get_glyph_h_advance(gid) / divisor,
                advance_y=font.get_glyph_v_advance(gid) / divisor,
                bearing_x=extents.x_bearing / divisor,
                bearing_y=extents.y_bearing / divisor,
                extent_width=extents.width / divisor,
                extent_height=extents.height / divisor,
            )
        )

    return GetGlyphMetricsResponse(glyphs=glyphs)
