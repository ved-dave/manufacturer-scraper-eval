# Sioux Chief: ambiguity log

Relabelled 2026-10-10 against SPEC v1.1 (robots override, `refines`, family-vs-variant rule, single-size ranges, installation photos excluded, sibling photos distinct, multilingual `lang`, family-page provenance).

## Spec source breakdown (15 families)

| Family specs come from | Families | Share |
|---|---|---|
| Both page and spec sheet | 13 | 87% |
| Page only | 2 (`304-06`, `230-2906101`) | 13% |
| PDF only | 0 | 0% |

`865-12ECD` moved from page-only to both: its `standards` overrides (sheet-cited) were folded into one family-level list.

Per spec value, family level plus variant overrides:

| | agree | refines | conflict | page_only | pdf_only | total | variant overrides |
|---|---|---|---|---|---|---|---|
| Before (old rules) | 78 | 0 | 28 | 95 | 79 | 280 | 178 |
| After (SPEC v1.1) | 65 | 8 | 15 | 43 | 57 | 188 | 79 |
| After blind v2 fixes | 76 | 8 | 15 | 32 | 57 | 188 | 79 |

The total drops mostly because per-variant overrides of list fields (`end_connections`, `standards`, `certifications`, `applications`) were merged into family-level lists, and single-size `size_range` values were added. Of the 28 old conflicts: 7 became `refines`. 2 (`687-3PH/3PH2` end_connections) are now part of the family-level `end_connections`, which is `refines`. The 5 per-variant `643WG2` certification conflicts became 1 family-level conflict. The other 14 stay `conflict`.

Coverage: 13 of 15 families have a spec-sheet PDF, 4 have BIM (`.rfa`), and 0 have 2D CAD or hosted CAD viewers (CAD/BIM = 4). 15 of 15 have `login_required` prices on every variant (SPEC: this satisfies price coverage).

## Refines (8)

The spec sheet value is a more specific form of the page value (SPEC 6a). Checked by hand; all 7 validator "should be refines" candidates are here, plus `687-3CH` end_connections (see below).

