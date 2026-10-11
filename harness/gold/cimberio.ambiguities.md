# cimberio — ambiguity log (gold, first pass 2026-10-11)

Spec-field sources (149 family spec fields over 15 families): **both page and PDF 142 (95.3%)** (agree 117, refines 18, conflict 7), **page only 3 (2.0%)**, **PDF only 4 (2.7%)**.

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

## SPEC changes made

None in the first pass.
