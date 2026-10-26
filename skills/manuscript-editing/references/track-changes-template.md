# Track Changes HTML Template

**Purpose:** Generate a standalone HTML file showing manuscript edits when user requests "Track Changes", "show diff", or "visualize edits".

---

## When to Use

ONLY generate this if the user explicitly asks for:

- "Track Changes"
- "Show diff"
- "Visualize edits"
- "Show what you changed"

---

## HTML Template Structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Manuscript Editing - Track Changes</title>
    <style>
      body {
        font-family: "Georgia", "Times New Roman", serif;
        line-height: 1.8;
        max-width: 800px;
        margin: 40px auto;
        padding: 20px;
        color: #333;
      }
      h1,
      h2 {
        font-family: "Helvetica Neue", Arial, sans-serif;
        color: #222;
      }
      h1 {
        font-size: 1.5em;
        border-bottom: 2px solid #333;
        padding-bottom: 10px;
      }
      h2 {
        font-size: 1.2em;
        margin-top: 30px;
      }

      /* Track Changes Styling */
      ins {
        color: #0070c0;
        text-decoration: underline;
        background-color: #e6f2ff;
      }
      del {
        color: #d32f2f;
        text-decoration: line-through;
        background-color: #ffe6e6;
      }
      .format-note {
        color: #666;
        font-style: italic;
        background-color: #eee;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 0.9em;
      }

      /* Editorial Summary Styling */
      .summary {
        background-color: #f8f9fa;
        border-left: 4px solid #0070c0;
        padding: 15px 20px;
        margin-top: 40px;
      }
      .summary h2 {
        margin-top: 0;
        color: #0070c0;
      }
      .summary ul {
        margin-bottom: 0;
      }

      /* Legend */
      .legend {
        background-color: #f0f0f0;
        padding: 10px 15px;
        margin-bottom: 30px;
        border-radius: 5px;
        font-size: 0.9em;
      }
      .legend span {
        margin-right: 20px;
      }
    </style>
  </head>
  <body>
    <h1>Manuscript Editing - Track Changes View</h1>

    <div class="legend">
      <span><ins>Insertions shown like this</ins></span>
      <span><del>Deletions shown like this</del></span>
    </div>

    <h2>Edited Text</h2>

    <!-- INSERT EDITED TEXT WITH <ins> AND <del> TAGS HERE -->
    <p>[Your edited content goes here with appropriate ins/del tags]</p>

    <div class="summary">
      <h2>Editorial Summary</h2>
      <p>
        <strong>Section Type:</strong>
        [Abstract/Introduction/Results/Discussion/Methods/Figure Legend]
      </p>
      <p><strong>Major Improvements:</strong></p>
      <ul>
        <li>[Improvement 1]</li>
        <li>[Improvement 2]</li>
        <li>[Improvement 3]</li>
      </ul>
    </div>
  </body>
</html>
```

---

## CSS Quick Reference

| Element Type     | CSS Styling                                                                                      |
| ---------------- | ------------------------------------------------------------------------------------------------ |
| **Insertions**   | `<ins style="color:#0070c0; text-decoration:underline; background-color:#e6f2ff;">text</ins>`    |
| **Deletions**    | `<del style="color:#d32f2f; text-decoration:line-through; background-color:#ffe6e6;">text</del>` |
| **Format Notes** | `<span style="color:#666; font-style:italic; background-color:#eee;">[formatted as bold]</span>` |

---

## Usage Guidelines

1. **File naming:** `manuscript_edit_track_changes.html`

2. **Structure requirements:**

   - Standard HTML5 boilerplate
   - CSS for readability (font-family, line-height, max-width container)
   - Edited text with `<ins>` and `<del>` tags
   - Editorial Summary at the bottom

3. **Keep it professional and minimal.** The user trusts the edits—no need to justify every change.

---

## Example Output

```html
<p>
  The results <del>shows</del><ins>show</ins> an association between age and
  protein abundance.
</p>
```
