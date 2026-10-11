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
- One record per product family (series). Variants are nested.
- **A variant is an orderable item with its own manufacturer identifier** (SKU, part number or model
  number) (decided 2026-10-10). Sizes or options listed without an identifier are NOT variants: they go
  in family-level fields (`sizes_available`, `end_connections`, material lists). A family whose site lists
  no identifiers has an empty `variants` list.
- **Option codes are not variants (decided 2026-10-11).** Variants are the identifiers that the page heading,
  a variant selector, or the spec sheet's own selection/dimension/part-number tables assign to this family.
  Codes named only in notes or option lines (suffixes such as `AT` = American thread or `.PF` = press-fit,
  "bare shaft available, Fig No ...", "please add suffix ...") are options: list them in
  `additional_specs.options`, not as variants. Identifiers on a shared sheet that have their own family page on
  the site belong to that family, not this one.
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
| Images | Every distinct product view (photos, 3D renders, cutaways) as `product_photo`; dimensional drawings as `dimensional_drawing`. Highest-quality version of each only: smaller renditions, and crops or zooms of an image already kept, are dropped. Exclude graphics that are mostly text or callouts (feature infographics). Min 300 px on the shortest side (decided 2026-10-10) |
| Installation / application / lifestyle photos (e.g. "rough-in", "finish installation", in-use scenes) | Exclude (decided 2026-10-09): only product photos and dimensional drawings |
| Site chrome (logos, icons, social previews, assets on >~20% of pages) | Exclude |
| PDFs | Include, labelled by `doc_type` (section 5) |
| CAD | Include direct files; hosted/gated CAD recorded as a link only (no form submission) |
| Price | Manufacturer-site sources only (section 7) |

**Image edge cases (decided 2026-10-11).** Text that belongs to the product itself (dome or nameplate markings, logos) and short letter/number markers on a cutaway do not make an image an infographic; it is excluded as an infographic only when sentences, leader-line labels or feature callouts carry its meaning. A collage of renders of the product's own options (indicator colours, body styles) without such text is one `product_photo`. When the page shows the same view both clean and with callouts added, keep the clean version and drop the annotated one. Candidates are only the image URLs the family page references (img src/srcset, data attributes, CSS backgrounds, links); "highest-quality version" means the largest of those, not an un-linked original found by editing a URL (e.g. removing a `mobile/` folder or a size suffix), so two labellers reach the same file.

## 5. Taxonomy
Documents (`doc_type`):
- Primary: `spec_sheet`, `submittal`, `price_list`
- Secondary: `iom_manual`, `brochure`, `catalog`, `certificate`, `warranty`, `other_doc`

**Classify by content (decided 2026-10-11).** A document's type follows what it is, not its file name, folder or site label; apply the first rule that fits. Certificates, warranties, submittals and price lists keep their own types.
1. `iom_manual`: instructions to install, commission, operate, configure, maintain or proof-test the product, including quick-start guides, safety / SIL / functional-safety manuals, and manuals for a communication protocol or option module (DeviceNet, PROFIBUS, AS-i).
2. `catalog`: technical or ordering data for several products (product or range overviews and product guides with a specification block per series; selection guides that list products with part numbers), part-numbering / ordering-code guides even for one family, and any technical (sales) manual longer than 4 pages, single- or multi-series.
3. `spec_sheet`: up to 4 pages about this family, or about one option, module or accessory sold for it, containing a technical-data block (specification table, materials/parts list, ratings or dimensions), whatever it calls itself ("Technical Manual", "Technical Sales Manual", "Product Brochure", "Recommended Specification", "Weights & Dimensions", a communication-protocol data sheet). A sheet for an option or accessory is a spec source only for values it states for the family itself.
4. `brochure`: marketing pieces of any length or product count (features, benefits, applications, solutions, facility or company presentations) with no per-product specification block or ordering data, and single-family documents over 4 pages that present themselves as a brochure.
5. `other_doc`: reference material not tied to choosing or ordering one product: technical bulletins, sizing or actuator-selection guides without part numbers, reference charts (e.g. hazardous-location classification charts), bolting guides.

Software and configuration files (EDS/GSD files, firmware, software ZIPs) are neither documents nor CAD and are not recorded.

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

**Controlled vocabularies (decided 2026-10-10).** `end_connections` and `applications` use only these
terms (exact spelling), mapped from whatever wording the source uses. A source term that maps to none of
them is kept verbatim in `additional_specs` under `end_connections_other` / `applications_other`.

`end_connections`:

