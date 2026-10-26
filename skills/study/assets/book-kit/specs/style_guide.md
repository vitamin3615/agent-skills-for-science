# Style guide (default)

This guide was derived from a survey of seven deep-learning textbooks (Chollet, Raff, Liu, Goodfellow and others). If the user names other reference books, re-survey them and adapt it. Running-example names below are illustrative.

Basis: sampled chapter openings, a math+code section (softmax/cross-entropy, attention, gradient descent, convolution, backprop) and chapter endings in 7 books. Line numbers refer to the .md conversions.

## 1. Verdict (ranked)
1. **Chollet, Deep Learning with Python 3e.** Best concept order: need -> naive approach fails -> idea -> pseudocode -> real layer. Attention is built up in four growing code versions (15.4, l.13232-13330). Listings are short, with `#1 #2` markers and a matching footnote under the block. He also re-implements a Dense layer and a training loop by hand in ch. 2. That is the model for "implement it alone".
2. **Raff, Inside Deep Learning.** Best math handling. He "shows" the math instead of deriving it. Each equation gets a plain-English boxed reading, a numeric example and an analogy (softmax l.1252-1331, attention l.6478-6600). Shape comments go on every line. Chapter openers have a roadmap and "Why X?" sidebars. Weakness: code is mangled in this conversion and the exercises are bare.
3. **Liu, Learn Generative AI with PyTorch.** Best running-example discipline. One concrete input ("How are you?") is tracked with its tensor shapes through every stage (9.1-9.3), and tensor shapes are stated in prose. Its "Listing N.M" numbering plus "Exercise N.M" mid-chapter is good. Weak on math, and some listings live in an external `util.py`, which breaks self-containment.
- Use Goodfellow only for the derivation-style proof (backprop 6.5.3) and for one motivating example per operation (the spaceship laser, 9.1). Do not copy its density.

## 2. Chapter template
1. **Title + "This chapter covers"**: 3-5 bullets, each a skill the reader will have.
2. **Opening (about 1 page)**: what the previous chapter left open -> this chapter's question -> the roadmap sentence ("First we..., then we..., finally...").
3. **Running example**: one concrete input (e.g., a 2 kb DNA window -> shapes) that is reused through the whole chapter.
4. **Concept sections (n.1, n.2, ...)**: each follows the order in section 3 below.
5. **Assemble**: all pieces are wired into one module, with a shape test on the running example.
6. **Train/check**: a tiny training or sanity run with the expected output shown.
7. **Pitfalls**: 3-5 bullets of bugs that actually occur (shapes, masks, numerics).
8. **Exercises**: 4-6 items, graded.
9. **Chapter summary**: 5-8 bullets, one line each.
10. **Bridge**: one sentence naming what the next chapter needs from this one.

