# Bray blind image / doc_type re-label (6 families)

Blind re-label under the current SPEC 4 (images) and SPEC 5 (doc types). Sources: the 6 live family pages (all tabs:
banner slider, Description, Features & Benefits accordions, Downloads) and every PDF linked from them; nothing else.
Not consulted: bray.json, bray.ambiguities.md, bray.sample.py, bray.family_index_meta.json, bray.evidence/, gold/bray branch, PR #3.
All 6 pages and all 25 distinct PDFs returned HTTP 200; every PDF starts with `%PDF`; all are English-only (`en`).
`revision_date` comes from the printed document code / date in the footer (e.g. `TM-1090_5A_aluminum_20221014` -> 2022-10-14);
only "© YYYY" -> year. `priority`: spec_sheet = primary, everything else secondary. Evidence text: `bray.blind-imgdoc.evidence/text/`.
`family_index` lists only these 6 families so `validate --gold` runs; it is not a full site index.

## Per-document and per-image decisions

### series-5a (https://www.bray.com/valves-actuators-controls/control-accessories/switch-boxes/series-5a-switch-box)

Documents:

- `tm-1090_5a_aluminum.pdf` -> **spec_sheet**, en, rev 2022-10-14: 2-page technical data sheet (technical data, materials, ratings, dimensions) for the 5A aluminum VSM; page label "Technical Sales Manual". Date from code TM-1090_5A_aluminum_20221014 (also "Rev. 10 2022").
- `b-1068-s5a-5b-5c-vsm-rev_compressed.pdf` -> **brochure**, en, rev 2022-04-11: 8-page marketing brochure covering Series 5A, 5B and 5C together (features, options); multi-series brochure of one product line -> brochure. Code EN_BR_BRO_CT_1068 S5A-B-C VSM_20220411.
- `en_vac_broc.pdf` -> **brochure**, en, rev 2024-08-13: 4-page brochure about the Bray Europe Valve Automation Centre (UK facility/services); not about this product at all, but it is linked in the family Downloads tab, so kept as brochure. Code EN_VAC_BROC_2024.08.13.
- `valve-status-monitors-series-5ab-om-en-us.pdf` -> **iom_manual**, en, rev 2022: 26-page "Installation, Operation and Maintenance Manual" for 5A/5B. Only "© 2022" printed, no document code date.
- `en_br_iom_ct_s5a_5b-is_halfsize.pdf` -> **iom_manual**, en, rev 2022-12-22: 11-page IOM for the intrinsically safe 5A/5B. Code ..._IOM_CT_S5A_5B I.S._Halfsize_20221222.
- `hazardous-location-products.pdf` -> **other_doc**, en, rev 2020-03: 1-page reference chart: NEC/ATEX hazardous-area classes plus which Bray series carry which rating; no ordering data, not product-specific -> other_doc. Code DG_1078_EL_CTRLS_HAZ_LOC_2020_03.
- `intriniscally-safe-product-selection.pdf` -> **catalog**, en, rev 2020-06: 8-page "Selection Guide - Intrinsically Safe Packages": multi-product packages (VSM, sensors, solenoids, barriers) with part numbers -> catalog. Code B-1079_EL_IS_GUIDE_2020-06.
- `en_sm_1007_5-abc-vsm_safety-manual.pdf` -> **iom_manual**, en, rev 2025-04-23: 13-page SIL safety manual for 5A/5B/5C: installation & commissioning, operating & maintenance, proof test, failure rates, start-up checklist -> iom_manual (SIL safety manual rule, see unclear cases). Code ..._Safety Manual_20250423.
- EXCLUDED `s5a_s5b-step-files.zip` (STEP Files): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- `series-5a-valve-status-monitor-technical-manual.pdf` -> **spec_sheet**, en, rev 2022-10-14: Same 2-page data sheet as tm-1090 (same TM-1090_..._20221014 code, file differs by 2 bytes), separate URL listed as "Technical Manual"; recorded as its own document.
- EXCLUDED site-wide nav-menu PDFs (Criminal Finance Act statement, REACH declaration): site chrome on every page, not in the Downloads tab.

Images:

- `2025_s5a_92-93_mccannalok-s40_41_8in_homehero_0100.webp` 2000x1269 -> **product_photo**: Hero view (VSM on valve/actuator). Un-resized original found by dropping the "5a--mobile/" folder of the Description-tab image (640x406); the banner 600x600 "-copy-600x600" is a square crop of it -> both dropped.
- `2025_s5a_exp_02-copy.webp` 2000x2000 -> **product_photo**: Second banner slide, VSM alone from a different angle; 2000x2000 is the largest (no un-suffixed original, 404).
- `series5a-cutaway-1-min.webp` 1145x1625 -> **product_photo**: Features-section cutaway render with small letter markers A-K (legend is HTML text, not in the image) -> cutaway kept as product_photo, not a text infographic. No larger original (series5a-cutaway-1.webp 404).
- EXCLUDED: related-product slider cards ("Card Image" thumbnails of other series), "More from Bray" industry photos, logos, chatbot icon, tracking pixel.

### series-70-haz (https://www.bray.com/valves-actuators-controls/actuators/electric-actuator/series-70-hazardous-location)

Documents:

- `en_vac_broc.pdf` -> **brochure**, en, rev 2024-08-13: 4-page brochure about the Bray Europe Valve Automation Centre (UK facility/services); not about this product at all, but it is linked in the family Downloads tab, so kept as brochure. Code EN_VAC_BROC_2024.08.13.
- `en_b-1100_actuators-controls_web.pdf` -> **catalog**, en, rev 2024-08-19: 16-page "Actuators & Controls Product Overview" with a technical-specification block for each of ~14 series (01, 70, 92/93, 98, 5A/B/C, 6A, 63, ...) -> catalog (multi-product line overview). Code EN_B-1100_Actuators Controls_2024-08-19.
- `b_1103_s70-quickstart-guide.pdf` -> **iom_manual**, en, rev 2024-08-16: 2-page Quick Start Guide: cam/limit calibration and wiring steps for Series 70 -> iom_manual. Code B_1103_S70 QuickStart Guide_20240816.
- `en_rss_s70_actuator.pdf` -> **spec_sheet**, en, rev 2023-09-15: 3-page "Recommended Specification Sheet" (guide spec, "The actuator shall ...") with enclosure, motor, gear train, ratings -> spec_sheet (guide-spec rule, see unclear cases). Covers Series 70 generally, not only HAZ. Code EN_RSS_S70 ACTUATOR_20230915.
- EXCLUDED site-wide nav-menu PDFs (Criminal Finance Act statement, REACH declaration): site chrome on every page, not in the Downloads tab.

Images:

- `s70_haz_s43-12in-_homehero_1-copy.webp` 2000x1311 -> **product_photo**: Hero view (actuator with handwheel on valve), 2000x1311 from the Description tab; banner 600x600 is a crop -> dropped.
- `s70_haz_thumbnail_2-copy.webp` 2000x2000 -> **product_photo**: Second banner slide, actuator alone with nameplate side, 2000x2000. (The un-suffixed s70_haz_thumbnail_2.webp is a 100x140 thumbnail, below 300 px, not used.)
- EXCLUDED: related-product slider cards ("Card Image" thumbnails of other series), "More from Bray" industry photos, logos, chatbot icon, tracking pixel.

### srh-series (https://www.bray.com/valves-actuators-controls/actuators/manual-operators/srh-series-manual-actuator)

Documents:

- `en_sds_spring-return-handle.pdf` -> **spec_sheet**, en, rev 2024-04-04: 2-page sales data sheet: description, compatibility chart (valve model/size -> SRH No.), parts list with materials, dimensions -> spec_sheet. Code EN_SDS_Spring Return Handle 4-4-2024.
- `manual-operators-srh-series-pb-en-us.pdf` -> **spec_sheet**, en, rev 2015-11: Older (Flow-Tek) 2-page version of the same data sheet: same description, compatibility chart, parts list, dimensions; page label "Product Brochure" but content is a data sheet -> spec_sheet. Code F-2810_EN_SHR_11-2015.
- EXCLUDED site-wide nav-menu PDFs (Criminal Finance Act statement, REACH declaration): site chrome on every page, not in the Downloads tab.

Images:

- `srh_ontriad_homehero_6-0070-copy600x600.webp` 600x600 -> **product_photo**: Banner slide 1: SRH handle mounted on a Triad ball valve (product render, not an installation scene). Only 600x600 exists (guessed originals 404).
- `srh_3_thumbnail_3-copy-600x600.webp` 600x600 -> **product_photo**: Banner slide 2: SRH handle alone with base plate; distinct view. Only 600x600 exists.
- EXCLUDED: related-product slider cards ("Card Image" thumbnails of other series), "More from Bray" industry photos, logos, chatbot icon, tracking pixel.

