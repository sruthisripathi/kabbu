"""Try a program from the command line:

    python -m skill_lang "VISIT_ALL() { SAY(dinner_ready) }"
"""
import sys
from pathlib import Path

from . import SkillSyntaxError, SkillValidationError, World, parse_and_validate, simulate

world = World.load(Path(__file__).parent.parent / "world.example.json")
text = " ".join(sys.argv[1:]) or "VISIT_ALL() { SAY(dinner_ready) }"
try:
    program = parse_and_validate(text, world)
except (SkillSyntaxError, SkillValidationError) as e:
    print(f"{type(e).__name__}: {e}")
    sys.exit(1)
print("Program:", program)
for event in simulate(program, world):
    print("  ", event)
