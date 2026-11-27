"""Render an app's docs/legal/*.md into hosted HTML pages for GitHub Pages.

Usage: python tools/build_app_pages.py <AppName> <path to app repo>

Writes <app>_privacy.html, <app>_terms.html and <app>_support.html next to
this repo's other policies (served at https://lancimator.github.io/privacy-policy/).
The Markdown sources stay the single source of truth in each app repo.
"""
import html
import pathlib
import re
import sys

import markdown

CONTACT = "lancimator@gmail.com"
BASE = "https://lancimator.github.io/privacy-policy/"

STYLE = """
    body { max-width: 720px; margin: 2rem auto; padding: 0 1rem 4rem;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      line-height: 1.6; color: #222; background: #fff; }
    h1, h2, h3 { line-height: 1.25; }
    h1 { margin-bottom: 0.25rem; }
    h2 { margin-top: 2.25rem; border-bottom: 1px solid #eee; padding-bottom: 0.3rem; }
    h3 { margin-top: 1.5rem; }
    hr { border: 0; border-top: 1px solid #eee; margin: 2rem 0; }
    a { color: #2c5fb3; }
    table { border-collapse: collapse; margin: 1rem 0; width: 100%; }
    td, th { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }
    th { background: #f7f7f7; }
    code { background: #f3f3f3; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.95em; }
    em { color: #555; }
    ul { padding-left: 1.4rem; }
    li { margin: 0.25rem 0; }
    nav { font-size: 0.9rem; margin-bottom: 1.5rem; color: #666; }
    @media (prefers-color-scheme: dark) {
      body { color: #e6e6e6; background: #141414; }
      a { color: #8ab4f8; }
      th { background: #222; } td, th { border-color: #333; }
      code { background: #222; } h2, hr { border-color: #2a2a2a; } em { color: #aaa; }
    }
"""


def page(title: str, body: str, slug: str) -> str:
    nav = (
        f'<nav><a href="{slug}_privacy.html">Privacy</a> · '
        f'<a href="{slug}_terms.html">Terms</a> · '
        f'<a href="{slug}_support.html">Support</a></nav>'
    )
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"  <title>{html.escape(title)}</title>\n  <style>{STYLE}  </style>\n</head>\n<body>\n"
        f"{nav}\n{body}\n</body>\n</html>\n"
    )


def render(md_text: str, slug: str) -> str:
    # Cross-links between the two documents point at the hosted pages.
    md_text = md_text.replace("(PRIVACY.md)", f"({slug}_privacy.html)")
    md_text = md_text.replace("(TERMS.md)", f"({slug}_terms.html)")
    out = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    return re.sub(r"(?<![\w.:/\"])" + re.escape(CONTACT), f'<a href="mailto:{CONTACT}">{CONTACT}</a>', out)


def support_page(name: str, slug: str, faq: list[tuple[str, str]]) -> str:
    items = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{a}</p>" for q, a in faq)
    body = f"""<h1>{html.escape(name)} support</h1>
<p>Questions, bug reports or ideas? Email <a href="mailto:{CONTACT}?subject={html.escape(name)}%20support">{CONTACT}</a>.
We read every message and usually answer within two working days.</p>
<p>When reporting a bug, please include your phone model, the operating system version and the app version
(shown in the app under Settings → About).</p>
<h2>Frequently asked questions</h2>
{items}
<h2>Legal</h2>
<p><a href="{slug}_privacy.html">Privacy policy</a> · <a href="{slug}_terms.html">Terms of use</a></p>
"""
    return page(f"{name} — Support", body, slug)


COMMON_FAQ = [
    ("How do I restore my purchase on a new phone?",
     "Install the app with the same Apple ID or Google account, open the paywall (Settings → Pro) and tap "
     "<em>Restore purchases</em>."),
    ("How do I cancel a subscription?",
     "On iPhone: Settings → your name → Subscriptions. On Android: Google Play → Profile → Payments &amp; "
     "subscriptions → Subscriptions. Cancel at least 24 hours before the renewal date."),
    ("How do I get a refund?",
     "Purchases are handled by the store. On iPhone use <a href=\"https://reportaproblem.apple.com\">"
     "reportaproblem.apple.com</a>; on Android see Google Play's refund page in your order history."),
    ("Do you collect my data?",
     "No account, no ads, no analytics. What the app keeps stays on your device; see the privacy policy for details."),
]

APP_FAQ = {
    "huejot": [("Where are my notes stored?", "On your device only. Use Settings → Backup to export a "
                ".huejot.json file you can keep in Files or Drive and import again later.")],
    "earwren": [("Which audiobooks can Earwren play?", "DRM-free files you own: MP3, M4A/M4B (with chapters), "
                 "AAC, FLAC, WAV, OGG and Opus. Books bought in stores that use copy protection (DRM) cannot be played."),
                ("Can I delete the original file after importing?", "Yes. Earwren keeps its own copy of every "
                 "imported book on your device, so it keeps playing after you move or delete the original.")],
    "laterlark": [("Where does search data come from?", "Optional online search uses Wikidata. Only your search "
                   "words are sent; your lists stay on your device.")],
}


def main() -> None:
    name, repo = sys.argv[1], pathlib.Path(sys.argv[2])
    slug = name.lower()
    here = pathlib.Path(__file__).resolve().parent.parent
    for doc, label in (("PRIVACY", "privacy"), ("TERMS", "terms")):
        src = (repo / "docs" / "legal" / f"{doc}.md").read_text(encoding="utf-8")
        if "[Developer" in src or "[Contact" in src or "[publish" in src:
            sys.exit(f"{doc}.md still has placeholders")
        title = src.splitlines()[0].lstrip("# ").strip()
        (here / f"{slug}_{label}.html").write_text(page(title, render(src, slug), slug), encoding="utf-8")
    faq = APP_FAQ.get(slug, []) + COMMON_FAQ
    (here / f"{slug}_support.html").write_text(support_page(name, slug, faq), encoding="utf-8")
    print(f"wrote {slug}_privacy.html, {slug}_terms.html, {slug}_support.html -> {BASE}")


if __name__ == "__main__":
    main()
