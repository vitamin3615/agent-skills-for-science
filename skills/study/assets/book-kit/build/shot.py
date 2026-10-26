"""Screenshot one built page in light and dark at 1280 px and 400 px wide.

Usage: python build/shot.py <page.html> <output prefix>
Writes <prefix>_light_1280.png, _dark_1280.png, _light_400.png, _dark_400.png and
prints console errors and horizontal overflow. Needs playwright with Chromium (playwright install chromium).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

page_path = Path(sys.argv[1]).resolve()
prefix = sys.argv[2]
Path(prefix).parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for scheme in ("light", "dark"):
        for width in (1280, 400):
            ctx = browser.new_context(
                viewport={"width": width, "height": 900}, color_scheme=scheme, ignore_https_errors=True
            )
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(page_path.as_uri())
            page.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            page.wait_for_timeout(500)
            over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            out = "%s_%s_%d.png" % (prefix, scheme, width)
            page.screenshot(path=out, full_page=True)
            print(out, "overflow_px=%d" % over, "errors=%s" % errors)
            ctx.close()
    browser.close()
