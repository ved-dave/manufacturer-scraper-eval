# crane (Crane Fluid Systems, https://www.cranefs.com/) — ambiguity log

**Spec source share (161 scored spec values, 15 families):** both page and PDF 92 (agree 68, refines 16, conflict 8) · PDF only 66 · page only 3.
Spec-sheet values display on conflict/refines; the page value is in `alt_values`. Numbers never refine.

## Conflicts (sheet value shown, page value in alt_values)
| family | field | sheet | page |
|---|---|---|---|
| d933 | pressure_rating | PN25 (title, P/T table 25 bar) | PN16 |
| d933 | end_connections | BSPT, threaded (ISO 228), NPT (ANSI B1.20.1AT) | BSPT, threaded, press ("complete with Press-Fit connectors") |
| d933 | standards | BS 7350 | "Vibration tested to DVGW and bend tested to BS EN331" |
| d901 | temperature_range | -10 to 120 °C | "10 - 120°C" (minus sign missing) |
| d171aexs | size_range | 1/2 to 2 in (SIZE (inch) table) | 1/4" to 2" |
| f611 | temperature_range | -10 to 90 °C ("Liner (F611) Nitrile Temp. -10 to 90°C") | -10 to 130 °C (the F626 EPDM figure) |
| fm638-fm639 | size_unit / size_range | SIZE (DN) 50-600 | 50mm to 600mm |

## SPEC changes made
Commit `spec: option codes are not variants; BSP parallel threads -> threaded; PN designations -> bar`:
1. SPEC 3: option codes named only in notes (AT suffix, .PF, "bare shaft Fig No ...", "add suffix ...") are options → `additional_specs.options`, not variants; identifiers on a shared sheet that have their own family page belong to that family.
2. SPEC 6 end_connections: BSPT = taper threads (and bare "BSP"); parallel pipe threads (BSP parallel, G, ISO 228, BS 2779) → `threaded` + verbatim in `end_connections_other`.
3. SPEC 6: PN designation → `pressure_rating` = PN number in bar; class-only (ANSI 125) → max of the same sheet's P/T table; cross-check compares the designations.

Stage 2 commit `spec: standards include thread/flange standards the product is made to (blind re-label disagreement)`:
4. SPEC 6 Standards scope: every standard the source says the product conforms to or is designed, tested, threaded, drilled or flanged to; "formerly ..." standards excluded. Cause of the only sub-80% row (standards 0/6 before fixes).

## Checkpoint self-review (after DEVIN_TASK steps 1–3; done unattended)
- (a) Family definition matches SPEC 3: one record per product page (one figure or a heading group such as "FA648L / FA644L / ..."); variants = identifiers in the page heading or the sheet's own tables.
- (b) family_index from 2 independent sources: product-sitemap.xml (via sitemap_index.xml) and a crawl of the top navigation category menus → category pages → product links. 217 in sitemap, 216 via crawl, 216 in both (1 sitemap only: /product/uncategorized/commpac/, which redirects to /product/commpac/commpac/ and is not linked from the menus; 0 crawl only after reconciliation). Recorded in gold_meta.family_index_method.
- (c) Sample: crane.sample.py, random.Random(42) over the index sorted by URL, grouped by top-level nav category (General Valves 102 → 7, Connected Solutions 34 → 2, Pipe Fittings 33 → 2, ProBalance 26 → 2, Public Health Valves 22 → 2; largest remainder). Coverage: CAD/BIM 9 ≥ 3; multi-variant swap: D15 (/product/globe-valves/d15/) → FM638/FM639 (/product/butterfly-valves/fm638fm639/). No prices on the site, so no price-family requirement. Note: the sample used a heading-based variant proxy; after labelling to SPEC 3, D103B (8) and D103B - Cast Iron (5) also have variants, so 5 sampled families are multi-variant.
- (d) Scope decisions applied (below).

