"""Check that the book's listings are the companion code, and that they run as printed.

Run from anywhere: python build/check_listings.py [chN_*.md ...]
With no arguments every chN_*.md is checked. Use the interpreter of the book's environment.

1. Drift: every code line of a listing must appear in the companion code (comments and spacing are ignored).
2. Execution: each chapter's listings run in book order in one namespace, in a fresh interpreter, with the
   working directory book/code, as a reader pasting them into a notebook would. Listings whose caption says
   "excerpt" or "abridged" are skipped: they are for reading, and nothing later may depend on them.
Prints one line per listing (OK, SKIP, FAIL, DRIFT) and exits 1 if any listing failed or drifted.
build_html.py imports `drift` from here and prints its findings during every build.
"""

import contextlib
import io
import multiprocessing
import os
import re
import sys
import time
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
CODE = BOOK / "code"
# SUBJECT-SPECIFIC: code outside book/code that listings may quote (e.g. a model port).
EXTRA_SOURCES = []
LISTING = re.compile(r"^\**(Listing \d+\.\d+[a-z]?)\**([^\n]*)\n\n```python\n(.*?)\n```", re.M | re.S)
READING_ONLY = re.compile(r"\b(excerpt|abridged)\b", re.I)
# Catch-up lines replay script cells (bookutil.run_cells), so they exist only in the book.
CATCH_UP = re.compile(r"^(import bookutil|bookutil\.run_cells\(.*\))$")


def listings(md_text):
    """Return the listings of a chapter in book order as (label, caption, code) tuples.

    md_text: chapter Markdown. A listing is a paragraph that starts with `Listing n.m` (bold or not)
    followed by a blank line and a ```python block.
    """
    return [(m.group(1), m.group(2).strip(" *"), m.group(3)) for m in LISTING.finditer(md_text)]


def drift(md_path):
    """Return (label, first stale line, number of stale lines) for each listing that differs from the companion code.

    md_path: chapter Markdown. Sources: code/chN_*.py of that chapter, every shared module in code/
    (any .py file not named chN_*), and EXTRA_SOURCES. Catch-up lines are exempt.
    """

    def norm(line):
        return re.sub(r"\s+", " ", re.sub(r"(^|\s)#.*$", "", line)).strip()

    n = re.match(r"ch(\d+)_", md_path.name).group(1)
    files = sorted(CODE.glob(f"ch{n}_*.py")) + [p for p in CODE.glob("*.py") if not re.match(r"ch\d+_", p.name)]
    known = {norm(line) for f in files + EXTRA_SOURCES for line in Path(f).read_text().splitlines()} | {"", "..."}
    found = []
    for label, _, code in listings(md_path.read_text()):
        stale = [line.strip() for line in code.splitlines() if norm(line) not in known and not CATCH_UP.match(norm(line))]
        if stale:
            found.append((label, stale[0], len(stale)))
    return found


def run_chapter(md_path):
    """Run one chapter's listings in book order in this process; exit with the number of failures.

    md_path: chapter Markdown. Call it in a fresh interpreter (main block below), because chapters set
    environment variables before their imports and the listings change global state.
    """
    os.chdir(CODE)
    sys.path.insert(0, str(CODE))
    os.environ.setdefault("MPLBACKEND", "Agg")
    namespace = {"__name__": "__main__"}
    failed = 0
    for label, caption, code in listings(Path(md_path).read_text()):
        if READING_ONLY.search(caption):
            print(f"SKIP {label}  {caption[:70]}", flush=True)
            continue
        start = time.time()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(code, label, "exec"), namespace)
            print(f"OK   {label} ({time.time() - start:.0f}s)  {caption[:70]}", flush=True)
        except Exception as e:
            failed += 1
            print(f"FAIL {label}  {caption[:70]}\n     {type(e).__name__}: {str(e)[:200]}", flush=True)
    sys.exit(failed)


if __name__ == "__main__":
    chapters = [BOOK / a for a in sys.argv[1:]] or sorted(BOOK.glob("ch[0-9]*_*.md"))
    bad = 0
    for md in chapters:
        print(f"== {md.name}", flush=True)
        for label, line, count in drift(md):
            bad += 1
            print(f"DRIFT {label}: {count} line(s) not in the companion code, first: {line}")
        proc = multiprocessing.get_context("spawn").Process(target=run_chapter, args=(md,))
        proc.start()
        proc.join()
        bad += proc.exitcode != 0  # failures, or a crash (negative code)
    sys.exit(1 if bad else 0)
