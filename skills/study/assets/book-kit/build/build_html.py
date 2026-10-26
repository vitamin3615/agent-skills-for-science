"""Build the HTML book from the Markdown chapters.

Run from anywhere: python build/build_html.py (needs pandoc 3+ on PATH and beautifulsoup4)
Optional arguments name the .md files (relative to book/) to build; with none,
README.md, every chN_*.md and build/test_components.md (if present) are built.
Never edit the generated .html files: edit the Markdown, a fragment in
build/visuals/, or this template, then rebuild.
"""
import copy
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString

from check_listings import READING_ONLY, drift

BOOK = Path(__file__).resolve().parent.parent
PANDOC = shutil.which("pandoc") or sys.exit("pandoc 3+ must be on PATH")
# SUBJECT-SPECIFIC: book title and the display/body/mono faces of this subject's identity.
BOOK_TITLE = "AlphaGenome from the Ground Up"
FONTS = (
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500"
    "&family=IBM+Plex+Sans+Condensed:wght@500;600;700"
    "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap"
)
LIBS = [
    "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js",
]
MATHJAX_CONFIG = (
    "window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']],tags:'none'},"
    "svg:{fontCache:'global'}};"
)
THEME_BOOT = (
    "try{var t=localStorage.getItem('ag-theme');"
    "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}"
)

# SUBJECT-SPECIFIC: signature device. The example is a resolution ruler:
# (exponent of 2 in bp, label, sublabel), with the stops each chapter highlights.
RULER = [(0, "1 bp", "base"), (7, "128 bp", "token"), (11, "2,048 bp", "pair bin"), (20, "1 Mb", "window")]
RULER_BY_CHAPTER = {1: [0, 20], 2: [0, 7], 3: [7, 11, 20], 4: [0, 7, 11], 5: [0, 20]}

CALLOUTS = [
    ("note", re.compile(r"^note\b", re.I)),
    ("why", re.compile(r"^why\b", re.I)),
    ("pitfall", re.compile(r"^pitfall\b", re.I)),
    ("bio", re.compile(r"^biology link\b", re.I)),
    ("check", re.compile(r"^check yourself\b", re.I)),
]
LISTING_RE = re.compile(r"^\s*Listing\s+(\d+)\.(\d+[a-z]?)")  # 3.1a: lettered listings keep their letter
FIGURE_RE = re.compile(r"^\s*Figure\s+\d+\.\d+")
NOTE_RE = re.compile(r"(?:^|\n)#(\d+)[ \t]+")
SHAPE_RE = re.compile(r"^\(.*,.*\)$")
CHAPTER_LINK_RE = re.compile(r"^(ch\d+_[^/#?]*)\.md(#.*)?$")
VISUAL_RE = re.compile(r"<!--\s*VISUAL-ID:\s*([A-Za-z0-9_-]+)\s*-->")


def run_pandoc(md):
    """Convert Markdown text to an HTML5 fragment with pandoc.

    md: Markdown source. Returns the HTML string (math left as \\(..\\) / \\[..\\] for MathJax).
    """
    out = subprocess.run(
        [PANDOC, "-f", "markdown", "-t", "html5", "--mathjax", "--no-highlight", "--wrap=preserve"],
        input=md, capture_output=True, text=True, check=True,
    )
    return out.stdout


def text_of(tag):
    """Return the stripped plain text of a tag."""
    return tag.get_text().strip()


def next_tag(node):
    """Return the next sibling that is a Tag (skipping whitespace), or None."""
    node = node.next_sibling
    while node is not None and not getattr(node, "name", None):
        if isinstance(node, NavigableString) and not isinstance(node, Comment) and node.strip():
            return None
        node = node.next_sibling
    return node


def new(soup, name, cls=None, **attrs):
    """Create a tag with an optional class and attributes (underscores become hyphens)."""
    tag = soup.new_tag(name, **{k.replace("_", "-"): v for k, v in attrs.items()})
    if cls:
        tag["class"] = cls
    return tag


# ---------- README facts ----------