## Scope: which products count
- In scope: every `/product/<category>/<slug>/` page in product-sitemap.xml that shows one Crane FS product (Crane-branded figures, actuators, controllers, fittings). All are Crane Fluid Systems products; no third-party/distributed brands are sold on the site.
- Excluded: `/product/%category%/` (sitemap placeholder), `/product/picv/actuators/` (aggregator listing several actuators, found by crawl only), category/news/case-study/company/contact pages.
- Redirect alias: `/product/picv/d995/` → `/product/connected-picv/d995/` (alias of the canonical page). `/product/uncategorized/commpac/` → `/product/commpac/commpac/`.

## Judgement calls (case | decision | proposed SPEC wording)
- Grouped sheets (D102B/D103B/D104B, F611/F626, D901/D902, D921/D923, D931/D933/D934, D171A/D171AEXS) | values taken for this family's figure only; sibling figures with their own page are not variants | SPEC 3 (added).
- D103B part numbers 0JG934xx in the "Dimensions D103B" table | 8 variants with sizes from the merged size column (5 × 1/2", 3 × 3/4"); cast-iron page 5 variants | identifiers in a sheet part-number table are variants (SPEC 3 as written).
- Butterfly heading groups (FA648L..., F646L..., FM638/FM639) | heading figures = variants, size null (each covers the full range); bare-shaft B figures and gearbox G figures (own pages) excluded | SPEC 3 (added).
- AT suffix / D933AT order code / D933.PF BIM title | options, not variants | SPEC 3 (added).
- PN16/PN25 | value = PN number, unit bar | SPEC 6 (added).
- FA648L "ANSI 125" only | 16 bar from the sheet P/T table; page and sheet both say ANSI 125 → agree | SPEC 6 (added).
- BSP Male/Female Parallel ISO-228 (D103B) | `threaded` + end_connections_other | SPEC 6 (added).
- Page "taper threaded"/"parallel threaded" with no standard (D921) | `threaded`; sheet list [BSPT, threaded, NPT] contains it → refines | none (SPEC 6 as written).
- Sheet adds US thread (ANSI B1.20.1, "add suffix AT") | Stage 2 (SPEC 6 Mapping strictness): "ANSI B1.20.1" is not listed NPT wording → end_connections_other, NPT removed (d171aexs, d921, d933); the standard is listed in `standards` | SPEC 6 (as merged).
- material_trim | closure member only (disc/ball/plug); stems not recorded | "trim = disc/ball/plug; stem is not trim".
- material_seals | O-rings / gaskets / stem packing material names; "Asbestos Free" packing (DM11) is not a material → omitted | none.
- Liner on butterfly valves | material_seat | "a resilient liner is the seat".
- Temperature by liner (EPDM -10..120, nitrile -10..82) | one family range -10..120 with `conditions`, no overrides (expressible as a range) | none.
- FM638 body differs by size (EN-GJS-400-15 DN50-300, EN-GJS-450-10 DN350-600) | comma list | SPEC 6 material rule.
- standards | Stage 2 `spec:` commit: every standard the product conforms to or is designed/tested/threaded/drilled/flanged to, "formerly ..." standards excluded; re-labelled in all 15 families | SPEC 6 Standards scope (added).
- certifications | WRAS approval, UL listing, BSI Kitemark | WRAS counts as a certification.
- applications | only explicit service terms: "potable water" from WRAS potable wording; D103B "heating and chilled water systems" from the IOM; malleable brochure cover "IDEAL FOR" list → fire protection (sprinkler), chilled water, hydronic heating, natural gas, compressed air, steam; "Hot Water", "Fuel Transfer", "building services" → applications_other | none.
- Malleable fittings brochure ("Brochure & Datasheets") | doc_type catalog (secondary); page outranks it, brochure-wide statements (standards, Kitemark, cover list) cited for 140/257 | "a range catalog is 'other PDF' even if linked as datasheet".
- 140 reducing bush sizes | sizes_available = the 40 "a x b" pairs; size_range = larger end 1/2 .. 6 (changed in Stage 2, blind was right: numeric and comparable) | HARNESS_ISSUES crane #4.
- 140 / 257 per-size PDF drawings under the CAD heading | documents, other_doc (SPEC 5: outline drawing with no technical-data block; PDF is not a CAD format). Changed in Stage 2 | none.
- 257 / 140 sizes have no identifiers | no variants | SPEC 3.
- D103B page size "½ Inch – ¾ Inch" vs sheet title "DN15/DN20" | same sizes, unit in (sheet tables use inches) → agree | none.
- D103B - Cast Iron | size_range in DN (both state DN20/DN50), sizes_available in inches (Kvs list and table) | none.
- BIMStore links | cad_viewer, gated true (account needed); hosts in crane cad_viewer_hosts, not allowed_hosts | HARNESS_ISSUES crane #1.
- Prices | none on the site (no price lists, no prices on pages; header has a distributor search) → every variant / family_prices `not_published` | none.
- market_flag | `non_na` (UK site, en-GB, UK flange/thread standards) | HARNESS_ISSUES crane #2.
- Document revision_date | datasheet "Valid as of ..." date; WRAS "Certificate issued" date; IOM footer codes like "CFS_BV_1224" read as MM/YY; UL issue date; Kitemark latest issue; no date → null | none.
- Images | all gallery images are product views (incl. valves shown with actuators and the 257 exploded part views); largest rendition = un-resized /app/uploads original; no infographics/scenes in the gallery | none.

