# Devin task: build the answer key (gold) for Sioux Chief and Bray

## Context
We are building a new, site-agnostic manufacturer scraping agent to compare against an existing
agent whose output is in `../{train,dev,test,challenge}/<site>/output.csv`. Before building anything,
we need a hand-verified answer key to score both agents against.

**Read first:** `../SPEC.md` (the rules for what counts and how to label it) and
`schema/siterun.schema.json` (the exact output format). `gold/_TEMPLATE.json` is a worked example.

**Do not** build the scraping agent in this task. **Do not** change the scoring logic in `mfr_harness/`.
If you find a bug in the harness or a gap in the spec, log it in `gold/HARNESS_ISSUES.md` and keep going.

## Setup
```bash
cd harness
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt imagehash Pillow pypdf
python -m unittest discover tests        # all tests must pass, including the schema test
```

## Rules of engagement (apply to every request)
- `robots.txt` is **not** obeyed (SPEC 1a): disallowed pages and files are in scope. At most 1 request per
  second per host. Use a descriptive User-Agent.
- No logins and no form submissions (this includes gated CAD download forms).
- If a site blocks you (403/challenge page), use a normal browser session at a slow rate. Do not use
  techniques intended to get around bot protection. If it stays blocked, record it in `flags` and `site_profile.blocked`.
- Use the US/Canada English version of every page (SPEC section 2).

## Deliverables (per site: `sioux-chief`, `bray`)
1. `gold/<site>.json`: answer key in the SiteRun format.
2. `gold/<site>.ambiguities.md`: every judgement call (see step 5).
3. `gold/<site>.evidence/`: everything you cited:
   - `files/`: downloaded PDFs and CAD zips, plus the HTML of every page you cited, each named `<sha256>.<ext>`.
     Keep these in your VM but **do not commit them** (they are git-ignored); commit `text/` and `manifest.csv`.
   - `text/<sha256>.txt`: extracted text of every cited PDF and page. This is what the validator checks quotes
     against. For pages, save the text **after** opening the tab or selecting the variant where the value appears.
   - `manifest.csv`: url, sha256, bytes, content_type, retrieved_at
   Images are optional; their dimensions and phash are enough.
4. `gold/HARNESS_ISSUES.md`: shared across sites; leave it empty if there are none.

## Steps

### 1. Site profile
Fill in `site_profile`: platform, locale scheme (path prefix, hreflang, subdomain), sitemap URLs,
whether there is a product feed/API, and the fetch mode needed (http or browser).
Confirm `config/sites.json` → `allowed_hosts` for the site (add the manufacturer's own CDN/asset hosts if
you find more; never distributors or other companies). Note any change in `HARNESS_ISSUES.md`.

### 2. family_index (complete list of product families)
- Collect candidate product URLs from **two independent sources**: (a) the sitemap(s) / product feed, and
  (b) crawling the product-category navigation.
- Group them into **product families** (series). On SKU-level sites (Sioux Chief), one family has many
  SKU pages: put the family's main URL in `url` and the SKU pages in `aliases`.
  If the site has no family page, use the most representative SKU page as `url` and explain this in `ambiguities.md`.
- Record the counts (sitemap only / crawl only / both) in `gold_meta.family_index_method`.
- Every family in the index must be an NA-English URL on an allowed host.

