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
- Sheet adds US thread (ANSI B1.20.1, "add suffix AT") | NPT included in the sheet list (offered option) → refines vs page | end_connections lists every connection the sheet offers.
- material_trim | closure member only (disc/ball/plug); stems not recorded | "trim = disc/ball/plug; stem is not trim".
- material_seals | O-rings / gaskets / stem packing material names; "Asbestos Free" packing (DM11) is not a material → omitted | none.
- Liner on butterfly valves | material_seat | "a resilient liner is the seat".
- Temperature by liner (EPDM -10..120, nitrile -10..82) | one family range -10..120 with `conditions`, no overrides (expressible as a range) | none.
- FM638 body differs by size (EN-GJS-400-15 DN50-300, EN-GJS-450-10 DN350-600) | comma list | SPEC 6 material rule.
- standards | design/conformance standards only (BS EN 593, BS 7350, MSS SP 67...); thread and flange standards stay in end_connections raw_text/other | "standards = what the product is designed/tested to; connection standards are end-connection detail".
- certifications | WRAS approval, UL listing, BSI Kitemark | WRAS counts as a certification.
- applications | only explicit service terms: "potable water" from WRAS potable wording; D103B "heating and chilled water systems" from the IOM; malleable brochure cover "IDEAL FOR" list → fire protection (sprinkler), chilled water, hydronic heating, natural gas, compressed air, steam; "Hot Water", "Fuel Transfer", "building services" → applications_other | none.
- Malleable fittings brochure ("Brochure & Datasheets") | doc_type catalog (secondary); page outranks it, brochure-wide statements (standards, Kitemark, cover list) cited for 140/257 | "a range catalog is 'other PDF' even if linked as datasheet".
- 140 reducing bush sizes | sizes_available = the 40 "a x b" pairs; size_range min/max = first/last pair | HARNESS_ISSUES crane #4.
- 140 per-size PDF drawings under the CAD heading | cad_file, formats [pdf] (not documents) | none.
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