## Blind re-label families (random.Random(42).sample(sorted(family_ids), 6))
f621, 257, 140, f634, d171aexs, d103b-cast-iron

## Applying the 2026-10-11 SPEC paragraphs from auto/integration (all 15 families)
- SPEC 4 Image edge cases (candidates = URLs the page references): every image switched from the un-referenced un-resized original (e.g. `..._0423-BF.jpg`) to the largest referenced rendition (`...-BF-scaled.jpg`, 2560 px), in all families whose gallery uses -scaled files (d103b, dm11, d171aexs, f611, f621, f634, fm638-fm639, 140, 257, d921, d901, d933, butterflies). Images that are already referenced originals are unchanged. No image dropped (no callout/collage cases).
- SPEC 5 Classify by content: 140 per-size outline PDFs (8) and 257-2.50.pdf → other_doc documents (were CAD entries); malleable brochure stays catalog (24 pp, many products); FODRV flow brochure (charts) and pn-pressure chart → other_doc (unchanged); stress-corrosion statement → other_doc (bulletin); grouped datasheets (D102B/D103B/D104B, F611/F626, D921/D923, D931/D933/D934, D171A/D171AEXS) stay spec_sheet: ≤ 4 pages, one technical block for one figure family and its siblings, not a per-series product guide. CAD zip formats: PDFs inside zips no longer counted as a format; Creo `.prt.1` → prt (257).
- SPEC 6 Mapping strictness: NPT removed where the source only says "ANSI B1.20.1" (d171aexs, d921, d933 → end_connections_other); butterfly pages that only say "to suit / compatible with ... flanges" are no longer `lug` sources (f611, f621, fa648l…, f646l… → end_connections pdf_only); applications: "Sprinkler Systems" (fire protection) and "Heating Water"/"heating" (hydronic heating) moved to applications_other (140, 257, d103b).
- SPEC 7 family_prices: already applied in the first pass (13 no-variant families carry `not_published` in family_prices).
- Also fixed after re-checking: material values drop non-material qualifiers ("(Epoxy Paint)", "(WRAS Approved)", "Epoxy coated") — f611, f621, fa648l…, f646l…; f634 disc page "Stainless Steel SS316 or CF8M" vs sheet "Stainless Steel 316 ASTM A531 CF8M" → refines; d103b-cast-iron material_body: page title "3 Port Valve – Cast Iron" is a page source → agree; 257 size_unit omitted (257 table header has no unit).

