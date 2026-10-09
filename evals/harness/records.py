"""The ``ndev-next/1`` record checks, loaded from the copy that ``nwork`` bundles.

The code lives in ``skills/ndev-next/nwork/scripts/check_records.py``: the
installed skill runs it alone, so it must live inside the skill folder. This
module executes that file and re-exports all its names, private helpers
included (``harness.checks`` uses ``VERIFIED``), so the harness has one copy of
the rules. Static type checkers do not see the re-exported names.
"""

from __future__ import annotations

import sys
import types

from harness.cases import NWORK, SKILL_DIRS

__all__ = [
    "FORMAT_LINE",
    "SCRIPT",
    "Record",
    "eligible",
    "format_problems",
    "link_problems",
    "load_records",
    "main",
    "now_listed",
    "now_problems",
    "problems",
    "section_problems",
]

SCRIPT = SKILL_DIRS[NWORK] / "scripts" / "check_records.py"

# Load the script with compile and exec, not an import: an import would write
# a __pycache__/ into the skill folder, which every eval run then installs.
# The module goes into sys.modules because dataclasses looks it up there.
_module = types.ModuleType("nwork_check_records")
_module.__file__ = str(SCRIPT)
sys.modules[_module.__name__] = _module
exec(compile(SCRIPT.read_text(), str(SCRIPT), "exec"), _module.__dict__)
globals().update({k: v for k, v in vars(_module).items() if not k.startswith("__")})
