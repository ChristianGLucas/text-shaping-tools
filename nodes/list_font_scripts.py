import uharfbuzz as hb

from gen.messages_pb2 import ListFontScriptsRequest, ListFontScriptsResponse, ScriptInfo
from gen.axiom_context import AxiomContext

from nodes._common import load_font


def list_font_scripts(ax: AxiomContext, input: ListFontScriptsRequest) -> ListFontScriptsResponse:
    """List every script the font's OpenType layout tables (GSUB
    substitution and/or GPOS positioning) declare support for, as both the
    font's own raw OpenType script tag (e.g. "latn", "arab", "DFLT") and
    the corresponding ISO 15924 script tag HarfBuzz resolves it to (e.g.
    "Latn", "Arab") -- empty when the OT tag has no Unicode-script mapping
    (e.g. "DFLT", "math"). Use these tags to drive ShapeText.script.
    """
    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return ListFontScriptsResponse(error=font_error)
    face = loaded.face

    ot_tags = set(face.get_table_script_tags("GSUB")) | set(
        face.get_table_script_tags("GPOS")
    )

    scripts = [
        ScriptInfo(ot_tag=tag, iso15924=hb.ot_tag_to_script(tag))
        for tag in sorted(ot_tags)
    ]

    return ListFontScriptsResponse(scripts=scripts)
