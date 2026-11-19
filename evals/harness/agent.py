"""Run ``opencode run`` headless, in an isolated HOME that holds only the skills under test.

Isolation matters: skills installed globally (``~/.agents/skills``,
``~/.claude/skills``, ...), the user's ``AGENTS.md``, plugins, and MCP servers
would all leak into the runs. Each run gets a fresh HOME with:

- ``opencode.json``: the user's resolved ``provider`` block, the plugins named in
  ``EVALS_PLUGINS`` (those that supply providers), all tool permissions
  allowed except paths outside the work tree (the installed skills stay
  reachable, for their ``references/``), and a tool-less ``evaluator`` agent
  for the judge and the simulated user;
- ``auth.json`` (and ``~/.aws``) symlinked from the real HOME, for credentials;
- ``skills/``: the skill folders under test, or nothing for a no-skill baseline.

The real ``~/.cache`` is shared, so provider packages download only once.
"""

from __future__ import annotations

import functools
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["EVALUATOR_AGENT", "TurnResult", "make_home", "run_turn"]

EVALUATOR_AGENT = "evaluator"

_REAL_HOME = Path.home()
_REAL_CONFIG = _REAL_HOME / ".config" / "opencode" / "opencode.json"
# Documentation inside a skill folder, never installed for a run.
_DOCS = shutil.ignore_patterns("README.md", "examples")


@dataclass
class TurnResult:
    """One ``opencode run`` call: its events and a summary of them."""

    events: list[dict] = field(default_factory=list)
    session_id: str | None = None
    texts: list[str] = field(default_factory=list)
    tokens: int = 0
    cost: float = 0.0
    duration_s: float = 0.0
    returncode: int = 0
    timed_out: bool = False
    stderr: str = ""

    @property
    def final_text(self) -> str:
        """The last text part the assistant wrote in this turn."""
        return self.texts[-1] if self.texts else ""

    @property
    def ok(self) -> bool:
        """True when the call exited cleanly and produced a session."""
        return self.returncode == 0 and not self.timed_out and self.session_id is not None


def make_home(home: Path, skills: list[Path]) -> None:
    """Create an isolated opencode HOME at ``home``.

    :param home: Folder to create; must not exist.
    :param skills: Skill folders to install (each holds a ``SKILL.md``).
    :raises FileExistsError: When ``home`` exists.
    """
    config_dir = home / ".config" / "opencode"
    data_dir = home / ".local" / "share" / "opencode"
    config_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    (home / ".local" / "state").mkdir(parents=True)

    auth = _REAL_HOME / ".local" / "share" / "opencode" / "auth.json"
    if auth.exists():
        (data_dir / "auth.json").symlink_to(auth)

    aws = _REAL_HOME / ".aws"
    if aws.exists():
        (home / ".aws").symlink_to(aws)

    (config_dir / "opencode.json").write_text(json.dumps(_config(config_dir / "skills"), indent=2))
    for skill in skills:
        # nwork's README.md and examples/ are documentation only: leave them out, as before nwork had its own folder.
        shutil.copytree(skill, config_dir / "skills" / skill.name, ignore=_DOCS)


def run_turn(
    prompt: str,
    *,
    workdir: Path,
    home: Path,
    model: str,
    session_id: str | None = None,
    agent: str | None = None,
    timeout_s: int = 1200,
) -> TurnResult:
    """Send one message with ``opencode run --format json`` and parse the events.

    The prompt goes through stdin: a single argv string is capped at 128 KiB.

    :param prompt: Message to send.
    :param workdir: Folder the agent works in.
    :param home: Isolated HOME made by ``make_home``.
    :param model: ``provider/model`` id.
    :param session_id: Session to continue, for multi-turn runs.
    :param agent: opencode agent name; ``None`` uses the default agent.
    :param timeout_s: Wall-clock limit for the call.
    :return: The parsed turn; check ``ok`` before trusting it.
    """
    cmd = ["opencode", "run", "--format", "json", "-m", model, "--dir", str(workdir)]
    if session_id:
        cmd += ["--session", session_id]

    if agent:
        cmd += ["--agent", agent]

    result = TurnResult(session_id=session_id)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=_env(home),
            cwd=workdir,
        )
        stdout, result.stderr, result.returncode = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = _decode(exc.stdout)
        result.stderr = _decode(exc.stderr)
        result.timed_out = True
        result.returncode = -1

    result.duration_s = round(time.monotonic() - start, 1)
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        result.events.append(event)
        result.session_id = event.get("sessionID") or result.session_id
        part = event.get("part") or {}
        if event.get("type") == "text" and part.get("text"):
            result.texts.append(part["text"])
        elif event.get("type") == "step_finish":
            result.tokens += int((part.get("tokens") or {}).get("total") or 0)
            result.cost += float(part.get("cost") or 0)

    return result