### series-5b-resin (https://www.bray.com/valves-actuators-controls/control-accessories/switch-boxes/series-5b-resin-switch-box)

Documents:

- `tm-1095_5b_resin.pdf` -> **spec_sheet**, en, rev 2022-11-21: 2-page technical data sheet for 5B Resin (switch options, approvals, dimensions). Code TM-1095_5B_Resin_20221121 ("Rev. 3 2022" is a revision number, not a month).
- `b-1068-s5a-5b-5c-vsm-rev_compressed.pdf` -> **brochure**, en, rev 2022-04-11: 8-page marketing brochure covering Series 5A, 5B and 5C together (features, options); multi-series brochure of one product line -> brochure. Code EN_BR_BRO_CT_1068 S5A-B-C VSM_20220411.
- `en_vac_broc.pdf` -> **brochure**, en, rev 2024-08-13: 4-page brochure about the Bray Europe Valve Automation Centre (UK facility/services); not about this product at all, but it is linked in the family Downloads tab, so kept as brochure. Code EN_VAC_BROC_2024.08.13.
- `valve-status-monitors-series-5ab-om-en-us.pdf` -> **iom_manual**, en, rev 2022: 26-page "Installation, Operation and Maintenance Manual" for 5A/5B. Only "© 2022" printed, no document code date.
- `series-5b_c-vsm-devicenet_halfsize-compressed.pdf` -> **iom_manual**, en, rev 2019-03-21: 16-page IOM for the 5B/5C DeviceNet communication module (wiring, network setup, EDS) -> iom_manual (protocol IOM rule). Code IOM-S5B VSM COMM PRO_DeviceNet_EL_03_21_2019.
- `series-5b_c-vsm-profibus_halfsize.pdf` -> **iom_manual**, en, rev 2019-03-21: 12-page IOM for the 5B/5C Profibus DP module -> iom_manual. Code IOM-S5B VSM COMM PRO_Profibus DP_EL_03_21_2019.
- `en_br_iom_ct_s5a_5b-is_halfsize.pdf` -> **iom_manual**, en, rev 2022-12-22: 11-page IOM for the intrinsically safe 5A/5B. Code ..._IOM_CT_S5A_5B I.S._Halfsize_20221222.
- `series-5b_c-vsm-as-iconnect_halfsize.pdf` -> **iom_manual**, en, rev 2019-03-14: 12-page IOM for the 5B/5C AS-i module -> iom_manual. Code IOM-S5B VSM COMM PRO_ASi_EL_03_14_2019.
- EXCLUDED `s5b_s5c-devicenet.zip` (Software): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- EXCLUDED `s5b_s5c-profibus-dp.zip` (Software): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- `hazardous-location-products.pdf` -> **other_doc**, en, rev 2020-03: 1-page reference chart: NEC/ATEX hazardous-area classes plus which Bray series carry which rating; no ordering data, not product-specific -> other_doc. Code DG_1078_EL_CTRLS_HAZ_LOC_2020_03.
- `intriniscally-safe-product-selection.pdf` -> **catalog**, en, rev 2020-06: 8-page "Selection Guide - Intrinsically Safe Packages": multi-product packages (VSM, sensors, solenoids, barriers) with part numbers -> catalog. Code B-1079_EL_IS_GUIDE_2020-06.
- `en_sm_1007_5-abc-vsm_safety-manual.pdf` -> **iom_manual**, en, rev 2025-04-23: 13-page SIL safety manual for 5A/5B/5C: installation & commissioning, operating & maintenance, proof test, failure rates, start-up checklist -> iom_manual (SIL safety manual rule, see unclear cases). Code ..._Safety Manual_20250423.
- EXCLUDED `s5a_s5b-step-files.zip` (STEP Files): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- `tm-1093_5bc_vsm_commpro.pdf` -> **spec_sheet**, en, rev 2020-10: 2-page technical data sheet for the 5B/C CommPro communication option (dimensions, enclosure material, wire gauge, temperature rating, protocols) -> spec_sheet (product option of this family). "Rev. 10_2020", code TM-1093_..._10.
- EXCLUDED site-wide nav-menu PDFs (Criminal Finance Act statement, REACH declaration): site chrome on every page, not in the Downloads tab.

Images:

