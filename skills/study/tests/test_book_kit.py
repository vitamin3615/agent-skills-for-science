"""Tests for the book kit's runnable-listing tools: bookutil and check_listings."""

## Imports
## Load the kit modules by path; everything runs offline on temporary files.
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import traceback
import unittest
from pathlib import Path


## Kit setup
## Make the kit's code and build directories importable without installing anything.
KIT = Path(__file__).resolve().parents[1] / "assets" / "book-kit"
sys.path.insert(0, str(KIT / "code"))
sys.path.insert(0, str(KIT / "build"))

import bookutil  # noqa: E402
from check_listings import READING_ONLY, listings  # noqa: E402


## Shared plumbing
## fetch caches a download; run_cells replays the cells above a named one.
class BookUtilTests(unittest.TestCase):
    """Exercise bookutil against temporary files."""

    def setUp(self) -> None:
        """Create a scratch directory per test."""
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_fetch_downloads_once(self) -> None:
        """A second fetch returns the cached file without downloading again."""
        source = self.tmp / "source.txt"
        source.write_text("ACGT")
        path = bookutil.fetch(source.as_uri(), "sub/seq.txt", root=self.tmp / "data")
        source.write_text("changed")
        again = bookutil.fetch(source.as_uri(), "sub/seq.txt", root=self.tmp / "data")
        self.assertEqual((path, again.read_text()), (again, "ACGT"))
        self.assertEqual(list(path.parent.glob("*.part")), [])

    def test_run_cells_stops_before_named_cell(self) -> None:
        """Cells above `until` run in the given namespace; the named cell and later ones do not."""
        script = self.tmp / "ch1_demo.py"
        script.write_text("# %% Setup\na = 1\n\n# %% Teachers\nb = a + 1\n\n# %% Listing 1.3 Use them\nc = 3\n")
        namespace = {}
        bookutil.run_cells(str(script), namespace, until="Listing 1.3")
        self.assertEqual((namespace["a"], namespace["b"], "c" in namespace), (1, 2, False))

    def test_run_cells_range_keeps_line_numbers(self) -> None:
        """`start` skips the cells above it, and an error points at its line in the script."""
        script = self.tmp / "ch1_demo.py"
        script.write_text("# %% Setup\na = 1\n\n# %% Cache\nb = a + 1\n\n# %% Listing 1.3\nc = 3\n")
        namespace = {"a": 10}
        bookutil.run_cells(str(script), namespace, start="Cache", until="Listing 1.3")
        self.assertEqual((namespace["a"], namespace["b"], "c" in namespace), (10, 11, False))
        try:
            bookutil.run_cells(str(script), {}, start="Cache")  # `a` is defined only in the skipped Setup cell
        except NameError as error:
            frame = traceback.extract_tb(error.__traceback__)[-1]
        self.assertEqual((frame.filename, frame.lineno), (str(script), 5))

    def test_run_cells_unknown_title_fails(self) -> None:
        """A cell title that does not exist raises instead of running the whole script."""
        script = self.tmp / "ch1_demo.py"
        script.write_text("# %% Setup\na = 1\n")
        with self.assertRaises(IndexError):
            bookutil.run_cells(str(script), {}, until="Listing 9.9")


## Listing check
## A temporary book whose chapter has one listing of each outcome.
CHAPTER = textwrap.dedent('''\
    # Chapter 1

    **Listing 1.0** Setup

    ```python
    x = 2
    ```

    Listing 1.1a Uses the setup

    ```python
    y = x * 3
    ```

    **Listing 1.2** The helper (excerpt of `bookutil.py`)

    ```python
    return path
    ```

    **Listing 1.3** Relies on an unshown cell

    ```python
    z = hidden + y
    ```

    **Listing 1.4** Edited after the run

    ```python
    w = y + 100
    ```

    **Listing 1.5** Catches up on the hidden cell

    ```python
    import bookutil

    bookutil.run_cells("ch1_demo.py", globals(), start="Hidden", until="Listings")  # hidden
    v = hidden + x
    ```
    ''')
SCRIPT = "# %% Setup\nx = 2\n\n# %% Hidden\nhidden = 1\n\n# %% Listings\ny = x * 3  # 6\nz = hidden + y\nw = y + 1\nv = hidden + x\n"


class CheckListingsTests(unittest.TestCase):
    """Run check_listings.py on a temporary book and read its report."""

    def setUp(self) -> None:
        """Lay out book/{build,code} with the kit tools, one script and one chapter."""
        self.book = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.book)
        (self.book / "build").mkdir()
        (self.book / "code").mkdir()
        shutil.copy(KIT / "build" / "check_listings.py", self.book / "build")
        shutil.copy(KIT / "code" / "bookutil.py", self.book / "code")
        (self.book / "code" / "ch1_demo.py").write_text(SCRIPT)
        (self.book / "ch1_demo.md").write_text(CHAPTER)

    def run_check(self) -> subprocess.CompletedProcess:
        """Run the copied checker with this interpreter and return the finished process."""
        return subprocess.run([sys.executable, str(self.book / "build" / "check_listings.py")],
                              capture_output=True, text=True, timeout=120)

    def test_parser_reads_captions_and_code(self) -> None:
        """Bold and plain captions, lettered numbers, and the reading-only marker are recognised."""
        found = listings(CHAPTER)
        self.assertEqual([label for label, _, _ in found],
                         ["Listing 1.0", "Listing 1.1a", "Listing 1.2", "Listing 1.3", "Listing 1.4", "Listing 1.5"])
        self.assertEqual(found[1][2], "y = x * 3")
        self.assertEqual([bool(READING_ONLY.search(caption)) for _, caption, _ in found],
                         [False, False, True, False, False, False])

    def test_report_flags_hidden_names_drift_and_skips_excerpts(self) -> None:
        """Hidden-cell names FAIL, edited lines DRIFT, excerpts SKIP, and the exit code is 1."""
        result = self.run_check()
        out = result.stdout
        self.assertEqual(result.returncode, 1, out + result.stderr)
        self.assertIn("OK   Listing 1.0", out)
        self.assertIn("OK   Listing 1.1a", out)
        self.assertIn("SKIP Listing 1.2", out)
        self.assertIn("FAIL Listing 1.3", out)
        self.assertIn("NameError: name 'hidden' is not defined", out)
        self.assertIn("DRIFT Listing 1.4: 1 line(s) not in the companion code, first: w = y + 100", out)
        self.assertNotIn("DRIFT Listing 1.2", out)  # quoted from the shared module bookutil.py
        self.assertIn("OK   Listing 1.5", out)  # the catch-up line runs the hidden cell
        self.assertNotIn("DRIFT Listing 1.5", out)  # and is exempt from the drift check

    def test_clean_chapter_exits_zero(self) -> None:
        """A chapter whose listings are all shown and current passes."""
        (self.book / "ch1_demo.md").write_text(CHAPTER.split("**Listing 1.3**")[0])
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


## Test entrypoint
## Support direct local execution as well as unittest discovery.
if __name__ == "__main__":
    unittest.main()