## Blind re-label (6 families)
Blind branch `blind/crane` (crane.blind.json). BEFORE = raw blind vs first-pass commit e78609d; AFTER = blind vs final gold. Script: `python gold/crane.blind.compare.py <gold> gold/crane.blind.json` (lists, sets and value strings compared case-insensitively; documents/images/variants as URL/SKU set overlap).

| row | BEFORE | AFTER |
|---|---|---|
| documents found | 20/29 (69%) | 29/29 (100%) |
| doc_type (common docs) | 20/20 (100%) | 29/29 (100%) |
| images | 1/33 (3%) | 17/17 (100%) |
| variants | 10/10 (100%) | 10/10 (100%) |
| cross_check | 51/62 (82%) | 58/63 (92%) |
| spec: applications | 1/3 | 2/3 |
| spec: certifications | 4/4 | 4/4 |
| spec: end_connections | 4/6 | 5/6 |
| spec: material_body | 5/6 | 6/6 |
| spec: material_seals | 4/4 | 4/4 |
| spec: material_seat | 2/3 | 3/3 |
| spec: material_trim | 4/4 | 4/4 |
| spec: pressure_rating | 6/6 | 6/6 |
| spec: size_range | 5/6 | 6/6 |
| spec: size_unit | 5/6 | 5/5 |
| spec: sizes_available | 6/6 | 6/6 |
| spec: standards | 0/6 | 5/6 |
| spec: temperature_range | 4/4 | 4/4 |
| **family spec fields overall** | **50/64 (78%)** | **60/63 (95%)** |

BEFORE < 80% → cause: SPEC 6 silent on standards scope (gold: conformance only; blind: also thread/flange standards) → `spec:` commit (Standards scope), standards re-labelled in all 15 families, re-measured once (AFTER).

Blind right (gold fixed, source re-checked): images (-scaled referenced renditions, SPEC 4); 140/257 per-size PDFs as other_doc documents; d171aexs end_connections (no NPT); 140 size_range 1/2..6; 257 size_unit omitted; f621 material qualifiers; f634 trim refines; d103b-cast-iron material_body page source; standards scope; applications without hydronic heating.
Gold kept (and why):
- d103b-cast-iron end_connections `threaded` (blind `BSPT`): "BSP Female Parallel ISO-228" is a parallel thread; SPEC 6 (commit 408d7c1) maps parallel pipe threads to `threaded`; the blind file predates that rule.
- 140 applications without `fire protection` (blind derived it from the UL-listed fittings list): SPEC 6 Mapping strictness — no source wording names fire protection ("Sprinkler Systems" is not listed wording) → applications_other.
- d171aexs standards include ANSI B1.20.1: the sheet says "US END CONNECTION: ANSI B1.20.1:1983"; SPEC 6 Standards scope lists standards the product is threaded to.
- 140/257 certifications `pdf_only` and material_body `page_only` (blind `agree`): the page only has download link titles ("UL Certificate", "Kitemark"), which are not spec statements, and the catalog states no material for these figures.
- f621 end_connections `pdf_only` (blind `agree`): the page row "To suit flange connections BS EN 1092-2 ..." describes mating flanges and names no lug term (SPEC 6 Mapping strictness).

## Top 5 ambiguities
1. Standards scope (resolved by spec commit): thread/flange standards are now standards.
2. Grouped sibling sheets (D102B/D103B/D104B etc.): which identifiers are variants, and whether a shared ≤ 4-page sheet is a spec_sheet.
3. Parallel BSP (ISO 228) → `threaded`, not `BSPT` (blind disagreed before the rule existed).
4. Range-wide catalog statements (malleable brochure cover list, Kitemark/BS EN 10242) used as family sources for 140/257.
5. Option codes (AT suffix, D933.PF, bare-shaft B figures) treated as options, not variants.

