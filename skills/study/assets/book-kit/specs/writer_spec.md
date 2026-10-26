# Writer spec template (one chapter)

Fill in the `{…}` placeholders, save the result to the scratchpad, and give each chapter writer this file plus a chapter brief. You write ONE chapter, its companion code and its solutions. A leader reviews your work, and an independent verifier checks every claim and runs your code. Accuracy beats length.

## Read first (required)
1. Front matter, notation and map: `{BOOK_DIR}/README.md`. Use its notation, node IDs and conventions exactly.
2. Style guide: `{SCRATCH}/style_guide.md`. Follow its chapter template and rules.
3. Learner state, if any: `{PLAN_OR_PROGRESS_FILES}`. Do not reteach material the learner has already demonstrated, and calibrate to their known misconceptions.

## Reader
{Background the reader has; what they have NOT done; the book's observable goals, e.g. "can write the training algorithm from scratch"}. Teach foundations just in time: introduce each one where the subject first needs it, build it from first principles, then specialize it. Keep domain background the reader already has short.

## Learning devices (required, in addition to the style guide)
- Open with: title, "This chapter covers", the whole-subject map from README redrawn with this chapter's nodes highlighted (the same labeled edges), and the chapter question tied to the anchor question.
- 4–8 `> **Predict.** …` pauses at high-information points (a shape, a number, a reason, a "what breaks if"), each followed by `<details><summary>Answer</summary>…</details>`. These do not count toward the callout limit.
- Teach relationships: for each map edge the chapter owns, state the edge in words ("A biases B because …").
- Epistemic labels: "the source states", "the reference code does", "our reading/inference". Flag source↔code disagreements where they affect a rebuild.
- End with Pitfalls, Exercises (4–6, graded, each with an expected observable, at least one transfer task), Summary (5–8 bullets), a recompressed map or mechanism chain, and a one-sentence Bridge.
- The book is rendered later as rich HTML; your Markdown stays the verified source. Wherever a diagram, animation or interactive widget would explain better than text, add `<!-- VISUAL: <what to show, what the reader should notice, which data or shapes> -->` (4–8 per chapter).

## Sources and citations
{List each source with its citation format, e.g. "SI p. N" from page markers; "official `path/file.py:123`" at a pinned commit; "port `file.py:45`"}. Read every page or line you cite. Never invent a number, quote, citation, line number or result. Every number comes from a cited source or from a run of your companion code (say which). If something cannot be verified, say so.

## Code
- Companion script `{BOOK_DIR}/code/chN_<topic>.py`, in the learner's preferred style ({e.g. `# %%` cells at top level, no main(), docstrings on custom functions}).
- Every numbered listing appears verbatim (or as a marked excerpt) in the script, in order. Outputs shown after listings are copied from your actual run, and come only from code inside that listing.
- Listings run as printed (style guide, *Code listings*): open with a setup listing, then every listing that is not captioned excerpt or abridged runs in book order with the working directory `{BOOK_DIR}/code`. Fetch every download with `bookutil.fetch` or a subject helper built on it, so a fresh copy of the code works. Check with `python {BOOK_DIR}/build/check_listings.py chN_<slug>.md` in the book's environment: it must report no FAIL and no DRIFT.
- Use real data ({paths, download URLs, size limits; download only into the git-ignored data dir, and skip files already present}).
- Environment: {run command, env name, RAM/CPU/GPU budget, time limit per script}. Other workers run in parallel, so stay within budget. Use reduced sizes and say so.
- Cross-implementation checks: where practical, compare your implementation numerically against the reference implementation with identical inputs and weights, and report max |Δ|. Make each check able to fail (no comparing a function with its own formula, no hard-coded expected constants).
- Figures: `{BOOK_DIR}/figures/chN_*.png` from real runs, embedded with relative links.
- Run the script end to end before reporting. It must finish without errors or unexplained warnings. Investigate warnings instead of suppressing them.

## Shared contract
{Modules built by earlier chapters and imported by later ones (names, function signatures, batch keys, shapes, dtypes), and the reference model's output naming}. `code/bookutil.py` (from the kit) holds the plumbing every chapter shares: `fetch` for cached downloads and `run_cells` for catching up on a long prerequisite. Add new plumbing there, never the mechanism a chapter teaches. Report bugs you find in shared modules to the leader; never silently rewrite another chapter's files.

## Deliverables
1. `{BOOK_DIR}/chN_<slug>.md` (~5,000–8,000 words of prose plus listings; as long as the content needs and no longer).
2. The companion code, run end to end.
3. `{BOOK_DIR}/solutions/chN.md`: concise answers to every exercise, checked by running.
4. Final reply (≤25 lines): the files written, run time and peak memory, every cross-check with its max |Δ|, every claim you could not verify, and any source↔code disagreement you found.
