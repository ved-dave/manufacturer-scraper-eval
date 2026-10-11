# cimberio — ambiguity log (gold, first pass 2026-10-11)

Spec-field sources after stage 2 (147 family spec fields, 15 families): **both page and PDF 123 (83.7%)** (agree 99, refines 17, conflict 7), **page only 22 (15.0%)**, **PDF only 2 (1.4%)**. (First pass: 149 fields, both 142, page only 3, PDF only 4.)

## Conflicts (spec sheet displayed, page value in alt_values)

| family | field | spec sheet (displayed) | page (alt) |
|---|---|---|---|
| 30xlc | material_body | TDS "manufactured from DZR “CR” corrosion-resistant brass" | Materials "Body: Hot Forged Brass ASTM C37700" (the page prose repeats the TDS wording) |
| 30xlc | material_seals | "EPDM-ASTM D 2002 M2 o-rings" | "O-Ring: EPDM - ASTM D 2000 M2" (different standard number, so a conflict, not a refinement) |
| 80prs | material_body | "DZR “CR” corrosion-resistant brass" | "Body: Hot Forged Brass ASTM C37700" |
| 80prs | material_trim (swing disc) | "hot-forged brass EN 12165-CW617N swing disc" | "Swing Disc: Hot Forged Brass ASTM C37700" |
| 80prs | material_seals | "EPDM-ASTM D 2002 M2 o-rings" | "O-Ring: EPDM - ASTM D 2000 M2" |
| 746 | size_range | TDS (series sheet, FNPT dimension table) ½"–2" | page Part Numbers ½"–1" (746-04/06/07 only) |
| 747nl | standards | TDS: MSS SP-110, PS117-2004, EN ISO 9001, ISO 5208, NSF/ANSI 61-2008 Annex G | page also says "complies with ANSI B1.20.1 standards", which is not on the sheet, so this is a conflict |

## Self-review after discovery (DEVIN_TASK checkpoint, not waited on)

