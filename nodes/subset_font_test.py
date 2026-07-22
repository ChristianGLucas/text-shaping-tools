from gen.messages_pb2 import Font, SubsetFontRequest
from nodes.subset_font import subset_font
from nodes.testkit import FakeAxiomContext, dejavu_sans_font, oracle_is_structurally_valid_sfnt


def test_subset_font_shrinks_and_produces_valid_font():
    """Subsetting to just "AB" must retain far fewer glyphs than the
    original (3: .notdef + A + B) and produce real, structurally valid
    font bytes -- verified by a from-scratch sfnt-directory parser,
    independent of HarfBuzz, not merely "HarfBuzz says it's fine."
    """
    ax = FakeAxiomContext()
    result = subset_font(ax, SubsetFontRequest(font=dejavu_sans_font(), text="AB"))
    assert result.error.code == ""
    assert result.original_num_glyphs == 120
    assert result.subset_num_glyphs == 3
    assert result.subset_size_bytes < result.original_size_bytes
    assert oracle_is_structurally_valid_sfnt(result.subset_font_data)


def test_subset_font_retain_layout_tables_still_valid():
    ax = FakeAxiomContext()
    result = subset_font(
        ax,
        SubsetFontRequest(
            font=dejavu_sans_font(), text="AB", retain_layout_tables=True
        ),
    )
    assert result.error.code == ""
    assert oracle_is_structurally_valid_sfnt(result.subset_font_data)


def test_subset_font_unicode_codepoints_equivalent_to_text():
    ax = FakeAxiomContext()
    by_text = subset_font(ax, SubsetFontRequest(font=dejavu_sans_font(), text="AB"))
    by_codepoints = subset_font(
        ax, SubsetFontRequest(font=dejavu_sans_font(), unicode_codepoints=[65, 66])
    )
    assert by_text.subset_num_glyphs == by_codepoints.subset_num_glyphs


def test_subset_font_requires_text_or_codepoints():
    ax = FakeAxiomContext()
    result = subset_font(ax, SubsetFontRequest(font=dejavu_sans_font()))
    assert result.error.code == "EMPTY_INPUT"


def test_subset_font_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = subset_font(
        ax, SubsetFontRequest(font=Font(font_data=b"garbage" * 5), text="A")
    )
    assert result.error.code == "INVALID_FONT"
