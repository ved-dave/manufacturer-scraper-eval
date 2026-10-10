# Sioux Chief: ambiguity log

## Spec source breakdown (15 families)

| Family specs come from | Families | Share |
|---|---|---|
| Both page and spec sheet | 12 | 80% |
| Page only | 3 (`304-06`, `230-2906101`, `865-12ECD`) | 20% |
| PDF only | 0 | 0% |

Per spec value (280 total, family-level plus variant overrides): agree 78, conflict 28 (106 on both), page_only 95, pdf_only 79. (Before the blind re-label corrections it was 266: agree 79, conflict 27, page_only 82, pdf_only 78.)

Coverage: 13 of 15 families have a spec-sheet PDF, 4 have BIM (`.rfa`), 0 have 2D CAD files or hosted CAD viewers. SPEC counts `bim` as a `cad_type`, so CAD/BIM coverage is 4 families. 15 of 15 have prices recorded as `login_required` and none show an amount.

## Page vs spec-sheet conflicts (28)

The spec-sheet value is displayed and the page value is kept in `alt_values`.

| Family | Where | Field | Displayed (spec sheet) | Spec-sheet source | Page value | Page source | PDF revision |
|---|---|---|---|---|---|---|---|
| 640wp02 | family | material_body | "polyphenylsulfone (PPSU)" | POWERPEX - F1960 POLY FITTING SYSTEM - SPEC SHEET.PDF p1 "Polyphenylsulfone (PPSU) - NSF Listed" | "plastic" | 640WP02 "Material Plastic" | 2021-02 |
| 640wp02 | family | standards | ["ASTM F1960"] | POWERPEX - F1960 POLY FITTING SYSTEM - SPEC SHEET.PDF p1 "DIMENSIONS per ASTM F1960" | ["ASTM F1960", "ASTM F877", "CSA B137.5"] | 640WP02 "ASTM - F1960, CSA - B137.5, ASTM - F877, NSF/ANSI - 14, NSF/ANSI/CAN - 61" | 2021-02 |
| 640wp02 | family | certifications | ["NSF"] | POWERPEX - F1960 POLY FITTING SYSTEM - SPEC SHEET.PDF p1 "Polyphenylsulfone (PPSU) - NSF Listed" | ["NSF/ANSI 14", "NSF/ANSI/CAN 61"] | 640WP02 "ASTM - F1960, CSA - B137.5, ASTM - F877, NSF/ANSI - 14, NSF/ANSI/CAN - 61" | 2021-02 |
| 605qg2 | family | material_body | "no-lead brass (C46500)" | PDQ - BRASS PUSH FITTING SYSTEM - SPEC SHEET.PDF p1 "Fitting Body: No-Lead Brass*" | "brass" | 605QG2 "Material Brass" | 2020-11 |
| 605qg2 | family | certifications | ["NSF/ANSI 61"] | PDQ - BRASS PUSH FITTING SYSTEM - SPEC SHEET.PDF p1 "ASSE 1061 and NSF 61 Standards" | ["NSF/ANSI 14", "NSF/ANSI/CAN 372", "NSF/ANSI/CAN 61"] | 605QG2 "ASSE - 1061, NSF/ANSI - 14, NSF/ANSI/CAN - 372, NSF/ANSI/CAN - 61" | 2020-11 |
| 643wg2 | family | standards | ["ASTM F1960"] | POWERPEX - F1960 BRASS FITTING SYSTEM - SPEC SHEET.PDF p1 "DIMENSIONS per ASTM F1960" | ["ASTM F1960", "CSA B137.5"] | 643WG2 "ASTM - F1960, CSA - B137.5" | 2020-06 |
| 643wg2 | 645WG3P | certifications | ["cUPC", "NSF/ANSI 14"] | 645 SERIES - PVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "CERTIFICATIONS cUPC NSF 14 = PEX end" | ["NSF/ANSI/CAN 372"] | 645WG3P "NSF/ANSI/CAN - 372" | 2016-02 |
| 643wg2 | 645WG4P | certifications | ["cUPC", "NSF/ANSI 14"] | 645 SERIES - PVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "CERTIFICATIONS cUPC NSF 14 = PEX end" | ["NSF/ANSI/CAN 372"] | 645WG4P "NSF/ANSI/CAN - 372" | 2016-02 |
| 643wg2 | 645WGC2 | certifications | ["cUPC"] | 645WGC SERIES - CPVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "CERTIFICATIONS cUPC" | ["NSF/ANSI/CAN 372"] | 645WGC2 "ASTM - D2846, CSA - B137.6, NSF/ANSI/CAN - 372" | 2021-10 |
| 643wg2 | 645WGC3 | certifications | ["cUPC"] | 645WGC SERIES - CPVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "CERTIFICATIONS cUPC" | ["NSF/ANSI/CAN 372"] | 645WGC3 "ASTM - D2846, CSA - B137.6, NSF/ANSI/CAN - 372" | 2021-10 |
| 643wg2 | 645WGC4 | certifications | ["cUPC"] | 645WGC SERIES - CPVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "CERTIFICATIONS cUPC" | ["NSF/ANSI/CAN 372"] | 645WGC4 "ASTM - D2846, CSA - B137.6, NSF/ANSI/CAN - 372" | 2021-10 |
| 525-02 | family | material_body | "high impact polypropylene" | 525 SERIES - SIMPLESTRAP - SPEC SHEET.PDF p1 "Standard: High impact polypropylene (gray)" | "ABS" | 525-02 "Material ABS" | 2017-11 |
| 523-31 | family | material_body | "galvanized steel" | 523 SERIES - VINYL-COATED STEEL CLAMPS - SPEC SHEET.PDF p1 "Clamp: galvanized steel" | "steel" | 523-31 "Material Steel" | 2018-09 |
| 523-31 | family | applications | ["PEX tube", "copper tube", "gas pipe", "conduit"] | 523 SERIES - VINYL-COATED STEEL CLAMPS - SPEC SHEET.PDF p1 "PEX tube, copper tube, gas pipe or other conduit" | ["hydronic heating"] | 523-31 "Perfect for hydronic heating." | 2018-09 |
| 687-3ch | family | material_body | "fire-rated ABS" | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "Access box: Fire-rated ABS" | "ABS" | 687-3CH "Durable ABS boxes with quarter-turn ball valves." | 2023-07 |
| 687-3ch | family | standards | ["ASME A112.18.1", "ASME A112.4.14", "ASTM E814"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "Meets ASME A112.18.1 and ASME A112.4.14" | ["IAPMO PS 54", "ASTM E814", "CAN/ULC S115"] | 687-3CH "IAPMO PS - 54, ASTM - E814, CAN/ULC - S115" | 2023-07 |
| 687-3ch | family | applications | ["water heater connections", "fire-rated walls"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "valved connection for water heaters is required" | ["fire-rated walls"] | 687-3CH "All models can be used in fire-rated walls." | 2023-07 |
| 687-3ch | 687-3PH | end_connections | ["MSWT/Press/Push", "MIP"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "3PH = 3/4" MSWT/Press/Push" | ["push (CTS)", "MIP"] | 687-3PH "Connection 1 Type Push CTS" | 2023-07 |
| 687-3ch | 687-3PH2 | end_connections | ["MSWT/Press/Push", "MIP"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "3PH = 3/4" MSWT/Press/Push" | ["push (CTS)", "MIP"] | 687-3PH2 "Connection 1 Type Push CTS" | 2023-07 |
| 861-q2286 | family | material_body | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "Sink: Enamel-coated cast iron" | "cast iron" | 861-Q2286 "Sink Body Material Cast Iron" | 2025-02 |
| 861-q2286 | family | standards | ["ASME A112.6.7"] | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "Designed in accordance with ASME A112.6.7" | ["ASME A112.6.7", "CSA B79.7"] | 861-Q2286 "ASME - A112.6.7, CSA - B79.7" | 2025-02 |
| 861-q2286 | 861-Q2286A | material_trim | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | 861-Q2286A "Grate Material A.R.E." | 2025-02 |
| 861-q2286 | 861-Q2386A | material_trim | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | 861-Q2386A "Grate Material A.R.E." | 2025-02 |
| 861-q2286 | 861-Q2486A | material_trim | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | 861-Q2486A "Grate Material A.R.E." | 2025-02 |
| 861-q2286 | 861-QF2286A | material_trim | "enamel-coated cast iron" | 861-QF SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | 861-QF2286A "Grate Material A.R.E." | 2025-02 |
| 861-q2286 | 861-QF2386A | material_trim | "enamel-coated cast iron" | 861-QF SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | 861-QF2386A "Grate Material A.R.E." | 2025-02 |
| 861-q2286 | 861-QF2486A | material_trim | "enamel-coated cast iron" | 861-QF SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | 861-QF2486A "Grate Material A.R.E." | 2025-02 |
| 120-tm3f | family | certifications | ["ASSE 1070", "NSF/ANSI 61 Annex G"] | 120-TM3F - THERMOSTATIC MIXING VALVE - SPEC SHEET.PDF p1 "Listed to ASSE 1070" + "compliant with NSF-61 Annex G" | ["ASSE 1070"] | 120-TM3F "Certification ASSE 1070" | 2024-04 |

## Judgement calls

`case | what I decided | proposed SPEC.md wording`

- **Family boundary** | Family = top-level category + the catalog name on the category card (also the second header line on each SKU page). The site has no family pages. | "On sites with no family page, a family is the manufacturer's own catalog grouping (category card / product-line name), not a related-products table."
- **Catalog name covering several product lines** | 28 card groups split by the product line in the SKU-page header (e.g. "Straight Adapter" → CPVC / F1807 / F1960). Approved at checkpoint. | "If one catalog name spans distinct product lines (different series/standard), split by product line."
- **SKUs listed in several categories** | Assigned to the family named by the SKU page's own breadcrumb. | "A cross-listed SKU belongs to the family its own page's breadcrumb names."
- **Shared accessories** | Kept in their own catalog family, not merged into every table that lists them. `864-WGP` and `865-12ECD` are accessory-only families. | "Accessories sold under their own catalog name are their own family, even if every SKU in it is an accessory."
- **Canonical URL** | Category cards link to `/Products/Details/…`, which redirects to the card's SKU page. So `canonical_url` = the first card's SKU page; other SKU and `/Products/Details/` URLs go in `alternates`. Matches the user's rule. | "If the family has no page and its category card resolves to a SKU page, use that SKU page as the family url."
- **Price behind login** | "Sign in for Pricing" → `availability: login_required`, `amount: null`, quoted from every SKU page. The price-file form was not submitted, and the price file is not listed as a document. The "≥1 family with price" target can't be met. | "`login_required` satisfies price labelling when no amount is shown anonymously."
- **Sizes in large families** | Every variant lists sku, size and page_url. Size sets/ranges are family-level (`sizes_available`, `size_range`), and `spec_overrides` are used only for non-size differences (connection, material, grate). User clarification. | "Variants carry size; family specs carry the size set/range; overrides only for non-size fields."
- **Variant size on reducing fittings (`643WG2`)** | Used the page header (e.g. `1/2'' F1960 × 3/4'' MSWT`), because the `Connection 1 Size` row contradicts it on some SKUs. | "When page rows contradict the page title on size, use the title and flag it."
- **Page-internal inconsistencies** | `525-2002PK2` header says 18" but its Length row says 20 IN. `861-Q2286S` header says 2" but its row says 3 IN. On `865-6PC/6RS/8PC/8RS` the Width rows (8/16 IN) contradict the headers (6"/8" outs). Header used in each case, and the cases are listed here. | "Inconsistencies within a page are logged; the title value wins."
- **Literal vs. semantic conflict** | A broader page value vs a more specific sheet value (Plastic vs PPSU, Brass vs No-Lead Brass, Steel vs galvanized steel, Cast Iron vs enamel-coated cast iron, A.R.E. vs enamel-coated cast iron) was labelled `conflict`, with the sheet value displayed. Standards/cert lists that differ as sets are also `conflict`. | "Any difference in value or set membership is `conflict`, even if one value refines the other."
- **Series-level spec sheets (provenance)** | The PDQ sheet (for `605QG`) and the 645/645WGC transition sheets (for `643WG2`) don't contain the family code, so the validator warns. They are linked from the family's own SKU pages, and their titles/contents name the product line. Kept. | "A PDF linked from the family's own SKU page passes provenance even if it names only the series/product line."
- **Sheet linked from variants it doesn't describe** | The `687` sheet is titled "FLOW-THROUGH DESIGN" but is linked from all 10 SKUs, including the Termination models. The `861` trap-primer-adapter sheet is linked from the floor-sink pages. Both are kept as documents. The adapter sheet isn't used for family specs. | "Record every linked PDF; use only sheets describing the product for spec values."
- **Language** | French-only `_FRENCH` brochures are marked excluded (the validator requires English-primary). The trilingual EN/FR/ES `687` installation guide is kept as `en`. | "Multilingual documents whose first/primary language is English count as `en`."
- **PDF text extraction** | pypdf missed most text on image-heavy sheets (`687`, `630-C`, `886`). All PDF evidence text was re-extracted with PyMuPDF. No OCR was used and no values were inferred. | "Evidence text may come from any extractor; quotes must appear in the saved text."
- **Revision date** | Taken from the footer `www.siouxchief.com M-YY` (e.g. `6-20` → `2020-06`). Null when absent. | "A footer month-year code is the revision date."
- **Combined catalogs / brochures** | Product-line brochures and "Trench Drain Overview" PDFs → `brochure`. Tech bulletins and hydraulic/load guides → `other_doc`. Installation guides/instruction sheets → `iom_manual`. | "Line brochures are `brochure`; per-series data sheets are `spec_sheet`."
- **Images** | Full-size product photos (`ProductImages/<sku>.JPG`) are `product_photo`. Photos in the SKU pages' "Rough-in Installation" / "Finish Installation" tabs (`RoughInPhotos/`, `FinishPhotos/`) are `other`. The first pass missed these; the blind re-label found one, and all 32 were then collected, giving 28 after the 300 px and duplicate rules. `_sm` thumbnails count as duplicates. Images within phash distance 6 of an already-kept image are dropped, because the validator rejects them (`PHASH_DUP_DISTANCE = 6`). That drops three distinct SKU photos (`821-200PNR`, `230-291616101`, `230-301621101`) whose phash is within 6 of a sibling SKU's photo. | "Installation/application photos on the product page are images (`other`). Duplicates are byte-identical files or renditions of the same photo; distinct photos of different SKUs are kept even when their phash distance is small."
- **Multi-valued page rows** | Some spec tabs repeat a row with different values (e.g. `230-*` "Connection 1 Type" lists FIP-Swvl. and Slip Joint; `525-*` "Product Type" lists CPVC/Copper/PEX). All values are kept for scored fields. `525` Product Type is not a scored field (it names the tube types the bracket fits) and is left out. | "A repeated spec row with different values is a list; keep every value."
- **Temperature range for a mixing valve (`120-TM3F`)** | `temperature_range` = inlet water range 39–180°F (cold inlet 39–85°F, hot inlet 120–180°F), because SPEC lists it under ratings. The selectable outlet range 80–120°F is kept in `additional_specs`. The first pass had used 80–120°F; changed after the blind re-label. | "temperature_range is the rated fluid temperature, not an adjustment range."
- **Regulatory compliance vs certification** | "California No Lead Plumbing Law" compliance is a law, not a certification, so it goes in `additional_specs`. "NSF-61 Annex G" compliance is recorded under certifications. | "Laws (e.g. California AB1953) are not certifications."
- **NSF/ANSI 14 as standard or certification (`230`)** | Kept as a certification and ASTM F409 as a standard. The blind re-labeller put both under standards. | "NSF/ANSI listings go in certifications; ASTM/ASME/CSA test standards in standards."
- **Printed revision dates** | Revision dates are taken from the "www.siouxchief.com MM-YY" footer. Three documents print the date in another form ("A. 11/14", "– 7/17", "#LT1-TMV 2-23"), which the first pass missed and the re-label caught. They were added by hand. | "Any printed revision mark counts; normalise to YYYY-MM."
- **BIM** | `.rfa` files → `cad_type: bim`, not gated, with `variant_skus` = the SKU pages linking them. No DWG/STEP and no hosted CAD viewers were found. | (Matches SPEC.)
- **robots.txt `/downloads/`** | No sampled page links under `/downloads/`, so nothing was skipped or flagged. The fetcher refused that path. | —
- **Blind re-label draw** | I first picked the three re-label families with an ad-hoc `Random(2026)` after labelling (`605QG2`, `687-3CH`, `821-200ANQ`). That seed wasn't fixed in advance, so I discarded that draw and used `Random(42)` over the sorted family IDs instead (`821-200ANQ`, `230-2906101`, `120-TM3F`). | "Fix the re-label seed before labelling."
- **Coverage swaps** | `904-25101` → `643WG2` (largest category). `861-52IN` → `861-Q2286`: the largest category had no other CAD family, so I fell back to the next-largest category (my own rule). | "If the largest category has no qualifying family, swap within the next-largest."
- **Stale sitemap** | 28 SKU URLs and 1 category page in the sitemap return 404. They are excluded from family_index. | "404 sitemap URLs are excluded and counted."
- **Single fixed size** | Single-size families (`886-ER`, `120-TM3F`, `687-3CH`) get `sizes_available` with one value and no `size_range`. | "Use size_range only when sizes span more than one value."

## Blind re-label (3 families)

**Method.** The families were drawn with `random.Random(42).sample(sorted(family_ids), 3)`: `821-200ANQ`, `230-2906101`, `120-TM3F`. A separate Devin session re-labelled them from scratch. It worked from `main` only, could not see this branch or PR, used its own crawl (1 req/s, same User-Agent policy), and PyMuPDF for PDF text. It verified every quote against its own saved text. The table compares its output with the first pass **before** any corrections.

| Dimension | Agreement | Notes |
|---|---|---|
| Variants (SKUs) | 20 / 20 (100%) | Same SKU sets. Both left out related items and repair kits. |
| Documents (URL set) | 7 / 7 (100%) | Same English documents. Both excluded the same 2 French brochures. |
| Document type / language / SHA-256 | 7 / 7 (100%) | |
| Document revision date | 4 / 7 (57%) | The first pass missed three non-footer date marks. Fixed. |
| CAD/BIM | 1 / 1 (100%) | `120TM3F.RFA`, `bim`, not gated. |
| Images (distinct files) | 13 / 17 (76%) | All 13 first-pass images are in the re-label. 3 of the 4 re-label-only images are distinct SKU photos the first pass dropped by the phash ≤ 6 rule (kept dropped: the validator rejects them). The 4th is the `821` finish-installation photo, which the first pass missed (fixed, see below). |
| Spec fields, family level (value) | 17 / 29 (59%); 17 / 26 (65%) excluding `size_range` | `size_range` differs by convention only: the first pass gives single-size families no range. |
| Spec `cross_check` label (on agreeing fields) | 15 / 17 | `size_unit`: `page_only` in the first pass vs `agree` in the re-label. |
| Variant spec overrides | 10 / 31 (32%) | `821` 7/7. `230` 3/24 (`end_connections` and washers, see below). |

**Per family (family-level spec fields):** `821-200ANQ` 7/8, `230-2906101` 2/9, `120-TM3F` 8/12.

**Where the re-label was right, and gold was corrected:**
- `230-2906101` `end_connections`: the first pass's page parser kept only one value of the repeated "Connection 1 Type" row, so FIP swivel and the 230-31xx "Direct Connect" were lost. Now the family value is slip joint + FIP swivel + direct connect, with per-variant overrides.
- `230-2906101` `material_seals`: "Washer Type Hard/Soft" was missing. It's now per-variant poly (hard) or soft washers.
- `120-TM3F` `temperature_range` (now inlet 39–180°F), `material_trim` (stainless steel springs and debris screens, added) and `certifications` (+ NSF/ANSI 61 Annex G, now a page/PDF conflict).
- Revision dates for 3 documents.
- Installation-tab photos (`RoughInPhotos/`, `FinishPhotos/`): the first pass never collected them. After this finding they were collected for all 15 families: 28 images (`image_type: other`) added across `640WP02`, `643WG2`, `525-02`, `523-31`, `687-3CH`, `630-C2412` and `821-200ANQ`.

**Where the first pass was kept:** the phash ≤ 6 image dedup (validator-enforced; logged in HARNESS_ISSUES). NSF/ANSI 14 as a certification. No `size_range` for single-size families. `230` `material_body` "plastic" and `applications` "Waste - Center Outlet" left out: the first comes from the category name "Plastic Tubular", the second is a product type, and neither is a spec row.
