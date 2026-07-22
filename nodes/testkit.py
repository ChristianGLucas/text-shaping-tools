# Shared test scaffolding for christiangeorgelucas/text-shaping-tools node tests.
import os
import struct

from gen.axiom_context import SecretStatus
from gen.messages_pb2 import Font

_FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "fixtures"
)


class FakeAxiomContext:
    """Minimal AxiomContext implementation for unit tests."""

    class _Logger:
        def debug(self, msg: str, **attrs) -> None: pass
        def info(self, msg: str, **attrs) -> None: pass
        def warn(self, msg: str, **attrs) -> None: pass
        def error(self, msg: str, **attrs) -> None: pass

    class _Secrets:
        def __init__(self, m: dict, revoked: set) -> None:
            self._m = m or {}
            self._revoked = revoked or set()

        def get(self, name: str):
            v = self._m.get(name)
            return (v, True) if v is not None else ("", False)

        def status(self, name: str) -> SecretStatus:
            if name in self._m:
                return SecretStatus.AVAILABLE
            if name in self._revoked:
                return SecretStatus.REVOKED
            return SecretStatus.UNSET

    def __init__(self, secrets_map: dict | None = None, revoked_names: set | None = None) -> None:
        self.log = self._Logger()
        self.secrets = self._Secrets(secrets_map or {}, revoked_names)
        self.execution_id = "test-execution-id"
        self.flow_id = "test-flow-id"
        self.tenant_id = "test-tenant-id"


def _load_fixture_bytes(filename: str) -> bytes:
    with open(os.path.join(_FIXTURES_DIR, filename), "rb") as fh:
        return fh.read()


def dejavu_sans_bytes() -> bytes:
    """DejaVu Sans (Bitstream Vera License, permissive) -- a static TTF with
    Latin/Cyrillic/Greek/Arabic/etc. cmap coverage and modest GSUB/GPOS
    (ccmp/dlig/kern) layout data. Our general-purpose shaping fixture.
    """
    return _load_fixture_bytes("DejaVuSans.ttf")


def dejavu_sans_font(face_index: int = 0) -> Font:
    return Font(font_data=dejavu_sans_bytes(), face_index=face_index)


def comfortaa_variable_bytes() -> bytes:
    """Comfortaa[wght].ttf (SIL OFL-1.1, permissive) -- a variable font with
    one "wght" axis (300-700, default 400). Our variable-font fixture.
    """
    return _load_fixture_bytes("Comfortaa-Variable.ttf")


def comfortaa_variable_font() -> Font:
    return Font(font_data=comfortaa_variable_bytes())


# ---------------------------------------------------------------------------
# From-scratch sfnt table parsing, used ONLY as an independent correctness
# oracle in tests -- deliberately not sharing a single line of code with
# HarfBuzz/uharfbuzz, so a test asserting against these functions is a real
# cross-check, not a comparison of the implementation against itself.
# ---------------------------------------------------------------------------


def _find_sfnt_table(font_bytes: bytes, tag: bytes):
    """Locate a table in an sfnt directory. Returns (offset, length) or None."""
    num_tables = struct.unpack(">H", font_bytes[4:6])[0]
    offset = 12
    for _ in range(num_tables):
        table_tag = font_bytes[offset : offset + 4]
        table_offset, table_length = struct.unpack(
            ">II", font_bytes[offset + 8 : offset + 16]
        )
        if table_tag == tag:
            return table_offset, table_length
        offset += 16
    return None


def oracle_units_per_em(font_bytes: bytes) -> int:
    """unitsPerEm, read straight from the 'head' table at its fixed offset
    (18) -- independent of HarfBuzz's face.upem.
    """
    head_offset, _ = _find_sfnt_table(font_bytes, b"head")
    return struct.unpack(">H", font_bytes[head_offset + 18 : head_offset + 20])[0]


def oracle_num_glyphs(font_bytes: bytes) -> int:
    """numGlyphs, read straight from the 'maxp' table at its fixed offset
    (4) -- independent of HarfBuzz's face.glyph_count.
    """
    maxp_offset, _ = _find_sfnt_table(font_bytes, b"maxp")
    return struct.unpack(">H", font_bytes[maxp_offset + 4 : maxp_offset + 6])[0]


def oracle_is_structurally_valid_sfnt(font_bytes: bytes) -> bool:
    """From-scratch structural sanity check: valid sfnt version tag, and
    every table directory entry's (offset, length) fits inside the blob.
    Independent of HarfBuzz -- used to confirm SubsetFont's output is a
    real, well-formed font file, not merely bytes HarfBuzz itself would
    accept.
    """
    if len(font_bytes) < 12:
        return False
    version = font_bytes[0:4]
    if version not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
        return False
    num_tables = struct.unpack(">H", font_bytes[4:6])[0]
    offset = 12
    if offset + num_tables * 16 > len(font_bytes):
        return False
    for _ in range(num_tables):
        table_offset, table_length = struct.unpack(
            ">II", font_bytes[offset + 8 : offset + 16]
        )
        if table_offset + table_length > len(font_bytes):
            return False
        offset += 16
    return True


def oracle_family_name(font_bytes: bytes) -> str:
    """The Windows-platform (3, *, langID 0x409 'en-US') nameID=1 (Family)
    string, parsed straight out of the 'name' table -- independent of
    HarfBuzz's face.get_name()/list_names().
    """
    name_offset, _ = _find_sfnt_table(font_bytes, b"name")
    count = struct.unpack(">H", font_bytes[name_offset + 2 : name_offset + 4])[0]
    string_offset = struct.unpack(">H", font_bytes[name_offset + 4 : name_offset + 6])[0]
    record_base = name_offset + 6
    for i in range(count):
        record = font_bytes[record_base + i * 12 : record_base + i * 12 + 12]
        platform_id, _encoding_id, language_id, name_id, length, rec_offset = (
            struct.unpack(">HHHHHH", record)
        )
        if platform_id == 3 and name_id == 1 and language_id == 0x409:
            start = name_offset + string_offset + rec_offset
            return font_bytes[start : start + length].decode("utf-16-be")
    return ""