| Term | Covers (source wording) |
|---|---|
| `NPT` | NPT, FNPT, MNPT, FIP, MIP, NPTF, "taper pipe thread (US)" |
| `BSPT` | BSPT, BSP (no parallel qualifier), R/Rc, ISO 7-1, BS EN 10226, BS 21 (taper threads) |
| `threaded` | threaded, with no thread standard stated; also parallel pipe threads (BSP parallel, G, ISO 228, BS 2779), with the verbatim wording in `end_connections_other` (decided 2026-10-11) |
| `solder` | solder, sweat, C, CxC, "copper tube end" |
| `press` | press, press-fit, ProPress, MegaPress |
| `PEX crimp` | ASTM F1807, F2159, crimp ring, clamp ring |
| `PEX expansion` | ASTM F1960, cold expansion, ProPEX |
| `PEX` | PEX with no joining standard stated |
| `push-fit` | push-fit, push-to-connect, PDQ, SharkBite-style |
| `compression` | compression |
| `flare` | flare, SAE flare |
| `grooved` | grooved, roll groove, cut groove, Victaulic-style |
| `flanged` | flanged, full flanged, ANSI/ASME class flanges (class goes in `raw_text`) |
| `wafer` | wafer |
| `lug` | lug, lugged, full lug |
| `butt weld` | butt weld, BW |
| `socket weld` | socket weld, SW |
| `solvent weld` | solvent weld, socket (PVC/CPVC/ABS), spigot for solvent cement |
| `hub` | hub, hubbed |
| `no-hub` | no-hub, hubless |
| `spigot` | spigot (not for solvent cement) |
| `union` | union, union end |
| `hose` | hose thread, GHT, hose barb |
| `closed` | closed end, capped, plugged, spun-closed |

Male/female is not recorded. A connection type counts once, even if the product has two such ends.

`applications` (service, i.e. what the product handles, then sector):

| Group | Terms |
|---|---|
| Service | `potable water`, `domestic hot water`, `hydronic heating`, `chilled water`, `HVAC`, `steam`, `condensate`, `natural gas`, `propane`, `compressed air`, `vacuum`, `fire protection`, `irrigation`, `DWV`, `sanitary drainage`, `storm drainage`, `wastewater`, `industrial process`, `chemical`, `oil and gas`, `food and beverage`, `marine`, `slurry`, `power generation`, `pulp and paper`, `mining` |
| Sector | `residential`, `commercial`, `industrial`, `institutional` |

Record every term the source supports; do not infer a sector from a service. "Water" alone maps to
`potable water` only if the source says potable/drinking; otherwise keep it in `applications_other`.

**Mapping strictness (decided 2026-10-11).** Map source wording to a term only when it names the term or
wording listed for it above; do not derive a term from context. Pipe or tube types a product holds,
room or building types (kitchens, hospitals, shower areas), "fire-rated" walls/applications, and
"hot and cold water" without potable/drinking/domestic stay in `applications_other`. For an end, map
the connection named (`2" Sch. 40 hub` → `hub`); a joining method the sheet describes for that same
end in prose is not a second term. Wording that lists alternatives for one end (`MSWT/Press/Push`)
records each (`solder`, `press`, `push-fit`). If no source wording for a field maps to a term, omit the
field from `specs` and keep the wording only in `*_other`; a source whose wording maps to no term is
no longer a source for the field, and `cross_check` follows the remaining sources.

**Single size.** A family available in one size records `size_range` with `min` = `max`.

**Standards scope (decided 2026-10-11).** `standards` lists every standard the source says the product conforms to
or is designed, tested, threaded, drilled or flanged to (e.g. BS EN 593, BS 7350, BS EN 10226-2, ISO 7-1, ISO 228,
BS EN 1092-2, ANSI B16.1), one entry per standard number as written (year and part suffixes as given). Standards
named only as "formerly ..." and test standards of other products are not listed. Thread or flange standards are
recorded here in addition to the `end_connections` term.

**PN and class designations (decided 2026-10-11).** A PN designation (PN16, PN25) is recorded as
`pressure_rating` value = the PN number, unit `bar`, `raw_text` the designation. When a source gives only a class
(e.g. ANSI 125) and the same sheet has a pressure/temperature table in bar or psi, the value is the table's maximum
pressure; the class stays in `raw_text`. Page and sheet are cross-checked on the designation they state.

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

**Families without variants (decided 2026-10-11).** A family that lists no identifiers (SPEC 3) has no variants to
hold a price, so its price status goes in the family field `family_prices` (same `price` object, `availability`
always filled, e.g. `request_quote` for a "Request a Quote" page). `family_prices` is used **only** when `variants`
is empty; families with variants keep prices on the variants. Its `availability` is scored with the variant prices.

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