def readme_facts(readme_md):
    """Parse the README chapter table.

    readme_md: README.md text. Returns {chapter number: (title, question, [node ids], md file name)}.
    """
    facts = {}
    row = re.compile(r"^\|\s*(\d+)\s*\|\s*\[(.+?)\]\((ch\d+_[^)]+)\.md\)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", re.M)
    for m in row.finditer(readme_md):
        nodes = [n.strip() for n in m.group(5).split(",")]
        facts[int(m.group(1))] = (m.group(2), m.group(4), nodes, m.group(3) + ".html")
    return facts


def parse_map(src):
    """Parse the whole-model mermaid map.

    src: mermaid source. Returns (node titles, edges as (from, label, to), highlighted node ids).
    """
    titles = {n: re.sub(r"<br\s*/?>", " ", t) for n, t in re.findall(r'^\s*(N\d+)\["(.*?)"\]', src, re.M)}
    edges = re.findall(r'^\s*(N\d+)\s*--\s*"(.*?)"\s*-->\s*(N\d+)', src, re.M)
    highlights = re.findall(r"^\s*style\s+(N\d+)\s", src, re.M)
    return titles, edges, highlights


# ---------- component transforms ----------

def fix_links(soup):
    """Rewrite relative chN_*.md links to .html; other links are left as written."""
    for a in soup.find_all("a", href=True):
        m = CHAPTER_LINK_RE.match(a["href"])
        if m:
            a["href"] = m.group(1) + ".html" + (m.group(2) or "")


def mark_shapes(soup):
    """Give inline tensor-shape code such as `(B, L, 4)` the .shape chip class."""
    for code in soup.find_all("code"):
        if code.parent.name != "pre" and SHAPE_RE.match(text_of(code)):
            code["class"] = code.get("class", []) + ["shape"]


def wrap_tables(soup):
    """Wrap each table in a horizontally scrollable container."""
    for table in soup.find_all("table"):
        wrap = new(soup, "div", "table-wrap")
        table.wrap(wrap)


def color_dna(soup):
    """SUBJECT-SPECIFIC signature detail; a no-op when no `.dna` blocks exist.

    Color A/C/G/T/N in `pre.dna` blocks and `code.dna` spans with run-length spans."""
    targets = [p.code for p in soup.select("pre.dna") if p.code] + soup.select("code.dna")
    for code in targets:
        seq = code.get_text()
        code.clear()
        for m in re.finditer(r"([ACGTNacgtn])\1*|[^ACGTNacgtn]+", seq):
            run = m.group(0)
            if run[0].upper() in "ACGTN":
                span = new(soup, "span", run[0].upper())
                span.string = run
                code.append(span)
            else:
                code.append(NavigableString(run))


def normalize_code(soup):
    """Give every fenced block a language-* class and wrap it in a .codebox.

    Blocks that are not python or bash get language-plaintext so highlight.js skips them.
    """
    langs = {"python": "python", "py": "python", "bash": "bash", "sh": "bash", "shell": "bash", "console": "bash"}
    for pre in soup.find_all("pre"):
        classes = pre.get("class", [])
        if "mermaid" in classes or "codebox" in pre.parent.get("class", []):
            continue
        code = pre.code
        if code is None:
            continue
        lang = next((langs[c] for c in classes if c in langs), "plaintext")
        pre["class"] = ["dna"] if "dna" in classes else ["code"]
        code["class"] = ["language-" + lang]
        pre.wrap(new(soup, "div", "codebox"))


