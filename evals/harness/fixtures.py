"""Build fixture work trees from the toy repo and layered ``.ndev/`` and ``.nwork/`` states.

A state is a folder under ``fixtures/states/<name>/`` with:

- ``state.json``: ``{"extends": "<parent state>", "description": "..."}``
  (``extends`` is optional);
- ``base/``: files overlaid on the repo, then committed as the base commit;
- ``work/``: files overlaid after that commit and left uncommitted, so that
  ``git diff`` shows them (for example code written by an earlier ``nbuild``).

Parents apply first, so a child only holds the files it adds or replaces.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

__all__ = [
    "FIXTURES",
    "HIDDEN",
    "IGNORED",
    "Changes",
    "copy_tree",
    "diff_trees",
    "is_ignored",
    "list_states",
    "materialize",
    "state_chain",
]

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
HIDDEN = FIXTURES / "hidden"

# Paths that never count as changes: caches and VCS internals.
IGNORED = (
    ".git",
    ".git/*",
    "*/__pycache__/*",
    "__pycache__/*",
    "*.pyc",
    ".pytest_cache/*",
    ".mypy_cache/*",
    ".ruff_cache/*",
)

_GIT = ["git", "-c", "user.name=ndev-evals", "-c", "user.email=ndev-evals@localhost", "-c", "commit.gpgsign=false"]


class Changes(dict):
    """Files ``created``, ``modified``, and ``deleted`` between two trees (relative POSIX paths)."""

    @property
    def all(self) -> list[str]:
        """Every changed path, sorted."""
        return sorted(self["created"] + self["modified"] + self["deleted"])


def list_states() -> list[str]:
    """Return the names of every state, sorted."""
    return sorted(p.parent.name for p in (FIXTURES / "states").glob("*/state.json"))


def state_chain(name: str) -> list[Path]:
    """Return the folders of ``name`` and its ancestors, root first.

    :param name: State name.
    :return: State folders, root first.
    :raises FileNotFoundError: When a state in the chain does not exist.
    :raises ValueError: When the chain has a cycle.
    """
    chain: list[Path] = []
    seen: set[str] = set()
    current: str | None = name
    while current:
        if current in seen:
            raise ValueError(f"state cycle at {current!r}")

        seen.add(current)
        folder = FIXTURES / "states" / current
        meta_path = folder / "state.json"
        if not meta_path.is_file():
            raise FileNotFoundError(f"unknown state {current!r}: {meta_path} missing")

        chain.append(folder)
        current = json.loads(meta_path.read_text()).get("extends")

    return chain[::-1]


def materialize(state: str, dest: Path) -> None:
    """Create a git work tree at ``dest`` for ``state``.

    :param state: State name.
    :param dest: Target folder; must not exist.
    :raises FileExistsError: When ``dest`` exists.
    :raises subprocess.CalledProcessError: When a git command fails.
    """
    if dest.exists():
        raise FileExistsError(dest)

    chain = state_chain(state)
    shutil.copytree(FIXTURES / "repo", dest)
    for folder in chain:
        if (folder / "base").is_dir():
            shutil.copytree(folder / "base", dest, dirs_exist_ok=True)

    subprocess.run([*_GIT, "init", "-q", "-b", "main"], cwd=dest, check=True)
    subprocess.run([*_GIT, "add", "-A"], cwd=dest, check=True)
    subprocess.run([*_GIT, "commit", "-q", "-m", f"base: {state}"], cwd=dest, check=True)
    for folder in chain:
        if (folder / "work").is_dir():
            shutil.copytree(folder / "work", dest, dirs_exist_ok=True)


def copy_tree(src: Path, dest: Path) -> None:
    """Copy ``src`` to ``dest`` without ignored paths (see ``IGNORED``)."""

    def ignore(folder: str, names: list[str]) -> set[str]:
        """Skip names whose relative path is ignored."""
        rel = Path(folder).relative_to(src)

        return {n for n in names if is_ignored((rel / n).as_posix())}

    shutil.copytree(src, dest, ignore=ignore, symlinks=True)


def diff_trees(before: Path, after: Path) -> Changes:
    """Compare two trees by content hash, skipping ignored paths.

    :param before: Tree before the run.
    :param after: Tree after the run.
    :return: The created, modified, and deleted paths.
    """
    old = _hashes(before)
    new = _hashes(after)

    return Changes(
        created=sorted(set(new) - set(old)),
        modified=sorted(p for p in set(old) & set(new) if old[p] != new[p]),
        deleted=sorted(set(old) - set(new)),
    )


def is_ignored(rel: str) -> bool:
    """Tell whether relative POSIX path ``rel`` is a cache or VCS path."""
    return any(fnmatch.fnmatch(rel, pattern) for pattern in IGNORED)


def _hashes(root: Path) -> dict[str, str]:
    """Map every non-ignored file under ``root`` to its SHA-256."""
    if not root.is_dir():
        return {}

    result = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_file() and not is_ignored(rel):
            result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()

    return result
