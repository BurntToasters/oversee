# notes-cli

A tiny command-line notes tool.

## Commands

- `python notes.py add <title> <body>` — adds a note and prints its id
- `python notes.py list` — prints one line per note: `<id>: <title>`
- `python notes.py show <id>` — prints the title and body of a note

## Tests

```bash
python -m unittest discover -s tests -v
```