- (a) **Family definition = SPEC 3.** Each BigCommerce product page is one series (e.g. 778, 778P, 778V, …; 3739C and 3739G are separate pages and series). Orderable identifiers from the page "Part Numbers" table or the family TDS "Cim No." table are variants. The 778 option suffixes (P/V/C/W/S) are separate product pages with their own Cim Nos., so each is its own family, not a variant of 778.
- (b) **Two independent index sources.** Product sitemap `xmlsitemap.php?type=products&page=1` gives 32. A crawl of header-nav category pages plus pagination also gives 32. **Sitemap only 0, crawl only 0, both 32**, union 32. This is recorded in `gold_meta.family_index_method`. No aliases or duplicate URLs.
- (c) **Sample.** `gold/cimberio.sample.py`: `random.Random(42)` over the index sorted by URL, proportional to breadcrumb category. Coverage: CAD/BIM 3 (746, 747nl, 778 Revit .rfa), multi-variant 15, price shown 13. **Coverage swaps: none.**
- (d) **Scope.** In scope: cimberiovalve.us, cdn11.bigcommerce.com/s-herjth7887, store-herjth7887.mybigcommerce.com (Cimberio's own store host; see HARNESS_ISSUES). web.cimberio.com: no sampled US product page links a file on it, so nothing is used from it. No forms submitted, nothing added to cart. Product pages have no option selectors; sizes are separate Cim Nos. in a static table.

## Blind re-label families (stage 1 draw)

`random.Random(42).sample(sorted(<15 family_ids>), 6)` = **778pvw, 30xlc, 1220nl, 778pvws, 747nl, 746**

## Judgement calls (`case | decision | proposed SPEC wording`)

- Prices: product pages show only "Request a Quote", but the Resources page links "List Price Book PL-CIM_V0016.02, Effective July 1, 2022" | an exact Cim No. row → `price_type=list`, `availability=price_shown`, USD, `effective_date=2022-07-01`, source = PDF row quote ("<Cim No.> <size> <box qty> $<amount>"). No row → `request_quote` with the page "Request a Quote" quote. Result: 54 variants priced; 1220NL-11/12/14, all 746 and all 3739C are request_quote | "A public manufacturer list price book linked from the site prices a variant when the Cim No./SKU matches exactly; otherwise record the page status."
- Price-book "Box Qty. Carton/Inner" column (e.g. `120/30`, `Order`) | kept in price `notes`. `pack_qty` is left null because the column is two numbers and the unit is not stated | —
- 747PRSNL identifiers | the page, TDS and price book all use `747PRS-04 … -10`, so the variant SKUs stay as printed (no "NL" added) | —
- 778 TDS (TechDataSheet-778_v5) says "Technical data applies to Cim 778 … ONLY (without any options)" | the TDS Technical Characteristics are used only for family 778. The option families (778P/V/VW/PVC/PVW/PVWS) use "Cim 778 SpecificationsV2" (the series specification, which lists all models) plus the TDS front page / Popular Models table | "If a sheet limits its data table to one model, use it only for that model."
- 778 TDS has a boilerplate legend box with "Working Pressure: 250 PSI" and "-4° F - 248° F" next to "Nominal Pressure: 360 PSI (PN 25)" and "Temperature: 15°F to 200°F" | the legend is treated as template text and not used. 360 PSI / 15–200 °F agree with SpecificationsV2 and the page | —
- 778 SpecificationsV2 (CSI-style "shall be" guide spec) | doc_type `spec_sheet` (no guide-spec type in SPEC 2) | add `guide_spec` or map it to spec_sheet explicitly
- 1220NL: table "-4° F - 248° F" vs prose "250° F temperature rating" (on both page and TDS) | temperature_range = the table value (−4 to 248, agree). The prose rating goes in additional_specs.temperature_rating_prose | —
- 746 TDS is a series sheet (FNPT, CC (SWT), Press). The family page is the NPT version (746-04/06/07) | following SPEC 6a, the sheet value is displayed: end_connections [NPT, solder, press] refines page [NPT]; sizes_available ½–2 refines page ½–1; size_range conflict | "When a sheet covers several connection versions with separate product pages, cross-check only the row for this page's version." (not applied, logged for the orchestrator)
- 3739 TDS covers 3739C and 3739G | only items marked "(3739C)" are used ("Flange (3739C)") | —
- Glyph mapping for TDS-746 / TDS-3739 (`\x10`=½, `\x11`=¼, `\x13`=¾, `¡`=°, `¥`=•) | applied in the committed evidence text and checked against page renders (HARNESS_ISSUES #2) | —
- Standards vs certifications | `certifications` only when the source says "certified" (778 series NSF/ANSI 61). "Based on NSF/ANSI 61-2008 Annex G", MSS SP-110, PS117-2004, EN ISO 9001, ISO 5208 test, ANSI B1.20.1, ISO 9001, EN 12266-1 → `standards` | —
- Page list ⊂ sheet list for standards (1220nl, 30xlc, 80prs, 74prsnl, 747prsnl, 778) | `refines` (SPEC 6a list rule) | —
- Applications: "heating (LPHW)" → `hydronic heating` (LPHW = low-pressure hot water heating); plain "heating", "cooling", "plumbing", "sanitary systems", "autoclaves", "pumps", "agricultural", "domestic water systems", "non-corrosive liquids", "50% glycol/water mixtures" → applications_other; "commercial plumbing" → `commercial`; "compressed air systems" → `compressed air` | 1220NL has no controlled application term, so the field is omitted (other wording is in additional_specs) | —
- Check-valve materials: material_trim = disc (30XLC EPDM page-only; 80PRS swing disc). Stem/spring/bonnet/gasket go in additional_specs. The 30XLC stem is "Hot Forged Brass ASTM C37700" in the page table but "Hostaform thermoplastic" in the page prose and TDS: recorded, not scored | —
- 74PRSNL body: sheet "DZR “CR” … no-lead brass" vs page "Cast Nondezincificable Brass “CR”" | `refines` (DZR = dezincification resistant, and the sheet adds no-lead). The validator warns | see HARNESS_ISSUES bray #2 / cimberio #3
- 778 body: page "Corrosion-Resistant Brass" vs SpecificationsV2 "DZR Brass ANSI C27453 or EN 12165 CW511L" | `refines` (validator warns) | —
- Images | photos only, shortest side ≥ 300 px, largest `/stencil/original/` rendition. Flow / pressure-drop / temperature charts are excluded as text graphics. 778VW, 778PVC and 778PVW have only a ~210–240 px tall banner photo, and 3739C has only a 215×253 photo, so these families have no qualifying image. 778PVWS shows two photos of the base 778 body as well as the assembly: kept, because they are on that page as product views | —
- 1220NL Instructions.pdf is titled "CIM 1220CRNL" | listed as `iom_manual` for 1220nl (linked from that page) but not used as a spec source | —
- Price-list document | listed on each family with ≥ 1 priced variant, found_on = Resources page, revision_date 2023-01 (footer "PL-CIM_V0016.02 · 1/23") | —


## Blind re-label (6 families)

Blind branch `blind/cimberio` @ c08c7db (778pvw, 30xlc, 1220nl, 778pvws, 747nl, 746). BEFORE = raw blind vs first-pass commit 75b1ffd. AFTER = blind vs final gold. Spec values are compared exactly after lowercasing and removing spaces and quote marks.

| row | BEFORE | AFTER |
|---|---|---|
| documents found | 9/14 (64%) | 9/14 (64%) |
| doc_type | 9/9 (100%) | 7/9 (78%) |
| images | 9/9 (100%) | 9/9 (100%) |
| variants (SKUs) | 27/27 (100%) | 27/27 (100%) |
| variant price availability | 6/27 (22%) | 6/27 (22%) |
| CAD | 2/2 (100%) | 2/2 (100%) |
| size_range | 6/6 | 6/6 |
| sizes_available | 6/6 | 6/6 |
| size_unit | 6/6 | 6/6 |
| material_body | 1/6 | 1/6 |
| material_trim | 1/1 | 1/1 |
| material_seals | 2/2 | 2/2 |
| end_connections | 6/6 | 6/6 |
| pressure_rating | 6/6 | 6/6 |
| temperature_range | 6/6 | 6/6 |
| certifications | 2/2 | 2/2 |
| standards | 1/6 | 1/6 |
| applications | 4/5 | 4/4 |
| cross_check | 50/55 (91%) | 44/55 (80%) |
| **family spec fields overall** | **47/58 (81%)** | **47/57 (82%)** |

BEFORE agreement on family spec fields is 81% (at least 80%), so no SPEC clarification round was needed.

Per disagreement (source re-checked each time):
- **747nl applications** (gold `hydronic heating` from TDS "heating (LPHW)"; blind omitted it) | **blind right** under the new SPEC 6 "Mapping strictness": "heating (LPHW)" does not name `hydronic heating`. The field was removed and the wording moved to applications_other. Same fix in 747prsnl.
- **1220nl Instructions revision_date** (gold null; blind 2019-06-17) | **blind right**: the footer says "QA1210 - rev. 11 17/06/2019". Fixed.
- **Price list document + 21 variant prices** (gold: `price_shown` list prices from "List Price Book PL-CIM_V0016.02", linked on https://cimberiovalve.us/resources/; blind: all request_quote) | **gold kept**. The blind pass did not find the price book. It is a public manufacturer price list (own store host), and the Cim Nos. match exactly. The 6 matching rows are the request_quote variants (1220NL-11/12/14 and 746-04/06/07).
- **standards, 5 families** (gold includes "NSF/ANSI 61-2008 Annex G" because sources say "Based on NSF/ANSI 61-2008 Annex G in compliance with Section 116875…"; blind put it in additional_specs.lead_free_compliance) | **gold kept**: it is a named standard that the product is stated to conform to. "PS117-2004" (gold) vs "PS 117-2004" (blind): gold keeps the source spelling. → top ambiguity #1.
- **material_body, 5 families** (wording only: comma or word order, e.g. "corrosion-resistant DZR brass" vs "DZR corrosion-resistant brass"; for the 778 series the blind pass also adds the page's "corrosion-resistant") | **gold kept**: gold copies the spec-sheet wording. Same material in every case.
- **778pvw/778pvws pressure_rating / temperature_range cross_check** (gold agree; blind conflict with 250 PSI / -4..248 °F from the TDS-778 p5 legend) | **gold kept**. The legend is the CV/CM/CS/MT ball-valve torque legend copied from a ball-valve template, next to "Nominal Pressure: 360 PSI". TDS-778 is now a `catalog` (see below), so it does not take part in the spec-sheet cross-check. Logged here, not hidden. → top ambiguity #2.
- **778pvw/778pvws size fields cross_check** (after: page_only; blind agree via the TDS table) | changed by the SPEC 5 reclassification of TDS-778. SpecificationsV2 gives sizes only for NPT ("½ inch NPT, ¾ inch NPT, or 1-inch NPT sizes"), so the press families are page_only.
- **TechDataSheet-778_v5 doc_type** (after: catalog; blind spec_sheet) | changed by the new SPEC 5 "Classify by content": it is 8 pages and covers 14 models, and rule 2 makes a technical manual over 4 pages a `catalog`. The blind pass predates this SPEC paragraph.
- 778pvw/778pvws standards (gold [Annex G] page_only; blind none) | see the standards item above.

## New SPEC paragraphs applied (auto/integration, 2026-10-11) to all 15 labelled families

- **SPEC 5 Classify by content.** I checked every document: TechDataSheet-778_v5 (8 pages) `spec_sheet` → **`catalog`** (secondary) in all 7 778-series families. In each of the 7, every TDS-778 spec source was removed: size fields now come from SpecificationsV2 for NPT models (778, 778V, 778VW) and are page_only for press models (778P, 778PVC, 778PVW, 778PVWS); material/pressure/temperature/certifications/applications come from SpecificationsV2 + page; standards = page value [NSF/ANSI 61-2008 Annex G], page_only. For family 778, "ANSI B1.20.1" (only in the catalog) is dropped because the page outranks a catalog. Unchanged: Cim 778 SpecificationsV2 (2 pages, guide specification, `spec_sheet`), all other TechDataSheets (1–2 pages, `spec_sheet`), the price book (`price_list`), 1220NL Instructions (`iom_manual`).
- **SPEC 6 Mapping strictness.** 747nl and 747prsnl `applications` removed ("heating (LPHW)" / "heating" / "cooling" go to applications_other). These stay as they are because the source names the term: 30xlc/80prs `commercial` ("commercial plumbing"), `compressed air`; 74prsnl `residential`, `industrial`; 746/3739c `HVAC`; 778 series `domestic hot water`; 746 end_connections `NPT`, `solder`, `press` (alternatives "FNPT / CC (SWT) / Press"). 1220nl already had no applications.
- **SPEC 4 Image edge cases.** No change. Every image URL is a `/stencil/original/` link that the family page itself references (gallery anchors). No annotated/clean pairs or option collages. Charts stay excluded because their meaning is carried by axis labels and legends.

## Consistency pass (SPEC changes of 2026-10-11)

Checked all 15 labelled families against the saved evidence text (pages, TDS, SpecificationsV2, TDS-778 catalog, price book) for SPEC 3 option codes, SPEC 6 BSPT/threaded, Standards scope and PN/class. The live site was not needed (every value is in the saved evidence). SPEC 4, 5, 6 "Mapping strictness" and 7 were already applied (see the section above). Re-checked here with no change: all images are `/stencil/original/` URLs the pages link; doc_types unchanged; all 15 families have variants, so no `family_prices`.

Changes (`family | field | before -> after | paragraph`):
- 30xlc | standards value (TDS) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope ("as written"; TDS: "MSS-SP-110")
- 30xlc | standards alt_values (page) | "MSS SP-110", "PS117-2004" -> "MSS-SP-110", "PS1172004" | SPEC 6 Standards scope (page: "MSS-SP-110, PS1172004")
- 80prs | standards value (TDS) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope
- 80prs | standards alt_values (page) | "MSS SP-110", "PS117-2004" -> "MSS-SP-110", "PS1172004" | SPEC 6 Standards scope (page: "MSS-SP-110, PS1172004")
- 747prsnl | standards value (TDS) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope
- 747nl | standards value (TDS) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope
- 1220nl | standards value (TDS) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope
- 1220nl | standards alt_values (page) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope (page: "Conforms to MSS-SP-110")
- 74prsnl | standards value (TDS) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope
- 74prsnl | standards alt_values (page) | "MSS SP-110" -> "MSS-SP-110" | SPEC 6 Standards scope

cross_check values are unchanged (spelling-only differences are the same standard; `spec:` commit below).

Checked, no change (`case | decision | proposed SPEC wording`):
- SPEC 3 option codes: TDS-778 (catalog) "Model Selection" chart builds Cim Nos. from 778/778P + V / S / C / W + size | every combination it names (778P, 778PV, 778PVC, 778PVW, 778PVS, 778PVWS, 778PVCS, 778V, 778VC, 778VW, 778VS, 778VCS, 778VWS) has its own product page in the sitemap, so these identifiers belong to those families (SPEC 3 last sentence) and the letters are not options of 778; no `additional_specs.options` added. All 15 families' variants are the page "Part Numbers" identifiers (also in their own TDS tables); no suffix/option codes found in any page or sheet. "CIM 30XLC.1" appears once in 30XLC page prose, in no table or selector: not a variant, not an option code | —
- 3739C "available with ANSI or DIN flanges" (page + TDS) | no codes, so it stays in `additional_specs.flange_options`; no standard number is given, so nothing is added to `standards` | —
- SPEC 6 BSPT vs threaded | no Cimberio source names BSP, G, ISO 228, BS 2779, R/Rc or ISO 7-1; NPT families stay `NPT` | —
- Standards scope, thread/flange standards | 746 already lists "ANSI B1.20.1" (TDS + page "FNPT (ANSI B1.20.1)"); 747nl keeps the page's "complies with ANSI B1.20.1 standards" in alt_values (still a conflict: the TDS does not state it). 778 "Threads: NPT - ANSI B1.20.1" is only in TDS-778, now a `catalog`, which ranks below the page (SPEC 6a), so 778 standards stay the page value. No "formerly" standards. Material designations (ASTM C37700, EN 12165-CW617N, ASTM D 2000/2002, EN 1982-CC7525) are material specs, not product standards, and stay in the material fields | —
- PN and class: 3739C page "Connection: Drilled Flange PN 16" next to "Max. Static Pressure: 232 PSI" (TDS "Max. static working pressure: 232 PSI") | the PN qualifies the flange drilling, so pressure_rating stays 232 psi (agree) and "Drilled Flange PN 16" stays the end_connections raw_text. TDS-778 "Nominal Pressure: 360 PSI (PN 25)" is in the catalog, which is not a display/cross-check source. No ANSI class designations | written into SPEC 6 (see below)

## Top 5 ambiguities

1. Lead-free statements "Based on NSF/ANSI 61-2008 Annex G…": `standards` (gold) or additional_specs (blind). SPEC should say whether a "based on / in compliance with" statement counts as a standard.
2. Template legend in TDS-778 (250 PSI, -4..248 °F) that contradicts the sheet's own 360 PSI / 15–200 °F: conflict or ignore. Gold ignores it (and the sheet is now a catalog).
3. Price-list PDF prices vs "Request a Quote" on the product page (HARNESS_ISSUES cimberio #4).
4. Series sheets covering versions sold on separate pages (746 FNPT/CC/Press; 3739C/G): SPEC 6a makes the sheet value (and refines/conflict) display even when the page is one version.
5. Self-contradicting page tables vs prose/TDS on check-valve materials (30XLC/80PRS body "Hot Forged Brass ASTM C37700" vs "DZR CR brass"; seals ASTM D 2000 vs D 2002).

## SPEC changes made

None by this labeller. (Applied the orchestrator's 2026-10-11 SPEC 4/5/6 paragraphs; see above.)

Consistency pass (2026-10-11):
- `spec:` SPEC 6 Standards scope: spelling-only differences (spaces, hyphens: `MSS SP-110` / `MSS-SP-110`, `PS117-2004` / `PS1172004`) are the same standard; each source's list keeps its own spelling and `cross_check` compares them as equal. Reason: "as written" would otherwise turn a dropped hyphen on a page into a `conflict`.
- `spec:` SPEC 6 PN and class: a PN that only qualifies a connection ("Drilled Flange PN 16") is a flange-drilling detail kept in the `end_connections` raw_text; when the same source states a working/maximum pressure, that pressure is the `pressure_rating`. Reason: the stated working pressure is what a builder compares, and both labellers find the same line. Other sites' gold files: the orchestrator should check flange-only PN designations.
