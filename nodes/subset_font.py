import uharfbuzz as hb

from gen.messages_pb2 import SubsetFontRequest, SubsetFontResponse
from gen.axiom_context import AxiomContext

from nodes._common import MAX_TEXT_CHARS, check_text, load_font, make_error, too_large_error

# Tables it's safe to drop for the "smallest possible" (retain_layout_tables
# = false) subset -- the caller asked for glyphs to render, not to shape or
# introspect further.
_DROPPABLE_LAYOUT_TABLES = ("GSUB", "GPOS", "GDEF")


def _tag_to_int(tag: str) -> int:
    b = tag.encode("ascii")
    return (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]


def subset_font(ax: AxiomContext, input: SubsetFontRequest) -> SubsetFontResponse:
    """Subset a font down to only the glyphs needed to render given text
    and/or code points, via HarfBuzz's subsetter (the same engine Google
    Fonts/Chrome use to shrink web-font downloads). By default produces the
    smallest possible subset (drops hinting, GSUB/GPOS/GDEF layout tables);
    set retain_layout_tables=true to keep glyph names and layout tables so
    the subset is still shapeable/introspectable by this package's other
    nodes.
    """
    if not input.text and not input.unicode_codepoints:
        return SubsetFontResponse(
            error=make_error(
                "EMPTY_INPUT",
                "at least one of text or unicode_codepoints must be given",
            )
        )

    if input.text:
        text_error = check_text(input.text)
        if text_error is not None:
            return SubsetFontResponse(error=text_error)

    if len(input.unicode_codepoints) > MAX_TEXT_CHARS:
        return SubsetFontResponse(
            error=too_large_error("unicode_codepoints", MAX_TEXT_CHARS)
        )

    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return SubsetFontResponse(error=font_error)
    face = loaded.face

    original_size = len(input.font.font_data)
    original_num_glyphs = face.glyph_count

    subset_input = hb.SubsetInput()
    for ch in input.text:
        subset_input.unicode_set.add(ord(ch))
    for codepoint in input.unicode_codepoints:
        subset_input.unicode_set.add(codepoint)

    if input.retain_layout_tables:
        subset_input.flags = hb.SubsetFlags.GLYPH_NAMES
    else:
        subset_input.flags = hb.SubsetFlags.NO_HINTING
        for table in _DROPPABLE_LAYOUT_TABLES:
            subset_input.drop_table_tag_set.add(_tag_to_int(table))

    try:
        new_face = subset_input.subset(face)
    except Exception as exc:
        return SubsetFontResponse(error=make_error("SUBSET_FAILED", str(exc)))

    if new_face.glyph_count == 0:
        return SubsetFontResponse(
            error=make_error(
                "SUBSET_FAILED",
                "the requested text/code points produced an empty subset "
                "(no matching glyphs found in the font)",
            )
        )

    subset_bytes = new_face.blob.data

    return SubsetFontResponse(
        subset_font_data=subset_bytes,
        original_size_bytes=original_size,
        subset_size_bytes=len(subset_bytes),
        original_num_glyphs=original_num_glyphs,
        subset_num_glyphs=new_face.glyph_count,
    )