def build_listings(soup):
    """Turn `**Listing n.m** caption` + code block (+ `#1` notes) into figure.listing."""
    for p in list(soup.find_all("p")):
        m = LISTING_RE.match(p.get_text())
        box = next_tag(p)
        if not m or box is None or "codebox" not in box.get("class", []):
            continue
        fig = new(soup, "figure", "listing", id="listing-%s-%s" % m.groups())
        cap = new(soup, "figcaption")
        label = new(soup, "span", "cap-label")
        label.string = "Listing %s.%s" % m.groups()
        cap.append(label)
        kids = list(p.children)
        lead = kids[0]
        if getattr(lead, "name", None) in ("strong", "em") and LISTING_RE.match(text_of(lead)):
            tail = text_of(lead)[LISTING_RE.match(text_of(lead)).end():]
            kids = ([NavigableString(tail)] if tail.strip() else []) + kids[1:]
        elif isinstance(lead, NavigableString):
            kids[0] = NavigableString(LISTING_RE.sub("", str(lead), count=1))
        if kids and isinstance(kids[0], NavigableString):
            kids[0] = NavigableString(re.sub(r"^[\s.:—–-]+", "", str(kids[0])))
        cap.append(label)
        cap.append(NavigableString(" "))
        for k in kids:
            cap.append(k.extract() if hasattr(k, "extract") else k)
        if READING_ONLY.search(cap.get_text()):  # excerpt or abridged: not part of the runnable sequence
            fig["class"] = ["listing", "listing--reading"]
            tag = new(soup, "span", "cap-tag")
            tag.string = "for reading"
            cap.append(NavigableString(" "))
            cap.append(tag)
        p.replace_with(fig)
        fig.append(cap)
        fig.append(box.extract())
        attach_notes(soup, fig, "#1" in box.get_text())


def attach_notes(soup, fig, code_has_marks):
    """Move `#n ...` paragraphs or a list that follow a listing into ol.listing-notes.

    fig: the figure.listing. code_has_marks: whether the code contains #n markers.
    """
    notes = []
    sib = next_tag(fig)
    while sib is not None:
        if sib.name == "p" and re.match(r"^#\d+\s", sib.get_text().lstrip()):
            for k in list(sib.children):
                if isinstance(k, NavigableString):
                    parts = NOTE_RE.split(str(k))
                    if parts[0].strip() and notes:
                        notes[-1][1].append(NavigableString(parts[0]))
                    for i in range(1, len(parts), 2):
                        notes.append((parts[i], [NavigableString(parts[i + 1])]))
                elif notes:
                    notes[-1][1].append(copy.copy(k))
            nxt = next_tag(sib)
            sib.decompose()
            sib = nxt
        elif sib.name in ("ol", "ul") and not notes and (code_has_marks or re.match(r"^#\d+\s", sib.get_text().lstrip())):
            for i, li in enumerate(sib.find_all("li", recursive=False), 1):
                content = [copy.copy(c) for c in li.children]
                if content and isinstance(content[0], NavigableString):
                    content[0] = NavigableString(re.sub(r"^#\d+\s+", "", str(content[0])))
                notes.append((str(i), content))
            nxt = next_tag(sib)
            sib.decompose()
            sib = nxt
            break
        else:
            break
    if not notes:
        return
    ol = new(soup, "ol", "listing-notes")
    for num, content in notes:
        li = new(soup, "li")
        badge = new(soup, "span", "badge")
        badge.string = num
        li.append(badge)
        body = new(soup, "span")
        for c in content:
            body.append(c)
        if body.contents and isinstance(body.contents[-1], NavigableString):
            body.contents[-1].replace_with(NavigableString(str(body.contents[-1]).rstrip()))
        li.append(body)
        ol.append(li)
    fig.append(ol)


def label_caption(soup, cap):
    """Wrap a leading `Figure n.m` in a figcaption with the display-face label span."""
    first = cap.contents[0] if cap.contents else None
    if isinstance(first, NavigableString):
        m = FIGURE_RE.match(str(first))
        if m:
            label = new(soup, "span", "cap-label")
            label.string = m.group(0).strip()
            first.replace_with(label)
            label.insert_after(NavigableString(str(first)[m.end():]))


