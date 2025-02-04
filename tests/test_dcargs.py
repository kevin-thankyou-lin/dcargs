import dataclasses
import enum
import pathlib
from typing import ClassVar, Optional

import pytest
from typing_extensions import Annotated, Final, Literal  # Backward compatibility.

import dcargs


def test_basic():
    @dataclasses.dataclass
    class ManyTypes:
        i: int
        s: str
        f: float
        p: pathlib.Path

    assert dcargs.parse(
        ManyTypes,
        args=[
            "--i",
            "5",
            "--s",
            "5",
            "--f",
            "5",
            "--p",
            "~",
        ],
    ) == ManyTypes(i=5, s="5", f=5.0, p=pathlib.Path("~"))


def test_init_false():
    @dataclasses.dataclass
    class InitFalseDataclass:
        i: int
        s: str
        f: float
        p: pathlib.Path
        ignored: str = dataclasses.field(default="hello", init=False)

    assert dcargs.parse(
        InitFalseDataclass,
        args=[
            "--i",
            "5",
            "--s",
            "5",
            "--f",
            "5",
            "--p",
            "~",
        ],
    ) == InitFalseDataclass(i=5, s="5", f=5.0, p=pathlib.Path("~"))

    with pytest.raises(SystemExit):
        dcargs.parse(
            InitFalseDataclass,
            args=["--i", "5", "--s", "5", "--f", "5", "--p", "~", "--ignored", "blah"],
        )


def test_required():
    @dataclasses.dataclass
    class A:
        x: int

    with pytest.raises(SystemExit):
        dcargs.parse(A, args=[])


def test_flag():
    """When boolean flags have no default value, they must be explicitly specified."""

    @dataclasses.dataclass
    class A:
        x: bool

    with pytest.raises(SystemExit):
        dcargs.parse(A, args=[])

    with pytest.raises(SystemExit):
        dcargs.parse(A, args=["--x", "1"])
    with pytest.raises(SystemExit):
        dcargs.parse(A, args=["--x", "true"])
    assert dcargs.parse(A, args=["--x", "True"]) == A(True)

    with pytest.raises(SystemExit):
        dcargs.parse(A, args=["--x", "0"])
    with pytest.raises(SystemExit):
        dcargs.parse(A, args=["--x", "false"])
    assert dcargs.parse(A, args=["--x", "False"]) == A(False)


def test_flag_default_false():
    """When boolean flags default to False, a --flag-name flag must be passed in to flip it to True."""

    @dataclasses.dataclass
    class A:
        x: bool = False

    assert dcargs.parse(A, args=[]) == A(False)
    assert dcargs.parse(A, args=["--x"]) == A(True)


def test_flag_default_true():
    """When boolean flags default to True, a --no-flag-name flag must be passed in to flip it to False."""

    @dataclasses.dataclass
    class A:
        x: bool = True

    assert dcargs.parse(A, args=[]) == A(True)
    assert dcargs.parse(A, args=["--no-x"]) == A(False)


def test_flag_default_true_nested():
    """When boolean flags default to True, a --no-flag-name flag must be passed in to flip it to False."""

    @dataclasses.dataclass
    class NestedDefaultTrue:
        x: bool = True

    @dataclasses.dataclass
    class A:
        x: NestedDefaultTrue

    assert dcargs.parse(A, args=[]) == A(NestedDefaultTrue(True))
    assert dcargs.parse(A, args=["--x.no-x"]) == A(NestedDefaultTrue(False))


def test_default():
    @dataclasses.dataclass
    class A:
        x: int = 5

    assert dcargs.parse(A, args=[]) == A()


def test_default_factory():
    @dataclasses.dataclass
    class A:
        x: int = dataclasses.field(default_factory=lambda: 5)

    assert dcargs.parse(A, args=[]) == A()


def test_optional():
    @dataclasses.dataclass
    class A:
        x: Optional[int]

    assert dcargs.parse(A, args=[]) == A(x=None)


def test_enum():
    class Color(enum.Enum):
        RED = enum.auto()
        GREEN = enum.auto()
        BLUE = enum.auto()

    @dataclasses.dataclass
    class EnumClassA:
        color: Color

    @dataclasses.dataclass
    class EnumClassB:
        color: Color = Color.GREEN

    assert dcargs.parse(EnumClassA, args=["--color", "RED"]) == EnumClassA(
        color=Color.RED
    )
    assert dcargs.parse(EnumClassB, args=[]) == EnumClassB()


