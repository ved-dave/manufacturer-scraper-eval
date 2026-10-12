# milwaukee — ambiguity log 

Labelled 2026-10-11 against SPEC on main. Independent of any scraper output (no scraper code, runs, reports or PRs opened).

## Conflicts
- **BA-300SBS size_range (conflict)** | sheet BA300SB300SBSOPT.pdf "¼”-2”" covers BA-300SB and BA-300SBS; the 8 BA-300SBS pages list only 3/4"–2". Displayed: sheet 1/4–2 (spec-sheet precedence); page 3/4–2 kept in `alt_values` | SPEC 6
- **Flatlist vs sheet, UPBA-490S pressure (not scored)** | flatlist description "250 PSIG @ 250 DEG F" vs page/sheet "200 psi @ 250 Degrees F" / "200 psig @ 250°F". The flatlist is used for prices only, never as a spec source, so the gold spec stays 200 psi (page and sheet agree) | SPEC 6/7

## Judgement calls
- **Crawl delay** | robots.txt declares `Crawl-delay: 10`. SPEC 1a says robots.txt is not obeyed, but I chose to use 10 s per request to this host anyway, so the site isn't overloaded. One host lock is shared by every crawler | operational choice
- **Index sources** | (1) `sitemap_index.xml` product sitemaps: 5,822 /product/ URLs; (2) a crawl of the Products-menu category pages (/product-category/<cat>/page/N/). The WooCommerce Store API (/wp-json/wc/store/v1/products) has 5,846 records; I used it for category membership only, not as a third index source. Counts: sitemap 5,822, category crawl 5,844, **both 5,820 / sitemap-only 2 (`p2641`, `test`) / crawl-only 24** (all 24 are Store API records). One page did not load (`/product/ba-100sh-p1-sh/`), logged in `unlinked`. 370 families (121 with several model pages)
- **Model page vs family (SPEC 3)** | each /product/<model>/ page is one model or configured order code (e.g. mw328nbad), with sizes listed on the page and no per-size order codes. A family is a manufacturer series: the site's own "<X> Series" product categories (M, H, 10, 20, 22, 30, 35, 41, C, F20, F90, F91 Series) and the product lines High Performance and Triple Offset (TØV). Pages outside those are grouped only when they link the same product spec-sheet PDF (e.g. 509 + 509T -> 509509T.pdf; 1548B + 1548T -> 1548T1548B.pdf). Otherwise a page is its own family | SPEC 3
- **Sitewide PDFs don't group** | the ISO 9001/14001 certificates, technical-service sheet 4388_001, the IOM manuals (bronze gate/globe/check, UltraPress, cast steel, cast-iron silent check) and accessory sheets (cast-steel chainwheels) are linked from many unrelated pages, so they are not family evidence | SPEC 3
- **Flatlist model numbers rejected as a family key** | the Jan 2026 flatlist (0126-mv-flatlist-for-website-dated-1-5-2026.xlsx) groups some models (509, 509-P2, 509T-P2, 509Y-P2 under "509"). Across the site its MODEL NUMBER column is inconsistent with the page slugs and with the spec sheets (509 and 509-P2 have different sheets), so it is not used for grouping | SPEC 3
- **Size-only fields** | sizes come from the page size list and the sheet's dimension table. Size alone never creates an override (SPEC 6) | SPEC 6
- **Prices** | the Store API returns price 0 for every product (no price published on pages). List prices come from the public flatlist workbook `0126-mv-flatlist-for-website-dated-1-5-2026.xlsx`, linked from /resources/price-lists/ as "Price Lists in Excel Format 0126 - Effective 01/05/2026". effective_date = 2026-01-05 (the linking page); the workbook's title row says "Revised 6-1-2026" (logged, not used). A variant gets a price only when its page heading equals a MODEL WITH OPTIONS entry (split on "/", e.g. "UP149/UP635"), one price per size row with the EDI part number in notes. Exceptions/strict calls: F-2983-M = flatlist "2983M" (same description, ratings, sizes, flanged ends; name difference logged); `/product/utzm200/` is headed UTZM177 and the flatlist has UTZM200 but no UTZM177 -> not_published; BA-350TE-2G/BA-350STE-2G (flatlist has only option-coded BA350STE2GOC, BA350TE2GLDOC…) and UPBA490S-LL/-MS/-OH/-TH (flatlist has only base UPBA490S) -> not_published rather than matched by prefix; marine 1041/1260/845-4687594 and BA-300SBS not listed -> not_published. 8 of 15 families have list prices | SPEC 7
- **CAD** | an embedded PARTcommunity viewer, recorded as `cad_viewer`, `gated` per whether a login or form is needed to download . The viewer (milwaukeevalve-embedded.partcommunity.com) loads, but "CAD Download" is a PrimeFaces form with `redirectLogin()`, so `gated: true`, `formats: []`; no form was submitted. One viewer per model (e.g. 1150_asmtab); the 30 Series shares one series viewer on 23 of its 124 pages -> one family-level record (variant_skus []). 7 of 15 families have a viewer | SPEC 8
- **SWP / WOG pressure pairs** | pages and sheets give two ratings ("150 SWP – 300 WOG"). `pressure_rating` = the highest stated pressure (the WOG figure, psi). The full designation, with the SWP steam rating, goes in `raw_text`. This follows sioux-chief ("600 psig WOG" -> 600 psi) and bray (CWP). Page and sheet are cross-checked on both numbers | SPEC 6 (proposed wording in HARNESS_ISSUES)
- **Page heading is the variant identifier** | each model page's heading (e.g. "BA-100 P2-LD", "30CS0F02", "803-1385541 (mod)") is the orderable identifier (SPEC 3); sizes listed on the page are not variants. 1041/1260 marine pages are headed with the Navy-style number (803-1385541 (mod), 803-1385637); the MV figure numbers (1041, 1260) are kept in `name`; `series_code` is null because the pages name no series | SPEC 3
- **UTZM200 URL vs UTZM177 heading** | slug utzm200, heading UTZM177, drawing unit-ut-zm177-dwg.pdf -> identifier UTZM177 | SPEC 3
- **30 Series pressure override** | steel 30CS/30SS/30CC are 1000 WOG (30SSCSCC.pdf); bronze 30BB0F02/30BS0F02 pages say 600 WOG -> `spec_overrides` on those two (page_only: 30BBBS.pdf has no pressure text). Body material is one family list (SPEC 6 material rule) | SPEC 6
- **Strict end-connection mapping** | "Sil Brazed" (BA-300SBS) and "Extended Tube Ends with 1/8" NPT Gauge Ports" (BA-350) have no controlled term -> `end_connections_other`; "F1 NPT" in the UPBA-490S sheet refines page "Threaded" to NPT | SPEC 6
- **Lead-free alloy refines (2 of the 3 validator warnings)** | UP149 "Lead Free Bronze" -> sheet "Bronze B584 C89833"; UPBA-490S "Lead Free Brass" -> "Brass, Forged B283 C27450". The sheet names the alloy, so `refines`; the validator's narrower-form check doesn't recognise it (as in caleffi/bray) | SPEC 6
- **Documents by content (SPEC 5)** | spec-sheets/*.pdf and unit-ut-zm177-dwg.pdf -> spec_sheet; ioms/*.pdf -> iom_manual; MV-ISO9001/14001 -> certificate (ISO14001 is image-only); 4388_001.pdf is the "MVC Conflict Minerals Policy" -> other_doc; UPSolderingConsiderations.pdf (sales memo) -> other_doc; 20-30-Series.pdf is image-only (16 chars) -> other_doc, not cited. `milwaukeevalve.com/wp-content/uploads/MV-ISO9001_2015.pdf` (no www) returns 404 -> `unlinked` | SPEC 5
- **PDF text** | pdfplumber with `dedupe_chars()` (several sheets double every glyph otherwise); garbled table cells (BA-100H-TIH pressure table, F-2983-M parts list) are not cited | evidence
- **BA-300SBS sizes_available (3rd validator warning)** | validator suggests `refines` because the sheet's list is a superset of the pages'; kept `conflict`, matching `size_range`: the sheet covers BA-300SB as well, so its extra sizes are not BA-300SBS sizes | SPEC 6
- **Images** | product images >= 300 px shortest side (SPEC 8); footer/newsletter graphics, category logos and 150 px renditions dropped; renditions de-duplicated by image key / phash <= 2 | SPEC 8

## Cross-check counts
96 family-level fields: agree 55, refines 14, conflict 2, pdf_only 5, page_only 20. Variant overrides: 2 (page_only 2). Families: both 11, page 3, none 1

## Sample (seed 42, proportional to category)
Actuation 1, Ball Valves 4, Check Valves 2, Gate Valves 2, Globe Valves 1, Lead-Free 1, Marine 3, UltraPress 1. 7 with CAD viewer, 5 with several model pages: coverage met without swaps (`milwaukee.sample.py`).

## Blind re-label
Separate session (https://outpostai.devinenterprise.com/sessions/0ae962ce727543bfb0e6d0e19edaedfb) re-labelled 6 families chosen by `random.Random(42).sample(sorted(family_ids), 6)` — 30 Series, BA-350TE-2G/350STE-2G, 1150, F-2983-M, 803-1385541 (mod), 510T — from an evidence-text packet only (no access to this key). Compared with `gold/milwaukee.blind.compare.py` (price_list documents compared through prices, not as documents).

| dimension | before fixes | after fixes |
|---|---|---|
| variants | 129/134 (96%) | 129/134 (96%) |
| documents | 31/31 (100%) | 31/31 (100%) |
| doc_type | 31/31 (100%) | 31/31 (100%) |
| CAD | 6/6 (100%) | 6/6 (100%) |
| images | 11/13 (85%) | 12/12 (100%) |
| family spec fields | 21/42 (50%) | 35/42 (83%) |
| variant overrides | 7/7 (100%) | 7/7 (100%) |
| cross_check | 23/28 (82%) | 36/40 (90%) |

Before-fix family spec agreement was 50% (< 80%), so proposed wording is in HARNESS_ISSUES `## milwaukee`.

**Fixed (gold was wrong or incomplete):** `sizes_available` and `size_unit` were missing on every family -> added from each page's "Product Size" list, cross-checked against the sheet's size row (agree on 11 families, page_only on the 3 marine pages, conflict on BA-300SBS where the sheet row 1/4"–2" covers BA-300SB too); 30 Series `standards` add "WW-V 35" (30BBBS.pdf "Conforms to: WW-V 35, Class A,"); 30 Series `end_connections` add solder (30BBBS.pdf ordering key "1 = Solder End"; refines, since no 30 Series page shows it); BA-350 image is now the 2560×1708 original instead of its 600×400 rendition (de-duplication keeps the largest).

**Kept (judgement calls, both readings logged):**
- material_body with an ASTM/UNS alloy on the sheet ("Bronze ASTM B62") vs page "Bronze": gold shows the sheet value as `refines` (as in caleffi/bray); blind used the generic word as `agree` (4 families).
- 803-1385541 (mod): the page heading (Navy drawing number) is the one orderable identifier; "MV Figure No. 1041, 1042, 1043, 1044" names the globe/angle/stop-check figures on one page with no separate codes or prices, so they are not split into 4 variants. Blind split them.
- 30 Series applications: "03 = Steam Service" is an ordering option code and "Rated 150 psi Steam" is a pressure rating, so no `applications` value; blind gave ["steam"].
- BA-350 end connections: "Female end copper-tube extensions" does not say solder; kept in `end_connections_other` (no inference). Blind mapped to solder.
