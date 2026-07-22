import uharfbuzz as hb

from gen.messages_pb2 import ShapeTextRequest, ShapeTextResponse, GlyphInfo
from gen.axiom_context import AxiomContext

from nodes._common import (
    DEFAULT_LANGUAGE,
    VALID_DIRECTIONS,
    apply_font_size,
    check_text,
    is_well_formed_tag,
    load_font,
    make_error,
)


def shape_text(ax: AxiomContext, input: ShapeTextRequest) -> ShapeTextResponse:
    """Shape text with a font via HarfBuzz, returning the positioned glyph
    run: each glyph's ID, name, source-character cluster, and x/y advance/
    offset. Script and direction are inferred from the Unicode text itself
    when left empty (deterministic — never from the host's OS locale);
    language defaults to "en" when left empty (also never locale-derived,
    unlike a naive HarfBuzz integration). Explicit OpenType feature
    settings (e.g. {"tag": "liga", "value": 0} to disable ligatures) can be
    layered on top of the shaper's normal defaults for the resolved script,
    optionally restricted to a cluster range. font_size scales every
    advance/offset to that unit; 0 (default) returns raw font design units.
    """
    text_error = check_text(input.text)
    if text_error is not None:
        return ShapeTextResponse(error=text_error)

    if input.script and not is_well_formed_tag(input.script):
        return ShapeTextResponse(
            error=make_error(
                "INVALID_ARGUMENT",
                f"script '{input.script}' must be a 4-letter ISO 15924 tag "
                "(e.g. 'Latn', 'Arab')",
            )
        )

    direction = input.direction.lower() if input.direction else ""
    if direction and direction not in VALID_DIRECTIONS:
        return ShapeTextResponse(
            error=make_error(
                "INVALID_ARGUMENT",
                f"direction '{input.direction}' must be one of "
                f"{', '.join(VALID_DIRECTIONS)}",
            )
        )

    for feature in input.features:
        if not is_well_formed_tag(feature.tag):
            return ShapeTextResponse(
                error=make_error(
                    "INVALID_ARGUMENT",
                    f"feature tag '{feature.tag}' must be exactly 4 characters",
                )
            )
        if feature.start > feature.end and feature.end != 0:
            return ShapeTextResponse(
                error=make_error(
                    "INVALID_ARGUMENT",
                    f"feature '{feature.tag}' has start ({feature.start}) > "
                    f"end ({feature.end})",
                )
            )

    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return ShapeTextResponse(error=font_error)

    divisor = apply_font_size(loaded, input.font_size)

    buf = hb.Buffer()
    buf.add_str(input.text)
    if input.script:
        buf.script = input.script
    if direction:
        buf.direction = direction
    # Fills in whatever script/direction we didn't set above, purely from
    # the Unicode contents of the text (deterministic, not locale-derived).
    buf.guess_segment_properties()
    # ALWAYS set explicitly -- HarfBuzz's own guess falls back to the host
    # OS locale for language, which would make output depend on where this
    # node happens to run. Never let that happen.
    buf.language = input.language or DEFAULT_LANGUAGE

    feature_map = {}
    for feature in input.features:
        if feature.start or feature.end:
            feature_map[feature.tag] = [(feature.start, feature.end, feature.value)]
        else:
            feature_map[feature.tag] = feature.value

    try:
        hb.shape(loaded.font, buf, feature_map)
    except Exception as exc:
        return ShapeTextResponse(
            error=make_error("INVALID_ARGUMENT", f"shaping failed: {exc}")
        )

    glyphs = []
    total_x = 0.0
    total_y = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        x_advance = pos.x_advance / divisor
        y_advance = pos.y_advance / divisor
        glyphs.append(
            GlyphInfo(
                glyph_id=info.codepoint,
                glyph_name=loaded.font.glyph_to_string(info.codepoint),
                cluster=info.cluster,
                x_advance=x_advance,
                y_advance=y_advance,
                x_offset=pos.x_offset / divisor,
                y_offset=pos.y_offset / divisor,
            )
        )
        total_x += x_advance
        total_y += y_advance

    return ShapeTextResponse(
        glyphs=glyphs,
        resolved_script=str(buf.script),
        resolved_language=str(buf.language),
        resolved_direction=str(buf.direction),
        total_advance_x=total_x,
        total_advance_y=total_y,
    )
