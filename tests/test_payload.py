from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "skills" / "oversee"
REFERENCES = PAYLOAD / "references"
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
# Built from parts so a repository-wide grep for these names finds only CHANGELOG history.
REMOVED = [stem + ext for stem, ext in [(b"harnesses", b".md"), (b"install", b".sh"), (b"install", b".bat"),
                                        (b"uninstall", b".sh"), (b"uninstall", b".bat"), (b"remote-" b"install", b".ps1")]]
LINK = re.compile(r"\]\(([^)\s]+)\)")


def frontmatter():
    text = (PAYLOAD / "SKILL.md").read_text(encoding="utf-8")
    return text.split("---", 2)[1]


def payload_files():
    return [p for p in PAYLOAD.rglob("*") if p.is_file()]


class PayloadTests(unittest.TestCase):
    def test_layout_for_skills_cli(self):
        # `npx skills add` copies the whole skill folder, so it must hold only the payload.
        self.assertFalse((ROOT / "SKILL.md").exists())
        self.assertEqual(sorted(p.name for p in PAYLOAD.iterdir()), ["SKILL.md", "references"])
        self.assertTrue(all(p.suffix == ".md" and p.is_file() for p in REFERENCES.iterdir()))
        self.assertIn("\nname: oversee\n", frontmatter())

    def test_frontmatter_keys_and_description(self):
        keys = set(re.findall(r"(?m)^([A-Za-z][\w-]*):", frontmatter()))
        self.assertLessEqual(keys, SPEC_KEYS)
        description = re.search(r"(?m)^description: (.+)$", frontmatter())[1]
        self.assertLessEqual(len(description), 640)

    def test_byte_budgets(self):
        self.assertLessEqual(len((PAYLOAD / "SKILL.md").read_bytes()), 13500)
        sizes = {p.name: len(p.read_bytes()) for p in REFERENCES.glob("*.md")}
        for name, size in sizes.items():
            self.assertLessEqual(size, 3500, name)
        self.assertLessEqual(sum(sizes.values()), 16000)
        self.assertLess(len((ROOT / "AGENTS.md").read_bytes()), 32768)

    def test_every_reference_linked_and_links_resolve(self):
        text = (PAYLOAD / "SKILL.md").read_text(encoding="utf-8")
        local = [t for t in LINK.findall(text) if "://" not in t]
        for target in local:
            self.assertTrue((PAYLOAD / target.split("#")[0]).is_file(), target)
        linked = {(PAYLOAD / t.split("#")[0]).resolve() for t in local}
        for path in REFERENCES.glob("*.md"):
            self.assertIn(path.resolve(), linked, path.name)

    def test_no_removed_names_or_carriage_returns(self):
        self.assertFalse((REFERENCES / REMOVED[0].decode()).exists())
        for path in payload_files():
            data = path.read_bytes()
            self.assertNotIn(b"\r", data, path.name)
            for name in REMOVED:
                self.assertNotIn(name, data, f"{path.name}: {name.decode()}")


if __name__ == "__main__":
    unittest.main()
