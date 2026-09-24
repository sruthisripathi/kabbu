"""Run a validated program on the room map and return what Kabbu would do.

Two programs that produce the same trace are execution-equivalent, which is
how the language model's outputs are scored (K-52).
"""
from __future__ import annotations

from .language import At, Emote, Goto, Play, Program, Return, Say, VisitAll, Wait, World

Event = tuple  # e.g. ("walk", "hall", "kitchen"), ("say", "dinner_ready", "kitchen")


def simulate(program: Program, world: World, start_room: str | None = None) -> list[Event]:
    state = {"room": start_room or world.home}
    trace: list[Event] = []
    scheduled: list[At] = []

    for st in program:
        if isinstance(st, At):
            scheduled.append(st)
            trace.append(("schedule", st.time))
        else:
            _run(st, world, state, trace)

    for st in sorted(scheduled, key=lambda a: a.time):
        trace.append(("at", st.time))
        for inner in st.body:
            _run(inner, world, state, trace)

    return trace


def _walk(to: str, state: dict, trace: list[Event]) -> None:
    if state["room"] != to:
        trace.append(("walk", state["room"], to))
        state["room"] = to


def _run(st, world: World, state: dict, trace: list[Event]) -> None:
    if isinstance(st, Goto):
        _walk(st.room, state, trace)
    elif isinstance(st, Return):
        _walk(world.home, state, trace)
    elif isinstance(st, Say):
        trace.append(("say", st.clip, state["room"]))
    elif isinstance(st, Play):
        trace.append(("play", st.recording, state["room"]))
    elif isinstance(st, Wait):
        trace.append(("wait", st.seconds))
    elif isinstance(st, Emote):
        trace.append(("emote", st.name))
    elif isinstance(st, VisitAll):
        for room in world.rooms:
            _walk(room, state, trace)
            for inner in st.body:
                _run(inner, world, state, trace)
    else:
        raise TypeError(f"unexpected statement {st!r}")
