"""Hidden contract check for T01 (slugify), run inside a fixture work tree.

Not shown to the agent. Exits 0 when ``textkit.slugify`` meets the contract
table in the fixture's design.md, 1 otherwise, printing each failure.
"""

import re
import sys

sys.path.insert(0, ".")

CASES = [
    (("Hello, World!",), {}, "hello-world"),
    (("Crème Brûlée 2",), {}, "creme-brulee-2"),
    (("  --a--b--  ",), {}, "a-b"),
    (("hello world foo",), {"max_length": 13}, "hello-world"),
    (("hello world foo",), {"max_length": 11}, "hello-world"),
    (("abcdefghij",), {"max_length": 4}, "abcd"),
    (("Straße",), {}, "stra-e"),
    (("a b",), {"max_length": 10}, "a-b"),
    (("one two three four",), {"max_length": 9}, "one-two"),
    (("one two three four",), {"max_length": 8}, "one-two"),
    (("one two three four",), {"max_length": 7}, "one-two"),
    (("one two three four",), {"max_length": 6}, "one"),
]
ERRORS = [
    (("!!!",), {}, ValueError, "slug is empty"),
    (("Привет",), {}, ValueError, "slug is empty"),
    (("a",), {"max_length": 0}, ValueError, None),
    ((3,), {}, TypeError, None),
]
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def main() -> int:
    """Run every case and report failures."""
    try:
        from textkit import slugify
    except Exception as exc:  # noqa: BLE001 - any import failure fails the check
        print(f"FAIL import: {exc!r}")

        return 1

    failures = 0
    for args, kwargs, expected in CASES:
        try:
            got = slugify(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            got = f"raised {exc!r}"
        if got != expected or not SLUG.fullmatch(str(got)):
            failures += 1
            print(f"FAIL slugify{args}{kwargs or ''}: expected {expected!r}, got {got!r}")

    for args, kwargs, error, message in ERRORS:
        try:
            got = slugify(*args, **kwargs)
        except error as exc:
            if message and message not in str(exc):
                failures += 1
                print(f"FAIL slugify{args}{kwargs or ''}: message {str(exc)!r} lacks {message!r}")
            continue
        except Exception as exc:  # noqa: BLE001
            got = f"raised {exc!r}"
        failures += 1
        print(f"FAIL slugify{args}{kwargs or ''}: expected {error.__name__}, got {got!r}")

    print(f"{len(CASES) + len(ERRORS) - failures}/{len(CASES) + len(ERRORS)} contract cases pass")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
