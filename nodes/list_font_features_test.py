from gen.messages_pb2 import Font, ListFontFeaturesRequest
from nodes.list_font_features import list_font_features
from nodes.testkit import FakeAxiomContext, dejavu_sans_font


def test_list_font_features_known_features_present():
    """Hand-verified directly against DejaVu Sans via HarfBuzz's own
    lower-level table-introspection calls (get_table_script_tags /
    get_language_feature_tags) run independently of this node's code: the
    "latn" script declares 'liga' among its GSUB features and 'kern'
    among its GPOS features.
    """
    ax = FakeAxiomContext()
    result = list_font_features(ax, ListFontFeaturesRequest(font=dejavu_sans_font()))
    assert result.error.code == ""

    by_tag = {s.script_tag: s for s in result.scripts}
    assert "latn" in by_tag
    latn = by_tag["latn"]
    assert "liga" in latn.gsub_features
    assert "kern" in latn.gpos_features

    assert "liga" in result.all_gsub_features
    assert "kern" in result.all_gpos_features


def test_list_font_features_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = list_font_features(
        ax, ListFontFeaturesRequest(font=Font(font_data=b"garbage" * 5))
    )
    assert result.error.code == "INVALID_FONT"
    assert len(result.scripts) == 0
