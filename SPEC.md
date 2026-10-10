# Manufacturer Scraper Spec — v1 (locked 2026-10-09)

Purpose: index manufacturer product families for builders in the US & Canada who are
choosing manufacturers. Priorities: spec sheets, CAD, structured specs, manufacturer price.
This spec defines what is "correct" for both the existing agent and the new agent.

## 1. Scope
- Target: the manufacturer site in `input.txt`, plus its own asset/CDN hosts (allowlisted per site,
  e.g. `aalberts.compano.com` for Apollo, `cdn.siouxchief.com` for Sioux Chief).
- Excluded: distributors, sister-company domains (e.g. amresist.com), regional parent sites
  (e.g. web.cimberio.com), unless the NA site links to them directly as an asset of that product.
- Market: United States and Canada.

### 1a. Crawling rules (decided 2026-10-09)
- **robots.txt is not obeyed.** Pages and files it disallows are in scope. Each run records how many
  disallowed URLs it fetched (`robots_overridden` in run stats), so the decision stays visible.
- Still required: at most 1 request/second per host (or the site's Crawl-delay if larger), an honest
  User-Agent, no logins, no form submissions.
- Sites that actively block automated access (HTTP 403/429 challenges) are fetched only with a normal
  browser at the same rate. Techniques to get around bot protection are not used; if a site stays
  blocked, it is reported as blocked.

## 2. Language
| Case | Rule |
|---|---|
| `en-US` / `en-CA` version exists | Use it |
| Only generic `en` | Use it |
| Only international English (`en-int`, `en-GB`) | Use it, set `market_flag: non_na` |
| Bilingual / multilingual document | Include only if English is primary (English first and >= 50% of text); list languages in order: `en+fr`, `en+fr+es` |
| No English | Exclude |

Language is verified from content (page/PDF text), not only the URL.

## 3. Unit of record: product family
- One record per product family (series). Variants (SKU / size / configuration) are nested.
- SKU-level sites are grouped into families via series code, breadcrumbs, or a shared spec sheet.
- Every document, CAD file, image, and price links to a family or variant. Unlinkable items go to
  `unlinked[]` and are reported, never silently dropped.

## 4. Inclusion rules
| Item | Rule |
|---|---|
| Product family page | Include, one canonical URL |
| Variant pages | Recorded as variants, not separate products |
| Category / company / news / careers / contact / search pages | Exclude |
| Locale duplicates | Exclude (kept as `alternates` metadata only) |
| Images | Highest-quality version of each distinct image only; all smaller renditions dropped; min 300 px on the shortest side |
| Installation / application / lifestyle photos (e.g. "rough-in", "finish installation", in-use scenes) | Exclude (decided 2026-10-09): only product photos and dimensional drawings |
| Site chrome (logos, icons, social previews, assets on >~20% of pages) | Exclude |
| PDFs | Include, labelled by `doc_type` (section 5) |
| CAD | Include direct files; hosted/gated CAD recorded as a link only (no form submission) |
| Price | Manufacturer-site sources only (section 7) |

## 5. Taxonomy
Documents (`doc_type`):
- Primary: `spec_sheet`, `submittal`, `price_list`
- Secondary: `iom_manual`, `brochure`, `catalog`, `certificate`, `warranty`, `other_doc`

CAD (`cad_type`):
- `cad_file`: .step/.stp, .dwg, .dxf, .igs/.iges, and zips containing them (classified by contents)
- `bim`: .rfa, .rvt
- `cad_viewer`: hosted/gated CAD (PARTcommunity/CADENAS, TraceParts, CADdetails, BIMobject, ...)

Images (`image_type`): `product_photo`, `dimensional_drawing`, `other`.

## 6. Spec fields (family level; variant overrides where they differ)
- Size: range, unit system (NPS / DN / in / mm / CTS / IPS; CTS = copper tube size, IPS = iron pipe size), list of available sizes
- Materials: body, trim/disc/ball, seat, seals
- End connection: NPT, solder, press, PEX, grooved, flanged (+ class), ...
- Ratings: pressure (with units and conditions, e.g. 600 WOG), temperature range
- Certifications / standards: NSF/ANSI 61, NSF/ANSI 372, UL, FM, CSA, ASME B16.xx, ASTM, MSS SP-xx
- Application / use case: potable, HVAC hydronic, fire protection, gas, industrial, ...
- Product type: ball valve, butterfly, check, strainer, ...

**Family vs variant level (decided 2026-10-09).** Specs live at family level. A variant gets a
`spec_overrides` entry **only** when its value for a scored field differs from the family value and
the difference cannot be expressed at family level (as a range, e.g. `size_range`, or a list, e.g.
`sizes_available`, `end_connections`). Size alone never needs an override (it is `variant.size`).

**Materials that differ by variant (decided 2026-10-10).** When variants differ only in a material
field, record the family-level value as a comma-separated list in order of first appearance
(e.g. `material_body: "PVC, ABS"`) and do **not** add per-variant overrides. Overrides remain only for
values that cannot be written as a family-level range or list (e.g. a pressure rating that differs by size).

**Single size.** A family available in one size records `size_range` with `min` = `max`.

Every value stores: `value`, `unit` (normalized), `raw_text`, `sources[]` (each: url, type page|pdf, PDF page number, section, verbatim quote, snapshot hash, retrieval time).

### 6a. Page vs spec sheet: cross-check and precedence (decided 2026-10-09)
Specs may appear on the web page, in the PDF, or both. **Every field is checked in both places.**
- Web pages are checked fully: every tab and accordion is opened, and every variant selector is stepped through (selection only; nothing is submitted).
- Each field records `cross_check`:
  | Value | Meaning |
  |---|---|
  | `agree` | the page and the spec sheet both state it, and they match |
  | `refines` | both state it; the spec sheet value is a **more specific form** of the page value (e.g. page "Plastic" → sheet "PPSU"; page "Brass" → sheet "No-Lead Brass"; the sheet's list contains every item of the page's list and more). Counts as agreement. |
  | `conflict` | both state it, and they **contradict** (e.g. 400 vs 600 psi; "Brass" vs "Bronze"; the page lists an item the sheet does not) |
  | `pdf_only` | only a PDF states it |
  | `page_only` | only the web page states it |
  | `not_checked` | not allowed in gold; counts against an agent |
- **Display precedence:**
  1. spec sheet or submittal PDF
  2. web page
  3. any other PDF (catalog, brochure, IOM)

  The highest-priority source that states the field supplies `value`, and `display_source` says which kind of source that was.
- **Conflicts are never resolved silently.** `value` = spec sheet value, `cross_check: conflict`, and the other value(s) are kept in `alt_values` with their own sources.
- **Refinements are recorded, not hidden.** `value` = spec sheet value, `cross_check: refines`, and the page's more general value is kept in `alt_values` with its source.
- Numbers never "refine": a different number, range or rating is a `conflict`.
- A family records `spec_source_summary`: `pdf`, `page`, `both` or `none`.

### 6b. Provenance: is this spec sheet really this manufacturer's and this product's?
A PDF used as a spec source must:
1. be served from an allowed host (the manufacturer's site or CDN, not a distributor copy);
2. be linked from one of the family's own pages (`found_on` = canonical, alternate or variant page);
3. mention the family's series code (or name) in its text.

Failing 1 or 2 is an error. Failing 3 is informational when 2 holds (series-level sheets often omit a family code), and the reason goes in the ambiguity log.

### 6c. Evidence
Every cited source (page or PDF) has a snapshot. Its extracted text is saved as `evidence/text/<sha256>.txt`, where the sha256 is that of the PDF file or the page HTML. Every `quote` must appear in that text, and this is checked automatically.

## 7. Price (manufacturer only, variant level)
| Field | Notes |
|---|---|
| `amount`, `currency` | USD / CAD |
| `price_type` | `list` / `sale` / `msrp` / `net` |
| `unit_of_measure`, `pack_qty` | each / box / case |
| `min_order_qty` | if stated |
| `availability` | `price_shown` / `login_required` / `request_quote` / `not_published` (always filled) |
| `effective_date` | price-list revision date, else scrape date |
| `price_list_id` | if from a price-list PDF |
| `notes` | e.g. "subject to distributor multiplier" |
| source | URL (+ page number if PDF) |

## 8. Output schema
```
ProductFamily
  family_id, name, series_code, product_type, canonical_url, alternates[], market_flag
  specs{field: {value, unit, raw_text, display_source, cross_check, sources[], alt_values[]}}, spec_source_summary
  variants[]:  { sku, size, spec_overrides{}, prices[], page_url }
  documents[]: { url, doc_type, priority, lang, title, revision_date, sha256, bytes, http_status, found_on }
  cad[]:       { url, cad_type, formats[], gated, found_on }
  images[]:    { url, image_type, width, height, phash, found_on }
SiteRun
  site, input_url, run_at, agent_version, site_profile,
  coverage{ families, pct_with_specs, pct_with_spec_sheet, pct_with_image, pct_with_cad, pct_with_price },
  unlinked[], flags[]
```
Also exported as a flat CSV (`url, url_type, family_id`) for row-level comparison with the existing agent.

## 9. Automatic quality checks (every run)
- No two images in one family with the same perceptual hash
- No non-English or off-allowlist URLs
- Every PDF has `doc_type`, `lang`, HTTP 200, and a file type verified from its first bytes
- Every spec value and price has a source citation
- Every quote is found in the saved snapshot text of its source
- Spec-sheet value is displayed when present; every page/PDF disagreement is flagged `conflict`
- Every PDF cited for specs passes the provenance checks (6b)
- Family count is compared with the sitemap; a gap of more than 15% raises a flag

## 10. Evaluation
- Answer key: about 15 hand-labelled families each on Sioux Chief (clean, SKU-level, BIM) and Bray
  (messy, multilingual, STEP zips), then extended to the other sites.
- The existing agent's output is filtered and relabelled to v1 before comparison.
- Metrics: family recall; spec-sheet recall and precision; CAD recall; image dedupe rate;
  spec completeness (any source); spec-field accuracy, split by page vs PDF; conflict-detection
  recall and precision; price accuracy; cost and time per site.

## 11. Implementation
The exact field names, value formats and output format are defined in `harness/schema/siterun.schema.json`.
Scoring and rule checks live in `harness/` (see `harness/README.md`); the answer-key brief is `harness/DEVIN_TASK.md`.
