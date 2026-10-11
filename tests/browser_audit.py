#!/usr/bin/env python3
"""Audit the served portfolio in Chromium and save review screenshots.

Requires Python Playwright and a Chromium installation. For accessibility,
pass --axe-path pointing to an installed axe-core/axe.min.js. Audit dependencies
are separate from the website; no scripts are injected into published pages.
Timings describe the local browser run, not field data or a Lighthouse score.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

sys.dont_write_bytecode = True
from check_site import ROUTES


WIDTHS = [320, 390, 768, 1440]
OBSERVER = """(() => {
  window.__audit = {lcp: 0, cls: 0};
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) window.__audit.lcp = e.startTime;
  }).observe({type: 'largest-contentful-paint', buffered: true});
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) if (!e.hadRecentInput) window.__audit.cls += e.value;
  }).observe({type: 'layout-shift', buffered: true});
})()"""
MEASURE = """() => {
  const n = performance.getEntriesByType('navigation')[0];
  const paints = Object.fromEntries(performance.getEntriesByType('paint').map(e => [e.name, e.startTime]));
  const resources = performance.getEntriesByType('resource');
  return {domContentLoadedMs: n.domContentLoadedEventEnd, loadMs: n.loadEventEnd,
    firstContentfulPaintMs: paints['first-contentful-paint'] ?? null,
    largestContentfulPaintMs: window.__audit.lcp, cumulativeLayoutShift: window.__audit.cls,
    requests: 1 + resources.length, transferredBytes: n.transferSize + resources.reduce((s,e) => s + e.transferSize, 0),
    decodedBytes: n.decodedBodySize + resources.reduce((s,e) => s + e.decodedBodySize, 0),
    resourceDetails: resources.map(e => ({name: new URL(e.name).pathname, bytes: e.transferSize, durationMs: e.duration}))};
}"""
OVERFLOW = """() => ({width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
  elements: [...document.querySelectorAll('body *')].filter(e => {
    const style = getComputedStyle(e); const r = e.getBoundingClientRect();
    return style.position !== 'fixed' && style.visibility !== 'hidden' && r.width > 0 && (r.left < -1 || r.right > innerWidth + 1);
  }).map(e => ({tag: e.tagName, class: e.className, id: e.id})).slice(0, 10)})"""


class AuditErrors(list):
    def append(self, issue):
        super().append(issue)
        print(f"FAIL: {issue}", flush=True)


def contrast_ratio(foreground, background):
    def luminance(color):
        components = [float(value) / 255 for value in re.findall(r"[\d.]+", color)[:3]]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in components]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    values = sorted((luminance(foreground), luminance(background)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--axe-path", type=Path)
    parser.add_argument("--require-axe", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    errors, warnings, audits, interactions, screenshots = AuditErrors(), [], [], [], []
    caption_contrast = []
    axe_available = bool(args.axe_path and args.axe_path.is_file())
    if not axe_available:
        (errors if args.require_axe else warnings).append("axe-core is unavailable; automated contrast and WCAG checks were not run")

    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(executable_path=args.chromium, args=["--no-sandbox"])
        browser_version = browser.version
        for width in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": 1000 if width > 768 else 844}, device_scale_factor=1)
            context.add_init_script(OBSERVER)
            for route in ROUTES:
                page = context.new_page()
                page_errors, failures = [], []
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.on("requestfailed", lambda request: failures.append({"url": request.url, "failure": request.failure}))
                page.on("response", lambda response: failures.append({"url": response.url, "status": response.status}) if response.status >= 400 else None)
                response = page.goto(base + route, wait_until="networkidle")
                page.wait_for_function("document.fonts.status === 'loaded'")
                page.wait_for_timeout(120)
                metrics = page.evaluate(MEASURE)
                # Verify and capture lazy figures too; performance is sampled above,
                # before deliberately loading resources below the initial viewport.
                page.locator("img").evaluate_all("""images => {
                  images.forEach(i => i.loading = 'eager');
                  return Promise.all(images.map(i => i.complete ? Promise.resolve() : new Promise(resolve => {
                    i.addEventListener('load', resolve, {once:true});
                    i.addEventListener('error', resolve, {once:true});
                    setTimeout(resolve, 5000);
                  })));
                }""")
                overflow = page.evaluate(OVERFLOW)
                broken_images = page.locator("img").evaluate_all("images => images.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)")
                if not response or response.status != 200:
                    errors.append(f"{width} {route}: HTTP {response.status if response else 'no response'}")
                if overflow["scrollWidth"] > width + 1:
                    errors.append(f"{width} {route}: horizontal overflow {overflow}")
                if page_errors or failures or broken_images:
                    errors.append(f"{width} {route}: errors={page_errors}, failed resources={failures}, broken images={broken_images}")
                violations = []
                incomplete = []
                if axe_available and width in (390, 1440):
                    page.add_script_tag(path=str(args.axe_path))
                    axe = page.evaluate("""async () => axe.run(document, {runOnly: {type:'tag', values:['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice']}})""")
                    violations = [{"id": v["id"], "impact": v["impact"], "description": v["description"], "nodes": [{"target": n["target"], "failureSummary": n.get("failureSummary")} for n in v["nodes"]]} for v in axe["violations"]]
                    incomplete = [{"id": v["id"], "impact": v["impact"], "nodes": [n["target"] for n in v["nodes"]]} for v in axe["incomplete"]]
                    for violation in violations:
                        errors.append(f"{width} {route}: axe {violation['id']} ({violation['impact']}): {violation['nodes']}")
                audits.append({"route": route, "width": width, "overflow": overflow, "metrics": metrics, "axeViolations": violations, "axeIncomplete": incomplete})

                if width in (390, 1440):
                    name = (route.strip("/").replace("/", "-") or "home") + f"-{width}.png"
                    path = args.output_dir / name
                    page.screenshot(path=str(path), full_page=True, animations="disabled")
                    screenshots.append(str(path))
                page.close()
            context.close()

        context = browser.new_context(viewport={"width": 390, "height": 844})
        for route in ROUTES:
            page = context.new_page()
            page.goto(base + route + "?view=research#main-content", wait_until="networkidle")
            expected_hash = "main-content"
            section_links = page.locator(".case-nav a[href^='#']")
            if section_links.count():
                expected_hash = section_links.first.get_attribute("href")[1:]
                page.evaluate("hash => location.hash = hash", expected_hash)
                page.wait_for_function("hash => [...document.querySelectorAll('[data-language-link]')].every(link => new URL(link.href).hash === '#' + hash)", arg=expected_hash)
            links = page.locator("[data-language-link]")
            french = route.startswith("/fr/")
            expected_route = route[3:] if french else "/fr" + route
            if links.count() == 0:
                errors.append(f"{route}: no language link")
            else:
                candidate = next((links.nth(i) for i in range(links.count()) if urlsplit(links.nth(i).get_attribute("href") or "").path == expected_route), None)
                if candidate is None:
                    errors.append(f"{route}: language link does not select {expected_route}")
                else:
                    candidate.click()
                    page.wait_for_load_state("networkidle")
                    result = urlsplit(page.url)
                    passed = result.path == expected_route and result.query == "view=research" and result.fragment == expected_hash
                    interactions.append({"type": "language-preservation", "route": route, "passed": passed, "expectedHash": expected_hash, "afterHashChange": bool(section_links.count())})
                    if not passed:
                        errors.append(f"{route}: language switch produced {page.url}")
            page.close()

        for route in ("/", "/fr/", "/projects/pde-image-denoising/", "/fr/projects/pde-image-denoising/"):
            page = context.new_page()
            page.goto(base + route, wait_until="networkidle")
            page.keyboard.press("Tab")
            skip = page.evaluate("""() => {const e=document.activeElement; const r=e.getBoundingClientRect();const s=getComputedStyle(e);return {tag:e.tagName,href:e.getAttribute('href'),visible:r.bottom>0 && r.top<innerHeight,outline:s.outlineStyle,outlineWidth:s.outlineWidth}}""")
            if not skip.get("href", "").startswith("#") or not skip["visible"]:
                errors.append(f"{route}: first Tab does not reveal the skip link: {skip}")
            else:
                page.keyboard.press("Enter")
                focus_id = page.evaluate("document.activeElement.id")
                if focus_id != skip["href"][1:]:
                    errors.append(f"{route}: skip link does not move keyboard focus to its target ({focus_id})")
            page.goto(base + route, wait_until="networkidle")
            buttons = page.locator("button[aria-controls][aria-expanded]")
            button = next((buttons.nth(i) for i in range(buttons.count()) if buttons.nth(i).is_visible()), None)
            if button is None:
                errors.append(f"{route}: mobile navigation toggle is missing")
            else:
                button.focus()
                page.keyboard.press("Enter")
                expanded = button.get_attribute("aria-expanded") == "true"
                controlled = button.get_attribute("aria-controls")
                page.keyboard.press("Tab")
                inside_nav = page.evaluate("id => !!document.getElementById(id)?.contains(document.activeElement)", controlled)
                page.keyboard.press("Escape")
                closed = button.get_attribute("aria-expanded") == "false"
                returned = button.evaluate("e => e === document.activeElement")
                passed = expanded and inside_nav and closed and returned
                interactions.append({"type": "keyboard-menu", "route": route, "passed": passed, "expanded": expanded, "tabInsideNavigation": inside_nav, "escapeClosed": closed, "focusReturned": returned, "skipLink": skip})
                if not passed:
                    errors.append(f"{route}: keyboard menu failed: expanded={expanded}, tab_inside={inside_nav}, escape_closed={closed}, focus_returned={returned}")
            page.close()
        table_routes = [route for route in ROUTES if any(name in route for name in (
            "pde-image-denoising", "nn-optimization-benchmark", "inverse-laplace-learning", "inverse-studies-synthesis"))]
        for route in table_routes:
            page = context.new_page()
            page.goto(base + route, wait_until="networkidle")
            regions = page.locator(".table-wrap")
            for index in range(regions.count()):
                region = regions.nth(index)
                caption = region.locator("caption").first
                if caption.count():
                    palette = caption.evaluate("""e => {
                      const foreground=getComputedStyle(e).color;
                      let background='rgb(255, 255, 255)', current=e;
                      while(current) {
                        const color=getComputedStyle(current).backgroundColor;
                        if(color!=='rgba(0, 0, 0, 0)' && color!=='transparent') {background=color;break;}
                        current=current.parentElement;
                      }
                      return {foreground,background};
                    }""")
                    ratio = contrast_ratio(palette["foreground"], palette["background"])
                    caption_contrast.append({"route": route, "tableIndex": index, **palette, "contrastRatio": ratio, "normalTextAA": ratio >= 4.5})
                    if ratio < 4.5:
                        errors.append(f"{route}: table caption contrast {ratio:.3f}:1 is below 4.5:1")
                scrollable = region.evaluate("e => e.scrollWidth > e.clientWidth")
                if not scrollable:
                    continue
                region.evaluate("e => e.scrollLeft = 0")
                region.focus()
                page.keyboard.press("ArrowRight")
                try:
                    page.wait_for_function("index => document.querySelectorAll('.table-wrap')[index].scrollLeft > 0", arg=index, timeout=3000)
                except PlaywrightTimeoutError:
                    pass
                offset = region.evaluate("e => e.scrollLeft")
                interactions.append({"type": "table-keyboard-scroll", "route": route, "tableIndex": index, "passed": offset > 0, "scrollLeft": offset})
                if offset <= 0:
                    errors.append(f"{route}: horizontally scrollable results table {index} does not respond to ArrowRight")
            page.close()
        context.close()

        context = browser.new_context(viewport={"width": 1440, "height": 900})
        for route in ("/", "/fr/"):
            page = context.new_page()
            page.goto(base + route, wait_until="networkidle")
            focus_sequence = []
            for _ in range(12):
                page.keyboard.press("Tab")
                # Browser focus may scroll smoothly; inspect after it has settled.
                try:
                    page.wait_for_function("""() => {
                      const r=document.activeElement.getBoundingClientRect();
                      return r.width>0 && r.height>0 && r.bottom>0 && r.top<innerHeight;
                    }""", timeout=3000)
                except PlaywrightTimeoutError:
                    pass
                focused = page.evaluate("""() => {
                  const e=document.activeElement, s=getComputedStyle(e), r=e.getBoundingClientRect();
                  return {tag:e.tagName, text:e.textContent.trim().slice(0,80), href:e.getAttribute('href'),
                    visible:r.width>0 && r.height>0 && r.bottom>0 && r.top<innerHeight,
                    focusIndicator:(s.outlineStyle!=='none' && parseFloat(s.outlineWidth)>0) || s.boxShadow!=='none'};
                }""")
                focus_sequence.append(focused)
                if not focused["visible"] or not focused["focusIndicator"]:
                    errors.append(f"{route}: keyboard focus is not visible: {focused}")
            interactions.append({"type": "desktop-tab-sequence", "route": route, "focusSequence": focus_sequence})
            page.close()
        context.close()

        context = browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        for route in ROUTES:
            page = context.new_page()
            page.goto(base + route, wait_until="networkidle")
            nav_links = page.locator("[data-site-nav] a")
            visible_navigation = nav_links.count() > 0 and all(nav_links.nth(i).is_visible() for i in range(nav_links.count()))
            expected_route = route[3:] if route.startswith("/fr/") else "/fr" + route
            destinations = page.locator("[data-language-link]").evaluate_all("links => links.map(link => new URL(link.href).pathname)")
            overflow = page.evaluate(OVERFLOW)
            passed = visible_navigation and expected_route in destinations and overflow["scrollWidth"] <= 391 and page.locator("h1").is_visible()
            interactions.append({"type": "no-javascript-mobile", "route": route, "passed": passed, "navigationVisible": visible_navigation, "counterpartRouteLinked": expected_route in destinations})
            if not passed:
                errors.append(f"{route}: no-JavaScript mobile fallback failed: navigation={visible_navigation}, counterpart={destinations}, overflow={overflow}")
            page.close()
        context.close()

        context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        for route in ("/", "/fr/"):
            page = context.new_page()
            page.goto(base + route, wait_until="networkidle")
            motion = page.evaluate("""() => ({scrollBehavior:getComputedStyle(document.documentElement).scrollBehavior,
              transitions:[...document.querySelectorAll('button, a, .nav-toggle-mark')].map(e=>getComputedStyle(e).transitionDuration)})""")
            passed = motion["scrollBehavior"] == "auto" and all(value == "0s" for value in motion["transitions"])
            interactions.append({"type": "reduced-motion", "route": route, "passed": passed, **motion})
            if not passed:
                errors.append(f"{route}: reduced motion preference failed: {motion}")
            page.close()
        context.close()

        # Separate cold-cache samples for honest, local-browser medians.
        performance_samples = []
        for route in ("/", "/fr/", "/projects/pde-image-denoising/", "/projects/inverse-studies-synthesis/"):
            for width in (390, 1440):
                samples = []
                for _ in range(3):
                    context = browser.new_context(viewport={"width": width, "height": 844})
                    context.add_init_script(OBSERVER)
                    page = context.new_page()
                    page.goto(base + route, wait_until="networkidle")
                    page.wait_for_function("document.fonts.status === 'loaded'")
                    samples.append(page.evaluate(MEASURE))
                    context.close()
                numerical = ("domContentLoadedMs", "loadMs", "firstContentfulPaintMs", "largestContentfulPaintMs", "cumulativeLayoutShift", "requests", "transferredBytes", "decodedBytes")
                performance_samples.append({"route": route, "width": width, "samples": samples, "median": {key: statistics.median(sample[key] for sample in samples if sample[key] is not None) for key in numerical}})

        throttled_samples = []
        for route in ("/", "/fr/", "/projects/pde-image-denoising/"):
            samples = []
            for _ in range(3):
                context = browser.new_context(viewport={"width": 390, "height": 844})
                context.add_init_script(OBSERVER)
                page = context.new_page()
                cdp = context.new_cdp_session(page)
                cdp.send("Network.enable")
                cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150, "downloadThroughput": 1_600_000 / 8, "uploadThroughput": 750_000 / 8, "connectionType": "cellular4g"})
                cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
                page.goto(base + route, wait_until="networkidle")
                page.wait_for_function("document.fonts.status === 'loaded'")
                samples.append(page.evaluate(MEASURE))
                context.close()
            throttled_samples.append({"route": route, "width": 390, "samples": samples, "median": {key: statistics.median(sample[key] for sample in samples if sample[key] is not None) for key in numerical}})
        browser.close()

    result = {"passed": not errors, "browser": "Chromium " + browser_version, "axeVersion": "4.10.3" if axe_available else None,
        "scope": {"routes": len(ROUTES), "viewportWidths": WIDTHS, "pageViewportChecks": len(audits), "axePageViewportChecks": sum(1 for audit in audits if audit['width'] in (390, 1440)) if axe_available else 0},
        "errors": errors, "warnings": warnings, "audits": audits, "interactions": interactions,
        "captionContrast": {"method": "Computed foreground and nearest solid ancestor background, WCAG sRGB relative luminance formula; complements axe incomplete checks for clipped mobile captions", "results": caption_contrast},
        "performance": {"method": "Three fresh Chromium contexts per route and viewport against a local HTTP server; no CPU/network throttling; medians are lab measurements, not production or field performance", "results": performance_samples},
        "mobileThrottledPerformance": {"method": "Three fresh Chromium contexts at 390px against a local server, CDP CPU slowdown 4x, network latency 150ms, download 1.6Mbps, upload 750kbps; simulated lab conditions, not a Lighthouse score or field data", "results": throttled_samples},
        "screenshots": screenshots}
    report = args.output_dir / "browser-audit.json"
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("passed", "browser", "axeVersion", "scope", "errors", "warnings", "screenshots")}, indent=2, ensure_ascii=False))
    print(f"Full report: {report}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