def build_figures(soup, base):
    """Style pandoc figures (images) and wrap captioned mermaid/map blocks in figures.

    base: folder of the source Markdown, which image paths are relative to.
    """
    for fig in soup.find_all("figure"):
        if "listing" in fig.get("class", []):
            continue
        fig["class"] = ["fig", "fig--wide"]
        for img in fig.find_all("img"):
            img["loading"] = "lazy"
            # intrinsic size reserves the box before a lazy image loads, so anchor jumps land where aimed
            src = base / img["src"]
            if src.suffix == ".png" and src.is_file():
                img["width"], img["height"] = struct.unpack(">II", src.read_bytes()[16:24])
        cap = fig.figcaption
        if cap:
            cap.attrs.pop("aria-hidden", None)
            label_caption(soup, cap)
    for node in soup.select("pre.mermaid, div.ag-map"):
        p = next_tag(node)
        if p is None or p.name != "p" or not FIGURE_RE.match(p.get_text()):
            continue
        fig = new(soup, "figure", "ag-fig" if "ag-map" in node.get("class", []) else "fig fig--wide")
        node.wrap(fig)
        cap = new(soup, "figcaption")
        em = p.find("em", recursive=False)
        for k in list((em or p).children):
            cap.append(k.extract())
        p.decompose()
        label_caption(soup, cap)
        fig.append(cap)


def build_mermaid(soup, links):
    """Turn mermaid fences into pre.mermaid; the whole-model map becomes div.ag-map.

    links: {node id: chapter html} for clickable nodes (index only).
    Returns the parsed (titles, edges, highlights) of the map, or None.
    """
    found = None
    for pre in soup.select("pre.mermaid"):
        src = pre.get_text()
        # SUBJECT-SPECIFIC: map detection. Match node ids that only the whole-subject map uses.
        if "N1" in src and "N10" in src and found is None:
            titles, edges, highlights = parse_map(src)
            found = (titles, edges, highlights)
            div = new(soup, "div", "ag-map")
            div["data-highlight"] = ",".join(highlights)
            if links:
                div["data-links"] = json.dumps(links)
            ns = new(soup, "noscript")
            ul = new(soup, "ul")
            for a, label, b in edges:
                li = new(soup, "li")
                li.string = "%s (%s) %s %s (%s)." % (a, titles[a], label, b, titles[b])
                ul.append(li)
            ns.append(ul)
            div.append(ns)
            pre.replace_with(div)
        else:
            code = pre.code
            if code is not None:
                text = code.get_text()
                pre.clear()
                pre.string = text
    return found


def build_callouts(soup, key):
    """Convert labeled blockquotes into callouts and Predict boxes.

    key: page key used in predict ids, e.g. 'ch2'.
    """
    k = 0
    for bq in soup.find_all("blockquote"):
        p = bq.find("p")
        strong = p.find("strong") if p else None
        if strong is None or p.contents[0] is not strong:
            continue
        label = text_of(strong).rstrip(".:").strip()
        kind = "predict" if re.match(r"^predict$", label, re.I) else next((c for c, rx in CALLOUTS if rx.match(label)), None)
        if kind is None:
            continue
        strong.extract()
        if p.contents and isinstance(p.contents[0], NavigableString):
            p.contents[0].replace_with(NavigableString(str(p.contents[0]).lstrip(" :.—-")))
        if kind == "predict":
            k += 1
            aside = new(soup, "aside", "predict")
            lab = new(soup, "span", "predict__label")
            lab.string = "Predict"
            aside.append(lab)
            details = bq.find("details") or (next_tag(bq) if next_tag(bq) is not None and next_tag(bq).name == "details" else None)
            q = new(soup, "div", "predict__q")
            for c in list(bq.children):
                if c is not details and (getattr(c, "name", None) or str(c).strip()):
                    q.append(c.extract())
            aside.append(q)
            ta = new(soup, "textarea", id="predict-%s-%d" % (key, k), rows="3", placeholder="Write your prediction before opening the answer.")
            ta["aria-label"] = "Your prediction"
            aside.append(ta)
            if details is not None:
                details.extract()
                details["class"] = ["predict__answer"]
                details.summary.string = "Reveal answer"
                aside.append(details)
            bq.replace_with(aside)
        else:
            aside = new(soup, "aside", ["callout", "callout--" + kind])
            lab = new(soup, "span", "callout__label")
            lab.string = label
            aside.append(lab)
            for c in list(bq.children):
                aside.append(c.extract())
            bq.replace_with(aside)