- `s5b-resin_hero2-copy.webp` 1800x1109 -> **product_photo**: Hero view (resin VSM on pneumatic actuator), 1800x1109 from the Description tab; banner "-copy-2-600x600" is a crop -> dropped.
- `s5b-resinthumb-copy.webp` 1333x1333 -> **product_photo**: Banner slide 2: VSM alone, 1333x1333 (no larger original).
- `5b-lr-min.webp` 640x505 -> **product_photo**: Features-section cutaway render with letter markers -> cutaway kept (same rule as 5A). 640x505; 5b-lr.webp 404.
- `s5a-s5b-indicators-min.png` 1920x960 -> **product_photo**: Accordion "B. High Visibility Position Indicator": 1920x960 composite of several photos of the VSM with the different dome/indicator colour options. Shows product variants, no text -> kept as product_photo (see unclear cases). Hosted in the s5a-resin folder.
- EXCLUDED: related-product slider cards ("Card Image" thumbnails of other series), "More from Bray" industry photos, logos, chatbot icon, tracking pixel.

### series-5b (https://www.bray.com/valves-actuators-controls/control-accessories/switch-boxes/series-5b-switch-box)

Documents:

- `b-1068-s5a-5b-5c-vsm-rev_compressed.pdf` -> **brochure**, en, rev 2022-04-11: 8-page marketing brochure covering Series 5A, 5B and 5C together (features, options); multi-series brochure of one product line -> brochure. Code EN_BR_BRO_CT_1068 S5A-B-C VSM_20220411.
- `en_vac_broc.pdf` -> **brochure**, en, rev 2024-08-13: 4-page brochure about the Bray Europe Valve Automation Centre (UK facility/services); not about this product at all, but it is linked in the family Downloads tab, so kept as brochure. Code EN_VAC_BROC_2024.08.13.
- `valve-status-monitors-series-5ab-om-en-us.pdf` -> **iom_manual**, en, rev 2022: 26-page "Installation, Operation and Maintenance Manual" for 5A/5B. Only "© 2022" printed, no document code date.
- `series-5b_c-vsm-devicenet_halfsize-compressed.pdf` -> **iom_manual**, en, rev 2019-03-21: 16-page IOM for the 5B/5C DeviceNet communication module (wiring, network setup, EDS) -> iom_manual (protocol IOM rule). Code IOM-S5B VSM COMM PRO_DeviceNet_EL_03_21_2019.
- `series-5b_c-vsm-profibus_halfsize.pdf` -> **iom_manual**, en, rev 2019-03-21: 12-page IOM for the 5B/5C Profibus DP module -> iom_manual. Code IOM-S5B VSM COMM PRO_Profibus DP_EL_03_21_2019.
- `en_br_iom_ct_s5a_5b-is_halfsize.pdf` -> **iom_manual**, en, rev 2022-12-22: 11-page IOM for the intrinsically safe 5A/5B. Code ..._IOM_CT_S5A_5B I.S._Halfsize_20221222.
- `series-5b_c-vsm-as-iconnect_halfsize.pdf` -> **iom_manual**, en, rev 2019-03-14: 12-page IOM for the 5B/5C AS-i module -> iom_manual. Code IOM-S5B VSM COMM PRO_ASi_EL_03_14_2019.
- EXCLUDED `s5b_s5c-devicenet.zip` (Software): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- EXCLUDED `s5b_s5c-profibus-dp.zip` (Software): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- `hazardous-location-products.pdf` -> **other_doc**, en, rev 2020-03: 1-page reference chart: NEC/ATEX hazardous-area classes plus which Bray series carry which rating; no ordering data, not product-specific -> other_doc. Code DG_1078_EL_CTRLS_HAZ_LOC_2020_03.
- `intriniscally-safe-product-selection.pdf` -> **catalog**, en, rev 2020-06: 8-page "Selection Guide - Intrinsically Safe Packages": multi-product packages (VSM, sensors, solenoids, barriers) with part numbers -> catalog. Code B-1079_EL_IS_GUIDE_2020-06.
- `en_sm_1007_5-abc-vsm_safety-manual.pdf` -> **iom_manual**, en, rev 2025-04-23: 13-page SIL safety manual for 5A/5B/5C: installation & commissioning, operating & maintenance, proof test, failure rates, start-up checklist -> iom_manual (SIL safety manual rule, see unclear cases). Code ..._Safety Manual_20250423.
- EXCLUDED `s5a_s5b-step-files.zip` (STEP Files): not a PDF (zip); STEP CAD / fieldbus EDS-GSD software is outside this documents-only re-label.
- `tm-1093_5bc_vsm_commpro.pdf` -> **spec_sheet**, en, rev 2020-10: 2-page technical data sheet for the 5B/C CommPro communication option (dimensions, enclosure material, wire gauge, temperature rating, protocols) -> spec_sheet (product option of this family). "Rev. 10_2020", code TM-1093_..._10.
- `tm-1091_5b_aluminum.pdf` -> **spec_sheet**, en, rev 2022-10-14: 2-page technical data sheet for the 5B aluminum VSM. Code TM-1091_5B_aluminum_20221014.
- EXCLUDED site-wide nav-menu PDFs (Criminal Finance Act statement, REACH declaration): site chrome on every page, not in the Downloads tab.

