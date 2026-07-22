from gen.messages_pb2 import Font, ListFontScriptsRequest
from nodes.list_font_scripts import list_font_scripts
from nodes.testkit import FakeAxiomContext, dejavu_sans_font


def test_list_font_scripts_known_scripts_present():
    """DejaVu Sans's GSUB/GPOS tables declare "latn" and "arab" (hand-
    verified via HarfBuzz's get_table_script_tags directly) and "DFLT",
    whose OpenType tag has no ISO 15924 mapping -- iso15924 must be empty
    for it rather than a guessed value.
    """
    ax = FakeAxiomContext()
    result = list_font_scripts(ax, ListFontScriptsRequest(font=dejavu_sans_font()))
    assert result.error.code == ""

    by_tag = {s.ot_tag: s.iso15924 for s in result.scripts}
    assert by_tag["latn"] == "Latn"
    assert by_tag["arab"] == "Arab"
    assert by_tag["DFLT"] == ""


def test_list_font_scripts_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = list_font_scripts(
        ax, ListFontScriptsRequest(font=Font(font_data=b"garbage" * 5))
    )
    assert result.error.code == "INVALID_FONT"
    assert len(result.scripts) == 0
