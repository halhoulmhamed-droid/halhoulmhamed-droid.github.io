# Mhamed Halhoul — Academic Portfolio

A dependency-free static academic portfolio for [Mhamed Halhoul](https://github.com/halhoulmhamed-droid), who is currently completing the second year (M2) of a Master’s degree in Mathematical Modelling, Applied Mathematics and Machine Learning at Abdelmalek Essaâdi University. He completed M1, and graduation is expected in July 2027.

The English programme wording above is descriptive for international readers. The official French programme title is *Modélisation, Mathématiques Appliquées et Apprentissage*.

The site presents interests in mathematical modelling, optimization, scientific computing, and machine learning in preparation for doctoral study. Python appears as a supporting tool for computation, experimentation, and software integration.

Canonical GitHub Pages address:

`https://halhoulmhamed-droid.github.io/`

## Information architecture

- Home — academic identity, current Master’s stage, interests, and selected academic and software projects
- About — education with distinct M1/M2 coursework status, teaching periods, current interests, doctoral direction, and selected coursework topics
- Projects — distinct academic-work and software-work categories
- Image Denoising with PDEs — reproducible M2 course project with archived experiments, a French report, slides, and explicit study limitations
- Talk-to-Agent — local real-time voice demo, including prototype and production boundaries
- Hujja — pre-alpha rules-as-code project, including missing implementation and advisory boundaries
- Custom 404 page

The Google verification file at the repository root is a service token, not a portfolio content page.

## Visual and technical approach

The interface uses an editorial, academic-journal-inspired system: an ivory canvas, navy text, a restrained teal accent, serif display typography, clear folios, and reusable record and case-study layouts.

The implementation uses:

- semantic HTML5;
- one responsive CSS file;
- minimal vanilla JavaScript for the mobile navigation and footer year;
- no framework, external font, CDN, analytics, cookie, form, package manager, or build step.

## Local preview

From the repository root, run a static HTTP server:

```text
py -m http.server 8000
```

Then visit `http://127.0.0.1:8000/`. Root-relative links and assets should be checked through the server rather than by opening the HTML files directly.

## Adding a documented academic project

Add an academic project only after the work can be documented accurately.

1. Prepare a public repository with a reproducible README: research question, mathematical model, assumptions, method, data or inputs, environment, and reproduction steps.
2. State the project status precisely and identify the sources or references used.
3. Document actual results together with limitations, unresolved questions, and any conditions needed to reproduce them.
4. Add a dedicated site case study using the existing case-page structure, then add a clearly labeled academic-work category and link on the Projects page.
5. Update the page title, description, Open Graph and Twitter metadata where applicable; update structured data only with verified facts.
6. Add the canonical URL to `sitemap.xml` and update `lastmod` only for pages changed in that release.
7. Recheck internal links, semantic heading order, keyboard navigation, responsive layouts, JSON-LD, XML, and `git diff --check`.
8. After factual verification, align the GitHub profile README and LinkedIn wording.

A commit alone is not a publication trigger. Projects remain manually curated so that repository activity cannot create unsupported academic claims.

## Release checks

Before any commit or push:

- review every visible status and limitation against the corresponding repository;
- serve the site locally and inspect desktop, tablet, and narrow mobile widths;
- test the mobile menu, focus states, skip links, and reduced-motion behavior;
- validate HTML, JSON-LD, internal paths, resources, `robots.txt`, and `sitemap.xml`;
- run `git diff --check` and inspect the complete diff.

## Public identity links

- [GitHub](https://github.com/halhoulmhamed-droid)
- [LinkedIn](https://www.linkedin.com/in/mhamed-halhoul/)
- [ORCID](https://orcid.org/0009-0007-3893-2603)
