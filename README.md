# Halhoul Mhamed — Academic portfolio

A complete English/French academic portfolio for **Halhoul Mhamed**, M2 in progress at **Université Abdelmalek Essaâdi**, **Faculté Polydisciplinaire de Larache**, in the Master **« Modélisation mathématique et applications et apprentissages »**.

Production address: <https://halhoulmhamed-droid.github.io/>.

## Site and language architecture

English is the default. Every content page has a complete French counterpart under `/fr/`. The language selector preserves the current page and, with JavaScript enabled, its query parameters and fragment. Both languages work without JavaScript. Canonical URLs, reciprocal `hreflang` entries, `x-default`, translated descriptions, Open Graph metadata and JSON-LD are rendered into each document.

Existing addresses are retained: `/`, `/about/`, `/projects/`, `/projects/pde-image-denoising/`, `/projects/talk-to-agent/`, `/projects/hujja/`, and `/404.html`. The Google verification file is unchanged. New addresses include `/contact/`, `/projects/nn-optimization-benchmark/`, `/projects/inverse-laplace-learning/` and `/projects/inverse-studies-synthesis/`, together with their French counterparts.

The production site uses semantic HTML, shared CSS, system fonts, a small navigation script and responsive WebP images. It has no framework, runtime package dependency, analytics, external font or contact form. A static HTTP server is sufficient. Committed HTML is served by GitHub Pages; `_config.yml` excludes development sources and documentation from the published site.

## Scientific scope and provenance

The academic entries are **Master’s scientific projects**, separate from software projects and peer-reviewed publications. No algorithmic novelty or general superiority is claimed. Positive results, unsuccessful criteria, inconclusive hypotheses and limitations are retained. Original academic PDFs are in French; the website explains their scientific content in both languages. Original figure labels are retained as published, with translated captions, English keys, alternative text and full-size links.

Sources inspected on 11 October 2026:

| Project | Documentary edition | Scientific archive |
| --- | --- | --- |
| PDE image denoising | `main`: `155bbe46d38e0c526493e77af288f08e748ed584` | `ae03109cdb2150b760e5a4b8bcffb56bba1b98e0` |
| NN optimization benchmark | `main`: `155036dcbcbc80b9ec076261c1f7ad90a081832b` | scientific base `194561b84e190d953f85d1f01281f0d758907a05` |
| Inverse study 1 and synthesis | `main`: `0b93908ce5258f2063e94c33882193bb731b3639` | study 1: `0ea95cd7e390c8a478469b36a043a5f99e4fcd10` |
| Inverse study 2 | `study2-covariances-20261011`: `1f11fea35d5367a355901c3866d21f5b3b21a5b0` | `57ab54ebc994029be3c24a8a34da56371547f4ac` |
| Inverse study 3 | `study3-covariance-h1-20261011`: `0846e8f6be44008ad26f31856531c8afdbd563f8` | `867144db98eba3c0f5fe7cece4261918a46f1c31` |

A sealed archive identifies inspected bytes; it does not establish an unrecorded historical execution commit. Every scientific page links to immutable PDF, LaTeX, code, data and provenance sources. Figure derivatives are resized/converted from existing scientific figures, without changing their results or rerunning experiments. Original plots and numerical archives remain available through source links.

PDE report and presentation: **Halhoul Mhamed and Khalil Amraoui**; supervisor **Pr. Hatim Tayeq**. NN supervisor: **Pr. Jamal Daoudi**. Inverse-problems supervisor: **Pr. Chakir Tajani**. Personal contributions are limited to what the published sources document; coauthor writing tasks are not inferred.

Hujja remains pre-alpha at the contract layer, with no operational screening engine claimed. Talk-to-Agent remains a local voice-integration prototype, with production limitations stated. Their current documentary sources are pinned in the corresponding pages.

## Local development and preview

Use the existing checkout; cloud tasks are already isolated and need no additional Git worktree.

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Use HTTP serving for root-relative links and assets. Cloud onboarding does not expose a user-facing loopback preview URL. Review captures are in `.github/review/`; CI retains a static `portfolio-preview` artifact without deploying it.

The current GitHub Pages deployment uses the committed HTML. A pull request or branch push does not change the production site. Merge and production publication require owner validation.

## Content editing

`content/pages.json` holds complete scientific and software case text in both languages. `tools/build_site.py` supplies the shared document layout, navigation, home, education and contact pages. Changes to those sources must be followed by:

```sh
python3 tools/build_site.py
python3 tests/check_site.py
node --check assets/js/main.js
git diff --check
```

The generator needs Python 3 only. It uses no package downloads or scientific dependencies. Running it again must leave committed generated HTML unchanged. No experiments are part of this workflow.

When updating a scientific entry, inspect relevant public branches, distinguish documentary and scientific versions, verify immutable target paths, preserve uncertainty and attribution, update both languages and recheck figure/data provenance. Only documented projects should be added.

## Browser and release checks

The standard-library static validator checks the 20 content routes, reciprocal language URLs, titles/descriptions, JSON-LD, internal links, anchors, image dimensions, assets and XML/sitemap coverage.

`tests/browser_audit.py` is a development-only audit using Python Playwright, Chromium and axe-core. It checks four widths (320, 390, 768 and 1440 px), language-page preservation, navigation/skip-link keyboard behaviour, table keyboard scrolling, resource loading, runtime errors and automated accessibility. It captures both languages and measures browser navigation, FCP/LCP/CLS and transferred bytes. Its separately throttled mobile samples are local laboratory measurements, not field Core Web Vitals or a Lighthouse score.

To run it with already installed audit tools, start the static server and consult:

```sh
python3 tests/browser_audit.py --help
```

The output directory and axe script path are explicit arguments. Keep reports, browser traces and work logs outside the published site. `.github/workflows/portfolio-checks.yml` runs the static checks and retains review artefacts; it does not deploy the site.

Before release, inspect the English and French screenshots, contrast, focus visibility, mobile menu, reduced-motion behaviour and the entire diff. External HTTP failures must be distinguished from proxy restrictions. Automated accessibility checks do not replace broader assistive-technology review.

## Contact

- University: <halhoul.mhamed@etu.uae.ac.ma>
- Personal: <halhoulmhamed@gmail.com>