def test_literal():
    @dataclasses.dataclass
    class A:
        x: Literal[0, 1, 2]

    assert dcargs.parse(A, args=["--x", "1"]) == A(x=1)
    with pytest.raises(SystemExit):
        assert dcargs.parse(A, args=["--x", "3"])


def test_literal_enum():
    class Color(enum.Enum):
        RED = enum.auto()
        GREEN = enum.auto()
        BLUE = enum.auto()

    @dataclasses.dataclass
    class A:
        x: Literal[Color.RED, Color.GREEN]

    assert dcargs.parse(A, args=["--x", "RED"]) == A(x=Color.RED)
    assert dcargs.parse(A, args=["--x", "GREEN"]) == A(x=Color.GREEN)
    with pytest.raises(SystemExit):
        assert dcargs.parse(A, args=["--x", "BLUE"])


def test_optional_literal():
    @dataclasses.dataclass
    class A:
        x: Optional[Literal[0, 1, 2]]

    assert dcargs.parse(A, args=["--x", "1"]) == A(x=1)
    with pytest.raises(SystemExit):
        assert dcargs.parse(A, args=["--x", "3"])
    assert dcargs.parse(A, args=[]) == A(x=None)


def test_annotated():
    """Annotated[] is a no-op."""

    @dataclasses.dataclass
    class A:
        x: Annotated[int, "some label"] = 3

    assert dcargs.parse(A, args=["--x", "5"]) == A(x=5)


def test_annotated_optional():
    """Annotated[] is a no-op."""

    @dataclasses.dataclass
    class A:
        x: Annotated[Optional[int], "some label"] = 3

    assert dcargs.parse(A, args=[]) == A(x=3)
    assert dcargs.parse(A, args=["--x", "5"]) == A(x=5)


def test_optional_annotated():
    """Annotated[] is a no-op."""

    @dataclasses.dataclass
    class A:
        x: Optional[Annotated[int, "some label"]] = 3

    assert dcargs.parse(A, args=[]) == A(x=3)
    assert dcargs.parse(A, args=["--x", "5"]) == A(x=5)


def test_final():
    """Final[] is a no-op."""

    @dataclasses.dataclass
    class A:
        x: Final[int] = 3

    assert dcargs.parse(A, args=["--x", "5"]) == A(x=5)


def test_final_optional():
    @dataclasses.dataclass
    class A:
        x: Final[Optional[int]] = 3

    assert dcargs.parse(A, args=[]) == A(x=3)
    assert dcargs.parse(A, args=["--x", "5"]) == A(x=5)


def test_classvar():
    """ClassVar[] types should be skipped."""

    @dataclasses.dataclass
    class A:
        x: ClassVar[int] = 5

    with pytest.raises(SystemExit):
        dcargs.parse(A, args=["--x", "1"])
    assert dcargs.parse(A, args=[]) == A()


# TODO: implement this!
# def test_optional_nested():
#     @dataclasses.dataclass
#     class OptionalNestedChild:
#         y: int
#         z: int
#
#     @dataclasses.dataclass
#     class OptionalNested:
#         x: int
#         b: Optional[OptionalNestedChild]
#
#     assert dcargs.parse(OptionalNested, args=["--x", "1"]) == OptionalNested(
#         x=1, b=None
#     )
#     with pytest.raises(SystemExit):
#         dcargs.parse(OptionalNested, args=["--x", "1", "--b.y", "3"])
#     with pytest.raises(SystemExit):
#         dcargs.parse(OptionalNested, args=["--x", "1", "--b.z", "3"])
#
#     assert dcargs.parse(
#         OptionalNested, args=["--x", "1", "--b.y", "2", "--b.z", "3"]
#     ) == OptionalNested(x=1, b=OptionalNestedChild(y=2, z=3))


def test_parse_empty_description():
    """If the file has no dosctring, it should be treated as an empty string."""

    @dataclasses.dataclass
    class A:
        x: int = 0

    assert dcargs.parse(A, description=None, args=[]) == A(x=0)
