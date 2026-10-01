# textkit

Small, dependency-free text utilities.

## Usage

```python
from textkit import normalize_whitespace, slugify, strip_accents

normalize_whitespace("  a   b ")  # "a b"
strip_accents("Crème")  # "Creme"
slugify("Crème Brûlée 2")  # "creme-brulee-2"
slugify("hello world foo", max_length=13)  # "hello-world" (cut at the last hyphen)
```

From the command line:

```sh
python3 -m textkit normalize "  a   b "
```

`slugify` raises `ValueError("slug is empty")` when nothing is left, for example for `"!!!"`.

## Tests

```sh
python3 -m unittest discover -s tests -t . -v
```
