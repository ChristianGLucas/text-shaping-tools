from gen.messages_pb2 import (
    ListFontFeaturesRequest,
    ListFontFeaturesResponse,
    ScriptFeatures,
)
from gen.axiom_context import AxiomContext

from nodes._common import load_font

# HarfBuzz's constant for "the script/language's default language system"
# (HB_OT_LAYOUT_DEFAULT_LANGUAGE_INDEX) -- every script has one even when it
# declares no other named languages.
DEFAULT_LANGUAGE_INDEX = 0xFFFF


def list_font_features(ax: AxiomContext, input: ListFontFeaturesRequest) -> ListFontFeaturesResponse:
    """List every OpenType layout feature (GSUB substitution + GPOS
    positioning) the font declares, broken down by script and by every
    language system under that script (including each script's default
    language system), plus the overall union across the whole font — the
    quick way to answer "does this font support ligatures/kerning/small
    caps/etc, and for which scripts."
    """
    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return ListFontFeaturesResponse(error=font_error)
    face = loaded.face

    per_script: dict = {}
    all_gsub: set = set()
    all_gpos: set = set()

    for table, feature_bucket, all_bucket in (
        ("GSUB", "gsub", all_gsub),
        ("GPOS", "gpos", all_gpos),
    ):
        script_tags = face.get_table_script_tags(table)
        for script_index, script_tag in enumerate(script_tags):
            entry = per_script.setdefault(
                script_tag, {"languages": set(), "gsub": set(), "gpos": set()}
            )
            language_tags = face.get_script_language_tags(table, script_index)
            entry["languages"].update(language_tags)

            language_indices = [DEFAULT_LANGUAGE_INDEX] + list(range(len(language_tags)))
            for language_index in language_indices:
                features = face.get_language_feature_tags(
                    table, script_index, language_index
                )
                entry[feature_bucket].update(features)
                all_bucket.update(features)

    scripts = [
        ScriptFeatures(
            script_tag=tag,
            languages=sorted(entry["languages"]),
            gsub_features=sorted(entry["gsub"]),
            gpos_features=sorted(entry["gpos"]),
        )
        for tag, entry in sorted(per_script.items())
    ]

    return ListFontFeaturesResponse(
        scripts=scripts,
        all_gsub_features=sorted(all_gsub),
        all_gpos_features=sorted(all_gpos),
    )