def build_exercises(soup):
    """Style the Exercises section (numbered items) and `Expected observable` labels."""
    for h in soup.find_all("h2"):
        if "exercise" not in text_of(h).lower():
            continue
        sib = next_tag(h)
        while sib is not None and sib.name != "h2":
            if sib.name == "ol":
                sib["class"] = ["exercises"]
            elif sib.name == "p" and re.match(r"^Exercise\s+\d", sib.get_text()):
                sib["class"] = ["exercise"]
            sib = next_tag(sib)
    for p in soup.find_all("p"):
        if re.match(r"^Exercise\s+\d+\.\d+", p.get_text()):
            p["class"] = ["exercise"]
    rx = re.compile(r"(Expected observables?:?)", re.I)
    for s in list(soup.find_all(string=rx)):
        parent = s.parent
        if parent.name in ("strong", "em") and rx.fullmatch(text_of(parent)):
            parent["class"] = ["obs-label"]
        elif parent.name not in ("script", "style", "code", "pre"):
            pieces = rx.split(str(s))
            nodes = []
            for i, piece in enumerate(pieces):
                if i % 2:
                    span = new(soup, "span", "obs-label")
                    span.string = piece.rstrip(":")
                    nodes.append(span)
                    nodes.append(NavigableString(":" if piece.endswith(":") else ""))
                elif piece:
                    nodes.append(NavigableString(piece))
            for n in reversed(nodes):
                s.insert_after(n)
            s.extract()


def extract_covers(soup):
    """Pull the 'This chapter covers' label and its list out of the body.

    Returns a div.opener__covers, or None when the chapter has no such list.
    """
    for el in soup.find_all(["p", "h2", "h3"]):
        if re.match(r"^This chapter covers", text_of(el), re.I) and text_of(el).lower().rstrip(":. ") == "this chapter covers":
            ul = next_tag(el)
            if ul is None or ul.name not in ("ul", "ol"):
                return None
            box = new(soup, "div", "opener__covers")
            lab = new(soup, "p", "opener__label")
            lab.string = "This chapter covers"
            box.append(lab)
            box.append(ul.extract())
            el.decompose()
            return box
    return None


def ruler_svg(active):
    """Return the resolution-ruler SVG (log2 scale, 1 bp to 1 Mb).

    active: list of exponents of 2 (0, 7, 11, 20) to highlight in --mark.
    """
    x0, x1 = 24, 416
    pos = lambda e: x0 + (x1 - x0) * e / 20
    out = ['<svg viewBox="0 0 440 52" role="img" aria-label="Resolution ruler on a log scale, 1 bp to 1 Mb. Highlighted: %s.">'
           % ", ".join(lab for e, lab, _ in RULER if e in active)]
    out.append('<line class="r-axis" x1="%d" y1="16" x2="%d" y2="16"/>' % (x0, x1))
    for e in range(21):
        out.append('<line class="r-minor" x1="%.1f" y1="12" x2="%.1f" y2="20"/>' % (pos(e), pos(e)))
    for e, lab, sub in RULER:
        on = " on" if e in active else ""
        out.append('<line class="r-tick" x1="%.1f" y1="9" x2="%.1f" y2="23"/>' % (pos(e), pos(e)))
        out.append('<circle class="r-dot%s" cx="%.1f" cy="16" r="4"/>' % (on, pos(e)))
        out.append('<text class="%s" x="%.1f" y="37">%s</text>' % (on.strip(), pos(e), lab))
        out.append('<text class="sub" x="%.1f" y="48">%s</text>' % (pos(e), sub))
    out.append("</svg>")
    return "".join(out)


def toc_html(soup):
    """Build the nested contents list from h2/h3 headings of the main content.

    Returns an HTML string; math inside headings is kept so MathJax typesets it.
    """
    heads = [h for h in soup.find_all(["h2", "h3"]) if h.get("id") and not h.find_parent(["details", "aside"])]
    out, depth = ["<ol>"], 0
    for i, h in enumerate(heads):
        level = 2 if h.name == "h2" else 3
        if level == 3 and depth == 0:
            out.append("<li><ol>")
            depth = 1
        elif level == 2 and depth == 1:
            out.append("</ol></li>")
            depth = 0
        inner = "".join(str(c) for c in copy.deepcopy(h).children)
        out.append('<li><a href="#%s">%s</a></li>' % (h["id"], inner))
    if depth:
        out.append("</ol></li>")
    out.append("</ol>")
    return "".join(out)


