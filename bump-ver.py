"""Synchronize the skill version from version.txt; never change harness versions."""

import argparse
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parent
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
# Register new current-version declarations here; historical versions are not targets.
TARGETS = {
    "SKILL.md": re.compile(rb'(?m)^  version: "([^"\r\n]+)"\r?$'),
    "README.md": re.compile(rb'(?m)^Version: `([^`\r\n]+)`[^\r\n]*\r?$'),
}


def atomic_write(path, content):
    descriptor, name = tempfile.mkstemp(prefix=".oversee-version-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.chmod(name, path.stat().st_mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def update(root, requested=None, dry_run=False):
    version_path = root / "version.txt"
    original = {version_path: version_path.read_bytes()}
    current = original[version_path].decode("ascii").strip()
    parsed = SEMVER.fullmatch(current)
    if not parsed:
        raise ValueError("version.txt must contain a semantic version, such as 0.1.0.")
    matches = {}
    for filename, pattern in TARGETS.items():
        path = root / filename
        original[path] = path.read_bytes()
        found = list(pattern.finditer(original[path]))
        if len(found) != 1 or found[0][1].decode("ascii") != current:
            raise ValueError(f"{filename}: expected exactly one current version matching version.txt ({current}).")
        matches[path] = found[0].span(1)
    if requested is None:
        return current
    if requested in ("major", "minor", "patch"):
        numbers = [int(parsed[i]) for i in (1, 2, 3)]
        index = ("major", "minor", "patch").index(requested)
        numbers[index] += 1
        numbers[index + 1:] = [0] * (2 - index)
        target = ".".join(map(str, numbers))
    else:
        target = requested
    if not SEMVER.fullmatch(target):
        raise ValueError("Use major, minor, patch, or an exact semantic version (for example 0.2.0-rc.1).")
    encoded = target.encode("ascii")
    newline = b"\r\n" if original[version_path].endswith(b"\r\n") else b"\n"
    changed = {version_path: encoded + newline}
    for path, (start, end) in matches.items():
        changed[path] = original[path][:start] + encoded + original[path][end:]
    if not dry_run:
        written = []
        try:
            for path, content in changed.items():
                atomic_write(path, content)
                written.append(path)
        except OSError as error:
            failures = []
            for path in reversed(written):
                try:
                    atomic_write(path, original[path])
                except OSError:
                    failures.append(path.name)
            if failures:
                raise OSError("Version update failed; restore these files manually: " + ", ".join(failures)) from error
            raise
    return f"{current} -> {target}" + (" (dry run)" if dry_run else "")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", help="major, minor, patch, or an exact semantic version")
    parser.add_argument("--check", action="store_true", help="Check synchronization without modifying files")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview a bump without writing")
    args = parser.parse_args(argv)
    if args.check and (args.version or args.dry_run):
        parser.error("--check cannot be combined with a version or --dry-run.")
    if not args.check and not args.version:
        parser.error("Provide a version/bump, or use --check.")
    try:
        print(update(ROOT, args.version, args.dry_run))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Version error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
