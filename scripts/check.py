#!/usr/bin/env python3
"""Check the generated website's links, anchors and publishable file types."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "_site"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.links = []
        self.errors = []
        self.main_count = 0
        self.h1_count = 0
        self.lang = ""

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "html":
            self.lang = attr.get("lang", "")
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1
        if "id" in attr:
            if attr["id"] in self.ids:
                self.errors.append(f"Duplicate ID: {attr['id']}")
            self.ids.add(attr["id"])
        if tag in {"a", "link"} and attr.get("href"):
            self.links.append(attr["href"])
        if tag in {"img", "script", "iframe"} and attr.get("src"):
            self.links.append(attr["src"])


def main():
    if not (ROOT / "index.html").is_file():
        raise SystemExit("Build the website first.")
    pages = {}
    for path in ROOT.rglob("*.html"):
        page = Page(path)
        page.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = page
    errors = []
    for path, page in pages.items():
        if not page.lang or page.main_count != 1 or page.h1_count != 1:
            errors.append(f"{path.relative_to(ROOT)}: Missing language or invalid main/h1 count")
        errors.extend(f"{path.relative_to(ROOT)}: {error}" for error in page.errors)
        for link in page.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme not in {"https", "http", "mailto"}:
                    errors.append(f"Unsupported URL: {link}")
                continue
            if parsed.path.startswith("/"):
                errors.append(f"Root-relative path will break project Pages sites: {link}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(ROOT):
                errors.append(f"Link leaves the public website: {link}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{path.relative_to(ROOT)}: Missing link target {link}")
            elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f"{path.relative_to(ROOT)}: Missing anchor {link}")
    allowed = {".html", ".css", ".js", ".svg", ".jpg", ".png", ".bib", ".xml"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix not in allowed and path.name != ".nojekyll":
            errors.append(f"Unexpected public file: {path.relative_to(ROOT)}")
        if path.is_symlink():
            errors.append(f"Symlink in public files: {path.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Checked {len(pages)} pages: internal links, anchors, headings and public files passed.")


if __name__ == "__main__":
    main()