Images:

- `2025_s5b_92-93_mccannalok-s40_41_8in_homehero_.webp` 1809x1416 -> **product_photo**: Banner slide 1 / Description image: VSM on actuator, 1809x1416 (same file in both places).
- `2025_s5b_exp_01-copy.webp` 2000x2000 -> **product_photo**: Banner slide 2: VSM alone, 2000x2000.
- `2025_s5b-topstemsea1cut180logo2.webp` 2000x1600 -> **product_photo**: Banner slide 3: clean cutaway render 2000x1600. The Features-section image s5b-topstemsea1cut180logo2-min.webp (1200x960) is the same cutaway with letter callouts added -> smaller rendition of a kept view, dropped.
- EXCLUDED: related-product slider cards ("Card Image" thumbnails of other series), "More from Bray" industry photos, logos, chatbot icon, tracking pixel.

### series-1b (https://www.bray.com/valves-actuators-controls/ball-valves/trunnion-mounted-valves/trunnion-mounted-ball-valve)

Documents:

- `en_sds_hipps_trilok_trunnion.pdf` -> **brochure**, en, rev 2026-05-27: 2-page "HIPPS-compliant fast-acting valve solutions" sheet: application/solution marketing covering Tri Lok butterfly valves and Series 1B, no product data table -> brochure despite the "Sales Data Sheet" label. Code EN_SDS_HIPPS_TriLok_Trunnion_20260527.
- `en_f-2811_trunnion-mbvalve_web.pdf` -> **brochure**, en, rev 2026-07-10: 8-page Series 1B product brochure: features & benefits, design/standards, materials, dimension tables. Single family, mixes marketing and data -> brochure (site label and layout). Code EN_F-2811_Trunnion MBValve_20260710.
- `en-iom-trunnion.pdf` -> **iom_manual**, en, rev 2026-01-28: 32-page IOM for trunnion mounted ball valves. Code EN_IOM_Trunnion_20260128.
- `iom_tmbv_cast-steel.pdf` -> **iom_manual**, en, rev 2026-01-28: 33-page IOM for cast-steel trunnion ball valves. Code EN_IOM_Trunnion Cast Steel_20260128.
- `en_sm_series-1b-tmbv.pdf` -> **iom_manual**, en, rev 2023-08-03: 9-page Functional Safety Manual (IEC 61508/61511): safety function, installation, proof testing, failure data -> iom_manual (SIL rule). Code EN_SM_Series 1B TMBV_20230803.
- EXCLUDED site-wide nav-menu PDFs (Criminal Finance Act statement, REACH declaration): site chrome on every page, not in the Downloads tab.

Images:

- `trunnion_12in_with_s98-2_homehero_2.webp` 4278x1416 -> **product_photo**: Hero: 12in valve with S98 actuator. Description-tab original 4278x1416 is the fuller view; banner "-copy" 2000x1302 is a crop of it -> dropped.
- `trunnion-6in_01-copy.webp` 2000x2000 -> **product_photo**: Banner slide 2: bare 6in valve, 2000x2000 (no un-suffixed original, 404).
- EXCLUDED: related-product slider cards ("Card Image" thumbnails of other series), "More from Bray" industry photos, logos, chatbot icon, tracking pixel.
## Unclear SPEC 4 / SPEC 5 cases (decision | proposed SPEC wording)