@functools.cache
def _providers() -> dict:
    """The user's ``provider`` block, as opencode resolves it.

    ``opencode debug config`` gives the resolved config: it accepts JSONC, and
    it holds the providers that plugins add (for example a proxy plugin), which
    the isolated HOME does not load. When that fails, read ``opencode.json``.
    """
    try:
        proc = subprocess.run(
            ["opencode", "debug", "config"], capture_output=True, text=True, timeout=60, cwd=_REAL_HOME,
        )
        if proc.returncode == 0:
            return json.loads(proc.stdout).get("provider", {})
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    try:
        return json.loads(_REAL_CONFIG.read_text()).get("provider", {})
    except (OSError, json.JSONDecodeError):
        return {}


def _plugins() -> list:
    """The user's plugins named in ``EVALS_PLUGINS``, for plugins that supply providers.

    ``EVALS_PLUGINS`` is a comma-separated list of substrings of plugin specs,
    for example ``tarvos-proxy``. Other plugins stay out of the runs. In their
    options, ``{file:~/...}`` points to the real HOME, not the isolated one.
    ``opencode debug config`` redacts secrets, so the plugins come from
    ``opencode.json`` itself, read as JSONC (whole-line ``//`` comments).
    """
    wanted = [w.strip() for w in os.environ.get("EVALS_PLUGINS", "").split(",") if w.strip()]
    if not wanted:
        return []

    try:
        lines = [line for line in _REAL_CONFIG.read_text().splitlines() if not line.lstrip().startswith("//")]
        plugins = json.loads("\n".join(lines)).get("plugin", [])
    except (OSError, json.JSONDecodeError):
        return []

    def spec(entry: object) -> str:
        return entry[0] if isinstance(entry, list) and entry else str(entry)

    kept = json.dumps([e for e in plugins if any(w in spec(e) for w in wanted)])

    return json.loads(kept.replace("{file:~/", "{file:" + str(_REAL_HOME) + "/"))


def _config(skills_dir: Path) -> dict:
    """Build the isolated ``opencode.json`` from the user's provider settings.

    :param skills_dir: Where the skills under test are installed. Tools may
        reach it, so that a skill can load its bundled ``references/``.
    """
    return {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "share": "disabled",
        "provider": _providers(),
        "plugin": _plugins(),
        # Headless runs cannot answer permission prompts. Keep the agent inside
        # its throwaway work tree instead, except for the installed skills, so
        # that a skill can read its references/. The last matching rule wins.
        "permission": {
            "*": "allow",
            "external_directory": {"*": "deny", f"{skills_dir}/*": "allow"},
        },
        "agent": {
            EVALUATOR_AGENT: {
                "description": "Tool-less evaluator for the judge and the simulated user.",
                "mode": "primary",
                "tools": {"*": False},
                "permission": {"*": "deny"},
            },
        },
    }


def _env(home: Path) -> dict[str, str]:
    """Environment for opencode: isolated HOME and XDG folders, shared cache."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE")}
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        XDG_DATA_HOME=str(home / ".local" / "share"),
        XDG_STATE_HOME=str(home / ".local" / "state"),
        XDG_CACHE_HOME=os.environ.get("XDG_CACHE_HOME", str(_REAL_HOME / ".cache")),
    )

    return env


def _decode(data: bytes | str | None) -> str:
    """Decode partial output captured on timeout."""
    if data is None:
        return ""

    return data if isinstance(data, str) else data.decode(errors="replace")
