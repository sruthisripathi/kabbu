"""Kabbu skill language: parse text into a program, then validate it against a world."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from lark import Lark, Transformer
from lark.exceptions import LarkError

EMOTIONS = {"neutral", "happy", "focused", "thinking", "surprised", "sleepy", "pout", "dizzy"}
MAX_STATEMENTS = 30
WAIT_MIN, WAIT_MAX = 1, 600


class SkillSyntaxError(ValueError):
    """The text is not a well-formed program."""


class SkillValidationError(ValueError):
    """The program is well-formed but not valid for this world."""


@dataclass(frozen=True)
class Goto:
    room: str


@dataclass(frozen=True)
class VisitAll:
    body: tuple


@dataclass(frozen=True)
class Say:
    clip: str


@dataclass(frozen=True)
class Play:
    recording: str


@dataclass(frozen=True)
class At:
    time: str
    body: tuple


@dataclass(frozen=True)
class Wait:
    seconds: int


@dataclass(frozen=True)
class Return:
    pass


@dataclass(frozen=True)
class Emote:
    name: str


Statement = Union[Goto, VisitAll, Say, Play, At, Wait, Return, Emote]
Program = tuple  # tuple[Statement, ...]


@dataclass
class World:
    rooms: list[str]
    home: str
    clips: set[str]
    recordings: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: str | Path) -> "World":
        data = json.loads(Path(path).read_text())
        return cls(
            rooms=list(data["rooms"]),
            home=data["home"],
            clips=set(data["clips"]),
            recordings=set(data.get("recordings", [])),
        )


class _ToAst(Transformer):
    def program(self, items):
        return tuple(items)

    def block(self, items):
        return items[0]

    def goto(self, items):
        return Goto(str(items[0]))

    def visit_all(self, items):
        return VisitAll(items[0])

    def say(self, items):
        return Say(str(items[0]))

    def play(self, items):
        return Play(str(items[0]))

    def at(self, items):
        return At(str(items[0]), items[1])

    def wait(self, items):
        return Wait(int(items[0]))

    def ret(self, items):
        return Return()

    def emote(self, items):
        return Emote(str(items[0]))


_GRAMMAR = (Path(__file__).parent / "grammar.lark").read_text()
_PARSER = Lark(_GRAMMAR, parser="lalr", lexer="contextual")


def parse(text: str) -> Program:
    """Text -> program. Raises SkillSyntaxError if the text is malformed."""
    try:
        tree = _PARSER.parse(text)
    except LarkError as e:
        raise SkillSyntaxError(str(e).splitlines()[0]) from None
    return _ToAst().transform(tree)


def validate(program: Program, world: World) -> None:
    """Raises SkillValidationError with every problem found, or returns None."""
    errors: list[str] = []
    count = _check(program, world, errors, inside=())
    if count > MAX_STATEMENTS:
        errors.append(f"too many statements ({count} > {MAX_STATEMENTS})")
    if errors:
        raise SkillValidationError("; ".join(errors))


def _check(program: Program, world: World, errors: list[str], inside: tuple[str, ...]) -> int:
    count = 0
    for st in program:
        count += 1
        if isinstance(st, Goto):
            if st.room not in world.rooms:
                errors.append(f"unknown room '{st.room}'")
            if "VISIT_ALL" in inside:
                errors.append("GOTO inside VISIT_ALL is not allowed")
        elif isinstance(st, Say):
            if st.clip not in world.clips:
                errors.append(f"unknown clip '{st.clip}'")
        elif isinstance(st, Play):
            if st.recording not in world.recordings:
                errors.append(f"unknown recording '{st.recording}'")
        elif isinstance(st, Emote):
            if st.name not in EMOTIONS:
                errors.append(f"unknown emotion '{st.name}'")
        elif isinstance(st, Wait):
            if not WAIT_MIN <= st.seconds <= WAIT_MAX:
                errors.append(f"WAIT must be {WAIT_MIN}-{WAIT_MAX} seconds, got {st.seconds}")
        elif isinstance(st, VisitAll):
            if "VISIT_ALL" in inside:
                errors.append("VISIT_ALL cannot be nested")
            count += _check(st.body, world, errors, inside + ("VISIT_ALL",))
        elif isinstance(st, At):
            if inside:
                errors.append("AT must be at the top level")
            count += _check(st.body, world, errors, inside + ("AT",))
    return count


def parse_and_validate(text: str, world: World) -> Program:
    program = parse(text)
    validate(program, world)
    return program
