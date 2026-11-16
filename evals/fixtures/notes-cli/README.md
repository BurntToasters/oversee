# notes-cli

A tiny command-line notes tool. Commands use `python3`; on Windows, use `python`.

## Commands

- `python3 notes.py add <title> <body>` — adds a note and prints its id
- `python3 notes.py list` — prints one line per note: `<id>: <title>`
- `python3 notes.py show <id>` — prints the title and body of a note

## Tests

```bash
python3 -m unittest discover -s tests -v
```
