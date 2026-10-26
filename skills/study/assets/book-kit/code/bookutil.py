"""Plumbing shared by every chapter of the book: cached downloads and catching up on earlier script cells.

Copy this file into the book's `code/` directory. Subject modules (data readers, model loaders) build on it.
Keep the subject's mechanisms out of here: a reader must see in the listings every line the chapter teaches.
"""

import re
import urllib.request
from pathlib import Path


def fetch(url, name, root="data"):
    """Return the local path of a downloaded file, downloading it first if it is missing.

    url: source address (https:// or file://).
    name: file name, or a relative path, under `root`.
    root: cache directory, git-ignored, relative to the working directory (the book's code/ directory).
    """
    path = Path(root) / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".part")  # a broken download never looks complete
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(path)
    return path


def run_cells(script, namespace, start=None, until=None):
    """Run a contiguous range of the `# %%` cells of a companion script in `namespace`.

    Lets a listing pick up the state of a long prerequisite (a training run, a data cache) in one visible line.
    script: path of the script, relative to the working directory.
    namespace: dict the cells run in, normally `globals()`, so their names become available to the caller.
    start: start of the title of the first cell to run, as written after `# %%`; None runs from the top.
    until: start of the title of the first cell NOT to run, e.g. "Listing 5.13"; None runs to the end.
    """
    cells = re.split(r"^(?=# %%)", Path(script).read_text(), flags=re.M)
    titles = [cell.split("\n", 1)[0].removeprefix("# %%").strip() for cell in cells]

    def find(prefix):
        return [i for i, title in enumerate(titles) if title.startswith(prefix)][0]  # IndexError: no such cell

    lo = find(start) if start else 0
    hi = find(until) if until else len(cells)
    pad = "\n" * "".join(cells[:lo]).count("\n")  # keeps the script's line numbers in tracebacks
    exec(compile(pad + "".join(cells[lo:hi]), script, "exec"), namespace)
