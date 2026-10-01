"""Command-line interface: ``python3 -m textkit <command> ...``."""

import argparse
import sys

from textkit.core import normalize_whitespace


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and run one subcommand.

    :param argv: Arguments without the program name; ``None`` reads ``sys.argv``.
    :return: The process exit code.
    """
    parser = argparse.ArgumentParser(prog="textkit")
    commands = parser.add_subparsers(dest="command", required=True)

    normalize = commands.add_parser("normalize", help="collapse whitespace")
    normalize.add_argument("text")
    normalize.set_defaults(handler=_normalize)

    args = parser.parse_args(argv)

    return args.handler(args)


def _normalize(args: argparse.Namespace) -> int:
    """Print the normalized text."""
    print(normalize_whitespace(args.text))

    return 0


if __name__ == "__main__":
    sys.exit(main())
