# textkit

Small, dependency-free text utilities.

## Usage

```python
from textkit import normalize_whitespace, strip_accents

normalize_whitespace("  a   b ")  # "a b"
strip_accents("Crème")  # "Creme"
```

From the command line:

```sh
python3 -m textkit normalize "  a   b "
```

## Tests

```sh
python3 -m unittest discover -s tests -t . -v
```
