from gen.messages_pb2 import (
    GetVariableFontAxesRequest,
    GetVariableFontAxesResponse,
    VariableAxis,
)
from gen.axiom_context import AxiomContext

from nodes._common import load_font

HIDDEN_AXIS_FLAG = 1  # HB_OT_VAR_AXIS_FLAG_HIDDEN


def get_variable_font_axes(ax: AxiomContext, input: GetVariableFontAxesRequest) -> GetVariableFontAxesResponse:
    """List an OpenType Variable Font's variation axes (e.g. "wght"
    weight, "wdth" width, "opsz" optical size) with their min/default/max
    values and display name. A static (non-variable) font is not an error
    -- is_variable is simply false and axes is empty.
    """
    loaded, font_error = load_font(input.font)
    if font_error is not None:
        return GetVariableFontAxesResponse(error=font_error)
    face = loaded.face

    axis_infos = face.axis_infos
    axes = []
    for axis in axis_infos:
        name = face.get_name(axis.name_id) or ""
        axes.append(
            VariableAxis(
                tag=axis.tag,
                name=name,
                min_value=axis.min_value,
                default_value=axis.default_value,
                max_value=axis.max_value,
                hidden=bool(int(axis.flags) & HIDDEN_AXIS_FLAG),
            )
        )

    return GetVariableFontAxesResponse(is_variable=bool(axes), axes=axes)