1. **"Technical Sales Manual" / "Technical Manual" (TM-1090, TM-1091, TM-1093, TM-1095 and the duplicate series-5a technical-manual URL).** These are 2-page data sheets, not manuals. | spec_sheet | "Classify by content: a short (1-4 page) document whose body is technical data, ratings, materials or dimensions of the family is spec_sheet whatever the site calls it (Technical Sales Manual, Technical Manual, Sales Data Sheet)."
2. **Same content at two URLs** (tm-1090_5a_aluminum.pdf and series-5a-valve-status-monitor-technical-manual.pdf, same document code, 2-byte difference). | both listed as separate documents with their own sha256 | "Every distinct linked PDF URL is its own document, even if the content duplicates another one."
3. **Safety / SIL manuals** (en_sm_1007 5A/5B/5C safety manual, en_sm_series-1b-tmbv functional safety manual). They cover installation, operation, proof testing and failure-rate data for using the product in a SIL loop. SPEC 5 has no safety-manual type. | iom_manual | "Safety (SIL / functional-safety) manuals are iom_manual; a SIL/IEC 61508 certificate issued by a third party is certificate."
4. **Communication-protocol documents** (DeviceNet, Profibus DP, AS-i IOMs: iom_manual; TM-1093 CommPro data sheet: spec_sheet). Fieldbus EDS/GSD software and STEP files are zips, not PDFs. | iom_manual / spec_sheet by content; zips excluded from `documents` | "Protocol/option module manuals are iom_manual and their data sheets spec_sheet when the option belongs to the family; software/configuration files (EDS, GSD, firmware) are not documents."
5. **Selection / reference guides.** IS package selection guide (multi-product, part numbers) -> catalog; hazardous-location chart (classification education plus a product/rating matrix, no ordering data) -> other_doc. | catalog when it lists several products with part numbers / ordering data; otherwise other_doc | "A selection guide that lists several products with ordering data is catalog; a reference chart without ordering data is other_doc."
6. **Multi-product brochures / overviews.** b-1068 (5A+5B+5C, one product line, marketing) -> brochure; en_b-1100 (16-page overview of ~14 actuator/control series with spec blocks) -> catalog; en_vac_broc (Valve Automation Centre services brochure, unrelated to the product) -> brochure, kept because it is linked in the family Downloads tab. | as stated | "Marketing piece for one family or one product line = brochure; an overview of a manufacturer's product range across several lines = catalog. Off-topic PDFs linked in a family's documents tab are still recorded with their content type."
7. **Brochure vs spec sheet when labels and content disagree.** SRH "Product Brochure" (F-2810, 2015) is a data sheet -> spec_sheet; HIPPS "Sales Data Sheet" is application marketing for two product lines -> brochure; Series 1B F-2811 brochure (features + materials + dimension tables, 8 pages) -> brochure. | content wins over the site label; a long document mixing marketing with data stays brochure | "If a document is mainly features/benefits marketing and longer than 4 pages it is brochure even if it contains data tables."
8. **Recommended (guide) specification** (en_rss_s70_actuator, "The actuator shall ..."). SPEC 5 has no guide-spec type; also covers Series 70 in general, not only 70-HAZ. | spec_sheet | "Architect/engineer guide specifications are spec_sheet."
9. **Revision date forms.** "Rev. 10 2022" (= October, matches code ..._20221014) but "Rev. 3 2022" on TM-1095 is a revision number (code ..._20221121). | use the footer document-code date when present, else printed month/year, else © year | "Prefer the dated document code; treat 'Rev. N YYYY' as a revision number unless a code date confirms the month."
10. **Cutaways with letter callouts** (5A series5a-cutaway-1-min, 5B Resin 5b-lr-min): the product render dominates; markers are single letters, the legend is page HTML. | product_photo | "A cutaway/render with only short markers (letters/numbers) is product_photo; it is an infographic only when text blocks/feature copy are inside the image."
11. **Same cutaway with and without callouts** (5B: clean 2000x1600 banner vs 1200x960 Features image with markers). | keep the clean, larger one only | "Annotated copy of a kept view = same view, drop it."
12. **Composite option photo** (s5a-s5b-indicators-min.png, several indicator-colour versions in one image, on the 5B Resin page). | product_photo | "A collage showing product options without text is product_photo."
13. **Hero banner vs wide original** (Series 1B 4278x1416 original vs 2000x1302 crop; 5A 0100.webp original found by removing the `5a--mobile/` folder). | keep the un-resized original as the fuller view | (covered by SPEC 4 "fuller view"; noted for consistency).
14. **Images below 600 px with no larger rendition** (SRH: both only 600x600). | kept (>= 300 px) | none needed.