## 3. Rules
**Concept introduction order** (each concept, in this order)
1. Problem or failure of the naive approach (Chollet's finite-difference-per-weight argument, l.1090-1105).
2. Intuition in one analogy, then stop (Raff's lunch order, Liu's library search). One analogy per concept.
3. Picture (figure or ASCII shape diagram).
4. Math, kept minimal (below).
5. Pseudocode or NumPy, then the PyTorch module.
6. What it computes on the running example, with a number or a shape.
- Introduce one new idea per section. Add refinements (scaling, heads, masking) as separate steps, each motivated by a problem it fixes.
- Define each term the first time it appears, in a bold phrase. Never forward-reference without saying where it will be explained.

**Code listings**
- Format: `Listing n.m <noun phrase>` caption above a fenced ```python block. Number per chapter. Number only listings the text refers to by number.
- Length: at most about 25 lines. Split anything longer into labelled steps that build one class (Raff's Combiner -> backbone -> attention net).
- Annotation: `#1`, `#2` markers in the code, with a matching `#1 ...` line below the block (Chollet l.13261). Add a shape comment on every tensor line, e.g. `# (B, T, D)` (Raff l.6527).
- Prose ratio: 2-6 sentences of prose before each listing and a "what you should see" paragraph after it. Never put two listings back-to-back.
- Always show printed output or a shape for the first run of a module.
- Show the naive loop version before the vectorised one when the vectorised form is not obvious (einsum).
- **Runnable as printed.** The chapter's first listing is its setup (`Listing N.0`, or `N.0a`/`N.0b` when long): imports, paths and the loading of the running example, copied verbatim from the script's first cells. It is exempt from the length limit. After it, every listing runs in book order in one namespace, the way a reader pastes listings into notebook cells.
- No listing uses a name, file or download that only unshown code creates. Data comes from code the book shows, directly or through a shared helper such as `bookutil.fetch`, never from files that another chapter or a lab happened to leave behind.
- A long prerequisite (a training run, a data cache, a 100-line setup) enters in one visible catch-up line, `bookutil.run_cells("chN_x.py", globals(), start="<cell title>", until="Listing N.M")`, with a comment naming what it creates. A listing taken from a second script starts with such a line or with that script's own setup listing. Catch-up lines exist only in the book; the drift check accepts them.
- An excerpt (lines of a shared module, an abridged cell, lines from inside a function) says "excerpt" or "abridged" in its caption. It is for reading; nothing later may depend on it. A listing that shows the first lines of a cell and runs as printed is not an excerpt: say "first lines".
- Helper modules hold plumbing only: downloads, caches, file readers, catch-up. The mechanism a chapter teaches is written out in its listings.

**Math**
- Notation table in chapter 1, then fixed. Use the same symbol as the code variable (`B, T, D, C`) wherever possible. Shapes are written next to symbols, e.g. $x \in \mathbb{R}^{B\times T\times D}$.
- Every displayed equation gets, directly above or below it, a one-sentence plain-language reading ("The probability of item i is its score divided by the sum of all scores", Raff l.1274).
- Give a numeric worked example (two or three numbers) right after the equation.
- Show the final equation and explain it. Derive only when the derivation is the insight (gradient, chain rule). Say so explicitly: "derivations are not the point of this book" (Raff l.1331).
- Do not mix math and code in one line. Place the equation, then the code that implements it, and name the correspondence ("this line is Eq. 2.3").
- Number only equations referenced later.

**Callouts** (use sparingly, at most 3 per chapter)
- `> **Note**`: a fact that is true but would interrupt the flow.
- `> **Why X?**`: the motivation for a design choice (Raff style, e.g. "Why is it called softmax?").
- `> **Pitfall**`: a real bug and how it shows up (shape broadcast, mask sign, float16 overflow in softmax).
- `> **Biology link**`: what a tensor axis means biologically (position = bp, channel = assay track).
- `> **Check yourself**`: a 1-3 line question with the answer visible in the next paragraph.
- Never use a callout for core content.

**Figures** (Markdown only)
- ```mermaid for data flow and architecture (block diagrams, training loop).
- ASCII for tensor shapes and masks, as small as possible:
  `(B, L, 4) --conv--> (B, L, 128) --pool--> (B, L/2, 128)`
- Every figure has a caption starting `Figure n.m` that states the takeaway, not just the content (Raff l.6489).
- Reuse the same box colours and names for the same module across chapters.

**Exercises**
- 4-6 per chapter, in order: (a) modify a hyperparameter and predict the effect, (b) re-implement a function without the library call, (c) debug a broken snippet, (d) one stretch task.
- Put 1-2 "Exercise n.m" items mid-chapter right after the concept (Liu), and the rest at the end.
- Each exercise names its expected observable (a shape, a loss value, a plot).
- Provide answers in a repo folder, not in the book (Raff gives none, which is a weakness).

**End-of-chapter summary**
- Bullets only, 5-8, each starting with the concept and ending with its consequence (Chollet l.1594: "Learning means finding..."). No new facts.
- Closing line: the one object the reader now owns (e.g., "a `ConvTower` that maps (B, L, 4) -> (B, L/128, D)").

## 4. Exemplar snippets
- Chollet 3e, l.13261 (annotation footnotes): `\#1 Take the dot product between all target and source vectors, where b= batch size, t= target length, s= source length, d= vector size.`
- Chollet 3e, l.13272 (analogy for notation): `The terminology comes from search engines and recommender systems. Imagine a search tool to look up photos in a database - the "query" is your search term, the "keys" are photo tags...`
- Raff, l.1274 (plain reading above an equation): `The probability of the ith item is the score of the ith item divided by the score of every item added together.`
- Raff, l.6527 (shape comments as a rule): `...we are making sure to add comments about the shape of each tensor on every line. Attention mechanisms involve many changing shapes, so it is a good idea for you to include comments like these`
- Raff, l.1331 (math honesty): `This may seem a bit mysterious, and that's OK... derivations are not the point of this book. We worked through the details because [it is] ubiquitous...`
- Liu, l.3595 (analogy then tensor mapping): `If you search for "machine learning in finance"... this phrase becomes your query. The book titles... serve as the keys... books (values).`

## 5. Anti-patterns to avoid
- **Advanced DL w/ TF2 and Keras**: listings dumped in whole files with a "we can see that" paragraph. Chapter openers are goal lists with no motivating problem. Conclusions only repeat the chapter. Reference lists replace explanation.
- **Deep Learning Patterns and Practices**: design history ("v1.5 moved the stride") with no mechanism. Near-duplicate listings that differ by one line, with no diff or annotation. Summary bullets are slogans.
- **Mastering PyTorch**: "the code is self-explanatory" followed by 40-line steps. Hyperparameter blocks with no reasoning. Many chapters end with "Summary" plus references only and no exercises. The attention section is a history paragraph, not a build-up.
- **Goodfellow**: algorithm boxes before any intuition. Symbols are introduced in bulk. No code, so the reader cannot check understanding. Good for reference only.
- **Learn GenAI w/ PyTorch**: listings that call helper modules (`ch09util.py`) so the reader cannot see the logic. Unnumbered inline classes. Symbol typos in equations (e.g. W^Q/Q^K mix-up, an inconsistency to avoid by generating equations from the same names as the code).
- **All**: do not use "easy enough!"/"simply" in place of steps. Do not leave a tensor shape implicit. Do not introduce a trick (scaling, normalisation, masking) without the failure it fixes. Do not use more than one analogy per concept.
