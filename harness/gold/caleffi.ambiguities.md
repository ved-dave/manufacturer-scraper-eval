# caleffi — ambiguity log

Labelled 2026-10-11 against SPEC on main. Locale `en-us`. Independent of any scraper output (no scraper code, runs, reports or PRs opened).

Spec source share (15 families, family-level fields): agree 18, refines 3, conflict 1, pdf_only 10, page_only 9 (41 fields). Variant overrides: 6 (all agree).

## Conflicts
- **3048 FlowShield DuC pressure_rating** | technical brochure 01403_NA p.1 and submittal 03506_NA p.1 "Max. working pressure: 160 psi (11 bar)"; all five product pages "Maximum working pressure : 175 psi" and sell sheet 03667_NA p.2 "MAX. WORKING PRESSURE 175 psi (12 bar)" -> 160 psi displayed (spec sheet + submittal), 175 psi in alt_values, cross_check conflict. The manufacturer's own sheets disagree with each other; the submittal is treated as decisive | SPEC 6a precedence

## Judgement calls
- **Locale** | about 31 path prefixes; `en-us` exists (North American English), no `en-ca`; `en-int` not used -> `en-us`, market_flag na | SPEC 2
- **Family index sources** | (1) `products--en-us/sitemap.xml` (372 product URLs); (2) crawl of the /en-us/ product category pages (196 category pages, 351 product URLs). Both 351, sitemap-only 21 (kept in `unlinked`, kind sitemap_only_product_page), crawl-only 0. The crawl also reached /en-us/education-and-resources/ask-caleffi-podcast, which is not a product page and is excluded | DEVIN_TASK step 2
- **HTTP 403 page** | /en-us/y-body-automatic-balancing-valve-128-caleffi-128440afc returns 403 on every attempt; not bypassed, left out of families; 371 accessible pages indexed | SPEC 1
- **Family definition** | the page "Series" field alone over-merges (574 = AutoFill and FlowShield; 116 mixes valves, gauges, jackets, cartridges) -> family = (series code, product name before the first comma); pages without a series code are their own family. 371 pages -> 292 families (35 multi-page, max 17 pages) | SPEC 3
- **Variants** | orderable codes = the codes in each page's "Drawings and specifications" table ("Expand details for <code>"). The URL suffix is not the code (…-342302 lists 342452) and some codes contain spaces (116240AC 006), so codes are read from the table, never the URL | SPEC 3
- **Sample** | `caleffi.sample.py`: Random(42), proportional to category size, sorted. The seed-42 draw already meets coverage (3 CAD families: 5461, 5024, NA5026; 8 with more than one variant; all 15 with price-sheet evidence), so no coverage swap was made | DEVIN_TASK step 3
- **Prices** | "June 1, 2026 List Price sheet.xlsx" linked from /en-us/caleffi-north-america-catalog; per-code "6.1.2026 List Price" in USD on variants. 75 of 76 sampled codes priced; NA16266L is not in the sheet -> availability not_published | SPEC 7
- **Price sheet citation type** | the schema's source `type` is page|pdf only; the xlsx is cited as `pdf` with page 1, section "Sheet1", against a TSV text snapshot of the sheet. Proposed wording in HARNESS_ISSUES.md | schema (silent)
- **Sell sheets** | 2-page sell sheets with a CODE table and a technical-data block (03555 DISCALDIRTMAG, 03667 FlowShield, 03618 QuickSetter) -> spec_sheet; 03619 (Z-one controls and zone valves, several products) -> catalog | SPEC 5 doc_type rules
- **Technical brochures** | 01131, 01287, 01009, 01090, 01149 (5-9 pages, several series) -> catalog; 01033, 01085, 01403, 01155, 01284, 01285 (<=4 pages, one family, technical-data block) -> spec_sheet | SPEC 5
- **Other documents** | Idronics journals, Revit-content guides (NA11038, NA11011, NA11030) and the water-treatment guide 03194_EN -> other_doc | SPEC 5
- **CAD** | per-code DWG/DXF/IGS/STP under /sites/default/files/media/external-drawing/, recorded with variant scope; each file re-fetched and checked by magic bytes (DWG "AC10", STEP "ISO-10303-21", IGES column 73) because cached responses had reported text/html. Share-intent links (twitter.com …?url=<cad>) are not CAD and are ignored. The generic BIM portal bim.caleffi.com is not product-specific and is not recorded | SPEC 5 CAD
- **Images** | JPG cover kept; WebP and 160x160 Drupal renditions of the same image dropped (phash distance <= 2, shortest side < 300 px); distinct full-size dimensional drawings (342302_dim, 502420_dim) kept as dimensional_drawing, 502420_sez cross-section kept as other | SPEC 5 images
- **5461 materials** | brass (1", 1-1/4") and epoxy-resin-painted steel (1-1/2", 2") pages -> material_body "brass, epoxy resin painted steel" at family level, no overrides (submittals 02921-2, 02922; page "brass" / "steel" in alt_values, refines) | SPEC 3 materials rule
- **5461 temperature** | brass 32-250°F, steel 32-230°F -> family value 32-250°F, temperature override 32-230°F on the six steel codes | SPEC 3 overrides
- **5461 sizes** | sizes from the two pages' "Sizes:" lines; 01287 lists only the steel sizes -> page_only
- **5024 ROBOCAL** | 01090 p.1 is a four-column table for several air vents; the 5024 column (brass, 150 psi (10 bar), 240°F (115°C)) agrees with the page (brass, 10 bar, 0-115 °C); page displayed (01090 is a catalog)
- **172 temperature_range** | the page and 01155 give a primary inlet maximum (195°F) and a control setting range (80-130°F); the inlet maximum is the rating, recorded as {max: 195}; the setting range is not a temperature rating. The sheet names a Grundfos UPS 15-58 pump, the page a UPMS 25-58 (not a scored field)
- **Max-only temperatures** | NA5026 (240°F), 5350 (140°F) and 172 (195°F) state only a maximum -> temperature_range {max: N}
- **3048 material_body** | sheet "DZR low-lead* brass CW724R-M" adds the alloy to the page's "DZR low lead brass" -> refines (Bray precedent: sheet adds alloy). Validator WARN accepted
- **3048 end_connections** | sheet adds PEX expansion (ASTM F1960) to the pages' NPT/PEX crimp/press/sweat; union ends on every page -> ["NPT","solder","press","PEX crimp","PEX expansion","union"], refines
- **ZSR** | "ETL certified to CSA and UL standards" -> certifications [ETL]; "Certified to CSA C22-2 No.24", "Conforms to UL Standard 873" -> standards | SPEC 6 standards scope
- **Parts without scored specs** | F19346 (stem; its documents describe the 132 QuickSetter valve, so no valve specs are copied), NA10979 alarm station (only 24 V AC), F69591 sensor, R0001458 washer: no scored spec fields
- **NA162** | the Presscon selector 03511 gives range-wide values, not NA162 values -> page_only sizes/connections ("union slip nut" -> union)

## Blind re-label
BLIND_PLACEHOLDER

## Top 5 ambiguities
1. 3048 pressure: two Caleffi sheets disagree (160 vs 175 psi).
2. Price workbook cited as `pdf` (schema has no spreadsheet source type).
3. Family definition (series + product name) on a site whose Series field spans unrelated products.
4. Sell sheets with a CODE table and a technical-data block: spec_sheet or brochure.
5. Multi-column catalog tables (01090) where the product's column must be identified by hand.
