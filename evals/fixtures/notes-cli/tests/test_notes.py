import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import notes
import store


class NotesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "notes.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = notes.main(["--file", str(self.db), *args])
        return code, out.getvalue(), err.getvalue()

    def test_add_and_list(self) -> None:
        code, out, _ = self.run_cli("add", "Buy milk", "2 liters")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "1")

        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "1: Buy milk")

    def test_show_found_and_missing(self) -> None:
        store.add_note("First", "Body text", self.db)
        code, out, _ = self.run_cli("show", "1")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "First\nBody text")

        code, _, err = self.run_cli("show", "99")
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


if __name__ == "__main__":
    unittest.main()
