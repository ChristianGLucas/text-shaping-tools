from gen.messages_pb2 import Font, GetFontNameTableRequest
from nodes.get_font_name_table import get_font_name_table
from nodes.testkit import FakeAxiomContext, dejavu_sans_bytes, dejavu_sans_font, oracle_family_name


def test_get_font_name_table_matches_independent_sfnt_oracle():
    """family must match a from-scratch parse of the font's own 'name'
    table (a separate code path from HarfBuzz's face.get_name()) -- a
    genuine correctness check, not a self-consistency check.
    """
    ax = FakeAxiomContext()
    result = get_font_name_table(ax, GetFontNameTableRequest(font=dejavu_sans_font()))
    assert result.error.code == ""
    assert result.family == oracle_family_name(dejavu_sans_bytes()) == "DejaVu Sans"
    assert result.full_name == "DejaVu Sans"
    assert result.version == "Version 2.37"
    assert result.subfamily == "Book"
    assert result.postscript_name == "DejaVuSans"
    assert len(result.names) > 0
    assert all(n.value for n in result.names)


def test_get_font_name_table_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = get_font_name_table(
        ax, GetFontNameTableRequest(font=Font(font_data=b"garbage" * 5))
    )
    assert result.error.code == "INVALID_FONT"
    assert result.family == ""
