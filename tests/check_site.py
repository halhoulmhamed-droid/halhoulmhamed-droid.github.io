#!/usr/bin/env python3
"""Validate the static portfolio without contacting external services.

Run from any directory: python tests/check_site.py
This checks the generated pages themselves, including their local destinations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


ORIGIN = "https://halhoulmhamed-droid.github.io"
EN_ROUTES = [
    "/", "/about/", "/projects/", "/contact/",
    "/projects/pde-image-denoising/", "/projects/nn-optimization-benchmark/",
    "/projects/inverse-laplace-learning/", "/projects/inverse-studies-synthesis/",
    "/projects/hujja/", "/projects/talk-to-agent/",
]
ROUTES = EN_ROUTES + ["/fr" + route for route in EN_ROUTES]


class Page(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str], int]] = []
        self.ids: list[str] = []
        self.jsonld: list[str] = []
        self.title = ""
        self._in_title = False
        self._in_jsonld = False
        self._json_buffer = ""
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes, self.getpos()[0]))
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        if tag == "title":
            self._in_title = True
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._json_buffer = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_jsonld:
            self.jsonld.append(self._json_buffer)
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_jsonld:
            self._json_buffer += data

    def attrs(self, tag):
        return [attrs for name, attrs, _ in self.tags if name == tag]


def site_path(root: Path, url_path: str) -> Path:
    path = root / unquote(url_path).lstrip("/")
    if url_path.endswith("/") or path.is_dir():
        path /= "index.html"
    return path


def check(root: Path) -> dict:
    errors: list[str] = []
    pages: dict[str, Page] = {}
    external: set[str] = set()
    checked_links = 0
    checked_resources: set[Path] = set()
    titles: dict[str, str] = {}

    def error(route, message):
        errors.append(f"{route}: {message}")

    for route in ROUTES:
        file = site_path(root, route)
        if not file.is_file():
            error(route, "required route is missing")
            continue
        pages[route] = Page(file.read_text(encoding="utf-8"))

    for route, page in pages.items():
        french = route.startswith("/fr/")
        en_route = route[3:] if french else route
        fr_route = "/fr" + en_route
        html = page.attrs("html")
        if len(html) != 1 or html[0].get("lang") != ("fr" if french else "en"):
            error(route, "incorrect or absent document language")
        if not page.title.strip():
            error(route, "missing page title")
        elif page.title in titles:
            error(route, f"duplicate page title with {titles[page.title]}")
        titles[page.title] = route
        if len(page.attrs("h1")) != 1:
            error(route, "expected one h1")
        duplicates = [item for item, count in Counter(page.ids).items() if count > 1]
        if duplicates:
            error(route, f"duplicate ids: {duplicates}")
        meta = page.attrs("meta")
        if not any(item.get("name") == "description" and item.get("content", "").strip() for item in meta):
            error(route, "missing description")
        if not any(item.get("name") == "viewport" for item in meta):
            error(route, "missing viewport")
        for property_name in ("og:title", "og:description", "og:url"):
            if not any(item.get("property") == property_name and item.get("content") for item in meta):
                error(route, f"missing {property_name}")
        canonical = [item.get("href") for item in page.attrs("link") if item.get("rel") == "canonical"]
        if canonical != [ORIGIN + route]:
            error(route, f"canonical is {canonical}; expected {ORIGIN + route}")
        alternatives = {item.get("hreflang"): item.get("href") for item in page.attrs("link") if item.get("rel") == "alternate"}
        expected = {"en": ORIGIN + en_route, "fr": ORIGIN + fr_route, "x-default": ORIGIN + en_route}
        for lang, href in expected.items():
            if alternatives.get(lang) != href:
                error(route, f"hreflang {lang} is {alternatives.get(lang)}; expected {href}")
        if not page.jsonld:
            error(route, "missing structured data")
        for data in page.jsonld:
            try:
                parsed = json.loads(data)
                if not isinstance(parsed, (dict, list)):
                    error(route, "structured data is not an object or array")
            except json.JSONDecodeError as exc:
                error(route, f"invalid JSON-LD: {exc}")
        language_links = [item for item in page.attrs("a") if "data-language-link" in item]
        if not language_links:
            error(route, "missing page-preserving language selector")
        elif not any(urlsplit(item.get("href", "")).path == (en_route if french else fr_route) for item in language_links):
            error(route, "language selector does not preserve the route")
        for tag, attrs, line in page.tags:
            if tag == "img":
                if "alt" not in attrs:
                    error(route, f"image without alternative text at line {line}")
                if not attrs.get("width") or not attrs.get("height"):
                    error(route, f"image without intrinsic dimensions at line {line}")
            if tag == "a" and attrs.get("target") == "_blank" and "noopener" not in attrs.get("rel", ""):
                error(route, f"new-window link without noopener at line {line}")
            if attrs.get("style") and re.search(r"(?:url\(['\"]?)(?:/tmp|/workspace)", attrs["style"]):
                error(route, f"private filesystem path in style at line {line}")
            destinations = []
            if tag in ("a", "link") and attrs.get("href"):
                destinations.append((attrs["href"], tag == "a"))
            if tag in ("img", "script", "source") and attrs.get("src"):
                destinations.append((attrs["src"], False))
            if tag in ("img", "source") and attrs.get("srcset"):
                destinations.extend((item.strip().split()[0], False) for item in attrs["srcset"].split(","))
            for href, anchor in destinations:
                resolved = urlsplit(urljoin(ORIGIN + route, href))
                if resolved.scheme in ("mailto", "tel", "data"):
                    continue
                if resolved.scheme not in ("http", "https"):
                    error(route, f"unsupported URL at line {line}: {href}")
                    continue
                if resolved.netloc != urlsplit(ORIGIN).netloc:
                    if anchor:
                        external.add(href)
                    continue
                checked_links += 1
                target = site_path(root, resolved.path)
                if not target.is_file():
                    error(route, f"missing local target at line {line}: {href}")
                    continue
                if not anchor:
                    checked_resources.add(target)
                if anchor and resolved.fragment and target.suffix == ".html":
                    target_page = pages.get(resolved.path) or Page(target.read_text(encoding="utf-8"))
                    if unquote(resolved.fragment) not in target_page.ids:
                        error(route, f"missing anchor at line {line}: {href}")

    for css in sorted(root.glob("assets/**/*.css")):
        for href in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css.read_text(encoding="utf-8")):
            resolved = urlsplit(urljoin(ORIGIN + "/" + css.relative_to(root).as_posix(), href))
            if resolved.scheme == "data" or resolved.netloc != urlsplit(ORIGIN).netloc:
                continue
            target = site_path(root, resolved.path)
            if not target.is_file():
                error(css.relative_to(root), f"missing CSS resource {href}")
            else:
                checked_resources.add(target)

    try:
        sitemap = ET.parse(root / "sitemap.xml")
        locations = {node.text for node in sitemap.iter() if node.tag.endswith("}loc") or node.tag == "loc"}
        if locations != {ORIGIN + route for route in ROUTES}:
            errors.append(f"sitemap route mismatch: missing={sorted({ORIGIN + route for route in ROUTES} - locations)}, extra={sorted(locations - {ORIGIN + route for route in ROUTES})}")
    except (OSError, ET.ParseError) as exc:
        errors.append(f"invalid or missing sitemap: {exc}")

    return {
        "passed": not errors, "routes": len(pages), "local_links_and_resources": checked_links,
        "unique_local_resources": len(checked_resources), "external_links": sorted(external),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.root.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {key: value for key, value in result.items() if key != "external_links"}
    summary["unique_external_links"] = len(result["external_links"])
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