def code_appendix(soup, n):
    """Return the 'Companion code' section for chapter n (None if no scripts exist yet).

    n: chapter number. Reads code/chN_*.py plus the shared modules assigned to chapter n below.
    """
    files = sorted((BOOK / "code").glob("ch%d_*.py" % n))
    # SUBJECT-SPECIFIC: shared modules shown with the chapter that builds them.
    files += [BOOK / "code" / name for name in {1: ["bookutil.py", "agdata.py"], 4: ["aglosses.py"]}.get(n, []) if (BOOK / "code" / name).exists()]
    if not files:
        return None
    sec = new(soup, "section", "appendix")
    h = new(soup, "h2", id="companion-code")
    h.string = "Companion code"
    sec.append(h)
    p = new(soup, "p")
    p.string = "The full scripts for this chapter, exactly as run. Open one to read or copy it."
    sec.append(p)
    for f in files:
        d = new(soup, "details", "code-file")
        s = new(soup, "summary")
        name = new(soup, "span", "code-file__name")
        name.string = "code/" + f.name
        s.append(name)
        d.append(s)
        box = new(soup, "div", "codebox")
        pre = new(soup, "pre", "code")
        code = new(soup, "code", "language-python")
        code.string = f.read_text()
        pre.append(code)
        box.append(pre)
        d.append(box)
        sec.append(d)
    return sec


# ---------- page assembly ----------

def render_page(title, body, toc, ruler, root, prev, nxt):
    """Wrap converted content in the page template and return the HTML string.

    title: page title ('' for the index). body: main content HTML. toc: contents list HTML. ruler: SVG string.
    root: relative path from the page to book/. prev, nxt: (href, label) or None.
    """
    def nav(link, cls, word):
        return '<a class="%s" href="%s"><small>%s</small><span>%s</span></a>' % (cls, link[0], word, link[1]) if link else ""

    top = "".join('<a href="%s" title="%s">%s</a>' % (l[0], l[1], w) for l, w in ((prev, "← Prev"), (nxt, "Next →")) if l)
    scripts = "\n".join('<script src="%s"></script>' % u for u in LIBS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title + ' | ' if title else ''}{BOOK_TITLE}</title>