### 3. Sample families to label in depth
- Group the index by product category (top-level category from the site's navigation).
- Draw **15 families** in proportion to category size using `random.Random(42)` over the index sorted by URL.
  Save the code you used in `gold/<site>.sample.py` so the draw can be reproduced.
- Coverage requirements. If the random draw misses one, replace the *last* drawn family in the
  largest category and log the swap:
  - at least 3 families with CAD/BIM (if the site has any)
  - at least 3 families with more than one variant (if the site lists identifiers; otherwise log it)
  - at least 1 family with price information or a price list (if the site has any). If prices sit behind a
    login, `login_required` on every variant satisfies this.

### 4. Label each sampled family completely
For every sampled family, record everything the spec includes:
- **variants**: every orderable item with its own identifier (SKU, part number or model number) listed on
  the page or in the family's spec sheet (SPEC section 3). Sizes without identifiers go in `sizes_available`, not variants.
- **documents**: every PDF linked from the family page or its SKU pages. Download each one and:
  - record `http_status`, `bytes` and `sha256`
  - set `mime_verified: true` only after checking the file starts with `%PDF`
  - read the content to set `doc_type` (not the filename) and `lang` (bilingual = `en+fr` only if English is first and is at least half the text)
  - set `revision_date` from the document if it is printed there
- **cad**: direct files (open zips and list the formats inside) plus viewer/gated links (`cad_viewer`, `gated: true`).
- **images**: for each distinct image, find the **largest available version** by checking `srcset`, the
  un-resized original URL (remove `-300x212`, `/styles/.../`, `stencil/WxH` and similar), and the full-size
  link if one exists. Record `width`, `height` and `phash` (`str(imagehash.phash(img))`). Skip anything under
  300 px on the shortest side, site decoration (logos, icons, social preview images), and installation,
  application or lifestyle photos (SPEC section 4). Photos of different sibling SKUs are distinct images.
- **specs**: check **both** the web page and every spec PDF for **every** field (SPEC 6a):
  - On the page, open every tab and accordion and step through every variant selector (select only, never submit).
    Where a value only appears with one variant selected, it is a variant `spec_overrides` entry with `variant_sku` set on its source.
  - Set `cross_check` to `agree`, `refines`, `conflict`, `pdf_only` or `page_only`. `refines` = the spec sheet
    is a more specific form of the page value (page "Plastic", sheet "PPSU"; the sheet's list contains the
    page's list and more). A contradiction, or any different number, is `conflict`.
  - **Displayed `value` precedence:** spec sheet or submittal PDF, then the web page, then any other PDF. `display_source` records which.
  - On a **conflict** or **refines**, display the spec sheet value and put the page value(s) in `alt_values` with
    their own sources. Log conflicts in `ambiguities.md`.
  - Variant `spec_overrides` only when a scored field differs and cannot be written as a family-level range
    or list (SPEC section 6). A single-size family has `size_range` min = max.
  - Every source needs a short verbatim `quote` that appears in its evidence text, plus `snapshot_sha256`, `section` and
    `retrieved_at`. PDF sources also need the page number.
  - Leave out fields that neither source states. Do not infer them. Value formats are in the schema `specs`
    description and `_TEMPLATE.json` (which shows agree, conflict, pdf_only and page_only).
  - Set the family's `spec_source_summary` (`pdf` / `page` / `both` / `none`).
- **Spec PDF provenance** (SPEC 6b). For every PDF you cite, confirm that it:
  - is on an allowed host (not a distributor copy)
  - is linked from one of this family's own pages (`found_on`)
  - mentions this family's series code or name in its text

  A PDF cited for specs or prices must also be listed in the family's `documents`, including site-wide
  price lists. If a spec sheet fails the series check (e.g. a multi-series catalog page), keep it, and explain why in `ambiguities.md`.
- **prices** (per variant): only from the manufacturer's site. Always set `availability`. Use
  `price_shown` only when an amount is visible; otherwise use `login_required`, `request_quote` or `not_published`.

### 5. Ambiguity log
In `gold/<site>.ambiguities.md`, list every page/PDF conflict first (field, both values, both sources, revision
date of the PDF if printed). Then write one entry per judgement call:
`case | what you decided | proposed SPEC.md wording`. Examples: is a category page also a family?
Is a combined catalog page a `spec_sheet` or a `catalog`? Is an image a product photo or a drawing?

### 6. Self-check
```bash
python -m mfr_harness.validate gold/<site>.json --site <site> --gold      # must report 0 errors
# (evidence is read from gold/<site>.evidence/text/; every quote is checked against it)
```
Then re-label **3 randomly chosen families from scratch** without looking at your first pass, and
report agreement (documents, images, specs) at the bottom of `ambiguities.md`. Fix the gold where the
second pass was right.

## Acceptance criteria
- [ ] `python -m unittest discover tests` passes
- [ ] `validate --gold` passes with 0 errors for both sites
- [ ] family_index built from 2 sources, with counts recorded
- [ ] 15 families labelled per site, with coverage requirements met or the reason they couldn't be documented
- [ ] Every spec value and price has a citation whose quote is found in the evidence text; every PDF has sha256 and mime_verified
- [ ] Every spec field was checked on both page and PDF; conflicts display the spec sheet value and are logged
- [ ] Every cited PDF passes the provenance checks, or the exception is explained in `ambiguities.md`
- [ ] The share of families whose specs are page-only, PDF-only or both is reported at the top of `ambiguities.md`
- [ ] Re-label agreement reported
- [ ] Do **not** run `score.py` against the legacy output yet. That is the next task, after review.
