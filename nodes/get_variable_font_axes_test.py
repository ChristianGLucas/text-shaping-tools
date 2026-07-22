from gen.messages_pb2 import Font, GetVariableFontAxesRequest
from nodes.get_variable_font_axes import get_variable_font_axes
from nodes.testkit import FakeAxiomContext, comfortaa_variable_font, dejavu_sans_font


def test_get_variable_font_axes_variable_font():
    """Comfortaa[wght].ttf declares one "wght" axis, min 300 / default
    400 / max 700 (hand-verified directly via HarfBuzz's face.axis_infos,
    and documented on Google Fonts' own Comfortaa variable-axes page).
    """
    ax = FakeAxiomContext()
    result = get_variable_font_axes(
        ax, GetVariableFontAxesRequest(font=comfortaa_variable_font())
    )
    assert result.error.code == ""
    assert result.is_variable is True
    assert len(result.axes) == 1
    axis = result.axes[0]
    assert axis.tag == "wght"
    assert axis.min_value == 300
    assert axis.default_value == 400
    assert axis.max_value == 700


def test_get_variable_font_axes_static_font_is_not_an_error():
    """A static font is a normal, non-error result: is_variable=false and
    an empty axes list -- not a failure.
    """
    ax = FakeAxiomContext()
    result = get_variable_font_axes(
        ax, GetVariableFontAxesRequest(font=dejavu_sans_font())
    )
    assert result.error.code == ""
    assert result.is_variable is False
    assert len(result.axes) == 0


def test_get_variable_font_axes_invalid_font_is_structured_error():
    ax = FakeAxiomContext()
    result = get_variable_font_axes(
        ax, GetVariableFontAxesRequest(font=Font(font_data=b"garbage" * 5))
    )
    assert result.error.code == "INVALID_FONT"
