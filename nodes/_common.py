# Shared helpers for christiangeorgelucas/text-shaping-tools nodes.
#
# Every node wraps HarfBuzz (via uharfbuzz) for one distinct capability —
# this module centralizes the repeated boilerplate: font-blob validation
# and parsing, size caps, error construction, and the raw-units-vs-scaled
# font_size convention shared by ShapeText and GetGlyphMetrics.

import uharfbuzz as hb

from gen.messages_pb2 import Error

# A font blob is untrusted input the caller fully controls; bound its size
# before any parsing happens. 640 KiB is deliberately conservative: the
# deployed HTTP/JSON invocation ingress in front of this package enforces
# an ~1 MiB REQUEST BODY ceiling (verified empirically against the
# deployed endpoint -- not documented anywhere, and invisible to local
# `axiom dev`/unit testing), and the JSON bridge base64-encodes `bytes`
# fields (~+33% over the wire). 640 KiB raw -> ~875 KB base64, leaving
# ~170 KB of headroom under that 1 MiB ceiling for the rest of the
# request (other fields, JSON structure). A caller with a larger font
# should subset it first with this package's own SubsetFont node.
MAX_FONT_BYTES = 640 * 1024

# Shaping/metric cost scales with text length; bound it before any
# HarfBuzz call. 10,000 UTF-16 code units is ample for any single
# paragraph/label/caption a caller would send in one node invocation.
MAX_TEXT_CHARS = 10_000

# Never inferred from the host OS locale (see messages.proto DETERMINISM
# note) — this is the fixed default when a caller leaves `language` empty.
DEFAULT_LANGUAGE = "en"

VALID_DIRECTIONS = ("ltr", "rtl", "ttb", "btt")


def make_error(code: str, message: str) -> Error:
    return Error(code=code, message=message)


def too_large_error(what: str, limit: int) -> Error:
    return make_error("TOO_LARGE", f"{what} exceeds the {limit}-byte/char cap")


def check_text(text: str, field_name: str = "text"):
    """Validate a text field. Returns an Error, or None if it's fine."""
    if not text:
        return make_error("EMPTY_INPUT", f"{field_name} was empty")
    if len(text) > MAX_TEXT_CHARS:
        return too_large_error(field_name, MAX_TEXT_CHARS)
    return None


def is_well_formed_tag(tag: str) -> bool:
    """True if `tag` is exactly 4 ASCII letters/digits/spaces — the shape of
    an OpenType/ISO-15924 tag. HarfBuzz itself silently truncates/pads a
    malformed tag string (e.g. "toolong" -> "Tool") instead of rejecting it,
    so callers get a confusing result rather than an error; we reject
    up front instead of trusting that leniency.
    """
    return len(tag) == 4 and all(c.isalnum() or c == " " for c in tag)


class LoadedFont:
    __slots__ = ("face", "font")

    def __init__(self, face, font):
        self.face = face
        self.font = font


def load_font(font_msg):
    """Validate + parse a Font message into a HarfBuzz Face+Font pair.

    Returns (LoadedFont, error) — on failure LoadedFont is None and error is
    a structured Error; on success error is None.
    """
    data = font_msg.font_data
    if not data:
        return None, make_error("EMPTY_INPUT", "font.font_data was empty")
    if len(data) > MAX_FONT_BYTES:
        return None, too_large_error("font.font_data", MAX_FONT_BYTES)
    if font_msg.face_index < 0:
        return None, make_error("INVALID_ARGUMENT", "font.face_index must be >= 0")

    data_bytes = bytes(data)
    try:
        probe = hb.Face(data_bytes, 0)
    except Exception as exc:
        return None, make_error(
            "INVALID_FONT", f"could not parse font_data as a font: {exc}"
        )

    if probe.glyph_count == 0:
        return None, make_error(
            "INVALID_FONT",
            "font_data is not a supported sfnt font (HarfBuzz produced an "
            "empty face with 0 glyphs) — only raw TTF/OTF/TTC is supported, "
            "not WOFF/WOFF2 wrappers",
        )

    num_faces = max(probe.count, 1)
    if font_msg.face_index >= num_faces:
        return None, make_error(
            "INVALID_ARGUMENT",
            f"face_index {font_msg.face_index} is out of range — this font "
            f"has {num_faces} face(s)",
        )

    if font_msg.face_index == 0:
        face = probe
    else:
        face = hb.Face(data_bytes, font_msg.face_index)
        if face.glyph_count == 0:
            return None, make_error(
                "INVALID_FONT", "selected face has 0 glyphs"
            )

    font = hb.Font(face)
    return LoadedFont(face=face, font=font), None


def apply_font_size(loaded: LoadedFont, font_size: float) -> float:
    """Scale `loaded.font` to `font_size` units-per-em if font_size > 0,
    else leave it at its default scale (raw font design units, i.e.
    units_per_em). Returns the divisor to apply to every raw HarfBuzz
    integer output value to get the caller's chosen unit.
    """
    if font_size and font_size > 0:
        scaled = int(round(font_size * 64))
        loaded.font.scale = (scaled, scaled)
        return 64.0
    return 1.0
