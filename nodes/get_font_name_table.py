from gen.messages_pb2 import GetFontNameTableRequest, GetFontNameTableResponse, NameRecord
from gen.axiom_context import AxiomContext

from nodes._common import load_font

# Predefined OpenType `name` table Name IDs we surface as convenience
# top-level fields (see the OpenType spec's Name IDs table).
FAMILY_ID = 1
SUBFAMILY_ID = 2
FULL_NAME_ID = 4
VERSION_ID = 5
POSTSCRIPT_NAME_ID = 6


def get_font_name_table(ax: AxiomContext, input: GetFontNameTableRequest) -> GetFontNameTableResponse:
    """Read every entry in the font's OpenType `name` table (every
    (name_id, language) pair the font declares, resolved to plain
    strings), plus convenience top-level extractions of the most common
    IDs -- family, subfamily, full name, version, and PostScript name --
    preferring the English ("en") entry when the font has one.
    """
    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return GetFontNameTableResponse(error=font_error)
    face = loaded.face

    names = []
    for entry in face.list_names():
        value = face.get_name(entry.name_id, entry.language)
        if value is None:
            continue
        names.append(
            NameRecord(
                name_id=int(entry.name_id),
                language=entry.language,
                value=value,
            )
        )

    def best(name_id: int) -> str:
        # Prefer an explicit English entry; else fall back to the first
        # entry recorded for this name_id in whatever language it has.
        candidates = [n for n in names if n.name_id == name_id]
        if not candidates:
            return ""
        for candidate in candidates:
            if candidate.language.lower() in ("en", "en-us", "en-gb"):
                return candidate.value
        return candidates[0].value

    return GetFontNameTableResponse(
        names=names,
        family=best(FAMILY_ID),
        subfamily=best(SUBFAMILY_ID),
        full_name=best(FULL_NAME_ID),
        version=best(VERSION_ID),
        postscript_name=best(POSTSCRIPT_NAME_ID),
    )