| Family | Where | Field | Displayed (spec sheet) | Spec-sheet source | Page value (alt_values) |
|---|---|---|---|---|---|
| 640wp02 | family | material_body | "polyphenylsulfone (PPSU)" | POWERPEX - F1960 POLY FITTING SYSTEM - SPEC SHEET.PDF p1 "Polyphenylsulfone (PPSU) - NSF Listed" | "plastic" |
| 605qg2 | family | material_body | "no-lead brass (C46500)" | PDQ - BRASS PUSH FITTING SYSTEM - SPEC SHEET.PDF p1 "Fitting Body: No-Lead Brass*" | "brass" |
| 523-31 | family | material_body | "galvanized steel" | 523 SERIES - VINYL-COATED STEEL CLAMPS - SPEC SHEET.PDF p1 "Clamp: galvanized steel" | "steel" |
| 687-3ch | family | material_body | "fire-rated ABS" | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "Access box: Fire-rated ABS" | "ABS" |
| 687-3ch | family | end_connections | ["MIP", "CPVC socket", "MSWT/Press/Push", "push socket (CTS)", "PEX ASTM F1960 expansion", "PEX ASTM F1807 crimp"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "cold-side MIP outlet with ball valve"; 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "3CH = 3/4" CPVC socket" | ["push (CTS)", "MIP"] |
| 687-3ch | family | applications | ["water heater connections", "fire-rated walls"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "valved connection for water heaters is required"; 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "Tested/Certified/Approved for use in fire-rated applications" | ["fire-rated walls"] |
| 861-q2286 | family | material_body | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "Sink: Enamel-coated cast iron" | "cast iron" |
| 120-tm3f | family | certifications | ["ASSE 1070", "NSF/ANSI 61 Annex G"] | 120-TM3F - THERMOSTATIC MIXING VALVE - SPEC SHEET.PDF p1 "Listed to ASSE 1070"; 120-TM3F - THERMOSTATIC MIXING VALVE - SPEC SHEET.PDF p1 "compliant with NSF-61 Annex G" | ["ASSE 1070"] |

## Conflicts (15)

Contradictions stay `conflict`: the page states something the sheet does not (or a different value). The sheet value is displayed and the page value kept in `alt_values`.

| Family | Where | Field | Displayed (spec sheet) | Spec-sheet source | Page value (alt_values) | Why not `refines` |
|---|---|---|---|---|---|---|
| 640wp02 | family | standards | ["ASTM F1960"] | POWERPEX - F1960 POLY FITTING SYSTEM - SPEC SHEET.PDF p1 "DIMENSIONS per ASTM F1960" | ["ASTM F1960", "ASTM F877", "CSA B137.5"] | page lists ASTM F877 and CSA B137.5, which the sheet does not |
| 640wp02 | family | certifications | ["NSF"] | POWERPEX - F1960 POLY FITTING SYSTEM - SPEC SHEET.PDF p1 "Polyphenylsulfone (PPSU) - NSF Listed" | ["NSF/ANSI 14", "NSF/ANSI/CAN 61"] | sheet says only "NSF Listed"; the page lists NSF/ANSI 14 and 61 (sheet is less specific, so it does not refine) |
| 605qg2 | family | certifications | ["NSF/ANSI 61"] | PDQ - BRASS PUSH FITTING SYSTEM - SPEC SHEET.PDF p1 "ASSE 1061 and NSF 61 Standards" | ["NSF/ANSI 14", "NSF/ANSI/CAN 372", "NSF/ANSI/CAN 61"] | page lists NSF/ANSI 14 and 372, which the sheet does not |
| 643wg2 | family | standards | ["ASTM F1960", "ASTM F1970", "ASTM D2846", "CSA B137.6", "ASTM F438"] | POWERPEX - F1960 BRASS FITTING SYSTEM - SPEC SHEET.PDF p1 "DIMENSIONS per ASTM F1960"; 645 SERIES - PVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "conforms to the ASTM F1960 standard" | ["ASTM F1960", "CSA B137.5"] | page lists CSA B137.5, which no sheet lists |
| 643wg2 | family | certifications | ["NSF/ANSI 61", "cUPC", "NSF/ANSI 14"] | POWERPEX - F1960 BRASS FITTING SYSTEM - SPEC SHEET.PDF p1 "compliant with NSF-61 Annex G"; 645 SERIES - PVC X F1960 TRANSITION FITTING - SPEC SHEET.PDF p1 "CERTIFICATIONS cUPC NSF 14 = PEX end" | ["NSF/ANSI/CAN 372"] | 645/645WGC pages list NSF/ANSI/CAN 372; the sheets list cUPC (+ NSF 14) instead |
| 525-02 | family | material_body | "high impact polypropylene" | 525 SERIES - SIMPLESTRAP - SPEC SHEET.PDF p1 "Standard: High impact polypropylene (gray)" | "ABS" | different materials (polypropylene vs ABS) |
| 523-31 | family | applications | ["PEX tube", "copper tube", "gas pipe", "conduit"] | 523 SERIES - VINYL-COATED STEEL CLAMPS - SPEC SHEET.PDF p1 "PEX tube, copper tube, gas pipe or other conduit" | ["hydronic heating"] | page says hydronic heating; the sheet lists tube types, not hydronic heating |
| 687-3ch | family | standards | ["ASME A112.18.1", "ASME A112.4.14", "ASTM E814"] | 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p1 "Meets ASME A112.18.1 and ASME A112.4.14"; 687 SERIES - SERVICEBOX WATER HEATER (F) ACCESS BOX - SPEC SHEET.PDF p2 "ASTM E814" | ["IAPMO PS 54", "ASTM E814", "CAN/ULC S115"] | page lists IAPMO PS 54 and CAN/ULC S115, which the sheet does not |
| 861-q2286 | family | standards | ["ASME A112.6.7"] | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "Designed in accordance with ASME A112.6.7" | ["ASME A112.6.7", "CSA B79.7"] | page lists CSA B79.7, which the sheet does not |
| 861-q2286 | 861-Q2286A | material_trim | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | "A.R.E." (acid-resistant enamel) vs "enamel-coated cast iron": neither contains the other (the sheet does not say acid-resistant), so not a refinement |
| 861-q2286 | 861-Q2386A | material_trim | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | "A.R.E." (acid-resistant enamel) vs "enamel-coated cast iron": neither contains the other (the sheet does not say acid-resistant), so not a refinement |
| 861-q2286 | 861-Q2486A | material_trim | "enamel-coated cast iron" | 861-Q SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | "A.R.E." (acid-resistant enamel) vs "enamel-coated cast iron": neither contains the other (the sheet does not say acid-resistant), so not a refinement |
| 861-q2286 | 861-QF2286A | material_trim | "enamel-coated cast iron" | 861-QF SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | "A.R.E." (acid-resistant enamel) vs "enamel-coated cast iron": neither contains the other (the sheet does not say acid-resistant), so not a refinement |
| 861-q2286 | 861-QF2386A | material_trim | "enamel-coated cast iron" | 861-QF SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | "A.R.E." (acid-resistant enamel) vs "enamel-coated cast iron": neither contains the other (the sheet does not say acid-resistant), so not a refinement |
| 861-q2286 | 861-QF2486A | material_trim | "enamel-coated cast iron" | 861-QF SERIES - 8X8X6 FLOOR SINK - SPEC SHEET.PDF p1 "A = enamel-coated cast iron grate" | "A.R.E." | "A.R.E." (acid-resistant enamel) vs "enamel-coated cast iron": neither contains the other (the sheet does not say acid-resistant), so not a refinement |

## Judgement calls

`case | what I decided | proposed SPEC.md wording`

- **Family boundary** | Family = top-level category + the catalog name on the category card (also the second header line on each SKU page). The site has no family pages. | "On sites with no family page, a family is the manufacturer's own catalog grouping (category card / product-line name), not a related-products table."
- **Catalog name covering several product lines** | 28 card groups split by the product line in the SKU-page header (e.g. "Straight Adapter" → CPVC / F1807 / F1960). Approved at checkpoint. | "If one catalog name spans distinct product lines (different series/standard), split by product line."
- **SKUs listed in several categories** | Assigned to the family named by the SKU page's own breadcrumb. | "A cross-listed SKU belongs to the family its own page's breadcrumb names."
- **Shared accessories** | Kept in their own catalog family, not merged into every table that lists them. `864-WGP` and `865-12ECD` are accessory-only families. | "Accessories sold under their own catalog name are their own family, even if every SKU in it is an accessory."
- **Canonical URL** | Category cards link to `/Products/Details/…`, which redirects to the card's SKU page. So `canonical_url` = the first card's SKU page; other SKU and `/Products/Details/` URLs go in `alternates`. Matches the user's rule. | "If the family has no page and its category card resolves to a SKU page, use that SKU page as the family url."
- **Price behind login** | "Sign in for Pricing" → `availability: login_required`, `amount: null`, quoted from every SKU page. The price-file form was not submitted, and the price file is not listed as a document. The "≥1 family with price" target can't be met. | "`login_required` satisfies price labelling when no amount is shown anonymously."
- **Sizes in large families** | Every variant lists sku, size and page_url. Size sets/ranges are family-level (`sizes_available`, `size_range`); size never needs an override. | (Adopted in SPEC 6.)
- **Variant size on reducing fittings (`643WG2`)** | Used the page header (e.g. `1/2'' F1960 × 3/4'' MSWT`), because the `Connection 1 Size` row contradicts it on some SKUs. | "When page rows contradict the page title on size, use the title and flag it."
- **Page-internal inconsistencies** | `525-2002PK2` header says 18" but its Length row says 20 IN. `861-Q2286S` header says 2" but its row says 3 IN. On `865-6PC/6RS/8PC/8RS` the Width rows (8/16 IN) contradict the headers (6"/8" outs). Header used in each case, and the cases are listed here. | "Inconsistencies within a page are logged; the title value wins."
- **`refines` vs `conflict` (SPEC 6a)** | Every old conflict was re-checked by hand. Refines: a narrower material (PPSU, no-lead brass, galvanized steel, fire-rated ABS, enamel-coated cast iron) or a sheet list that contains every page item. Kept as conflict: lists where the page names an item the sheet lacks, different materials, and "A.R.E." vs "enamel-coated cast iron" (neither contains the other). `640WP02` certifications: sheet "NSF Listed" is *less* specific than the page's NSF/ANSI 14 + 61, so conflict. | Matches SPEC 6a.
- **Variant overrides (SPEC 6)** | List-kind fields (`end_connections`, `standards`, `certifications`, `applications`) that differed per variant are merged into one family-level list (union of values and sources), so they no longer need overrides: `643WG2` (4 fields), `687-3CH` and `230-2906101` (end_connections), `865-12ECD` (standards). Overrides remain only for text/numeric fields that differ by variant and can't be a list or range: `643WG2` material_seals (EPDM on the PVC/CPVC transitions) and temperature_range (180°F max on 645WGC); `525-02G` material_body; `821-200ANQ` ABS vs PVC body; `861-Q2286` grate material (A/N/S); `865-12ECD` body/grate materials; `230-2906101` hard vs soft washers. Downside: a family-level certification list now includes cUPC (645 transitions) next to NSF/ANSI 61 (brass adapters), so it no longer says which variant holds which listing. | "A family list is the union over variants; it does not claim every variant has every item."
- **`687-3CH` end_connections** | The union of the page's inlet types plus MIP outlet, with the sheet's "MSWT/Press/Push" for the 3PH inlet. The page says "Push CTS" for 3PH. The sheet value contains push and more, and the page's items are all covered, so the family value is `refines`. The validator agrees (no warning). | —
- **Series-level spec sheets (provenance)** | The PDQ sheet (`605QG2`) and the 645/645WGC transition sheets (`643WG2`) don't contain the family code. Each is linked from the family's own SKU pages, which SPEC 6b now accepts; the validator no longer warns. | (Adopted in SPEC 6b.)
- **Sheet linked from variants it doesn't describe** | The `687` sheet is titled "FLOW-THROUGH DESIGN" but is linked from all 10 SKUs, including the Termination models. The `861` trap-primer-adapter sheet is linked from the floor-sink pages. Both are kept as documents. The adapter sheet isn't used for family specs. | "Record every linked PDF; use only sheets describing the product for spec values."
- **Language (SPEC 2)** | French-only `_FRENCH` brochures stay excluded. Three trilingual EN/FR/ES instruction sheets are now **excluded**, not relabelled `en+fr+es`: `525 SERIES - SIMPLESTRAP STUB OUT BRACKET - INSTRUCTION SHEET`, `687 SERIES - SERVICEBOX - INSTALLATION GUIDE` and `PREFORMED COPPER FOR CPVC - INSTRUCTION SHEET` (`630-C2412`). They carry the same text in all three languages, so English is only about 22–28% of the extracted text (line-level language count), below the ≥ 50% threshold. No spec value cited them. No other document is multilingual, so no `en+…` value is used. | "A document with parallel full translations is not English-primary."
- **PDF text extraction** | pypdf missed most text on image-heavy sheets (`687`, `630-C`, `886`). All PDF evidence text was re-extracted with PyMuPDF. No OCR was used and no values were inferred. | "Evidence text may come from any extractor; quotes must appear in the saved text."
- **Revision date** | Taken from the footer `www.siouxchief.com M-YY` (e.g. `6-20` → `2020-06`). Null when absent. | "A footer month-year code is the revision date."
- **Combined catalogs / brochures** | Product-line brochures and "Trench Drain Overview" PDFs → `brochure`. Tech bulletins and hydraulic/load guides → `other_doc`. Installation guides/instruction sheets → `iom_manual`. | "Line brochures are `brochure`; per-series data sheets are `spec_sheet`."
- **Images (SPEC 4)** | Only product photos (`ProductImages/<sku>.JPG`, ≥ 300 px) are kept. The 28 installation-tab photos (`RoughInPhotos/`, `FinishPhotos/`, `image_type: other`) are removed. Dedup is now by file: a sibling URL serving a byte-identical file is the same image; a different file for a different SKU is kept even at small phash distance. That restores 19 sibling-SKU photos the old phash ≤ 6 rule had dropped (`865-12ECD` 8, `861-Q2286` 4, `687-3CH` 3, `230-2906101` 2, `643WG2` 1, `821-200ANQ` 1). 8 pairs among them have phash ≤ 2 and draw validator warnings: `861-Q2286N`/`-S` (nickel-bronze vs stainless grate) and `865-M12PCBEA`/`FA`, `865-M6CBDA`/`F1A`/`FA`, `865-M8CBDA`/`F1A`/`FA` (different catch-basin SKUs). They are different SKUs and different files, so they are kept. | (Adopted in SPEC 4.)
- **Multi-valued page rows** | Some spec tabs repeat a row with different values (e.g. `230-*` "Connection 1 Type" lists FIP-Swvl. and Slip Joint; `525-*` "Product Type" lists CPVC/Copper/PEX). All values are kept for scored fields. `525` Product Type is not a scored field (it names the tube types the bracket fits) and is left out. | "A repeated spec row with different values is a list; keep every value."
- **Temperature range for a mixing valve (`120-TM3F`)** | `temperature_range` = inlet water range 39–180°F (cold inlet 39–85°F, hot inlet 120–180°F), because SPEC lists it under ratings. The selectable outlet range 80–120°F is kept in `additional_specs`. The first pass had used 80–120°F; changed after the blind re-label. | "temperature_range is the rated fluid temperature, not an adjustment range."
- **Regulatory compliance vs certification** | "California No Lead Plumbing Law" compliance is a law, not a certification, so it goes in `additional_specs`. "NSF-61 Annex G" compliance is recorded under certifications. | "Laws (e.g. California AB1953) are not certifications."
- **NSF/ANSI 14 as standard or certification (`230`)** | Kept as a certification and ASTM F409 as a standard. The blind re-labeller put both under standards. | "NSF/ANSI listings go in certifications; ASTM/ASME/CSA test standards in standards."
- **Printed revision dates** | Revision dates are taken from the "www.siouxchief.com MM-YY" footer. Three documents print the date in another form ("A. 11/14", "– 7/17", "#LT1-TMV 2-23"), which the first pass missed and the re-label caught. They were added by hand. | "Any printed revision mark counts; normalise to YYYY-MM."
- **BIM** | `.rfa` files → `cad_type: bim`, not gated, with `variant_skus` = the SKU pages linking them. No DWG/STEP and no hosted CAD viewers were found. | (Matches SPEC.)
- **robots.txt `/downloads/` (SPEC 1a)** | Re-checked all 179 saved SKU pages for links under `/downloads/`: there are none (every document link points to `cdn.siouxchief.com`). 0 documents added. | —
- **Blind re-label draw** | I first picked the three re-label families with an ad-hoc `Random(2026)` after labelling (`605QG2`, `687-3CH`, `821-200ANQ`). That seed wasn't fixed in advance, so I discarded that draw and used `Random(42)` over the sorted family IDs instead (`821-200ANQ`, `230-2906101`, `120-TM3F`). | "Fix the re-label seed before labelling."
- **Coverage swaps** | `904-25101` → `643WG2` (largest category). `861-52IN` → `861-Q2286`: the largest category had no other CAD family, so I fell back to the next-largest category (my own rule). | "If the largest category has no qualifying family, swap within the next-largest."
- **Stale sitemap** | 28 SKU URLs and 1 category page in the sitemap return 404. They are excluded from family_index. | "404 sitemap URLs are excluded and counted."
- **Single fixed size (SPEC 6)** | Families with one size now get `size_range` min = max, with the same quotes as `sizes_available`: `687-3CH`, `886-ER`, `821-200ANQ`, `864-WGP`, `230-2906101`, `120-TM3F`. `304-06` states no size, so it has neither. | (Adopted in SPEC 6.)

## Blind re-label v1 (3 families, old rules, 2026-10-09)

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

**Where the first pass was kept (at the time):** the phash ≤ 6 image dedup, NSF/ANSI 14 as a certification, and no `size_range` for single-size families. Under SPEC v1.1 the installation photos above were removed again, the 3 dropped sibling photos restored, and single-size ranges added. `230` `material_body` "plastic" and `applications` "Waste - Center Outlet" left out: the first comes from the category name "Plastic Tubular", the second is a product type, and neither is a spec row.


## Blind re-label v2 (6 families, SPEC v1.1, 2026-10-10)

Separate session ([01438a45](https://outpostai.devinenterprise.com/sessions/01438a4541944e989ce3659b3c5c6aa2)), working from `main` and the live site only, with no access to the gold branch, PR #1 or `sioux-chief.*` files. Families: the 3 from v1 (`821-200ANQ`, `230-2906101`, `120-TM3F`) plus 3 drawn with `Random(43).sample(sorted(ids), 3)` over the other 12 sampled family IDs: `304-06`, `630-C2412`, `525-02`. Agreement was measured against the gold **before** any v2 fix. Spec fields count as matching when the harness `compare_spec` score is 1.0 or the values are identical.

| Row | v1: 3 families, old rules | v2: 6 families, SPEC v1.1 | v2 after fixes |
|---|---|---|---|
| Variants (SKU set) | 20/20 | 37/37 | 37/37 |
| Documents (URL set) | 7/7 | 10/10 | 10/10 |
| Doc type / lang / sha256 | 7/7 each | 10/10 each | 10/10 each |
| Doc revision_date | 4/7 | 9/10 | 10/10 |
| CAD/BIM | 1/1 | 1/1 | 1/1 |
| Images | 13/17 (76%) | 25/25 (100%) | 25/25 |
| Family spec fields | 17/29 (59%) | 31/45 (69%) | 31/45 |
| Variant overrides | 10/31 | 0/20 | 0/20 |
| cross_check (field in both) | 15/17 | 35/42 (83%) | 39/42 (93%) |

**Gold corrections that came from blind v2 (the re-label was right):**
1. **`size_unit` was `page_only` in 11 families, now `agree`.** The spec sheet also states the size in inches. Fixed for `640WP02`, `605QG2`, `643WG2`, `525-02`, `687-3CH`, `630-C2412`, `821-200ANQ`, `864-WGP`, `861-Q2286`, `865-12ECD` and `120-TM3F`, each with a verbatim sheet quote (e.g. `Drain body shall have a 2" Sch. 40 hub connection`). The blind pass flagged 4 of these; I applied the same check to all 15. `523-31` and `886-ER` stay `page_only`: their sheets show only dimensions, not the product size.
2. **`630-C2412` end_connections:** added `closed`. The page says `Connection 2 Type Closed` and the sheet says `Type L copper tubing with a spun-closed end`.
3. **`525-02` brochure revision_date:** `2021-09`, from the footer date code `09-2021`.

**Where gold was kept (the blind value is not better):**
- **Variant overrides (0/20).** The blind pass put per-variant materials into family-level lists, e.g. `821-200ANQ` material_body `["PVC","ABS"]`, and recorded no washer type for `230-2906101`. Gold keeps overrides for these text fields: `material_body` / `material_seals` are single-valued text kinds in the harness, so a list loses which variant is which. The `230` washer quotes (`Washer Type Hard` / `Washer Type Soft`) are verified in the evidence. Logged in HARNESS_ISSUES.
- **`525-02` material_body.** Both passes say `conflict`: the sheet gives polypropylene for the standard strap and ABS for the glueable one, but every SKU page says ABS. Gold displays the sheet value, with an ABS override on `525-02G`.
- **`525-02` size_unit `CTS` vs `in`.** SPEC 6 lists unit systems "NPS / DN / in", and CTS is not one of them, so gold keeps `in`. Logged in HARNESS_ISSUES.
- **`525-02` temperature_range min 0.** `Impact resistant to 0ºF` is an impact rating, not an operating minimum, so gold keeps min null and max 140.
- **`525-02` applications / certifications.** The blind pass cited the page title "Cost-Effective Stub Out Bracket" for applications and `IAPMO PS - 42` (a product standard, already in `standards`) for certifications. Gold keeps the sheet-only `residential` / `commercial` and `IAPMO`, both `pdf_only`.
- **`120-TM3F` certifications / material_trim.** The blind pass missed `compliant with NSF-61 Annex G` and `Stainless steel springs`. Both are verified in the evidence, so `refines` / `pdf_only` stay.
- **Wording only, kept:** `821-200ANQ` / `120-TM3F` applications and end_connections (`2" Sch. 40 hub` vs `Sch. 40 hub`, `3/8" compression` vs `compression`), and `630-C2412` "Type L copper tube" vs "Type L copper".
