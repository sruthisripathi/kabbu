from pathlib import Path

import pytest

from skill_lang import (
    At, Goto, Return, Say, SkillSyntaxError, SkillValidationError, VisitAll, World,
    parse, parse_and_validate, simulate,
)

WORLD = World.load(Path(__file__).parent.parent / "world.example.json")

VALID = [
    "GOTO(kitchen)",
    "VISIT_ALL() { SAY(dinner_ready) }",
    "AT(17:00) { GOTO(bedroom); SAY(reminder_call); RETURN() }",
    "GOTO(terrace); SAY(bring_clothes_in); RETURN()",
    "EMOTE(happy); SAY(dinner_ready)",
    "WAIT(30); GOTO(kitchen)",
    "GOTO(bedroom); PLAY(msg_1); RETURN();",
    "AT(07:30) { VISIT_ALL() { SAY(dinner_ready) } }",
    "GOTO(kitchen);\n  SAY(need_water);\n  RETURN()",
    "RETURN()",
]

SYNTAX_ERRORS = [
    "",                                    # empty
    "GOTO kitchen",                        # missing brackets
    "GOTO(Kitchen)",                       # names are lowercase
    "goto(kitchen)",                       # keywords are uppercase
    "GOTO(kitchen",                        # unclosed bracket
    "GOTO(kitchen) SAY(dinner_ready)",     # missing semicolon
    "VISIT_ALL { SAY(dinner_ready) }",     # missing ()
    "VISIT_ALL() { }",                     # empty block
    "AT(25:00) { GOTO(hall) }",            # invalid hour
    "AT(5pm) { GOTO(hall) }",              # wrong time format
    "WAIT(-5)",                            # negative number
    "RETURN(hall)",                        # RETURN takes no argument
    "FLY(kitchen)",                        # unknown skill
    'SAY("dinner")',                       # quotes not allowed
]

VALIDATION_ERRORS = [
    "GOTO(garage)",                                             # unknown room
    "SAY(unknown_clip)",                                        # unknown clip
    "PLAY(msg_99)",                                             # unknown recording
    "EMOTE(furious)",                                           # unknown emotion
    "WAIT(0)",                                                  # too short
    "WAIT(9999)",                                               # too long
    "AT(08:00) { AT(09:00) { GOTO(hall) } }",                   # nested AT
    "VISIT_ALL() { VISIT_ALL() { SAY(dinner_ready) } }",        # nested VISIT_ALL
    "VISIT_ALL() { GOTO(kitchen) }",                            # GOTO inside VISIT_ALL
]


@pytest.mark.parametrize("text", VALID)
def test_valid_programs(text):
    parse_and_validate(text, WORLD)


@pytest.mark.parametrize("text", SYNTAX_ERRORS)
def test_syntax_errors(text):
    with pytest.raises(SkillSyntaxError):
        parse(text)


@pytest.mark.parametrize("text", VALIDATION_ERRORS)
def test_validation_errors(text):
    with pytest.raises(SkillValidationError):
        parse_and_validate(text, WORLD)


def test_too_many_statements():
    text = "; ".join(["WAIT(1)"] * 31)
    with pytest.raises(SkillValidationError):
        parse_and_validate(text, WORLD)


def test_ast_shape():
    program = parse("AT(17:00) { GOTO(bedroom); SAY(reminder_call); RETURN() }")
    assert program == (At("17:00", (Goto("bedroom"), Say("reminder_call"), Return())),)


def test_visit_all_trace():
    program = parse_and_validate("VISIT_ALL() { SAY(dinner_ready) }", WORLD)
    assert simulate(program, WORLD) == [
        ("say", "dinner_ready", "hall"),
        ("walk", "hall", "kitchen"), ("say", "dinner_ready", "kitchen"),
        ("walk", "kitchen", "bedroom"), ("say", "dinner_ready", "bedroom"),
        ("walk", "bedroom", "balcony"), ("say", "dinner_ready", "balcony"),
        ("walk", "balcony", "terrace"), ("say", "dinner_ready", "terrace"),
    ]


def test_scheduled_block_runs_after_immediate_part():
    program = parse_and_validate(
        "AT(17:00) { GOTO(bedroom); SAY(reminder_call); RETURN() }; EMOTE(happy)", WORLD
    )
    assert simulate(program, WORLD) == [
        ("schedule", "17:00"),
        ("emote", "happy"),
        ("at", "17:00"),
        ("walk", "hall", "bedroom"),
        ("say", "reminder_call", "bedroom"),
        ("walk", "bedroom", "hall"),
    ]


def test_equivalent_programs_have_equal_traces():
    a = parse_and_validate("GOTO(kitchen); SAY(dinner_ready); RETURN()", WORLD)
    b = parse_and_validate("GOTO(kitchen); SAY(dinner_ready); GOTO(hall)", WORLD)
    assert simulate(a, WORLD) == simulate(b, WORLD)