<meta name="color-scheme" content="light dark">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}assets/book.css">
<script>{THEME_BOOT}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
<a class="topbar__title" href="{root}index.html">{BOOK_TITLE}</a>
<nav class="topbar__nav" aria-label="Chapters">{top}</nav>
<button class="theme-toggle" type="button">Theme: auto</button>
</header>
<div class="ruler"><span class="ruler__label">Resolution</span>{ruler}</div>
<div class="page">
<aside class="rail"><details class="toc" open><summary>Contents</summary><nav aria-label="On this page">{toc}</nav></details></aside>
<main id="main" class="main">
{body}
</main>
</div>
<footer class="pager">{nav(prev, "pager__prev", "Previous")}{nav(nxt, "pager__next", "Next")}</footer>
<script>{MATHJAX_CONFIG}</script>
{scripts}
<script src="{root}assets/book.js"></script>
</body>
</html>
"""


def convert(md_path, chapters, facts, index_links, root, out_path):
    """Convert one Markdown file into an HTML page.

    md_path: source file. chapters: ordered [(number, md Path)] of existing chapters.
    facts: README chapter table. index_links: node-to-chapter links for the index map.
    root: relative path from the output page to book/. out_path: destination file.
    """
    md = md_path.read_text()
    used = set()

    def slot(m):
        used.add(m.group(1))
        return '\n\n<div class="visual-slot" data-id="%s"></div>\n\n' % m.group(1)

    md = VISUAL_RE.sub(slot, md)
    for vid in used:
        if not (BOOK / "build" / "visuals" / (vid + ".html")).exists():
            raise SystemExit("%s: missing visual fragment build/visuals/%s.html" % (md_path.name, vid))
    soup = BeautifulSoup(run_pandoc(md), "html.parser")

    is_index = md_path.name == "README.md"
    num = int(re.match(r"ch(\d+)_", md_path.name).group(1)) if re.match(r"ch\d+_", md_path.name) else None
    key = "ch%d" % num if num else "test"
    if num:
        for label, line, count in drift(md_path):
            print("%s, %s: %d line(s) not in the companion code, first: %s" % (md_path.name, label, count, line))

    fix_links(soup)
    build_callouts(soup, key)
    mark_shapes(soup)
    color_dna(soup)
    normalize_code(soup)
    build_listings(soup)
    wrap_tables(soup)
    found_map = build_mermaid(soup, index_links if is_index else None)
    build_figures(soup, md_path.parent)
    build_exercises(soup)

    h1 = soup.find("h1")
    title = text_of(h1) if h1 else md_path.stem
    short = re.sub(r"^(Chapter\s*)?\d+\s*[.:·—-]\s*", "", title) if num else title
    h1.extract()
    covers = extract_covers(soup)
    opener = new(soup, "header", "opener" + (" opener--cover" if is_index else ""))
    if num:
        p = new(soup, "p", "opener__num")
        p.append(NavigableString("Chapter "))
        b = new(soup, "b")
        b.string = str(num)
        p.append(b)
        opener.append(p)
    t = new(soup, "h1", "opener__title")
    t.string = short
    opener.append(t)
    if num in facts:
        q = new(soup, "p", "opener__q")
        q.string = facts[num][1]
        opener.append(q)
    if covers is not None:
        opener.append(covers)
    fig = None
    if found_map and not is_index:
        node = soup.select_one("div.ag-map")
        fig = node.find_parent("figure") or node
        fig.extract()

    appendix = code_appendix(soup, num) if num else None
    if appendix is not None:
        soup.append(appendix)
    toc = toc_html(soup)
    main = BeautifulSoup("", "html.parser")
    main.append(opener)
    if fig is not None:
        main.append(fig)
    for c in list(soup.contents):
        main.append(c.extract())
    body = str(main)

    for vid in used:
        frag = (BOOK / "build" / "visuals" / (vid + ".html")).read_text()
        body = re.sub(r'<div class="visual-slot" data-id="%s">\s*</div>' % re.escape(vid), lambda _: frag, body)

    pos = [i for i, (n, _) in enumerate(chapters) if n == num]
    prev = nxt = None
    if is_index and chapters:
        nxt = (chapters[0][1].stem + ".html", "Chapter %d" % chapters[0][0])
    elif pos:
        i = pos[0]
        prev = ("index.html", "Contents") if i == 0 else (chapters[i - 1][1].stem + ".html", "Chapter %d" % chapters[i - 1][0])
        nxt = (chapters[i + 1][1].stem + ".html", "Chapter %d" % chapters[i + 1][0]) if i + 1 < len(chapters) else None
    active = [e for e, _, _ in RULER] if is_index else RULER_BY_CHAPTER.get(num, [7])
    out_path.write_text(render_page('' if is_index else short, body, toc, ruler_svg(active), root, prev, nxt))
    print("wrote", out_path.relative_to(BOOK))


# ---------- main ----------
chapters = sorted(
    ((int(re.match(r"ch(\d+)_", p.name).group(1)), p) for p in BOOK.glob("ch[0-9]*_*.md")), key=lambda t: t[0]
)
facts = readme_facts((BOOK / "README.md").read_text())
index_links = {}
for _, (_, _, nodes, html_name) in facts.items():
    for n in nodes:
        index_links[n] = html_name

if sys.argv[1:]:
    jobs = [BOOK / a for a in sys.argv[1:]]
else:
    jobs = [BOOK / "README.md"] + [p for _, p in chapters]
    if (BOOK / "build" / "test_components.md").exists():
        jobs.append(BOOK / "build" / "test_components.md")
for job in jobs:
    if job.name == "README.md":
        convert(job, chapters, facts, index_links, "", BOOK / "index.html")
    elif job.parent.name == "build":
        convert(job, chapters, facts, index_links, "../", job.with_suffix(".html"))
    else:
        convert(job, chapters, facts, index_links, "", job.with_suffix(".html"))