## Consistency pass (SPEC changes of 2026-10-11)
Standards source spelling (878f517): 8 changes in 7 families; cross_check unchanged everywhere (it already compared spelling-insensitively). The 140/257 catalog spellings "BS EN 10242" (thin space in the PDF) and "BS 143 & 1256" stay as before: a spacing-only difference and an abbreviated second number (recorded as BS 1256).
PN qualifying a flange (aecaeb9): 0 changes. Checked all 15: every pressure_rating comes from a "PRESSURE RATING:" / "Pressure rating" row or a P/T table, never from a flange-drilling PN. Flange-only PNs seen (F621 "BS EN 1092-2 PN10 or PN16", F646L/FM638/F634 "between EN 1092-2 PN16 flanges") were never used as the rating; FM638 keeps the stated "25 Bar".

| family | field | before -> after | paragraph |
|---|---|---|---|
| d933 | standards (alt_values, page) | BS EN 10226-2, ISO 7-1, BS 2779, ISO 228, DVGW, BS EN 331 -> BS EN 10226-2, ISO 7-1, BS 2779, ISO 228, DVGW, BS EN331 | SPEC 6 Standards scope: source spelling (878f517) |
| 140 | standards | BS 21, ISO 7 -> BS21, ISO7 | SPEC 6 Standards scope: source spelling (878f517) |
| f646l-f641l-f656l-f651l-f676l-f671l | standards | BS EN 593, BS EN 1092-2, ANSI B16.1 -> BS EN593, BS EN 1092-2, ANSI B16.1 | SPEC 6 Standards scope: source spelling (878f517) |
| fm638-fm639 | standards | BS EN 558, BS EN 593, BS EN 12266-1, ISO 5211, BS EN 1092-2 -> BS EN 558, BS EN 593, BS EN 12266-1, ISO 5211, BS EN1092-2 | SPEC 6 Standards scope: source spelling (878f517) |
| fm638-fm639 | standards (alt_values, page) | BS EN 1092-2 -> BS EN1092-2 | SPEC 6 Standards scope: source spelling (878f517) |
| d103b-cast-iron | standards | ISO 228 -> ISO-228 | SPEC 6 Standards scope: source spelling (878f517) |
| d103b | standards | ISO 228 -> ISO-228 | SPEC 6 Standards scope: source spelling (878f517) |
| 257 | standards | BS 21, ISO 7 -> BS21, ISO7 | SPEC 6 Standards scope: source spelling (878f517) |
| 140 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| 257 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| d103b | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| d103b-cast-iron | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| d171aexs | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| d901 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| d921 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| d933 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| dm11 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| f611 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| f621 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| f634 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| f646l-f641l-f656l-f651l-f676l-f671l | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| fa648l-fa644l-fa658l-fa654l-fa678l-fa674l | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |
| fm638-fm639 | pressure_rating | unchanged | SPEC 6 PN qualifying a connection (aecaeb9) |

### Consistency pass 2 (SPEC commit cb6232e, 2026-10-11)
SPEC 3 accessory pages (models of another labelled family are not the accessory's variants): 0 changes. None of the 15 families is an accessory; every variant SKU is the family's own figure number or part number (FA648L…, F646L…, FM638/FM639, D103B 0JG934xx, D103B Cast Iron), and no SKU is a variant of another labelled family.
SPEC 6 several PNs in one source → highest PN, class+PN rows recorded by the PN: 0 changes. No pressure_rating source lists more than one PN (d933's PN16 is the page and PN25 the sheet, two sources, kept as conflict). The class+PN rows F611/F621 "PN16 / CLASS 125" and F646L… "PN16 & ANSI Class 125" are already value 16 bar with the class in raw_text. FA648L… "ANSI 125" (class only) is unchanged.

| family | field | before -> after | paragraph |
|---|---|---|---|
| all 15 | variants / family_prices | unchanged | SPEC 3 accessory models (cb6232e) |
| all 15 | pressure_rating | unchanged | SPEC 6 several PNs / class+PN (cb6232e) |
